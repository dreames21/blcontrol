import numpy as np
import matplotlib.pyplot as plt
from fwhm import cen_fwhm

datadir = '/home/bladmin/SiW_for_LLNL/beamline_data/SiW49_NFM1C_R6_RR216/NFM1c_R6_Rr216_29nov2016/'
samplename = 'SiW49_RR216'
date = '29nov2016'
bg = np.loadtxt(datadir + 'noopt_5mm.txt')
opt = np.loadtxt(datadir + 'optic.txt')

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
cen, fwhm = cen_fwhm(refl[:,0], refl[:,1])
print cen, fwhm

np.savetxt(datadir + 'reflectivity.txt', refl)
np.savetxt(datadir + 'rsq.txt', R_sq)

plt.figure(1)
plt.clf()
plt.plot(refl[:,0], refl[:,1], color='b')
plt.plot([cen-fwhm/2., cen+fwhm/2.], [max(refl[:,1])/2, max(refl[:,1])/2],
    color='g')
plt.text(cen+fwhm, max(refl[:,1])/2,
    'FWHM = {0:0.2f} keV\n     @ {1:0.2f} keV'.format(fwhm, cen), color='g')
plt.xlim(0,max(refl[:,0]))
plt.xlabel('Energy (keV)')
plt.ylabel('Reflectivity')
plt.title(samplename + ' reflectivity, ' + date)
plt.savefig(datadir + 'refl.png')

plt.figure(2)
plt.clf()
plt.plot(bg[:,0], bg[:,1])
plt.plot(opt[:,0], opt[:,1])
plt.xlim(0,max(refl[:,0]))
plt.title(samplename + ' raw data, ' + date)
plt.xlabel('Energy (keV)')
plt.ylabel('Counts')
plt.savefig(datadir + 'raw.png')

plt.figure(3)
olddata = np.loadtxt('/home/bladmin/SiW_for_LLNL/beamline_data/' + 
    'SiW49_NFM1C_R6_RR216/NFM1c_R6_RR216_21nov2016/reflectivity.txt')
plt.clf()
plt.plot(refl[:,0], refl[:,1], color='b', label=date+'\ncen @ 18.67')
plt.plot(olddata[:,0], olddata[:,1], color='r', label='21nov2016\ncen @ 18.73')
plt.legend()
plt.title('RR216 reflectivity measurement comparison')
plt.xlabel('Energy (kev)')
plt.ylabel('Reflectivity')
plt.xlim(0,40)
plt.savefig(datadir + 'comparison.png')
