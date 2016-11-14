import numpy as np
import os
from scipy import interpolate, optimize

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
        energycol = self.spectra[0].energies
        outarr = np.array([energycol])
        if self.samplename:
            samp = self.samplename
        else:
            samp = ''
        metadata = (os.path.abspath(filename) +'\n'+ 'Linear Scan of ' +
                    self.motorname +' '+ self.timestamp +'\n'+ samp + '\n')
        locline = 'Locations: '
        for i, x in enumerate(self.locations):
            locline += '{0:0.3f} '.format(x)
            spectrum = np.array([self.spectra[i].counts])
            outarr = np.append(outarr, spectrum, axis=0)
        status = self.spectra[-1].status
        settings = self.spectra[-1].settings
        header = metadata + locline + '\n' + 'keV\tcounts'
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

    def export(self, filename):
        energycol = self.spectra[0,0].energies
        outarr = np.array([energycol])
        if self.samplename:
            samp = self.samplename
        else:
            samp = ''
        metadata = (os.path.abspath(filename) +'\n'+ 'Grid scan dx, dy' +' '+
                  self.timestamp +'\n'+ samp + '\n')
        locline = 'Locations: ' 
        for i, x in enumerate(self.xlocs):
            for j, y in enumerate(self.ylocs):
                locline += '({0:0.3f}, {1:0.3f}) '.format(x,y)
                spectrum = np.array([self.spectra[i,j].counts])
                outarr = np.append(outarr, spectrum, axis=0)
        header = metadata + locline + '\n' + 'keV\tcounts'
        status = self.spectra[-1,-1].status
        settings = self.spectra[-1,-1].settings
        footer = '\nDetector status:\n'
        for key, value in status.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        footer += '\nDetector settings:\n'
        for key, value in settings.iteritems():
            footer += '{0} = {1}\n'.format(key, value)
        np.savetxt(filename, outarr.T, fmt='%9s', header=header, footer=footer,
                   delimiter='')
                

def cen_fwhm(xdata, ydata):
    xdata = np.array(xdata)
    ydata = np.array(ydata, dtype=float)
    assert len(xdata) == len(ydata)
    ydata -= min(ydata)
    max_y = max(ydata)
    max_ind = ydata.tolist().index(max_y)
    max_x = xdata[max_ind]
    ydata -= max_y/2.
    interp = interpolate.interp1d(xdata, ydata)

    brack_left_ind = brack_right_ind = max_ind
    while ydata[brack_left_ind] > 0 and brack_left_ind > 0:
        brack_left_ind -=1
    if brack_left_ind == 0:
        hm_left = xdata[0]
    else:
        brack_left = xdata[brack_left_ind]
        hm_left = optimize.brentq(interp, brack_left, max_x)
        
    while ydata[brack_right_ind] > 0 and (brack_right_ind < len(xdata) - 1):
        brack_right_ind += 1
    if brack_right_ind == len(xdata) - 1:
        hm_right = xdata[-1]
    else:
        brack_right = xdata[brack_right_ind]
        hm_right = optimize.brentq(interp, max_x, brack_right)

    fw = hm_right - hm_left
    cen = (hm_right + hm_left)/2.
    return cen, fw


def com(array, xvals, yvals):
    array -= array.min()
    try:
        xcounts = array.sum(1).tolist()
        xmoms = [xcounts[i]*value for i, value in enumerate(xvals)]
        xcom = sum(xmoms)/sum(xcounts)
    except ZeroDivisionError:
        ## if there are no counts then return the geometric center
        xcom = 0.5*(xvals[0] + xvals[-1])
    try:
        ycounts = array.sum(0).tolist()
        ymoms = [ycounts[i]*value for i, value in enumerate(yvals)]
        ycom = sum(ymoms)/sum(ycounts)
    except ZeroDivisionError:
        ycom = 0.5*(yvals[0] + yvals[-1])
    return (xcom, ycom)
