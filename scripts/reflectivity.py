import numpy as np
import matplotlib.pyplot as plt
from fwhm import cen_fwhm

datadir = '/home/bladmin/SiW_for_LLNL/optic_data/SiW69_NFM1C_R11_RR305/beamline_data/19Dec2016'
if datadir[-1] is not '/':
    datadir += '/'
samplename = 'RR301'
date = '22Dec2016'
bg_filename = 'nooptic_Alfilter.txt'
opt_filename = 'optic_Alfilter.txt'
line_energy = 22.16  #keV
line_name = "Ag K alpha"

bg = np.loadtxt(datadir + bg_filename)
opt = np.loadtxt(datadir + opt_filename)

bg_pin = 5 #diameter, mm
bg_area = np.pi * (bg_pin/2.)**2
opt_area = 18.5 #mm^2

d_opt = 600  #mm
d_detector = 3000  #mm

correction = bg_area*d_opt**2/(opt_area*d_detector**2)

R_sq = np.zeros_like(bg)
R_sq[:,0] = bg[:,0]
R_sq[:,1] = np.nan_to_num(correction*np.divide(opt[:,1], bg[:,1]))

refl = np.zeros_like(R_sq)
refl[:,0] = R_sq[:,0]
refl[:,1] = np.sqrt(R_sq[:,1])

np.savetxt(datadir + 'reflectivity_Alfilter.txt', refl)
refl = np.loadtxt(datadir + 'reflectivity_Alfilter.txt')


cen, fwhm = cen_fwhm(refl[:,0], refl[:,1])
max_refl = max(refl[:,1])
print 'Cen = {0:0.2f} keV\nFWHM = {1:0.2f} keV'.format(cen, fwhm)

plt.figure(1)
plt.clf()
plt.axvline(x=line_energy, ymin=0, ymax=1, color='g', lw=2, label=line_name +
	', ' + str(line_energy) + ' keV\nR = 0.15')
plt.plot(refl[:,0], refl[:,1], color='b', label='Measured Reflectivity')
plt.plot([cen-fwhm/2., cen+fwhm/2.], [max_refl/2, max_refl/2],
    color='r')
plt.text(cen-fwhm, max_refl/2,
    'FWHM = {0:0.2f} keV\n     @ {1:0.2f} keV'.format(fwhm, cen), color='r', ha='right')
#plt.text(cen, max_refl,
         #"Max reflectivity = {0:0.2f}".format(max_refl), color='r',
         #va='bottom')
plt.xlim(8,30)
plt.ylim(0,0.25)
plt.xlabel('Energy (keV)')
plt.ylabel('Reflectivity')
#plt.title(samplename + ' reflectivity with 1mm Al filter, ' + date)
plt.legend(loc='upper left')
plt.grid()
plt.savefig(datadir + 'refl_Alfilter.png')
#plt.show()


plt.title(samplename + ' raw data, ' + date)
plt.xlabel('Energy (keV)')
plt.ylabel('Counts')
plt.grid()
plt.savefig(datadir + 'raw_Alfilter.png')
