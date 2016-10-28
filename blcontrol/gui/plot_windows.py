import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import Queue
import sys
import warnings
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
            self.plotloop = self.after(50, lambda: self.plot(specqueue, roi))
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
        specqueue.task_done()
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
        self.plot_objs = []

    def clear_plot(self):
        self.figure.clf()
        self.plot_objs = []

    def remove_plot_objs(self):
        for thing in self.plot_objs:
            thing.remove()
        self.plot_objs = []
        for cax in self.caxes:
            if cax:
                cax.cla()

    def make_widgets(self):
        self.figure = Figure(figsize=(15,5))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.axes = [self.figure.add_subplot(111), None]
        self.caxes = [None, None]
        self.axes[0].set_xlabel('Location')
        self.axes[0].set_ylabel('Counts')
        self.canvas.show()

    def pre_plot_lin(self, locs, samplename, unit):
        self.clear_plot()
        self.axes[0] = self.figure.add_subplot(111)
        self.axes[0].set_xlim(min(locs), max(locs))
        self.axes[0].set_title(samplename)
        self.axes[0].set_xlabel('Location ({0})'.format(unit))
        self.axes[0].set_ylabel('Counts')
        self.canvas.show()

    def plot_lin(self, scanqueue, roi):
        try:
            scan = scanqueue.get_nowait()
        except Queue.Empty:
            self.plotloop = self.after(100, lambda: self.plot_lin(scanqueue, roi))
            return
        self.remove_plot_objs()
        plot1, = self.axes[0].plot(scan.locations, scan.counts, '.-g')
        self.plot_objs.append(plot1)
        if len(scan.counts) > 1:
            tot_text = ("Total:\nPeak is {0[1]} @ {0[0]}\nFWHM is {1[1]:0.3f} @"
                "{1[0]:0.3f}").format(scan.peakloc_max(), scan.cen_fwhm())
            self.plot_objs.append(self.axes[0].text(0.02, 0.98, tot_text,
                transform=self.axes[0].transAxes, va="top", color='g'))
        if roi:
            plot2, = self.axes[0].plot(scan.locations, scan.roi_counts(roi),
                                       '.-b')
            self.plot_objs.append(plot2)
            if len(scan.counts) > 2:
                roi_text = ("ROI:\nPeak is {0[1]} @ {0[0]}\nFWHM is "
                    "{1[1]:0.3f} @ {1[0]:0.3f}").format(
                        scan.peakloc_max_roi(roi), scan.cen_fwhm_roi(roi))
                self.plot_objs.append(self.axes[0].text(0.5, 0.98, roi_text,
                    transform=self.axes[0].transAxes, va="top", color='b'))
            self.axes[0].set_ylim(bottom=0.8*min(scan.roi_counts(roi)))
        self.axes[0].set_ylim(top=1.25*max(scan.counts))
        self.canvas.show()
        scanqueue.task_done()
        self.plotloop = self.after(100, lambda: self.plot_lin(scanqueue, roi))

    def pre_plot_grid(self, xlocs, ylocs):
        self.clear_plot()
        self.axes[0] = self.figure.add_subplot(121)
        self.axes[0].set_title('Total counts')
        self.axes[1] = self.figure.add_subplot(122)
        self.axes[1].set_title('ROI counts')
        ptsize = xlocs[1] - xlocs[0]
        for axes in self.axes:
            axes.xaxis.set_ticks(xlocs)
            axes.yaxis.set_ticks(ylocs)
            axes.set_xlim(xlocs[0] - 0.5*ptsize, xlocs[-1] + 0.5*ptsize)
            axes.set_ylim(ylocs[-1] + 0.5*ptsize, ylocs[0] - 0.5*ptsize)
            axes.set_xlabel('dx')
            axes.set_ylabel('dy')
        self.caxes[0], _ = matplotlib.colorbar.make_axes(self.axes[0])
        self.caxes[1], _ = matplotlib.colorbar.make_axes(self.axes[1])

    def plot_grid(self, scanqueue, roi):
        try:
            scan = scanqueue.get_nowait()
        except Queue.Empty:
            self.plotloop = self.after(100, lambda: self.plot_grid(scanqueue, roi))
            return
        self.remove_plot_objs()
        
        palette = plt.cm.Greens
        palette.set_bad(color='gray', alpha=1.0)
        ptsize = scan.xlocs[1] - scan.xlocs[0]
        ext = [scan.xlocs[0] - 0.5*ptsize, scan.xlocs[-1] + 0.5*ptsize,
                scan.ylocs[-1] + 0.5*ptsize, scan.ylocs[0] - 0.5*ptsize]
        masked_cts = np.ma.masked_where(scan.counts.T==-1, scan.counts.T)
        im1 = self.axes[0].imshow(masked_cts, interpolation='None',
            cmap='Greens', extent=ext)
        self.plot_objs.append(im1)
        self.figure.colorbar(im1, ax=self.axes[0], cax=self.caxes[0])
        plot1, = self.axes[0].plot(scan.cen[0], scan.cen[1], 's', markersize=15,
            mfc='orange', mec='orange')
        self.plot_objs.append(plot1)
        cen_txt = "Cen @\n({0[0]:0.2f}, {0[1]:0.2f})".format(scan.cen)
        self.plot_objs.append(self.axes[0].annotate(cen_txt, xy=scan.cen,
            xytext=(0,10), ha='center', textcoords='offset points',
            color='orange'))
        
        roi_cts = scan.roi_counts(roi).T
        masked_roicts = np.ma.masked_where(roi_cts==-1, roi_cts)
        im2 = self.axes[1].imshow(masked_roicts, interpolation='None',
            cmap='Greens', extent=ext)
        self.plot_objs.append(im2)
        self.figure.colorbar(im2, ax=self.axes[1], cax=self.caxes[1])
        roi_cen = scan.roi_cen(roi)
        plot2, = self.axes[1].plot(roi_cen[0], roi_cen[1], 's', markersize=15,
            mfc='orange', mec='orange')
        self.plot_objs.append(plot2)
        roi_cen_txt = "Cen @\n({0[0]:0.2f}, {0[1]:0.2f})".format(roi_cen)
        self.plot_objs.append(self.axes[1].annotate(roi_cen_txt, xy=roi_cen,
            xytext=(0,10), ha='center', textcoords='offset points',
            color='orange'))
        self.plot_objs.append(self.axes[1].imshow(masked_roicts, interpolation='None',
            cmap='Greens', extent=ext))
            
        #ignore warning for plots containg only masked data
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.canvas.show()
        scanqueue.task_done()
        self.plotloop = self.after(100, lambda: self.plot_grid(scanqueue, roi))
        
    def stop_plot(self):
        if self.plotloop:
            self.after_cancel(self.plotloop)
        self.plotloop = None
    

    
