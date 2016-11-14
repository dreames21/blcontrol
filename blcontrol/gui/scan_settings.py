import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
from blcontrol.gui.float_entry import FloatEntry

class ScanSettingsFrame(ttk.Frame):
    """Base class for different types of scan settings frames."""
    def __init__(self, parent, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.variables = {}
        self.scantype = ''
    
    def clear_widgets(self):
        """Set all string variables to empty strings."""
        for var in self.variables.values():
            var.set('')

    def get_params(self):
        """Return scan parameters from settings input by user."""
        params = {}
        for key, val in self.variables.iteritems():
            try:
                params[key] = float(val.get())
            except ValueError:
                params[key] = val.get()
        params['type'] = self.scantype
        return params

    def is_ready(self):
        """Return True if all scan variables are set, False otherwise."""
        vals = [v.get() for v in self.variables.values()]
        return all(vals)


class LinearScanSettings(ScanSettingsFrame):
    """Frame containing settings for a linear scan."""
    
    def __init__(self, parent, stageio, **options):
        ScanSettingsFrame.__init__(self, parent, **options)
        self.stageio = stageio
        self.scantype = 'linear'
        keys = ['motorname', 'acctime', 'stepsize', 'start', 'end']
        self.variables = {key: StringVar() for key in keys}
        self.stepunit = StringVar(value=' mm')
        self.make_widgets()

    def make_widgets(self):
        motselframe = ttk.Frame(self)
        ttk.Label(motselframe, text='Motor: ').pack(side=LEFT)
        motornames = self.stageio.motors.keys()
        self.motorsel = ttk.Combobox(motselframe, width=3, state='readonly',
            textvariable=self.variables['motorname'], values=motornames)
        self.motorsel.bind('<<ComboboxSelected>>', self.change_unit)
        self.motorsel.pack(side=LEFT)
        motselframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        self.acctime = StringVar()
        accent = FloatEntry(acctimeframe, width=5,
                            textvariable=self.variables['acctime'])
        accent.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' s/pt').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        stepsizeframe = ttk.Frame(self)
        ttk.Label(stepsizeframe, text='Step size: ').pack(side=LEFT)
        self.stepsize = StringVar()
        stepent = FloatEntry(stepsizeframe, width=5,
                             textvariable=self.variables['stepsize'])
        stepent.pack(side=LEFT)        
        lab = ttk.Label(stepsizeframe, textvariable=self.stepunit)
        lab.pack(side=LEFT)
        stepsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        extframe = ttk.Frame(self)
        ttk.Label(extframe, text='Extent: ').pack(side=LEFT)
        self.start = StringVar()
        startent = FloatEntry(extframe, width=4,
                              textvariable=self.variables['start'])
        startent.pack(side=LEFT)
        ttk.Label(extframe, text=' to ').pack(side=LEFT)
        self.end = StringVar()
        endent = FloatEntry(extframe, width=4,
                            textvariable=self.variables['end'])
        endent.pack(side=LEFT)
        lab2 = ttk.Label(extframe, textvariable=self.stepunit)
        lab2.pack(side=LEFT)
        extframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

    def change_unit(self, _):
        """Toggle between linear and angular units based on motor travel."""
        self.motorsel.selection_clear()
        motname = self.motorsel.get()
        if self.stageio.motors[motname].travel: #has finite travel == is linear stage
            self.stepunit.set(' mm')
        else:
            self.stepunit.set(' deg')
            

class GridScanSettings(ScanSettingsFrame):
    """Frame containing settings for a grid scan of detector stages."""
    
    def __init__(self, parent, **options):
        ScanSettingsFrame.__init__(self, parent, **options)
        self.scantype = 'grid'
        keys = ['acctime', 'stepsize', 'gridsize']
        self.variables = {key: StringVar() for key in keys}
        self.make_widgets()

    def make_widgets(self):
        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        accent = FloatEntry(acctimeframe, width=5,
                            textvariable=self.variables['acctime'])
        accent.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' s/pt').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        stepsizeframe = ttk.Frame(self)
        ttk.Label(stepsizeframe, text='Step size: ').pack(side=LEFT)
        self.stepsize = StringVar()
        stepent = FloatEntry(stepsizeframe, width=5,
                             textvariable=self.variables['stepsize'])
        stepent.pack(side=LEFT)
        ttk.Label(stepsizeframe, text=' mm').pack(side=LEFT)
        stepsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        gridsizeframe = ttk.Frame(self)
        vals = ['{0}x{0}'.format(i).center(6) for i in range(3, 13, 2)]
        ttk.Label(gridsizeframe, text='Grid size: ').pack(side=LEFT)
        gridsizesel = ttk.Combobox(gridsizeframe, values=vals, width=5,
            state='readonly')
        def gridcallback(*_):
            curr = gridsizesel.get()
            gridsize = int(curr.split('x')[0])
            self.variables['gridsize'].set(gridsize)
            gridsizesel.selection_clear()
        gridsizesel.bind('<<ComboboxSelected>>', gridcallback)
        gridsizesel.pack(side=LEFT)
        gridsizeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)
        

class SpectrumSettings(ScanSettingsFrame):
    """Frame containing settings for an individual spectrum acquisition."""
    
    def __init__(self, parent, **options):
        ScanSettingsFrame.__init__(self, parent, **options)
        keys = ['acctime', 'chans']
        self.variables = {key: StringVar() for key in keys}
        self.scantype = 'spectrum'
        self.make_widgets()

    def make_widgets(self):
        acctimeframe = ttk.Frame(self)
        ttk.Label(acctimeframe, text='Acc time: ').pack(side=LEFT)
        acctime = FloatEntry(acctimeframe, width=5,
                             textvariable=self.variables['acctime'])
        acctime.pack(side=LEFT)
        ttk.Label(acctimeframe, text=' sec').pack(side=LEFT)
        acctimeframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)

        chanframe = ttk.Frame(self)
        ttk.Label(chanframe, text='MCA Channels: ').pack(side=LEFT)
        vals = [256, 512, 1024, 2048, 4096, 8192]
        chansel = ttk.Combobox(chanframe, values=vals, state='readonly',
            textvariable=self.variables['chans'], width=4)
        chansel.bind('<<ComboboxSelected>>',
                          lambda x: chansel.selection_clear())
        chansel.pack(side=LEFT)
        chanframe.pack(side=TOP, fill=BOTH, expand=1, pady=3)
        

class SettingsFrame(ttk.Frame):
    """Contains settings for each type of scans as well as common settings."""
    
    def __init__(self, parent, sio, **options):
        ttk.Frame.__init__(self, parent, **options)
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
        self.roistart = FloatEntry(nameframe, width=5)
        self.roistart.grid(row=1, column=1, sticky=W, pady=3)
        ttk.Label(nameframe, text=' to ').grid(row=1, column=2)
        self.roiend = FloatEntry(nameframe, width=5)
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
        for var in (self.gridset.variables.values() +
                    self.linset.variables.values() +
                    self.specset.variables.values()):
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

    def change_scan_type(self, *_):
        """Toggles scan settings between different types of scans."""
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
        """Returns a dictionary of scan parameters."""
        params = self.curr_scan.get_params()
        roistart = self.roistart.get()
        roiend = self.roiend.get()
        if roistart and roiend:
            roi = (float(self.roistart.get()), float(self.roiend.get()))
        else:
            roi = None
        params['roi'] = roi
        params['samplename'] = self.samplename.get()
        return params
        
    def check_if_ready(self, *_):
        if self.curr_scan.is_ready():
            self.startbutt.config(state=NORMAL)
        else:
            self.startbutt.config(state=DISABLED)
