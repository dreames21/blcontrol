import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

class FloatEntry(ttk.Entry):
    """Entry that allows values that can be converted to floats."""
    def __init__(self, parent, **options):
        ttk.Entry.__init__(self, parent, **options)
        self.vcmd = (self.register(self.float_validate), '%P')
        self.config(validatecommand=self.vcmd, justify=RIGHT, validate='key')

    def float_validate(self, P):
        """Validation for entries requiring valid floats."""
        allowed = ('', '-', '.')
        if P in allowed:
            return True
        try:
            float(P)
        except ValueError:
            self.bell()
            return False
        else:
            return True
