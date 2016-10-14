import copy
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
            self.specplot.stop_plot()
        else:
            self.checker = self.after(1000, self.check_is_running)
        
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
        self.scanplot.plot(thread.plotqueue, params['roi'])

       
        

    def start_grid_scan(self, params):
        pass


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
        print 'waiting for final spectrum'
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
        self.scan_data = LinearScan([], [], self.motor.name, time.asctime())
        self.daemon = True

    def run(self):
        for l in self.locs:
            if not self.stopper.is_set():
                self.motor.start_move(l)
                self.motor.finish_move()
                specthread = SpectrumAcqThread(self.det, self.acctime,
                                               self.specqueue)
                specthread.start()
                spectrum = specthread.get_final_value()
                print 'got final spectrum'
                self.scan_data.locations.append(l)
                self.scan_data.spectra.append(spectrum)
                self.plotqueue.put(copy.deepcopy(self.scan_data))
        self.stopper.set()

    def get_final_value(self):
        self.stopper.wait()
        return self.scan_data
            
