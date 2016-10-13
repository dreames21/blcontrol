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

    def change_unit(self, _):
        self.motorsel.selection_clear()
        motname = self.motorsel.get()
        if self.stageio.motors[motname].travel: #has finite travel = is linear stage
            self.stepunit.set(' mm')
        else:
            self.stepunit.set(' deg')


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


class SettingsFrame(FloatValFrame):
    def __init__(self, parent, sio, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.sio = sio
        self.make_widgets()
        
    def make_widgets(self):
        title = ttk.Label(self, text='Scan Settings', font='TkHeadingFont', anchor=CENTER)
        title.grid(row=0, column=0, pady=7, sticky=W+E)
                
        roiframe = ttk.Frame(self)
        ttk.Label(roiframe, text='ROI: ').pack(side=LEFT)
        self.roistart = ttk.Entry(roiframe, width=4, validate='key',
                                  validatecommand=self.vcmd)
        self.roistart.pack(side=LEFT)
        ttk.Label(roiframe, text=' to ').pack(side=LEFT)
        self.roiend = ttk.Entry(roiframe, width=4, validate='key',
                                validatecommand=self.vcmd)
        self.roiend.pack(side=LEFT)
        ttk.Label(roiframe, text=' keV').pack(side=LEFT)
        roiframe.grid(row=1, column=0, pady=3, padx=5)

        scantypeframe = ttk.Frame(self)
        ttk.Label(scantypeframe, text='Scan Type: ').pack(side=LEFT)
        self.scantype = StringVar()
        self.scantype.trace('w', self.change_scan_type)
        scantypes = ['Single Spectrum', 'Linear Scan', 'Grid Scan']
        scansel = ttk.Combobox(scantypeframe, values=scantypes, width=13,
                               textvar=self.scantype, state='readonly')
        scansel.bind('<<ComboboxSelected>>', lambda x: scansel.selection_clear())
        scansel.pack(side=LEFT)
        scantypeframe.grid(row=2, column=0, pady=5, padx=5)

        self.curr_scan = ttk.Frame(self)
        self.curr_scan.grid(row=3, column=0, pady=3, padx=5, sticky='nswe')
        self.curr_scan.config(borderwidth=1, relief=SUNKEN)
        self.curr_scan.rowconfigure(0, weight=1)
        self.rowconfigure(3, minsize=115)
        self.gridset = GridScanSettings(self.curr_scan)
        self.linset = LinearScanSettings(self.curr_scan, self.sio)
        self.specset = SpectrumSettings(self.curr_scan)
        self.scantype.set('Single Spectrum')

        buttonframe = ttk.Frame(self)
        ttk.Button(buttonframe, text='Start', command=self.start_scan).pack(
            side=LEFT)
        ttk.Button(buttonframe, text='Stop', command=self.stop_scan).pack(
            side=RIGHT)
        buttonframe.grid(row=4, column=0, pady=3, padx=5)

        self.columnconfigure(0, weight=1)
        for r in (0,3,4):
            self.rowconfigure(r, weight=1)

    def change_scan_type(self, *args):
        value = self.scantype.get()
        for child in self.curr_scan.winfo_children():
            child.grid_forget()
        if value == 'Single Spectrum':
            newscan = self.specset
        elif value == 'Linear Scan':
            newscan = self.linset
        elif value == 'Grid Scan':
            newscan = self.gridset
        newscan.grid(row=0, column=0, pady=3, padx=5)

    def start_scan(self):
        pass

    def stop_scan(self):
        pass
    
