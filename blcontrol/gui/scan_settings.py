import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
from blcontrol.gui.misc import FloatValFrame

class LinearScanSettings(FloatValFrame):
    def __init__(self, parent, stageio, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.stageio = stageio
        self.make_widgets()

    def make_widgets(self):
        motselframe = ttk.Frame(self)
        ttk.Label(motselframe, text='Motor: ').pack(side=LEFT)
        self.motorsel = ttk.Combobox(motselframe, width=3, state='readonly',
                                     values=self.stageio.motors.keys())
        self.motorsel.bind('<<ComboboxSelected>>', self.change_unit)
        self.motorsel.pack(side=LEFT)
        motselframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        self.acctime = ttk.Entry(acctimeframe, width=5, validate='key',
                                 validatecommand=self.vcmd)
        self.acctime.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' s/pt').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        stepsizeframe = ttk.Frame(self)
        ttk.Label(stepsizeframe, text='Step size: ').pack(side=LEFT)
        self.stepsize = ttk.Entry(stepsizeframe, width=5, validate='key',
                                  validatecommand=self.vcmd)
        self.stepsize.pack(side=LEFT)
        self.stepunit = StringVar(value=' mm')
        lab = ttk.Label(stepsizeframe, textvariable=self.stepunit)
        lab.pack(side=LEFT)
        stepsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        extframe = ttk.Frame(self)
        ttk.Label(extframe, text='Extent: ').pack(side=LEFT)
        self.start = ttk.Entry(extframe, width=4, validate='key',
                                  validatecommand=self.vcmd)
        self.start.pack(side=LEFT)
        ttk.Label(extframe, text=' to ').pack(side=LEFT)
        self.end = ttk.Entry(extframe, width=4, validate='key',
                                validatecommand=self.vcmd)
        self.end.pack(side=LEFT)
        lab2 = ttk.Label(extframe, textvariable=self.stepunit)
        lab2.pack(side=LEFT)
        extframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        ttk.Button(self, text='Start', command=self.start_scan).pack(side=LEFT,
                                                                     pady=3)
        ttk.Button(self, text='Stop', command=self.stop_scan).pack(side=RIGHT)

    def change_unit(self, _):
        self.motorsel.selection_clear()
        motname = self.motorsel.get()
        if self.stageio.motors[motname].travel: #has finite travel = is linear stage
            self.stepunit.set(' mm')
        else:
            self.stepunit.set(' deg')

    def start_scan(self):
        pass

    def stop_scan(self):
        pass

class GridScanSettings(FloatValFrame):
    def __init__(self, parent, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.make_widgets()

    def make_widgets(self):
        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        self.acctime = ttk.Entry(acctimeframe, width=5, validate='key',
                                 validatecommand=self.vcmd)
        self.acctime.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' s/pt').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        stepsizeframe = ttk.Frame(self)
        ttk.Label(stepsizeframe, text='Step size: ').pack(side=LEFT)
        self.stepsize = ttk.Entry(stepsizeframe, width=5, validate='key',
                                  validatecommand=self.vcmd)
        self.stepsize.pack(side=LEFT)
        ttk.Label(stepsizeframe, text=' mm').pack(side=LEFT)
        stepsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        gridsizeframe = ttk.Frame(self)
        vals = ['{0}x{0}'.format(i).center(6) for i in range(3, 13, 2)]
        self.gridvals = {v: int(v.split('x')[0]) for v in vals}
        ttk.Label(gridsizeframe, text='Grid size: ').pack(side=LEFT)
        self.gridsizesel = ttk.Combobox(gridsizeframe, values=vals, width=5,
                                        state='readonly')
        self.gridsizesel.bind('<<ComboboxSelected>>',
                           lambda x: self.gridsizesel.selection_clear())
        self.gridsizesel.pack(side=LEFT)
        gridsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        ttk.Button(self, text='Start', command=self.start_scan).pack(side=LEFT,
                                                                     pady=3)
        ttk.Button(self, text='Stop', command=self.stop_scan).pack(side=RIGHT)

    def start_scan(self):
        pass

    def stop_scan(self):
        pass

class SpectrumSettings(FloatValFrame):
    def __init__(self, parent, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.make_widgets()

    def make_widgets(self):
        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        self.acctime = ttk.Entry(acctimeframe, width=5, validate='key',
                                 validatecommand=self.vcmd)
        self.acctime.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' sec').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        chanframe = ttk.Frame(self)
        ttk.Label(chanframe, text='MCA Channels: ').pack(side=LEFT)
        vals = [256, 512, 1024, 2048, 4096, 8192]
        self.chansel = ttk.Combobox(chanframe, values=vals, state='readonly',
                                    width=4)
        self.chansel.bind('<<ComboboxSelected>>',
                          lambda x: self.chansel.selection_clear())
        self.chansel.pack(side=LEFT)
        chanframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        ttk.Button(self, text='Start', command=self.start_scan).pack(side=LEFT,
                                                                     pady=3)
        ttk.Button(self, text='Stop', command=self.stop_scan).pack(side=RIGHT)

    def start_scan(self):
        pass

    def stop_scan(self):
        pass

class SettingsFrame(ttk.Frame):
    def __init__(self, parent, sio, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.sio = sio
        self.gridset = GridScanSettings(self)
        self.linset = LinearScanSettings(self, self.sio)
        self.specset = SpectrumSettings(self)
        self.make_widgets()
        
    def make_widgets(self):
        
        scanframe = ttk.Frame(self)
        

    
