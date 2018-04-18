import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

# want:
#  -drop down menu to choose motor
#  -zero position ??
#  -command num = data val
#  -get + set buttons (like det settings)

class StageSettingsWindow(Toplevel):
    def __init__(self, parent, sio, **options):
        Toplevel.__init__(self, parent, **options)
        self.sio = sio
        self.make_widgets()

    def make_widgets(self):
        pass
        
