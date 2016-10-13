import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

class FloatValFrame(ttk.Frame):
    def __init__(self, parent, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.vcmd = (self.register(self.float_validate), '%P')
    
    def float_validate(self, P):
        """Validation for entries requiring valid floats."""
        if P == '':
            return True
        try:
            float(P)
        except ValueError:
            self.bell()
            return False
        else:
            return True
