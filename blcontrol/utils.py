import ConfigParser
import numpy as np
import os
import Queue
from scipy import interpolate, optimize
import struct


def add16b(sequence):
    """Implements 16 bit addition of integers.

    Arguments:
        sequence: a list or tuple of integers.

    This implementation does not include adding back in the carry-over
    digits.  It simply returns the sum of the arguments masked by
    0xFFFF.
    """
    result = sum(sequence)
    if not isinstance(result, int):
        raise ValueError("Arguments must be of type int.")
    return result & 0xFFFF


def byte2int(bytestring, little_endian=True, signed=False):
    """Converts a byte string to a base 10 integer.

    Args:
        bytestring (str): A byte string representation of an integer.
        little_endian (bool): Indicator of the endianness of the string.
            If little_endian == True, then the leftmost byte in the
            string is the least significant, otherwise it is the most.
        signed (bool): True if `bytestring` is signed, False otherwise.
    """
    if signed:
        fmtstr = 'b'*len(bytestring)
        bytesize = 7
    else:
        fmtstr = 'B'*len(bytestring)
        bytesize = 8
    unpacked = struct.unpack(fmtstr, bytestring)
    if little_endian:
        places = range(len(unpacked))
    else:
        places = list(reversed(range(len(unpacked))))
    result = 0
    for i in range(len(bytestring)):
        result += (1<<bytesize)**places[i]*unpacked[i]
    return result


def load_conf_file(conf_path='~/.blconf'):
    xconfpath = os.path.expanduser(conf_path)
    config = ConfigParser.SafeConfigParser()
    configfile = open(xconfpath, 'r')
    config.readfp(configfile)
    configfile.close()
    return config


def cen_fwhm(xdata, ydata):
    xdata = np.array(xdata)
    ydata = np.array(ydata, dtype=float)
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


def com(array, xvals, yvals):
    array -= array.min()
    try:
        xcounts = array.sum(1).tolist()
        xmoms = [xcounts[i]*value for i, value in enumerate(xcounts)]
        xcom = sum(xmoms)/sum(xcounts)
    except ZeroDivisionError:
        ## if there are no counts then return the geometric center
        xcom = 0.5*(xvals[0] + xvals[-1])
    try:
        ycounts = array.sum(0).tolist()
        ymoms = [ycounts[i]*value for i, value in enumerate(ycounts)]
        ycom = sum(ymoms)/sum(ycounts)
    except ZeroDivisionError:
        ycom = 0.5*(yvals[0] + yvals[-1])
    return (xcom, ycom)


class SingleValQueue(Queue.Queue):
    def __init__(self):
        Queue.Queue.__init__(self, maxsize=1)

    def put(self, item):
        if self.full():
            self.get()
        Queue.Queue.put(self, item)
