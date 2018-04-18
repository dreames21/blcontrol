import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import erf


def fit_func(d, A, b, x0, y0):
    return A*(1-np.exp(-(d/2-x0)**2/b)) + y0

def find_HPD(x, y):
    # copy lists so insertion doesn't alter originals
    xdata = list(x)
    ydata = list(y)
    
    if xdata[0]:
        xdata.insert(0,0.)
        ydata.insert(0,0.)
        
    g = [300000, 1, 0, 0] #guess
    popt, pcov = curve_fit(fit_func, xdata, ydata, p0=g, maxfev=1000000)
    A, b, x0, y0 = popt

    #print popt

    half_pow = 0.5*(A+y0)
    HPD = 2*(np.sqrt(b*np.log(2*A/(y0+A)))+x0)
    print 'HPD = {0:0.3f} mm'.format(HPD)

    fig = plt.figure(1, (7,5))
    ax = fig.gca()
    plt.clf()
    plt.title('HPD Measurement')
    plt.xlabel('Pinhole diameter (mm)')
    plt.ylabel('Counts')
    plt.plot(xdata, ydata, 'o', label='Measured')
    xvals = np.linspace(0, 8, 1000)
    yvals = fit_func(xvals, A, b, x0, y0)
    plt.plot(xvals, yvals, label='Fit')
    #plt.plot(xvals, fit_func(xvals, g[0], g[1], g[2], g[3]), label='Guess')
    plt.plot([0,8], [half_pow, half_pow], c='r')
    plt.text(HPD+0.25, half_pow, 'HPD = {0:0.3f} mm'.format(HPD), va='bottom', ha='left',
             color='r')
    #yloc=0
    #for (i, x) in enumerate(xvals):
        #if x>= 0.387:
            #yloc = yvals[i]
            #break
    #plt.plot([0,8], [yloc, yloc], c='r')
    #plt.text(0.387+0.25, yloc, '387 microns, {0}% flux'.format(int(100*yloc/(half_pow*2))),
        #va='bottom', ha='left', color='r')
    
    plt.legend(loc='lower right')
    plt.xlim(0,6)
    minor_ticks = np.arange(0,6,0.5)
    major_ticks = np.arange(0,6,1)
    plt.xticks(minor_ticks)
    plt.ylim(ymin=0)
    plt.grid(which='both')
    plt.show()

if __name__ == "__main__":
    xdata = [0.5, 1, 2, 3, 4, 5]
    ydata = [17878, 39415, 48214, 50467, 51626, 52468]
    find_HPD(xdata, ydata)
