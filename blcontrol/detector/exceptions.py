""" This module defines special exceptions raised by the `dp5io` module.
"""

class DeviceError(Exception):
    """Exception raised when device returns an error condition."""
    pass

class TimeoutError(Exception):
    """Exception raised when read times out."""
    def __str__(self):
        return "Read timed out."

class ChecksumError(Exception):
    """Exeption raised when reply from device has bad checksum."""
    def __str__(self):
        return "Bad checksum in reply."

class UnexpectedReplyError(Exception):
    """Exception raised when device returns an unexpected reply."""
    def __init__(self, pid, message=None):
        super(UnexpectedReplyError, self).__init__(message)
        self.pid = pid

    def __str__(self):
        return "Unexpected reply from device: {0}".format(self.pid)
