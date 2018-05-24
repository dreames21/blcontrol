#! /home/bladmin/blcontrol/venv/bin/python

import matplotlib.pyplot as plt
import numpy as np
import sys
sys.path.append('/home/bladmin/blcontrol/scripts')
from fwhm import cen_fwhm
import scipy.optimize as opt

################################################################################
## To use:
##
## Copy this script into the directory containing the calibration source
## spectrum data files.
##
## Edit the bottom portion of the script (under "if __name__ == '__main__'") to
## have the right filenames, spectral lines, and a guess for the channel number
## of each peak.
##
## Preamp gain and number of channels will be extracted from the spectrum data
## files. Note that every calibration spectrum NEEDS to have the same preamp
## gain and number of MCA channels (the script checks for this and will throw
## an error if the condition is not met). The amount of acquisition time doesn't
## matter and can be different for different sources.
##
## To run, cd into the directory with the script and data files. If necessary,
## make this script executable by typing
## chmod +x calib.py
## Then run the script by typing
## ./calib.py
##
## A plot of the calibration fit will be saved in the data directory and the
## script will print the calibration factor and offset which can be copied and
## pasted into blcontrol/config/blconf.txt to set the calibration for the
## detector.
################################################################################

class CalibSource:
    """Class for storing and fitting data from a single calibration source"""
    
    def __init__(self, filename, lines, guesses):
        """
        Args:
            filename (str): filename to open for reading source calib data
            lines (list): list of spectral lines, in keV, to look for in source
                spectrum
            guesses (list): list of guesses for the peak channel corresponding
                to each spectral line (must be same length as 'lines')
        """
        self.filename = filename
        self.data = np.loadtxt(self.filename)[:,1]
        assert len(lines) == len(guesses)
        self.lines = lines
        self.guesses = guesses
        self.gain = self.get_gain()
        self.det_sernum = self.get_det_sernum()

    def get_gain(self):
        """Reads the preamp gain from the footer of a data file"""
        with open(self.filename, 'r') as f:
            while True:
                line = f.readline()
                if line.startswith('# GAIN'):
                    return float(line.split()[-1])
                    break
                #throw error if no gain is found by end of file
                #(last line of file is empty string)
                assert line, "gain not found in {0}".format(filename)

    def get_det_sernum(self):
        """Reads the detector serial number from footer of data file"""
        with open(self.filename, 'r') as f:
            while True:
                line = f.readline()
                if line.startswith('# serial number'):
                    return int(line.split()[-1])
                    break
                #throw error if no gain is found by end of file
                #(last line of file is empty string)
                assert line, "serial number not found in {0}".format(filename)

    def match_lines(self, radius=50):
        """Finds peaks in data based on guesses provided.
        
        Args:
            radius: the distance in +/- channels to search for a peak around the
                guessed channels.
        Returns:
            a list of fitted peak locations and FWHMS for each peak energy
                provided.
        """
        matches = []
        for i, peak_energy in enumerate(self.lines):
            guess = self.guesses[i]
            start = guess-50 if guess-50 >= 0 else 0
            end = guess+50 if guess+50 <= self.num_chans else self.num_chans
            peak, fwhm = cen_fwhm(range(start, end), self.data[start:end])
            matches.append((peak,fwhm))
        return matches

    def plot(self):
        """Plots the spectrum data and shows the location of the peak channel
        matches."""
        plt.figure()
        plt.clf()
        title = self.filename.split('.')[0]
        plt.title(title)
        plt.plot(range(self.num_chans), self.data)
        plt.grid()
        plt.xlabel("MCA Channel")
        plt.ylabel("Counts")
        plt.xlim(0, self.num_chans)
        for match in self.match_lines():
            plt.axvline(x=match[0], color='g')
        plt.savefig(title + '.png')

    @property
    def num_chans(self):
        """Returns the number of MCA channels in the spectrum data"""
        return len(self.data)


def lin(x,a,b):
    """Just a linear function for fitting the energy vs. channel data"""
    return x/a+b


def fit_peaks(calib_sources):
    """ Finds the best linear fit to energy vs channel for all sources.

    Using the linear fit and the hardware gain info from each calib source file,
    returns the fit parameters as a tuple of (calib_factor, offset) that can be
    copied into the blconf.txt file. Energy is calculated as:

    energy = (channel number)/((calib factor)*(hardware gain)*(num channels))
            + offset
            
    calib_factor units are 1/keV
    offset units are keV

    Args:
        calib_sources: a list of CalibSource objects
    """

    # initialize number of channels, gain and det serial number from first calib
    # source. Later will check to make sure all sources have same parameters
    num_chans = calib_sources[0].num_chans
    gain = calib_sources[0].gain
    det_sernum = calib_sources[0].det_sernum

    # put all data from calib sources together in lists
    energies, peak_chans, fwhms = [], [], []
    for source in calib_sources:
        assert source.num_chans == num_chans
        assert source.gain == gain
        assert source.det_sernum == det_sernum
        for i, match in enumerate(source.match_lines()):
            energies.append(source.lines[i])
            peak_channel, fwhm = match
            peak_chans.append(peak_channel)
            fwhms.append(fwhm)

    # fit to line and calculate calibration parameters
    popt, pcov = opt.curve_fit(lin, peak_chans, energies, sigma=fwhms)
    conv_gain, offset = popt
    calib_factor = conv_gain /(gain * num_chans)

    # plot result
    plt.figure()
    plt.clf()
    plt.title('Linear calibration fit')
    plt.xlim(0,num_chans)
    x = range(num_chans)
    y = [lin(ch, conv_gain, offset) for ch in x]
    plt.plot(x, y, label="Fit")
    plt.plot(peak_chans, energies, label="Spectrum Peaks", marker="o", ls='')
    plt.xlabel("MCA Channnel")
    plt.ylabel("Energy (keV)")
    plt.legend(loc="upper left")
    s = "calib_factor={0}\noffset={1}".format(calib_factor, offset)
    plt.text(num_chans/2, 5, s)
    plt.savefig("linfit.png")

    print "\nCalibration parameters for detector with S/N {0}:".format(
        det_sernum)
    print s + '\n'
        

if __name__ == '__main__':

### See http://www.spectrumtechniques.com/products/sources/ for the spectral 
### lines from our sealed sources. Lines that are very close together are 
### combined with a weighted average based on % of flux

    calib_sources = [

    ## Fe55
        CalibSource("Fe55_22May2018.txt",
            # Spectral lines
            [(5.88765*8.45 + 5.89875*16.57)/(8.45+16.57),    # Mn K-alpha
             (6.49045+6.5352)/2.                             # Mn K-beta
             ],                          
            # Channel guesses for each peak
            [1332, 1464]),

    ## Co57
        CalibSource("Co57_22May2018.txt",
            # Spectral lines
            [(6.391*16.4 + 6.404*32.5)/(16.4+32.5),  # Fe K alpha
             7.058,                                  # Fe K beta
             14.4119                                 # gamma M1
             ],                           
            # Channel guesses for each peak
            [1450, 1605, 3250]),

    ## Cs137
        CalibSource("Cs137_22May2018.txt",
            # Spectral lines
            [32.194,  
             36.357,
             ],                           
            # Channel guesses for each peak
            [7200, 8150])
    ]

    ### comment this if you don't want a plot produced for each source
    for src in calib_sources:
        src.plot()

    fit_peaks(calib_sources)
