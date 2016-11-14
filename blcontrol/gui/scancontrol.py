import Queue
import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import tkFileDialog as filedialog
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
from blcontrol.gui.scan_settings import SettingsFrame
from blcontrol.gui.plot_windows import SpectrumDisplay, ScanDisplay
from blcontrol.scan_threads import (SpectrumAcqThread, LinearScanThread,
    GridScanThread)

#TODO: implement dialog to edit detector settings (and maybe other settings?
#   like number of mca chans used in a linear/grid scan?)

class ScanController(ttk.Frame):
    """Controls starting/ending scans and plotting."""
    
    def __init__(self, parent, det, sio, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.det = det
        self.sio = sio
        self.last_scan = None
        self.make_widgets()

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
        self.settings.savebutt.config(command=self.save_scan, state=DISABLED)

    def start_scan(self):
        """Start a scan of type indicated in the settings frame."""
        params = self.settings.get_scan_params()
        scantype = params['type']
        if scantype == 'spectrum':
            self.start_spectrum_acq(params)
        elif scantype == 'linear':
            self.start_linear_scan(params)
        elif scantype == 'grid':
            self.start_grid_scan(params)
        self.settings.startbutt.config(state=DISABLED)
        self.settings.savebutt.config(state=DISABLED)

    def stop_scan(self):
        """Stop all motors and scans, and disable the MCA."""
        self.sio.stop_all()
        if self.last_scan:
            self.last_scan.stop()
        self.det.disable_mca()

    def save_scan(self):
        """Export the last scan to a text file."""
        self.last_scan.join()
        data = self.last_scan.data
        filename = filedialog.asksaveasfilename()
        data.export(filename)

    def check_is_running(self):
        """Loop to check whether scan threads are still alive."""
        if self.last_scan.is_alive():
            self.checker = self.after(200, self.check_is_running)
        else:
            self.settings.startbutt.config(state=NORMAL)
            self.settings.savebutt.config(state=NORMAL)
            self.specplot.stop_plot()
            self.scanplot.stop_plot()
            self.after_cancel(self.checker)

    def start_spectrum_acq(self, params):
        """Begin a spectrum acquisition based on settings frame parameters."""
        num_chans = params['chans']
        self.det.set_setting('MCAC', num_chans)
        samplename = params['samplename']
        self.specplot.ax.set_title(samplename)
        acctime = params['acctime']
        roi = params['roi']
        specqueue = Queue.Queue()
        thread = SpectrumAcqThread(self.det, acctime, specqueue)
        self.last_scan = thread
        thread.start()
        self.specplot.plot(specqueue, roi)
        self.check_is_running()

    def start_linear_scan(self, params):
        """Begin a linear scan based on settings frame parameters."""
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
        self.last_scan = thread
        thread.start()
        self.specplot.plot(thread.specqueue, params['roi'])
        unit = self.settings.linset.stepunit.get().strip()
        self.scanplot.pre_plot_lin(locs, params['samplename'], unit)
        self.scanplot.plot_lin(thread.plotqueue, params['roi'])
        self.check_is_running()

    def start_grid_scan(self, params):
        """Begin a grid scan based on settings frame parameters."""
        dx = self.sio.motors['dx']
        dy = self.sio.motors['dy']
        stepsize = params['stepsize']
        gridsize = params['gridsize']
        xlocs = [dx.pos - (gridsize-1)*stepsize/2.0 + i*stepsize for i in
                 range(int(gridsize))]
        ylocs = [dy.pos - (gridsize-1)*stepsize/2.0 + i*stepsize for i in
                 range(int(gridsize))]
        if not (dy.is_in_range(ylocs[0]) and dy.is_in_range(ylocs[-1])):
            errmsg = "Scan outside of limits of travel of dy"
            messagebox.showerror('Scan Limits', errmsg)
            return
        if not (dx.is_in_range(xlocs[0]) and dx.is_in_range(xlocs[-1])):
            errmsg = "Scan outside of limits of travel of dx"
            messagebox.showerror('Scan Limits', errmsg)
            return
        thread = GridScanThread(self.det, self.sio, xlocs, ylocs,
                                params['acctime'])
        self.last_scan = thread
        thread.start()
        self.specplot.plot(thread.specqueue, params['roi'])
        self.scanplot.pre_plot_grid(xlocs, ylocs)
        self.scanplot.plot_grid(thread.plotqueue, params['roi'])
        self.check_is_running()


