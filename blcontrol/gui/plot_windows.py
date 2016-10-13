import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import Queue
import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

class SpectrumDisplay(ttk.Frame):
    def __init__(self, parent, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.energies = None
        self.make_widgets()

    def make_widgets(self):
        f = Figure(figsize=(6,5))
        self.ax = f.gca()
        self.ax.set_ylabel('Counts')
        self.canvas = FigureCanvasTkAgg(f, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    def pre_start(self, samplename, energies):
        self.energies = energies
        self.ax.set_xlim(0, self.energies[-1])
        self.ax.set_title(samplename)
        self.canvas.show()

    #def update_spec(self):
        #try:
            #specdata = self.specqueue.get_nowait()
        #except Queue.Empty:
            #pass
        #else:
            #self.ax.cla()
            #if self.energies is None:
                #self.ax.plot(specdata)
            #else:
                #self.ax.plot(self.energies, specdata)
            #self.canvas.show()
        #self.update_loop = self.after(100, self.update_spec)

class ScanDisplay(ttk.Frame):
    def __init__(self, parent, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.make_widgets()

    def make_widgets(self):
        self.figure = Figure(figsize=(10,5))
        canvas = FigureCanvasTkAgg(self.figure, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
