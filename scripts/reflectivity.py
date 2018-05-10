#! /home/bladmin/blcontrol/venv/bin/python

import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('/home/bladmin/blcontrol/scripts')
from fwhm import cen_fwhm

#### USAGE: Copy this script into the directory where your beamline data is
#### To run:
#### cd to data directory, in terminal type:
#### ./reflectivity.py
#### OR in file browser, double click and select "run in terminal"

#### Geometric Parameters ####
D_OPT = 677.8   # distance from src to optic, mm
D_DET = 3050    # distance from src to detector, mm
PIN_SIZE = 3    # pinhole radius used to take src spectrum
OPT_AREA = 46.7 # collecting area of optic in mm**2


#### Data Locations ####
# Must give absolute path to files if data is not in the same directory as this
# script
OPT_FILENAME = 'optic.txt'          # filename of optic spectrum
SRC_FILENAME = 'nooptic.txt'        # filename of src spectrum (no optic)
REFL_FILENAME = 'reflectivity.txt'  # where you want the calculated reflectivity
                                    # to be saved


#### Plot Parameters ####
TITLE = 'optic name + date' # plot title
REF_LINE = 22.16            # location of reference line to be plotted, in keV
                            # if you don't want one, change to REF_LINE = None
PLOT_START_ENERGY = 8       # where to start the x-axis (keV)
PLOT_END_ENERGY = 30        # where to end the x-axis (kev)                          
PLOT_FILENAME = 'refl.png'  # location where you want plot to be saved


#### Options ####
# the following line creates the reflectivity text file-- change to False
# if the file already exists
CREATE_TXT_FILE = True

# the following line creates the plot-- change to False if you don't want a plot
CREATE_PLOT     = True

def calculate_reflectivity():
    """Calculates the reflectivity using global variables defined above and
    saves result to a text file."""
    
    # load data
    src_spec = np.loadtxt(SRC_FILENAME)
    opt_spec = np.loadtxt(OPT_FILENAME)

    # collecting area of detector when source spectrum was taken with pinhole
    src_pin_area = np.pi*(PIN_SIZE/2.)**2

    # correction factor for source-to-optic distance & collecting area
    # (see analysis section of manual for more explanation)
    correction = src_pin_area*D_OPT**2/(OPT_AREA*D_DET**2)

    # calculate R**2 with correction factor
    R_sq = np.zeros_like(src_spec)
    R_sq[:,0] = src_spec[:,0]
    # ignore div by 0 warning for now
    with np.errstate(divide='ignore', invalid='ignore'):
        R_sq[:,1] = np.nan_to_num(correction*np.divide(opt_spec[:,1],
                                                        src_spec[:,1]))

    # take square root to get single-bounce reflectivity
    refl = np.zeros_like(R_sq)
    refl[:,0] = R_sq[:,0]
    refl[:,1] = np.sqrt(R_sq[:,1])

    # save to file
    np.savetxt(REFL_FILENAME, refl)

def plot_reflectivity():
    """Plots single bounce reflectivity from file using parameters defined
    above."""
    # load reflectivity file
    refl = np.loadtxt(REFL_FILENAME)

    # calculate peak and fwhm
    cen, fwhm = cen_fwhm(refl[:,0], refl[:,1])
    max_refl = max(refl[:,1])

    # plotting
    plt.figure(1)
    plt.clf()
    if REF_LINE:
        plt.axvline(x=REF_LINE, ymin=0, ymax=1, color='g', lw=2,
            label=str(REF_LINE)+' keV')
    plt.plot(refl[:,0], refl[:,1], color='b', label='Measured Reflectivity')
    plt.plot([cen-fwhm/2., cen+fwhm/2.], [max_refl/2, max_refl/2],
        color='r')
    fwhm_label = 'FWHM = {0:0.2f} keV\n     @ {1:0.2f} keV'.format(fwhm, cen)
    plt.text(cen-fwhm, max_refl/2, fwhm_label, color='r', ha='right')
    plt.xlim(PLOT_START_ENERGY, PLOT_END_ENERGY)
    plt.xlabel('Energy (keV)')
    plt.ylabel('Reflectivity')
    plt.title(TITLE)
    plt.legend(loc='upper left')
    plt.grid()
    plt.savefig(PLOT_FILENAME)

if __name__ == "__main__":
    if CREATE_TXT_FILE:
        calculate_reflectivity()

    if CREATE_PLOT:
        plot_reflectivity()
    
