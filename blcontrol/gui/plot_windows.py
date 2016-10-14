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
        self.plot_objs = [None, None, None, None]
        self.plotloop = None

    def make_widgets(self):
        f = Figure(figsize=(7,6))
        self.ax = f.gca()
        self.canvas = FigureCanvasTkAgg(f, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    def plot(self, specqueue, roi):
        try:
            spectrum = specqueue.get_nowait()
        except Queue.Empty:
            self.plotloop = self.after(250, lambda: self.plot(specqueue, roi))
            return
        for thing in self.plot_objs:
            if thing:
                thing.remove() #clear previous plot objects
        self.ax.set_ylim(0, max(spectrum.counts)*1.25)
        self.plot_objs[0], = self.ax.plot(spectrum.energies, spectrum.counts,
                                          'g')
        total_text = ("Total counts: {0}\nPeak is {1[1]} ct @ {1[0]:0.2f} keV\n"
            "FWHM {2[1]:.2f} keV @ {2[0]:.2f} keV").format(
            spectrum.total_count(), spectrum.peakloc_max(), spectrum.cen_fwhm())
        self.plot_objs[1] = self.ax.text(0.02, 0.98, total_text,
            transform=self.ax.transAxes, va="top", color='g')
        if roi:
            roistart, roiend = roi
            self.plot_objs[2] = self.ax.axvspan(roistart, roiend, facecolor='b',
                                                alpha=0.2)
            roi_text = ("ROI counts: {0}\nPeak is {1[1]} ct @ {1[0]:0.2f} keV\n"
                "FWHM {2[1]:.2f} keV @ {2[0]:.2f} keV").format(
                spectrum.roi_total_count(roi), spectrum.roi_peakloc_max(roi),
                spectrum.roi_cen_fwhm(roi))
            self.plot_objs[3] = self.ax.text(0.52, 0.98, roi_text, color='b',
                transform=self.ax.transAxes, va="top")
        self.canvas.show()
        self.plotloop = self.after(250, lambda: self.plot(specqueue, roi))

    def stop_plot(self):
        if self.plotloop:
            self.after_cancel(self.plotloop)
        self.plotloop = None

    def set_energies(self, energies):
        self.ax.set_ylabel('Counts')
        self.ax.set_xlabel('Energy (keV)')
        self.ax.set_xlim(0, energies[-1])
        self.canvas.show()


class ScanDisplay(ttk.Frame):
    def __init__(self, parent, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.make_widgets()
        self.plotloop = None

    def make_widgets(self):
        self.figure = Figure(figsize=(10,5))
        canvas = FigureCanvasTkAgg(self.figure, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    def plot(self, plotqueue, roi):
        pass
