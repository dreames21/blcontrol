import ConfigParser
import os
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
