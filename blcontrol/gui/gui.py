import sys
#import traceback
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
import ConfigParser
import os
from stages.stageio import StageIO
from detector.dp5io import DP5Device
from motor_widget import MotorFrame
from det_status import DetectorStatus
from scancontrol import ScanController
from menu_bar import BLMenuBar

class BeamlineGUI(Tk):
    def __init__(self, config, **options):
        Tk.__init__(self, **options)
        self.config = config
        self.sio = StageIO(config)
        self.det = DP5Device(config)
        self.make_widgets()
        
    def make_widgets(self):
        #self.option_add('*tearOff', FALSE)
        #self.menubar = BLMenuBar(self)
        #self['menu'] = self.menubar
        
        self.det_status_widget = DetectorStatus(self, self.det)
        self.det_status_widget.grid(row=0, column=2, sticky='nsew')
        
        self.motorwidget = MotorFrame(self, self.sio)
        self.motorwidget.grid(row=1, column=2, sticky='nsew')
        
        self.scancontrol = ScanController(self, self.det, self.sio)
        self.scancontrol.grid(row=0, column=0, columnspan=2, rowspan=2, sticky='nsew')
        
        for child in self.winfo_children():
            child.config(borderwidth=2, relief=GROOVE)
        for r in range(0,3):
            self.rowconfigure(r, weight=1)
        for c in range(0,3):
            self.columnconfigure(c, weight=1)
        self.protocol('WM_DELETE_WINDOW', self.terminate)
        self.wm_title('GBeamline Control')

    def terminate(self):
        """Cancel all queue-checking loops before closing window"""
        self.motorwidget.cancel_loops()
        if self.det.is_connected:
            self.det.disable_mca()
        self.destroy()
        
    def report_callback_exception(self, exc, val, tb):
        """Displays a dialog window with traceback when exception is raised."""
        #err = traceback.format_exception(*args)
        messagebox.showerror('Exception', message=str(val))

module_dir = os.path.dirname(__file__)
cfg_full_path = os.path.join(module_dir, '..','..','config','blconf.txt')

def load_conf_file(conf_path=cfg_full_path):
    config = ConfigParser.SafeConfigParser()
    config.read(conf_path)
    return config


