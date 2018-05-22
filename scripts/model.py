import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import scipy.constants as spc
from scipy.io import readsav
from scipy.ndimage.filters import gaussian_filter1d
import sys
sys.path.append('/home/bladmin/blcontrol/scripts')
from fwhm import cen_fwhm

# load idl sav files
# THETA: edge to int
big = readsav('big_end.sav')
small = readsav('sm_end.sav')

# convert wavelength to energy
c = spc.c * 1e10 #meters to angstroms
h = spc.h * spc.physical_constants['joule-electron volt relationship'][0]
energy = h*c/(big['lambda'] * 1000) #kev

# calculate average reflectivity & smooth
dbl_bounce = np.multiply(big.r, small.r)
avg = np.mean(dbl_bounce, axis=1)
delta_E = energy[1] - energy[0]
sigma = 0.4/(delta_E*2*np.sqrt(2*np.log(2))) #0.4 keV det resolution
smoothed = gaussian_filter1d(avg, sigma)
single_bounce = np.sqrt(smoothed)
np.savetxt('refl1.txt', single_bounce)

cen, fwhm = cen_fwhm(energy, single_bounce)
print 'FWHM = {0:0.2f} keV @ {1:0.2f} keV'.format(fwhm, cen)
max_refl = max(single_bounce)
max_energy = energy[np.argmax(single_bounce)]
print 'Peak = {0:0.1f}% @ {1:0.2f} keV'.format(max_refl*100, max_energy)

measured_refl = np.loadtxt('../beamline_data/reflectivity.txt')


plt.axvline(x=22.3, ymin=0, ymax=1, color='r', lw=2, label='Target peak 22.3 keV')
#plt.plot(energy, single_bounce, label='IMD model')
plt.plot(energy, single_bounce, label='IMD model')
plt.plot(measured_refl[:,0], measured_refl[:,1], label='Measured')
plt.plot([cen-fwhm/2., cen+fwhm/2.], [max_refl/2, max_refl/2],
    color='r')
plt.text(cen-fwhm, max_refl/2,
    'FWHM = {0:0.2f} keV\n     @ {1:0.2f} keV'.format(fwhm, cen), color='r', ha='right')
plt.xlim(15,30)
plt.ylim(0,.5)
plt.grid()
plt.legend(loc='upper left')
plt.ylabel('Single-bounce reflectivity')
plt.xlabel('Energy (keV)')
plt.title('Ag optic model, big end 27.2 sm end 26.0')
plt.savefig('model1.png')
