import numpy as np
import os
import threading
import time

from blcontrol.utils import cen_fwhm, com

class Spectrum(ScanData):
    def __init__(self, cts, energies, settings):
        self.counts = cts
        self.energies = energies
        self.settings = settings
        self.status = None
        super(Spectrum, self).__init__()

    def total_count(self):
        return sum(self.counts)

    def roi_counts(self, roi):
        """Returns the data corresponding to the ROI energies.

         Args:
            roi (tuple): A tuple of the form (start, end) indicating
                the beginning and end of the region of interest.
        """
        start, end = roi
        energies = self.energies
        data = self.counts
        return [data[i] for i in range(len(data))
                if energies[i] >= start and energies[i] <= end]

    def roi_energies(self, roi):
        start, end = roi
        return [e for e in self.energies if e >= start and e <= end]

    def roi_total_count(self, roi):
        return sum(self.roi_counts(roi))

    def export(self, filename):
        filename = os.path.expanduser(filename)
        outarr = np.array([self.energies, self.counts]).T
        header = (os.path.abspath(filename) + '\n' +
                  'MCA Spectrum ' + self.timestamp + '\n' +
                  self.samplename + '\n\n' +
                  'keV       cts')
        footer = '\nDetector status:\n'
        for key, value in self.status.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        footer += '\nDetector settings:\n'
        for key, value in self.settings.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        np.savetxt(filename, outarr, fmt='%8.4f\t%d', header=header,
                   footer=footer)

    def cen_fwhm(self):
        return cen_fwhm(self.energies, self.counts)

    def roi_cen_fwhm(self, roi):
        return cen_fwhm(self.roi_energies(roi), self.roi_counts(roi))

    def peakloc_max(self):
        maximum = max(self.counts)
        peakloc = self.energies[self.counts.index(maximum)]
        return peakloc, maximum

    def roi_peakloc_max(self, roi):
        maximum = max(self.roi_counts(roi))
        peakloc = self.energies[self.roi_counts(roi).index(maximum)]
        return peakloc, maximum


class LinearScan(ScanData):
    def __init__(self, locations, spectra, motorname):
        self.locations = locations
        self.spectra = spectra
        self.motorname = motorname
        super(LinearScan, self).__init__()

    def export(self, filename):
        filename = os.path.expanduser(filename)
        energycol = np.append(self.spectra[0].energies, 'Total')
        outarr = [energycol]
        for spectrum in self.spectra:
            column = [np.append((spectrum.counts), spectrum.total_count())]
            outarr = np.append(outarr, column, axis=0)
        header = (os.path.abspath(filename) +'\n'+
                  'Linear Scan of ' +self. motorname +' '+ self.timestamp +'\n'+
                  self.samplename + '\n\n' +
                  '{:>20s}'.format('Locations:')+ '\n' + 
                  '{:>7s}'.format('keV') +
                  ''.join('{:>9}'.format(loc) for loc in self.locations))
        status = self.spectra[0].status
        settings = self.spectra[0].settings      
        footer = '\nDetector status:\n'
        for key, value in status.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        footer += '\nDetector settings:\n'
        for key, value in settings.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        np.savetxt(filename, outarr.T, fmt='%9s', header=header, footer=footer,
                   delimiter='')

    def counts(self):
        return [spectrum.total_count for spectrum in self.spectra]

    def roi_counts(self, roi):
        return [spectrum.roi_total_count(roi) for spectrum in self.spectra]

    def cen_fwhm(self):
        return cen_fwhm(self.locations, self.counts)

    def cen_fwhm_roi(self, roi):
        return cen_fwhm(self.locations, self.roi_counts(roi))

    def peakloc_max(self):
        maximum = max(self.counts)
        peakloc = self.locations[self.counts().index(maximum)]
        return peakloc, maximum

    def peakloc_max_roi(self, roi):
        roi_cts = self.roi_counts(roi)
        maximum = max(roi_cts)
        peakloc = self.locations[self.roi_counts(roi).index(maximum)]
        return peakloc, maximum


class GridScan(ScanData):
    def __init__(self, xlocs, ylocs, spectra):
        self.xlocs = xlocs
        self.ylocs = ylocs
        self.spectra = spectra
        super(GridScan, self).__init__()

    def counts(self):
        M, N = np.shape(self.spectra)
        cts = np.zeros((M,N))
        for i in range(M):
            for j in range(N):
                if self.spectra[i,j]:
                    cts[i,j] = self.spectra[i,j].total_count()

    def roi_counts(self, roi):
        M, N = np.shape(self.spectra)
        cts = np.zeros((M,N))
        for i in range(M):
            for j in range(N):
                if self.spectra[i,j]:
                    cts[i,j] = self.spectra[i,j].roi_total_count(roi)

    def cen(self):
        return com(self.counts(), self.xlocs, self.ylocs)

    def roi_cen(self, roi):
        return com(self.roi_counts(roi), self.xlocs, self.ylocs)
