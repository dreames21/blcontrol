#! /home/bladmin/blcontrol/venv/bin/python

import numpy as np
import matplotlib.pyplot as plt
import scipy.constants as spc
from scipy.io import readsav
from scipy.ndimage.filters import gaussian_filter1d
import sys
sys.path.append('/home/bladmin/blcontrol/scripts')
from fwhm import cen_fwhm

################################################################################
## To use:
## -Produce IMD .sav files for the big end and the small end of the optic (see
##  Beamline Manual section 6.2.2 for more detailed instructions)
## -Copy this script into the directory with the .sav files
## -Edit the bottom portion of this script, after "if __name__ == '__main__'",
##  to use the correct parameters and filenames
################################################################################


#### Physical constants ####
 # speed of light in angstroms/second
c = spc.c*1e10
 # Planck's constant in units of keV * seconds
h = spc.h*spc.physical_constants['joule-electron volt relationship'][0]/1000


def double_bounce_refl(big_end_filename, small_end_filename):
    """Reads .sav files from IMD, multiplies and averages them to produce
    theoretical double-bounce reflectivity vs energy data for the optic as a
    whole. Follows the mathematical basis outlined in Section 6.2.2 of the
    Beamline Manual."""

    # load .sav files
    big = readsav(big_end_filename)
    small = readsav(small_end_filename)

    # check wavelength values are the same in both files and convert to keV
    assert (big['lambda'] == small['lambda']).all()
    energy = h*c/(big['lambda'])

    # multiply and average over graze angles
    dbl_bounce = np.multiply(big.r, small.r)
    avg = np.mean(dbl_bounce, axis=1)
    return np.array([energy, avg])

def smooth(refl, res):
    """Smooths reflectivity data with gaussian filter.

    Args:
        refl: numpy array of reflectivity data where the first column is energy
            and the second column is reflectivity
        res (float): resolution (fwhm) of Gaussian filter to use for smoothing,
            in the same energy units as used for the reflectivity (probably keV)

    Returns: numpy array of same shape as refl, with the energy values unchanged
        and the reflectivity values smoothed.
    """
    energy, reflectivity = refl
    delta_E = energy[1] - energy[0]
    
    ## convert FWHM to sigma and energy to channels
    sigma = res/(delta_E*2*np.sqrt(2*np.log(2)))  
    smoothed = gaussian_filter1d(reflectivity, sigma)
    return np.array([energy, smoothed])

def plot_model(refl, measured_filename, ref_line=None):
    """Plots single-bounce reflectivity from model against measured data.

    Args:
        refl: numpy array of reflectivity data where the first column is energy
            and the second column is reflectivity
        measured_filename: filename of measured data file
        ref_line: energy value at which vertical reference line will be plotted
    """
    energy = refl[0,:]
    single_bounce = np.sqrt(refl[1,:])
        
    cen, fwhm = cen_fwhm(energy, single_bounce)
    max_refl = max(single_bounce)
    max_energy = energy[np.argmax(single_bounce)]

    plt.clf()
    if ref_line:
        plt.axvline(x=ref_line, ymin=0, ymax=1, color='r', lw=2,
            label='Reference line\n{0} keV'.format(ref_line))
    if measured_filename:
        measured_refl = np.loadtxt(measured_filename)
        plt.plot(measured_refl[:,0], measured_refl[:,1], label='Measured')
    plt.plot(energy, single_bounce, label='Model')
    plt.plot([cen-fwhm/2., cen+fwhm/2.], [max_refl/2, max_refl/2],
        color='r')
    plt.text(cen-fwhm, max_refl/2,
        'FWHM = {0:0.2f} keV\n     @ {1:0.2f} keV'.format(fwhm, cen), color='r', ha='right')
    plt.xlim(energy[0], energy[-1])
    plt.grid()
    plt.legend(loc='upper left')
    plt.ylabel('Single-bounce reflectivity')
    plt.xlabel('Energy (keV)')
    plt.savefig('model.png')


if __name__ == "__main__":

    ## comment the following if the .txt file is already created
    dbl_bounce = double_bounce_refl("big_end.sav", "sm_end.sav")
    smoothed = smooth(dbl_bounce, 0.4)
    np.savetxt("model_refl.txt", smoothed)

    ## uncomment if .txt file already exists
    #smoothed = np.loadtxt("model_refl.txt")

    plot_model(smoothed, "../beamline_data/reflectivity.txt", ref_line=22.5)
    
    
