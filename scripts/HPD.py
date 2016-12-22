import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def fit_func(d, A, b, x0, y0):
    return A*(1-np.exp(-(d/2-x0)**2/b)) + y0

def find_HPD(ydata):
    xdata = [0., 1., 2., 3., 4., 5.]
    if ydata[0]:
        ydata.insert(0, 0.)
    g = [25000, 4, 0, 0] #guess
    popt, pcov = curve_fit(fit_func, xdata, ydata, p0=g, maxfev=10000)
    A, b, x0, y0 = popt

    half_pow = 0.5*(A+y0)
    HPD = 2*(np.sqrt(b*np.log(2*A/(y0+A)))+x0)
    print 'HPD = {0:0.2f} mm'.format(HPD)

    plt.figure(1)
    plt.title('HPD Measurement')
    plt.xlabel('Pinhole diameter')
    plt.ylabel('Counts')
    plt.plot(xdata, ydata, 'o', label='Measured')
    xvals = np.linspace(0, 10, 1000)
    plt.plot(xvals, fit_func(xvals, A, b, x0, y0), label='Fit')
    plt.plot([0,10], [half_pow, half_pow], c='r')
    plt.text(HPD+0.25, half_pow, 'HPD = {0:0.2f} mm'.format(HPD), va='bottom', ha='left',
             color='r')
    plt.legend(loc='upper left')
    plt.show()
