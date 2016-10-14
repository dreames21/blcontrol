### unfinished!!!!!!!!!!!! ###

import sys
import traceback
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
from blcontrol.stages.stageio import StageIO
from blcontrol.gui.motor_widget import MotorFrame
from blcontrol.gui.det_status import DetectorStatus
from blcontrol.gui.scancontrol import ScanController

from blcontrol.testing import FakeDet

class BeamlineGUI(Tk):
    def __init__(self, config, **options):
        Tk.__init__(self, **options)
        self.sio = StageIO(config)
        self.det = FakeDet()
        self.make_widgets()
        
    def make_widgets(self):
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
        ### should have an 'are you sure' dialog?
        self.motorwidget.cancel_loops()
        self.det.disable_mca()
        self.destroy()

    def report_callback_exception(self, *args):
        """Displays a dialog window with traceback when exception is raised."""
        err = traceback.format_exception(*args)
        messagebox.showerror('Exception', err)
