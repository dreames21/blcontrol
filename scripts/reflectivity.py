import numpy as np
import matplotlib.pyplot as plt
from fwhm import cen_fwhm

datadir = '/home/bladmin/SiW_for_LLNL/optic_data/SiW69_NFM1C_R11_RR305/beamline_data'
if datadir[-1] is not '/':
    datadir += '/'
samplename = 'SiW69'
date = '19Dec2016'
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
cen, fwhm = cen_fwhm(refl[1000:,0], refl[1000:,1])
max_refl = max(refl[1000:,1])
print 'Cen = {0:0.2f} keV\nFWHM = {1:0.2f} keV'.format(cen, fwhm)

np.savetxt(datadir + 'reflectivity_nofilter.txt', refl)

plt.figure(1)
plt.clf()
plt.axvline(x=line_energy ,ymin=0, ymax=1, color='g', lw=2, label=line_name +
	'\n' + str(line_energy) + ' keV')
plt.plot(refl[:,0], refl[:,1], color='b', label='Measured Reflectivity')
plt.plot([cen-fwhm/2., cen+fwhm/2.], [max_refl/2, max_refl/2],
    color='r')
plt.text(cen+fwhm, max_refl/2,
    'FWHM = {0:0.2f} keV\n     @ {1:0.2f} keV'.format(fwhm, cen), color='r')
plt.text(cen, max_refl,
         "Max reflectivity = {0:0.2f}".format(max_refl), color='r',
         va='bottom')
plt.xlim(0,30)
plt.xlabel('Energy (keV)')
plt.ylabel('Reflectivity')
plt.title(samplename + ' reflectivity with Al filter, ' + date)
plt.legend(loc='upper left')
plt.grid()

#plt.savefig(datadir + 'refl_Alfilter.png')
plt.show()

plt.figure(2)
plt.clf()
plt.plot(bg[:,0], bg[:,1])
plt.plot(opt[:,0], opt[:,1])
plt.xlim(0,30)
plt.title(samplename + ' raw data, ' + date)
plt.xlabel('Energy (keV)')
plt.ylabel('Counts')
plt.grid()
plt.savefig(datadir + 'raw_Alfilter.png')

src_scale_fac = 0.000002

plt.figure(3)
plt.clf()
plt.axvline(x=line_energy ,ymin=0, ymax=1, color='g', lw=2, label=line_name +
	'\n' + str(line_energy) + ' keV')
plt.plot(refl[:,0], refl[:,1], color='b', label='Measured Reflectivity')
plt.plot(bg[:,0], bg[:,1]*src_scale_fac, color='grey',
    label="Source spectrum\n(multiplied by {0:0g})".format(src_scale_fac))
plt.plot([cen-fwhm/2., cen+fwhm/2.], [max_refl/2, max_refl/2],
    color='r')
plt.text(cen+fwhm, max_refl/2,
    'FWHM = {0:0.2f} keV\n     @ {1:0.2f} keV'.format(fwhm, cen), color='r')
plt.text(cen, max_refl,
         "Max reflectivity = {0:0.2f}".format(max_refl), color='r',
         va='bottom')
plt.xlim(6,30)
plt.ylim(0,0.4)
plt.xlabel('Energy (keV)')
plt.ylabel('Reflectivity')
plt.title(samplename + ' reflectivity with Al filter, ' + date)
plt.legend(loc='upper right')
plt.grid()
plt.savefig(datadir + samplename+ '_refl+src_Alfilter.png')


#plt.figure(3)
#olddata = np.loadtxt('/home/bladmin/SiW_for_LLNL/beamline_data/' + 
    #'SiW49_NFM1C_R6_RR216/NFM1c_R6_RR216_21nov2016/reflectivity.txt')
#plt.clf()
#plt.plot(refl[:,0], refl[:,1], color='b', label=date+'\ncen @ 18.67')
#plt.plot(olddata[:,0], olddata[:,1], color='r', label='21nov2016\ncen @ 18.73')
#plt.legend()
#plt.title('RR216 reflectivity measurement comparison')
#plt.xlabel('Energy (kev)')
#plt.ylabel('Reflectivity')
#plt.xlim(0,30)
#plt.savefig(datadir + 'comparison.png')
