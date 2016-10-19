import copy
import numpy as np
import Queue
import sys
import threading
import time
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

from blcontrol.gui.scan_settings import SettingsFrame
from blcontrol.gui.plot_windows import SpectrumDisplay, ScanDisplay
from blcontrol.scans import Spectrum, LinearScan, GridScan
from blcontrol.utils import SingleValQueue

#TODO: -change how spectrum thread gets detector settings
#      -implement saving data to a file
#      -implement dialog to edit detector settings (and maybe other settings?
#           like number of mca chans used in a linear/grid scan?)

class ScanController(ttk.Frame):
    def __init__(self, parent, det, sio, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.det = det
        self.sio = sio
        self.stopper = threading.Event()
        self.make_widgets()
        self.check_is_running()

    def make_widgets(self):
        self.scanplot = ScanDisplay(self)
        self.scanplot.pack(side=BOTTOM, fill=BOTH, expand=1)
        self.specplot = SpectrumDisplay(self)
        self.specplot.pack(side=RIGHT, fill=BOTH, expand=1)
        self.specplot.set_energies(self.det.get_energies())
        self.settings = SettingsFrame(self, self.sio)
        self.settings.pack(side=LEFT, fill=BOTH, expand=1)
        self.settings.startbutt.config(command=self.start_scan)
        self.settings.stopbutt.config(command=self.stop_scan)

    def start_scan(self):
        params = self.settings.get_scan_params()
        scantype = params['type']
        if scantype == 'spectrum':
            self.start_spectrum_acq(params)
        elif scantype == 'linear':
            self.start_linear_scan(params)
        elif scantype == 'grid':
            self.start_grid_scan(params)
        self.settings.startbutt.config(state=DISABLED)
        self.check_is_running()

    def stop_scan(self):
        self.sio.stop_all()
        self.det.disable_mca()
        self.stopper.set()

    def check_is_running(self):
        if self.stopper.is_set():
            self.settings.startbutt.config(state=NORMAL)
            self.after(500, self.specplot.stop_plot())
            self.after(500, self.scanplot.stop_plot())
        else:
            self.checker = self.after(200, self.check_is_running)
        
    def start_spectrum_acq(self, params):
        num_chans = params['chans']
        self.det.set_setting('MCAC', num_chans)
        samplename = params['samplename']
        self.specplot.ax.set_title(samplename)
        acctime = params['acctime']
        roi = params['roi']
        specqueue = SingleValQueue()
        thread = SpectrumAcqThread(self.det, acctime, specqueue)
        self.stopper = thread.finished
        thread.start()
        self.specplot.plot(specqueue, roi)

    def start_linear_scan(self, params):
        self.det.set_setting('MCAC', 256)
        motor = self.sio.motors[params['motorname']]
        start, end = params['start'], params['end']
        if not (motor.is_in_range(start) and motor.is_in_range(end)):
            errmsg = "Scan outside of limits of travel of motor {0}".format(
                motor.name)
            messagebox.showerror('Scan Limits', errmsg)
            return
        stepsize = params['stepsize']
        if start > end:
            stepsize*= -1
        numpts = int((end - start)/stepsize + 1)
        locs = [start + stepsize*i for i in range(numpts)]
        thread = LinearScanThread(self.det, motor, params['acctime'], locs)
        self.stopper = thread.stopper
        thread.start()
        self.specplot.plot(thread.specqueue, params['roi'])
        unit = self.settings.linset.stepunit.get().strip()
        self.scanplot.pre_plot_lin(locs, params['samplename'], unit)
        self.scanplot.plot_lin(thread.plotqueue, params['roi'])

    def start_grid_scan(self, params):
        dx = self.sio.motors['dx']
        dy = self.sio.motors['dy']
        stepsize = params['stepsize']
        gridsize = params['gridsize']
        xlocs = [dx.pos - (gridsize-1)*stepsize/2.0 + i*stepsize for i in
                 range(gridsize)]
        ylocs = [dy.pos - (gridsize-1)*stepsize/2.0 + i*stepsize for i in
                 range(gridsize)]
        if not (dy.is_in_range(ylocs[0]) and dy.is_in_range(ylocs[-1])):
            errmsg = "Scan outside of limits of travel of dy"
            messagebox.showerror('Scan Limits', errmsg)
            self.stopper.set()
            return
        if not (dx.is_in_range(xlocs[0]) and dx.is_in_range(xlocs[-1])):
            errmsg = "Scan outside of limits of travel of dx"
            messagebox.showerror('Scan Limits', errmsg)
            self.stopper.set()
            return
        thread = GridScanThread(self.det, self.sio, xlocs, ylocs,
                                params['acctime'])
        self.stopper = thread.stopper
        thread.start()
        self.specplot.plot(thread.specqueue, params['roi'])
        self.scanplot.pre_plot_grid(xlocs, ylocs)
        self.scanplot.plot_grid(thread.plotqueue, params['roi'])


class SpectrumAcqThread(threading.Thread):
    def __init__(self, det, acctime, plotqueue):
        super(SpectrumAcqThread, self).__init__()
        self.det = det
        self.acctime = acctime
        self.plotqueue = plotqueue
        self.spec = Spectrum([], self.det.get_energies(), {}, '')
        self.finished = threading.Event()
        self.daemon = True

    def run(self):
        self.spec.timestamp = time.asctime()
        self.det.begin_acq(self.acctime)
        mca_enabled = True
        while mca_enabled:
            self.spec.counts, self.spec.status = self.det.get_spectrum()
            mca_enabled = self.spec.status['MCA enabled']
            if not mca_enabled:
                settings = self.det.get_setting(['PRET', 'MCAC', 'THSL', 'THFA',
                    'GAIN', 'TPEA', 'TECS'])
                self.spec.settings = settings
                self.finished.set()
            self.plotqueue.put(copy.deepcopy(self.spec))
            time.sleep(0.5)

    def get_final_value(self):
        self.finished.wait()
        return self.spec


class LinearScanThread(threading.Thread):
    def __init__(self, det, motor, acctime, locs):
        super(LinearScanThread, self).__init__()
        self.det = det
        self.motor = motor
        self.acctime = acctime
        self.locs = locs
        self.stopper = threading.Event()
        self.plotqueue = Queue.Queue()
        self.specqueue = SingleValQueue()
        self.scan_data = None
        self.daemon = True

    def run(self):
        self.scan_data = LinearScan([], [], self.motor.name, time.asctime())
        for l in self.locs:
            if not self.stopper.is_set():
                self.motor.start_move(l)
                self.motor.finish_move()
                specthread = SpectrumAcqThread(self.det, self.acctime,
                                               self.specqueue)
                specthread.start()
                spectrum = specthread.get_final_value()
                self.scan_data.locations.append(l)
                self.scan_data.spectra.append(spectrum)
                self.plotqueue.put(copy.deepcopy(self.scan_data))
        self.stopper.set()

    def get_final_value(self):
        self.stopper.wait()
        return self.scan_data


class GridScanThread(threading.Thread):
    def __init__(self, det, sio, xlocs, ylocs, acctime):
        self.det = det
        self.acctime = acctime
        self.xlocs = xlocs
        self.ylocs = ylocs
        self.dx = sio.motors['dx']
        self.dy = sio.motors['dy']
        self.stopper = threading.Event()
        self.plotqueue = Queue.Queue()
        self.specqueue = SingleValQueue()
        spectra = np.empty((len(xlocs), len(ylocs)), dtype=object)
        self.scan_data = GridScan(xlocs, ylocs, spectra, time.asctime())
        super(GridScanThread, self).__init__()
        self.daemon = True

    def run(self):
        spectra = np.empty((len(self.xlocs), len(self.ylocs)), dtype=object)
        self.scan_data = GridScan(self.xlocs, self.ylocs, spectra,
                                  time.asctime())
        xlocscopy = list(self.xlocs)
        self.plotqueue.put(copy.deepcopy(self.scan_data))
        for y in self.ylocs:
            for x in xlocscopy:
                if not self.stopper.is_set():
                    self.dy.start_move(y)
                    self.dx.start_move(x)
                    self.dy.finish_move()
                    self.dx.finish_move()
                    specthread = SpectrumAcqThread(self.det, self.acctime,
                                                   self.specqueue)
                    specthread.start()
                    spectrum = specthread.get_final_value()
                    i, j = self.xlocs.index(x), self.ylocs.index(y)
                    self.scan_data.spectra[i, j] = spectrum
                    self.plotqueue.put(copy.deepcopy(self.scan_data))
            xlocscopy.reverse()
        time.sleep(0.25)
        self.stopper.set()
        
    def get_final_value(self):
        self.stopper.wait()
        return self.scan_data
