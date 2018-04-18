import numpy as np
from scipy import interpolate, optimize

def cen_fwhm(xdata, ydata):
    xdata = list(xdata)
    ydata = list(ydata)
    assert len(xdata) == len(ydata)
    ydata -= min(ydata)
    max_y = max(ydata)
    max_ind = ydata.tolist().index(max_y)
    max_x = xdata[max_ind]
    ydata -= max_y/2.
    interp = interpolate.interp1d(xdata, ydata)

    brack_left_ind = brack_right_ind = max_ind
    while ydata[brack_left_ind] > 0 and brack_left_ind > 0:
        brack_left_ind -=1
    if brack_left_ind == 0:
        hm_left = xdata[0]
    else:
        brack_left = xdata[brack_left_ind]
        hm_left = optimize.brentq(interp, brack_left, max_x)
        
    while ydata[brack_right_ind] > 0 and (brack_right_ind < len(xdata) - 1):
        brack_right_ind += 1
    if brack_right_ind == len(xdata) - 1:
        hm_right = xdata[-1]
    else:
        brack_right = xdata[brack_right_ind]
        hm_right = optimize.brentq(interp, max_x, brack_right)

    fw = hm_right - hm_left
    cen = (hm_right + hm_left)/2.
    return cen, fw
