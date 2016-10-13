import sys
import time
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

from blcontrol.gui.scan_settings import SettingsFrame
from blcontrol.gui.plot_windows import SpectrumDisplay, ScanDisplay

class ScanController(ttk.Frame):
    def __init__(self, parent, det, sio, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.det = det
        self.sio = sio
        self.make_widgets()

    def make_widgets(self):
        self.scanplot = ScanDisplay(self)
        self.scanplot.pack(side=BOTTOM, fill=BOTH, expand=1)
        self.specplot = SpectrumDisplay(self)
        self.specplot.pack(side=RIGHT, fill=BOTH, expand=1)
        self.settings = SettingsFrame(self, self.sio)
        self.settings.pack(side=LEFT, fill=BOTH, expand=1)

    def start_scan(self):
        params = self.settings.get_scan_params()
        scantype = params['type']
        if scantype == 'spectrum':
            self.start_spectrum_acq(params)
        elif scantype == 'linear':
            self.start_linear_scan(params)
        elif scantype == 'grid':
            self.start_grid_scan(params)

    def stop_scan(self):
        self.det.disable_mca()
        self.sio.stop_all()

    def start_spectrum_acq(self, params):
        num_chans = params['chans']
        self.det.set_setting('MCAC', num_chans)
        samplename = params['samplename']
        energies = self.det.get_energies()
        self.specplot.pre_start(samplename, energies)

    def start_linear_scan(self, params):
        pass

    def start_grid_scan(self, params):
        pass

