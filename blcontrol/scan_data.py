import numpy as np
import os
from blcontrol.utils import cen_fwhm, com

#TODO: write export for gridscan

class Spectrum(object):
    def __init__(self, cts, energies, status, timestamp):
        self.counts = cts
        self.energies = energies
        self.settings = None
        self.status = status
        self.timestamp = timestamp
        self.samplename = None

    def total_count(self):
        return sum(self.counts)

    def roi_counts(self, roi):
        """Returns the data corresponding to the ROI energies.

         Args:
            roi (tuple): A tuple of the form (start, end) indicating
                the beginning and end of the region of interest.
        """
        start, end = roi
        return [self.counts[i] for i in range(len(self.counts))
                if self.energies[i] >= start and self.energies[i] <= end]

    def roi_energies(self, roi):
        start, end = roi
        return [e for e in self.energies if e >= start and e <= end]

    def roi_total_count(self, roi):
        return sum(self.roi_counts(roi))

    def export(self, filename):
        outarr = np.array([self.energies, self.counts]).T
        if self.samplename:
            samp = self.samplename
        else:
            samp = ''
        header = (os.path.abspath(filename) + '\n' +
                  'MCA Spectrum ' + self.timestamp + '\n' +
                  samp + '\n\nkeV       cts')
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


class LinearScan(object):
    def __init__(self, locations, spectra, motorname, timestamp):
        self.locations = locations
        self.spectra = spectra
        self.motorname = motorname
        self.timestamp = timestamp
        self.samplename = None

    def export(self, filename):
        energycol = np.append(self.spectra[0].energies, 'Total')
        outarr = [energycol]
        for spectrum in self.spectra:
            column = [np.append((spectrum.counts), spectrum.total_count())]
            outarr = np.append(outarr, column, axis=0)
        if self.samplename:
            samp = self.samplename
        else:
            samp = ''
        header = (os.path.abspath(filename) +'\n'+
                  'Linear Scan of ' +self.motorname +' '+ self.timestamp +'\n'+
                  samp + '\n\n' + '{:>20s}'.format('Locations:')+ '\n' + 
                  '{:>7s}'.format('keV') +
                  ''.join('{:>9}'.format(loc) for loc in self.locations))
        status = self.spectra[-1].status
        settings = self.spectra[-1].settings      
        footer = '\nDetector status:\n'
        for key, value in status.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        footer += '\nDetector settings:\n'
        for key, value in settings.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        np.savetxt(filename, outarr.T, fmt='%9s', header=header, footer=footer,
                   delimiter='')

    @property
    def counts(self):
        return [spectrum.total_count() for spectrum in self.spectra]

    def roi_counts(self, roi):
        return [spectrum.roi_total_count(roi) for spectrum in self.spectra]

    def cen_fwhm(self):
        return cen_fwhm(self.locations, self.counts)

    def cen_fwhm_roi(self, roi):
        return cen_fwhm(self.locations, self.roi_counts(roi))

    def peakloc_max(self):
        maximum = max(self.counts)
        peakloc = self.locations[self.counts.index(maximum)]
        return peakloc, maximum

    def peakloc_max_roi(self, roi):
        roi_cts = self.roi_counts(roi)
        maximum = max(roi_cts)
        peakloc = self.locations[self.roi_counts(roi).index(maximum)]
        return peakloc, maximum


class GridScan(object):
    def __init__(self, xlocs, ylocs, spectra, timestamp):
        self.xlocs = xlocs
        self.ylocs = ylocs
        self.spectra = spectra
        self.timestamp = timestamp
        self.samplename = None

    @property
    def counts(self):
        M, N = np.shape(self.spectra)
        cts = -1*np.ones((M,N))
        for i in range(M):
            for j in range(N):
                if self.spectra[i,j]:
                    cts[i,j] = self.spectra[i,j].total_count()
        return cts

    def roi_counts(self, roi):
        M, N = np.shape(self.spectra)
        cts = -1*np.ones((M,N))
        if roi:
            for i in range(M):
                for j in range(N):
                    if self.spectra[i,j]:
                        cts[i,j] = self.spectra[i,j].roi_total_count(roi)
        return cts

    @property
    def cen(self):
        counts_cl = np.clip(self.counts, 0, self.counts.max())
        return com(counts_cl, self.xlocs, self.ylocs)

    def roi_cen(self, roi):
        counts_cl = np.clip(self.roi_counts(roi), 0, self.roi_counts(roi).max())
        return com(counts_cl, self.xlocs, self.ylocs)