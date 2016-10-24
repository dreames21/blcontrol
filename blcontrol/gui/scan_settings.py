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
        self.motorname = StringVar()
        self.motorsel = ttk.Combobox(motselframe, width=3, state='readonly',
            textvariable=self.motorname, values=self.stageio.motors.keys())
        self.motorsel.bind('<<ComboboxSelected>>', self.change_unit)
        self.motorsel.pack(side=LEFT)
        motselframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        self.acctime = StringVar()
        accent = ttk.Entry(acctimeframe, width=5, validate='key',
            validatecommand=self.vcmd, textvariable=self.acctime)
        accent.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' s/pt').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        stepsizeframe = ttk.Frame(self)
        ttk.Label(stepsizeframe, text='Step size: ').pack(side=LEFT)
        self.stepsize = StringVar()
        stepent = ttk.Entry(stepsizeframe, width=5, validate='key',
            textvariable=self.stepsize, validatecommand=self.vcmd)
        stepent.pack(side=LEFT)
        self.stepunit = StringVar(value=' mm')
        lab = ttk.Label(stepsizeframe, textvariable=self.stepunit)
        lab.pack(side=LEFT)
        stepsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        extframe = ttk.Frame(self)
        ttk.Label(extframe, text='Extent: ').pack(side=LEFT)
        self.start = StringVar()
        startent = ttk.Entry(extframe, width=4, validate='key',
            textvariable = self.start, validatecommand=self.vcmd)
        startent.pack(side=LEFT)
        ttk.Label(extframe, text=' to ').pack(side=LEFT)
        self.end = StringVar()
        endent = ttk.Entry(extframe, width=4, validate='key',
            textvariable=self.end, validatecommand=self.vcmd)
        endent.pack(side=LEFT)
        lab2 = ttk.Label(extframe, textvariable=self.stepunit)
        lab2.pack(side=LEFT)
        extframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        self.variables = [self.motorname, self.acctime, self.stepsize,
                          self.start, self.end]

    def change_unit(self, _):
        self.motorsel.selection_clear()
        motname = self.motorsel.get()
        if self.stageio.motors[motname].travel: #has finite travel = is linear stage
            self.stepunit.set(' mm')
        else:
            self.stepunit.set(' deg')

    def clear_widgets(self):
        self.motorname.set('')
        self.acctime.set('')
        self.stepsize.set('')
        self.start.set('')
        self.end.set('')

    def get_scan_params(self):
        return {'type'     : 'linear',
                'motorname': self.motorname.get(),
                'acctime'  : float(self.acctime.get()),
                'stepsize' : float(self.stepsize.get()),
                'start'    : float(self.start.get()),
                'end'      : float(self.end.get())
                }

    def is_ready(self):
        return (self.motorname.get() and self.acctime.get() and
                self.stepsize.get() and self.start.get() and self.end.get())


class GridScanSettings(FloatValFrame):
    def __init__(self, parent, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.make_widgets()

    def make_widgets(self):
        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        self.acctime = StringVar()
        accent = ttk.Entry(acctimeframe, width=5, validate='key',
            textvariable = self.acctime, validatecommand=self.vcmd)
        accent.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' s/pt').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        stepsizeframe = ttk.Frame(self)
        ttk.Label(stepsizeframe, text='Step size: ').pack(side=LEFT)
        self.stepsize = StringVar()
        stepent = ttk.Entry(stepsizeframe, width=5, validate='key',
            textvariable=self.stepsize, validatecommand=self.vcmd)
        stepent.pack(side=LEFT)
        ttk.Label(stepsizeframe, text=' mm').pack(side=LEFT)
        stepsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        gridsizeframe = ttk.Frame(self)
        vals = ['{0}x{0}'.format(i).center(6) for i in range(3, 13, 2)]
        ttk.Label(gridsizeframe, text='Grid size: ').pack(side=LEFT)
        self.gridsize = StringVar()
        gridsizesel = ttk.Combobox(gridsizeframe, values=vals, width=5,
            textvariable=self.gridsize, state='readonly')
        gridsizesel.bind('<<ComboboxSelected>>',
                           lambda x: gridsizesel.selection_clear())
        gridsizesel.pack(side=LEFT)
        gridsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        self.variables = [self.acctime, self.stepsize, self.gridsize]

    def clear_widgets(self):
        self.acctime.set('')
        self.stepsize.set('')
        self.gridsize.set('')
        
    def get_scan_params(self):
        return {'type'     : 'grid',
                'acctime'  : float(self.acctime.get()),
                'stepsize' : float(self.stepsize.get()),
                'gridsize' : int(self.gridsize.get().split('x')[0])
                }

    def is_ready(self):
        return (self.acctime.get() and self.stepsize.get()
                and self.gridsize.get())


