import matplotlib.pyplot as plt
import numpy as np
import sys
sys.path.append('/home/bladmin/blcontrol/scripts')
from fwhm import cen_fwhm
import scipy.optimize as opt

energies = []
channels = []
fwhms    = []

#### Fe55 ####
Fe55spec = np.loadtxt('Fe55.txt')[:,1]

numchans = len(Fe55spec)

plt.figure(1)
plt.clf()
plt.title('Fe55')
plt.plot(Fe55spec)
plt.grid()
plt.ylabel('Energy (keV)')

Fe55peak1en = (5.88765*8.45 + 5.89875*16.57)/(8.45+16.57)
Fe55peak1ch, Fe55peak1fw = cen_fwhm(range(0,270), Fe55spec[0:270])
plt.axvline(x=Fe55peak1ch,color='g')
energies.append(Fe55peak1en)
channels.append(Fe55peak1ch)
fwhms.append(Fe55peak1fw)

#Fe55peak2en = 0.5*(6.49045+6.5352)
#Fe55peak2ch, Fe55peak2fw = cen_fwhm(range(280,290), Fe55spec[280:290])
#plt.axvline(x=Fe55peak2ch,color='g')
#energies.append(Fe55peak2en)
#channels.append(Fe55peak2ch)
#fwhms.append(Fe55peak2fw)

plt.xlim(0,numchans-1)
plt.savefig('Fe55.png')


###### Co57 ####
Co57spec = np.loadtxt('Co57.txt')[:,1]

plt.figure(2)
plt.clf()
plt.title('Co57')
plt.plot(Co57spec)
plt.grid()
plt.ylabel('Channel')

Co57peak1en = (6.391*16.4 + 6.404*32.5)/(16.4+32.5) # Fe K alpha
Co57peak1ch, Co57peak1fw = cen_fwhm(range(0,numchans), Co57spec)
plt.axvline(x=Co57peak1ch,color='g')
energies.append(Co57peak1en)
channels.append(Co57peak1ch)
fwhms.append(Co57peak1fw)

#Co57peak2en = 7.058 # Fe K beta
#Co57peak2ch, Co57peak2fw = cen_fwhm(range(305,315), Co57spec[305:315])
#plt.axvline(x=Co57peak2ch,color='g')
#energies.append(Co57peak2en)
#channels.append(Co57peak2ch)
#fwhms.append(Co57peak2fw)

Co57peak3en = 14.4119 # gamma M1
Co57peak3ch, Co57peak3fw = cen_fwhm(range(400,numchans), Co57spec[400:])
plt.axvline(x=Co57peak3ch,color='g')
energies.append(Co57peak3en)
channels.append(Co57peak3ch)
fwhms.append(Co57peak3fw)

plt.xlim(0,numchans-1)
plt.savefig('Co57.png')


##### Cs137 ####
Cs137specA = np.loadtxt('Cs137A.txt')[:,1]
Cs137specB = np.loadtxt('Cs137B.txt')[:,1]
Cs137spec = [A + B for A, B in zip(Cs137specA, Cs137specB)]

plt.figure(3)
plt.clf()
plt.title('Cs137')
plt.plot(Cs137spec)
plt.ylabel('Channel')
plt.grid()

Cs137peak1en = 32.194
Cs137peak1ch, Cs137peak1fw = cen_fwhm(range(0,numchans), Cs137spec)
plt.axvline(x=Cs137peak1ch,color='g')
energies.append(Cs137peak1en)
channels.append(Cs137peak1ch)
fwhms.append(Cs137peak1fw)

#Cs137peak2en = 36.357
#Cs137peak2fw, Cs137peak2ch = fwhm(range(6800,7050), Cs137spec[6800:7050])
#plt.axvline(x=Cs137peak2ch,color='g')
#energies.append(Cs137peak2en)
#channels.append(Cs137peak2ch)
#fwhms.append(Cs137peak2fw)

plt.xlim(0,numchans-1)
#plt.savefig('Cs137.png')


##### Fit ###

hw_gain = 29.999

def lin(x,m,b):
    return m*x+b

popt, pcov = opt.curve_fit(lin, channels, energies)
m = popt[0]
b = popt[1]

plt.figure('lin')
plt.clf()
plt.xlim(0,numchans)
x = range(numchans)
y = [lin(ch, m, b) for ch in x]
plt.plot(x, y, label='Fit')
plt.plot(channels, energies, 'o', label='Spectrum Peaks')
plt.legend()
plt.title('XR-100 SDD Calibration 20 April 2017')
plt.ylim(0,max(y))


conv_gain = 1./m
calib_factor = conv_gain /(hw_gain * numchans)
perr = np.sqrt(np.diag(pcov))

print "Actual:\t\tMeasured:\tFWHM:\n"
for i, en in enumerate(energies):
    print "{0:0.3f}\t\t{1:0.3f}\t\t{2:0.3f}".format(en, lin(channels[i],m,b),
                                                m*fwhms[i])
s = "calib factor = {0}\noffset = {1}".format(calib_factor, b)
print s

plt.text(1000, 20, s)

plt.savefig('linfit.png')
