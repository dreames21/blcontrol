import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
from float_entry import FloatEntry
from detector.exceptions import DeviceError

SETTINGS = ['GAIN', 'TPEA', 'THSL', 'THFA', 'TECS']

class BasicSettingsFrame(ttk.Frame):
    def __init__(self, parent, det, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.det = det
        self.variables = {setting: StringVar() for setting in SETTINGS}
        self.make_widgets()

    def make_widgets(self):
        self.reset_values()
        title = ttk.Label(self, text="Basic", font='TkHeadingFont')
        title.grid(column=0, row=0, columnspan=3, pady=7)
        ttk.Label(self, text='Gain: ').grid(row=1, column=0, sticky=E)
        FloatEntry(self, textvar=self.variables['GAIN'], width=7).grid(row=1,
            column=1, pady=2)
        
        ttk.Label(self, text='Peaking time (us): ').grid(row=2, column=0,
            sticky=E)
        FloatEntry(self, textvar=self.variables['TPEA'], width=7).grid(row=2,
            column=1, pady=2)

        ttk.Label(self, text='Slow threshold (%): ').grid(row=3, column=0,
            sticky=E)
        FloatEntry(self, textvar=self.variables['THSL'], width=7).grid(row=3,
            column=1, pady=2)

        ttk.Label(self, text='Fast threshold: ').grid(row=4, column=0, sticky=E)
        FloatEntry(self, textvar=self.variables['THFA'], width=7).grid(row=4,
            column=1, pady=2)

        ttk.Label(self, text='TEC set point (K): ').grid(row=5, column=0,
            sticky=E)
        FloatEntry(self, textvar=self.variables['TECS'], width=7).grid(row=5,
            column=1, pady=2)

        ttk.Button(self, text='Reset', command=self.reset_values).grid(row=7, 
            column=0)
        ttk.Button(self, text='Apply', command=self.send_values).grid(row=7,
            column=1, pady=7, padx=(0,4))

    def reset_values(self):
        current = self.det.get_settings_dict(SETTINGS)
        for string in current:
            self.variables[string].set(current[string])

    def send_values(self):
        settings_dict = {}
        for setting in SETTINGS:
            value = self.variables[setting].get()
            settings_dict[setting] = value
        try:
            self.det.set_settings_dict(settings_dict)
        except DeviceError as e:
            messagebox.showerror(title='Device Error', message=e)
            self.master.lift()
        self.reset_values()


class AdvancedSettingsFrame(ttk.Frame):
    def __init__(self, parent, det, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.det = det
        self.make_widgets()

    def make_widgets(self):
        title = ttk.Label(self, text='Advanced', font='TkHeadingFont')
        title.pack(side=TOP, pady=7)

        pvalcmd = (self.register(self.param_validate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        
        ef = ttk.Frame(self)
        ef.pack(side=TOP, pady=20)
        self.param_entry = ttk.Entry(ef, width=5, validatecommand=pvalcmd,
                                     validate='key')
        self.param_entry.pack(side=LEFT)
        ttk.Label(ef, text=' = ').pack(side=LEFT)
        self.val_entry = ttk.Entry(ef, width=5)
        self.val_entry.pack(side=LEFT)

        bf = ttk.Frame(self)
        bf.pack(side=BOTTOM, pady=7)
        sb = ttk.Button(bf, text='Set', command=self.send_value)
        sb.pack(side=LEFT, padx=4)
        gb = ttk.Button(bf, text='Get', command=self.get_value)
        gb.pack(side=LEFT, padx=4)

    def param_validate(self, d, i, P, s, S, v, V, W):
        return (P=='' or P.isalnum()) and len(P) < 5

    def send_value(self):
        paramname = self.param_entry.get()
        value = self.val_entry.get()
        try:
            self.det.set_setting(paramname, value)
        except DeviceError as e:
            message = 'Bad parameter: {0} = {1}'.format(paramname, value)
            messagebox.showerror(title='Device Error', message=message)
            self.master.lift()

    def get_value(self):
        paramname = self.param_entry.get()
        value = self.det.get_setting(paramname)
        self.val_entry.delete(0, END)
        self.val_entry.insert(0, value)
        
    
class DetSettingsWindow(Toplevel):
    def __init__(self, parent, det, **options):
        Toplevel.__init__(self, parent, **options)
        self.det = det
        self.make_widgets()

    def make_widgets(self):
        tf = ttk.Frame(self, borderwidth=2, relief=GROOVE)
        ttk.Label(tf, text='Detector Settings', font='TkHeadingFont').pack(side=TOP, pady=7)
        tf.pack(side=TOP, expand=True, fill=BOTH)
        basf = BasicSettingsFrame(self, self.det, borderwidth=2, relief=GROOVE)
        basf.pack(side=LEFT, expand=True, fill=BOTH)
        advf = AdvancedSettingsFrame(self, self.det, borderwidth=2, relief=GROOVE)
        advf.pack(side=LEFT, expand=True, fill=BOTH)
