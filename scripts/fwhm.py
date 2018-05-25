import numpy as np
from scipy import interpolate, optimize

def cen_fwhm(xdata, ydata):
    """Calculates the center and full width at half maximum of y=f(x).

    This function only finds the tallest peak in the data, i.e. the GLOBAL
    maximum. To use on data with multiple peaks, it is necessary to split the
    data set up into chunks containing the different peaks.
    
    Args:
        xdata (list/array): the independent variable, x-values
        ydata (list/array): the dependent variable, y-values. Must be same
        length as xdata.

    Returns: A tuple containing the centroid of the peak and its calculated
        FWHM.
    """
    
    # copy and convert to numpy arrays
    xlist = np.array(xdata)
    ylist = np.array(ydata)

    # sort data so that x is in ascending order
    idx   = np.argsort(xlist)
    xlist = xlist[idx]
    ylist = ylist[idx]
    
    assert len(xlist) == len(ylist)
    max_ind = np.argmax(ylist)
    max_x = xlist[max_ind]

    # subtract half maximum from y-values so that the problem of calculating
    # FWHM becomes the problem of finding the zeroes
    ylist -= ylist.min()
    ylist -= ylist[max_ind]/2

    # interpolate a function that represents the data
    interp = interpolate.interp1d(xlist, ylist)

    brack_left_ind = brack_right_ind = max_ind

    # iterate to the left of the peak until we find a value that's below 0
    while ylist[brack_left_ind] > 0 and brack_left_ind > 0:
        brack_left_ind -=1
    # if we found no values that are below zero, then just use the smallest x
    # value as the "zero" of the function
    if ylist[brack_left_ind] > 0:
        hm_left = xlist[0]
    # if we found a negative value, that means that the function has a zero
    # in this region. use Brent's method to find the zero of the interpolated
    # function.
    else:
        brack_left = xlist[brack_left_ind]
        hm_left = optimize.brentq(interp, brack_left, max_x)

    # repeat the above iteration on the right side of the peak
    while ylist[brack_right_ind] > 0 and (brack_right_ind < len(xlist) - 1):
        brack_right_ind += 1
    if brack_right_ind == len(xlist) - 1:
        hm_right = xlist[-1]
    else:
        brack_right = xlist[brack_right_ind]
        hm_right = optimize.brentq(interp, max_x, brack_right)

    fw = hm_right - hm_left
    cen = (hm_right + hm_left)/2.
    return cen, fw
