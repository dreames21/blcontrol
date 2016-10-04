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

class BeamlineGUI(Tk):
    def __init__(self, config, **options):
        Tk.__init__(self, **options)
        self.sio = StageIO(config)
        self.det = FakeDet()
        self.motorwidget = MotorFrame(self, self.sio)
        self.motorwidget.pack(side=LEFT, fill=BOTH, expand=1)
        self.det_status_widget = DetectorStatus(self, self.det)
        self.det_status_widget.pack(side=RIGHT, fill=BOTH, expand=1)
        for child in self.winfo_children():
            child.config(borderwidth=2, relief=GROOVE)
        self.protocol('WM_DELETE_WINDOW', self.terminate)
        self.wm_title('GBeamline Control')

    def terminate(self):
        """Cancel all queue-checking loops before closing window"""
        self.motorwidget.cancel_loops()
        self.destroy()

    def report_callback_exception(self, *args):
        """Displays a dialog window with traceback when exception is raised."""
        err = traceback.format_exception(*args)
        messagebox.showerror('Exception', err)


class FakeDet(object):
    """Representation of a detector with dummy data for testing."""
    def get_status(self):
        import random
        return {'accumulation time': 30.0,
                'real time': 33.0,
                'MCA enabled': True,
                'slow count': 45678,
                'fast count': 54322,
                'detector temperature (K)': round(219.5 + random.random(), 1),
                'board temperature (C)': round(35.0 + random.random(), 1)
                }
    def get_setting(self, *args):
        return ['PRET=30.0', 'MCAC=2048', 'THSL=8.034', 'THFA=113',
                'GAIN=12.045', 'TPEA=3.200', 'TECS=220.0']