class SpectrumSettings(FloatValFrame):
    def __init__(self, parent, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.make_widgets()

    def make_widgets(self):
        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        self.acctime = StringVar()
        acctime = ttk.Entry(acctimeframe, width=5, validate='key',
            textvariable=self.acctime, validatecommand=self.vcmd)
        acctime.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' sec').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        chanframe = ttk.Frame(self)
        ttk.Label(chanframe, text='MCA Channels: ').pack(side=LEFT)
        vals = [256, 512, 1024, 2048, 4096, 8192]
        self.chans = StringVar()
        chansel = ttk.Combobox(chanframe, values=vals, state='readonly',
            textvariable=self.chans, width=4)
        chansel.bind('<<ComboboxSelected>>',
                          lambda x: chansel.selection_clear())
        chansel.pack(side=LEFT)
        chanframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        self.variables = [self.acctime, self.chans]

    def clear_widgets(self):
        self.acctime.set('')
        self.chans.set('')

    def get_scan_params(self):
        return {'type'    : 'spectrum',
                'acctime' : float(self.acctime.get()),
                'chans'   : self.chans.get()
                }

    def is_ready(self):
        return self.acctime.get() and self.chans.get()

class SettingsFrame(FloatValFrame):
    def __init__(self, parent, sio, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.sio = sio
        self.make_widgets()
        
    def make_widgets(self):
        title = ttk.Label(self, text='Scan Settings', font='TkHeadingFont',
                          anchor=CENTER)
        title.grid(row=0, column=0, pady=7, sticky=W+E)

        nameframe = ttk.Frame(self)
        ttk.Label(nameframe, text='Sample Name: ').grid(row=0, column=0, pady=3,
                  padx=(5,0))
        self.samplename = ttk.Entry(nameframe)
        self.samplename.grid(row=0, column=1, columnspan=4, padx=(0,5))
        ttk.Label(nameframe, text='ROI: ').grid(row=1, column=0, sticky=E)
        self.roistart = ttk.Entry(nameframe, width=5, validate='key',
                                  validatecommand=self.vcmd)
        self.roistart.grid(row=1, column=1, sticky=W, pady=3)
        ttk.Label(nameframe, text=' to ').grid(row=1, column=2)
        self.roiend = ttk.Entry(nameframe, width=5, validate='key',
                                validatecommand=self.vcmd)
        self.roiend.grid(row=1, column=3)
        ttk.Label(nameframe, text=' keV').grid(row=1, column=4, sticky=E)
        nameframe.grid(row=2, column=0, pady=3, padx=5)

        scantypeframe = ttk.Frame(self)
        ttk.Label(scantypeframe, text='Scan Type: ').pack(side=LEFT)
        self.scantype = StringVar()
        self.scantype.trace('w', self.change_scan_type)
        scantypes = ['Single Spectrum', 'Linear Scan', 'Grid Scan']
        scansel = ttk.Combobox(scantypeframe, values=scantypes, width=13,
                               textvar=self.scantype, state='readonly')
        scansel.bind('<<ComboboxSelected>>', lambda x: scansel.selection_clear())
        scansel.pack(side=LEFT)
        scantypeframe.grid(row=3, column=0, pady=5, padx=5)

        self.paramframe = ttk.Frame(self)
        self.paramframe.grid(row=4, column=0, pady=3, padx=5, sticky='nswe')
        self.paramframe.config(borderwidth=1, relief=SUNKEN)
        self.paramframe.rowconfigure(0, weight=1)
        self.rowconfigure(4, minsize=115)
        self.gridset = GridScanSettings(self.paramframe)
        self.linset = LinearScanSettings(self.paramframe, self.sio)
        self.specset = SpectrumSettings(self.paramframe)
        self.scantype.set('Single Spectrum')
        for var in (self.gridset.variables + self.linset.variables +
                    self.specset.variables):
            var.trace('w', self.check_if_ready)

        buttons = ttk.Frame(self)
        self.startbutt = ttk.Button(buttons, text='Start', state=DISABLED)
        self.startbutt.pack(side=LEFT, expand=1)
        self.stopbutt = ttk.Button(buttons, text='Stop')
        self.stopbutt.pack(side=LEFT, expand=1)
        self.savebutt = ttk.Button(buttons, text='Save Scan')
        self.savebutt.pack(side=RIGHT, expand=1)
        buttons.grid(column=0, row=5, pady=3, padx=5, sticky='nswe')

        self.columnconfigure(0, weight=1)
        for r in (0,3,4):
            self.rowconfigure(r, weight=1)

    def change_scan_type(self, *args):
        value = self.scantype.get()
        for child in self.paramframe.winfo_children():
            child.clear_widgets()
            child.grid_forget()
        if value == 'Single Spectrum':
            self.curr_scan = self.specset
        elif value == 'Linear Scan':
            self.curr_scan = self.linset
        elif value == 'Grid Scan':
            self.curr_scan = self.gridset
        self.curr_scan.grid(row=0, column=0, pady=3, padx=5)

    def get_scan_params(self):
        params = self.curr_scan.get_scan_params()
        roistart = self.roistart.get()
        roiend = self.roiend.get()
        if roistart and roiend:
            roi = (float(self.roistart.get()), float(self.roiend.get()))
        else:
            roi = None
        params['roi'] = roi
        params['samplename'] = self.samplename.get()
        return params
        
    def check_if_ready(self, *args):
        if self.curr_scan.is_ready():
            self.startbutt.config(state=NORMAL)
        else:
            self.startbutt.config(state=DISABLED)
