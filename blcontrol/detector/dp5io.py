""" This module defines classes for interacting with an Amptek DP5 device.

For a full description of the software capabilities of the DP5, see the
DP5 Programmer's Guide.
"""

import Queue
import serial
import struct
import threading
import time
from detector import pids
from detector.exceptions import (DeviceError, TimeoutError,
                                 UnexpectedReplyError)

class DP5Device(object):
    """A class representing a DP5 device.

    Attributes:
        config (ConfigParser): Represents the configuration file for the
            detector.
        port (DP5Serial): Serial port to which the detector is connected.
        dtype (str): Type of detector (SDD or CdTe, for example)
        calibration (tuple of floats): Calibration factor and offset for
            converting from channel to energy.
        gain (float): Amplifier gain setting.
        num_chans (int): Number of MCA channels in use.
    """
    def __init__(self, config):
        self.config = config
        serialport = self.config.get("Detector Port", "serialport")
        to = self.config.getint("Detector Port", "timeout")
        br = self.config.getint("Detector Port", "baudrate")
        self._port = serial.Serial(port=serialport, timeout=to, baudrate=br)
        #self._port.flushInput()

        # The following 2 lines will raise TimeoutError if det is not
        # connected/ready
        self._write(pids.ECHO_REQ, "Detector Ready")
        self._read()
        
        self._lock = threading.Lock()  #read/write lock for serial port access
        self.status_queue = Queue.Queue()
        self.status_thread = StatusThread(self)
        self.status_thread.start()
        
    @property
    def is_connected(self):
        return self._port.is_open
        
    def reconnect(self):
        if not self.is_connected:
            self._port.open()
            self.status_thread = StatusThread(self)
            self.status_thread.start()

    def disconnect(self):
        if self.is_connected:
            if self.status_thread.is_alive():
                self.status_thread.stop()
                self.status_thread.join()
            self._port.close()

    def send(self, *args):
        """Sends a command and checks the reply for errors.

        Note: Blocks until a reply is received or port times out.  The DP5
        should return either a response or acknowledge packet immediately after
        receiving a command.
        
        Args: a DP5Command or pid and data representing the command to be sent
            to the DP5.

        Returns (DP5Reply): Reply received from the device.
        """
        with self._lock:
            self._write(*args)
            reply = self._read()
        return reply

    def _write(self, *args):
        #self._port.flush()
        if len(args) == 2:
            pid, data = args
            command = DP5Command(pid, data)
        else:
            command = args[0]
        if isinstance(command, int) or isinstance(command, str):
            output = DP5Command(command).encode()
        elif isinstance(command, DP5Command):
            output = command.encode()
        else:
            raise TypeError("`command` type invalid")
        self._port.write(output)

    def _read(self):
        """Reads a reply from the device.

        Raises:
            DeviceError: The device replied with an error condition.
            TimeoutError: Read timed out or synced incorrectly.
            ValueError: Device reply has bad checksum.
            
        Returns: A DP5Reply object encoding the packet received.
        """
        first = self._port.read(2)
        if first != pids.SYNC:
            raise TimeoutError('Read timed out. Check detector connection.')
        header = first + self._port.read(4)
        datalen = byte2int(header[4:6], little_endian=False)
        data = self._port.read(datalen)
        checksum = self._port.read(2)
        if len(header) + len(data) + len(checksum) != datalen + 8:
            raise TimeoutError('Read timed out.  Check detector connection.')
        reply = DP5Reply(header, data, checksum)
        if reply.pid[0] == pids.ACK and reply.pid != pids.ACK_OK:
            errorstr = pids.ERRORS[reply.pid]
            errmsg = 'DP5 Device returned error: {0}: "{1}"'.format(errorstr,
                                                                  reply.data)
            raise DeviceError(errmsg)
        elif not reply.is_checksum_good():
            raise ValueError('Bad checksum in reply')
        else:
            return reply

    def enable_mca(self):
        """Enables the MCA.

        Raises:
            UnexpectedReplyError: Device reply is not an Ack OK packet.
        """
        reply = self.send(DP5Command(pids.ENMCA))
        if reply.pid != pids.ACK_OK:
            raise UnexpectedReplyError(reply.pid)

    def disable_mca(self):
        """Disables the MCA.

        Raises:
            UnexpectedReplyError: Device reply is not an Ack OK packet.
        """
        reply = self.send(DP5Command(pids.DISMCA))
        if reply.pid != pids.ACK_OK:
            raise UnexpectedReplyError(reply.pid)

    def begin_acq(self, acqtime):
        """ Begins acquisition for a set time period.

        Args:
            acqtime (float): The time to acquire the spectrum.
        """
        self.clear_spectrum()
        self.set_setting('PRET', acqtime)
        self.enable_mca()

    def get_spectrum(self):
        """Requests the spectrum in the buffer and status packet.

        Raises:
            UnexpectedReplyError: Reply is not a spectrum + status
                packet.

        Returns: A Spectrum object representing the reply received.
        """
        reply = self.send(DP5Command(pids.GETSPECSTAT))
        try:
            numchans = pids.SPEC_CHAN[reply.pid]
        except KeyError:
            raise UnexpectedReplyError(reply.pid)
        specdata = reply.data[:numchans*3]
        spectrum = [byte2int(specdata[i:i+3]) for i in range(0,len(specdata),3)]
        statdata = reply.data[numchans*3:]
        status = parse_status(statdata)
        return spectrum, status
        
    def clear_spectrum(self):
        """Clears the current MCA spectrum.

        Raises:
            UnexpectedReplyError: Device reply is not an Ack OK packet.
        """
        reply = self.send(DP5Command(pids.CLRSPEC))
        if reply.pid != pids.ACK_OK:
            raise UnexpectedReplyError(reply.pid)

    def arm_scope(self):
        """Arms the digital oscilloscope."""
        reply = self.send(DP5Command(pids.ARMSCOPE))
        if reply.pid != pids.ACK_OK:
            raise UnexpectedReplyError(reply.pid)

    def get_scopedata(self, out='SHAPED'): 
        """Reads digital oscilloscope readout data.

        Args:
            out (str): The type of output signal to display on the scope.

        Raises:
            ValueError: `out` is not one of 'SHAPED', 'FAST', 'INPUT' or 'PEAK'.

        Returns: A tuple of two lists: (time, voltages) where `time` is in ms
            and `voltages` is in volts.
        """
        if out.upper() not in ('SHAPED', 'FAST', 'INPUT', 'PEAK'):
            raise ValueError('Invalid output type')
        self.set_setting('DACO', out.upper())
        reply = self.send(DP5Command(pids.GETSCOPE))
        if reply.pid not in (pids.SCOPEDATA, pids.SCOPE_OVFL):
            raise UnexpectedReplyError(reply.pid)
        voltages = [byte2int(byte)/256. for byte in reply.data]
        fpga_clock = self.get_status()['clock_MHz']
        if fpga_clock == 20:
            tb_dict = pids.SCOPE_TB_FPGA20
        elif fpga_clock == 80:
            tb_dict = pids.SCOPE_TB_FPGA80
        peaktime = float(self.get_setting('TPEA'))
        for key, value in tb_dict.iteritems():
            if key[0] <= peaktime <= key[1]:
                timebase = value
                break
        time = [timebase*i for i in range(len(reply.data))]
        return time, voltages

    def set_setting(self, param, value):
        """Sets the value of an ASCII setting parameter.

        Args:
            param(str): A 4 character ASCII string representing the
                setting to be edited.
            value: A number or string representing the value of the
                parameter to be set. Will be converted to a string.

        Raises:
            UnexpectedReplyError: Device returns an unexpected reply.

        Returns:
            A string representing the resulting parameter value pair.

        See DP5 Programmer's Guide section 5 for possible parameters and
        their allowed values.
        """
        data = "{0}={1};".format(param.upper(), str(value))
        command1 = DP5Command(pids.CONFIG, data)
        reply1 = self.send(command1)
        if reply1.pid != pids.ACK_OK:
            raise UnexpectedReplyError(reply1.pid)

    def set_settings_dict(self, settings_dict):
        datastr = ''
        for param, value in settings_dict.iteritems():
            datastr += '{0}={1};'.format(param.upper(), value)
        command = DP5Command(pids.CONFIG, datastr)
        reply = self.send(command)
        if reply.pid != pids.ACK_OK:
            raise DeviceError(reply.data)

    def get_setting(self, arg):
        """Returns the value of a list of ASCII parameters.

        Args:
            arg: Either a list of four letter parameter strings, or
                a single string with parameters separated by semicolons.

        Raises:
            UnexpectedReplyError: Device returns an unexpected
                reply.

        Returns:
            A string containing the values of the requested parameters.

        See Section 5.1 in the DP5 Programmer's Guide for a list of
        allowed parameters.
        """
        param = arg.upper() + ';'
        command = DP5Command(pids.CONFIG_REQ, param)
        reply = self.send(command)
        if reply.pid != pids.CONFIG_READ:
            raise UnexpectedReplyError(reply.pid)
        res = reply.data.rstrip(';').split('=')[1]
        return res

    def get_settings_dict(self, params_list):
        data = ''
        for param in params_list:
            data += param.upper() + ';'
        command = DP5Command(pids.CONFIG_REQ, data)
        reply = self.send(command)
        if reply.pid != pids.CONFIG_READ:
            raise UnexpectedReplyError(reply.pid)
        res = reply.data.rstrip(';').split(';')
        settings_dict = {}
        for s in res:
            key, value = s.split('=')
            settings_dict[key] = value
        return settings_dict

    def get_all_settings(self):
        """Return a dictionary of all settings of the detector."""
        resp1 = self.get_settings_dict(pids.SETTINGS_LIST[0:18])
        resp2 = self.get_settings_dict(pids.SETTINGS_LIST[18:36])
        resp3 = self.get_settings_dict(pids.SETTINGS_LIST[36:])
        settings_dict = {}
        for d in (resp1, resp2, resp3):
            settings_dict.update(d)
        if settings_dict['RTDE'] == 'ON':
            respr = self.get_settings_dict(pids.RTD_SETTINGS)
            settings_dict.update(respr)
        for sca in range(1, 17):
            self.set_setting(pids.SCA_INDEX, sca)
            resps = self.get_settings_dict(pids.SCA_SETTINGS16)
            for i in resps:
                settings_dict.update(resps)
            if sca <= 8:
                resps8 = {pids.SCA_OUTPUT:self.get_setting(pids.SCA_OUTPUT)}
                settings_dict.update(resps)
        return settings_dict

    def get_status(self):
        """Requests a status packet from the detector.

        Returns (dict): Parsed detector status information."""
        reply = self.send(pids.GETSTAT)
        if reply.pid != pids.STATUS:
            raise UnexpectedReplyError(reply.pid)
        return parse_status(reply.data)

    @property
    def sernum(self):
        """Returns the detector serial number (int)"""
        return self.get_status()['serial number']

    @property
    def calibration(self):
        """Returns a tuple of the form (calib_factor, offset).

        To obtain energy from channel number:
            E = chan/((calib_factor)*(hardware_gain)*(num_chans)) + offset
        """
        config_section = "{0} Calib".format(self.sernum)
        calib_factor = self.config.getfloat(config_section, "calib_factor")
        offset = self.config.getfloat(config_section, "offset")
        return calib_factor, offset

    @property
    def gain(self):
        """Returns total amplifier gain."""
        return float(self.get_setting("GAIN"))

    @gain.setter
    def gain(self, g):
        """Sets the total amplifier gain."""
        self.set_setting("GAIN", round(float(g), 4))

    @property
    def num_chans(self):
        """Returns the number of MCA channels in use."""
        return int(self.get_setting("MCAC"))

    #def chan2energy(self, chan):
        #"""Convert from channel number to channel energy.

        #Returns: energy of the given channel number in keV."""
        calib_factor, offset = self.calibration
        return chan/(calib_factor*self.gain*self.num_chans) + offset

    def energy2chan(self, energy):
        """Convert from channel number to channel energy.

        Returns: the MCA channel corresponding to the given energy."""
        calib_factor, offset = self.calibration
        return int(round((energy - offset)*calib_factor*self.gain
                   *self.num_chans))

    def get_energies(self):
        """Return a list of energy bins in use in the MCA."""
        calib_factor, offset = self.calibration
        chans = self.num_chans
        gain = self.gain
        return [ch/(calib_factor*gain*chans) + offset for ch in range(chans)]


class DP5Command(object):
    """A class for creating commands to be sent to the DP5."""

    def __init__(self, pid, data=''):
        """Creates a new instance of DP5Command class.

        Args:
            pid (str): A 2-byte string representing the Packet ID for
                the command to be sent.
            data (str): An optional string, 512 bytes or fewer in
                length, of data to be sent in the packet to the DP5.
                The format of the data field depends on the type of
                packet. See the DP5 Programmer's Guide for details.

        Raises:
            ValueError: `pid` is not 2 bytes in length, or `data`
                exceeds 512 bytes in length.
        """
        if len(pid) != 2:
            raise ValueError("`pid` must be exactly 2 bytes in length.")
        if len(data) >= 512:
            raise ValueError("Length of `data` string exceeds 512 "
                             "bytes.")
        self.pid = pid
        self.data = data

    def get_len(self):
        """Calculates the length of the data field.

        Returns:
            A 2-character string whose ASCII codes are the most- and
            least-significant byte of the length of the data field.
        """
        intlen = len(self.data)
        lenmsb = intlen / 256
        lenlsb = intlen - lenmsb * 256
        return chr(lenmsb) + chr(lenlsb)

    def get_checksum(self):
        """Calculates the checksum of the packet.

        Returns:
            A 2-character string representing the most- and least-
            significant bytes of the two's-complement of the sum of all
            bytes in packet.
        """
        packet = pids.SYNC + self.pid + self.get_len() + self.data
        mod = 1 << 16
        ints = [ord(char) for char in packet]
        packetsum = add16b(ints)
        intchksum = mod - packetsum
        chkmsb = intchksum / 256
        chklsb = intchksum - chkmsb * 256
        return chr(chkmsb) + chr(chklsb)

    def encode(self):
        """Encodes a packet to be sent to the DP5 as a byte string.

        Returns:
            A byte string formatted according to the DP5 Programmer's
            Guide.
        """
        return (pids.SYNC + self.pid + self.get_len() + self.data +
                self.get_checksum())


class DP5Reply(object):
    """A class for parsing replies from the DP5.

    Attributes:
        pid (str): A 2-byte string encoding the pid of the reply.
        length (str): A 2-byte string encoding the length of the reply.
        data (str): A bytestring encoding the data field of the reply.
        checksum (str): A 2-byte string encoding the checksum of the reply.
    """

    def __init__(self, header, data, checksum):
        """
        Args:
            header (str): A 6-byte string representing the header data
                received.  Includes the sync, PID, and len fields.
            data (str): The contents of the data field from the packet
                received.
            checksum (str): A 2-byte string encoding the checksum of the
                packet, i.e. the last two bytes received.
        """
        self.pid = header[2:4]
        self.length = header[4:6]
        self.data = data
        self.checksum = checksum

    def encode(self):
        """Returns the reply as a binary string in the form it was received."""
        return (pids.SYNC + self.pid + self.length + self.data +
                self.checksum)

    def is_checksum_good(self):
        """Verifies that the checksum from the reply is valid.

        The checksum is valid if the 16-bit sum of the checksum and all
        other bytes in the packet is zero.

        Returns: True if the checksum is valid, False otherwise.
        """
        encoded = self.encode()
        packet = encoded[:len(encoded)-2]
        checksum = encoded[len(encoded)-2:]
        intchecksum = byte2int(checksum, little_endian=False)
        ints = [ord(char) for char in packet]
        packetsum = add16b(ints)
        return add16b((packetsum, intchecksum)) == 0

def parse_status(status_data):
    """Parses a DP5 status bytestring into a dict."""
    return {
        'fast count': byte2int(status_data[0:4]),
        'slow count': byte2int(status_data[4:8]),
        'GP count': byte2int(status_data[8:12]),
        'accumulation time': (ord(status_data[12])/100.0 +
                             byte2int(status_data[13:16]))/10.0,
        'real time': byte2int(status_data[20:24])/1000.0,
        'firmware version': (ord(status_data[24]) & 0b11110000)/16 +
                            0.01*(ord(status_data[24]) & 0b1111),
        'FPGA version': (ord(status_data[25]) & 0b11110000)/16 +
                         0.01*(ord(status_data[25]) & 0b1111),
        'serial number': byte2int(status_data[26:30]),
        'high voltage': 0.5*byte2int(status_data[30:32],
                                     little_endian=False, signed=True),
        'detector temperature (K)': 0.1*byte2int(chr(ord(status_data[32])
                                                 &0b1111) + status_data[33],
                                             little_endian=False),
        'board temperature (C)': byte2int(status_data[34],
                                          little_endian=True, signed=True),
        'preset real time reached': bool(ord(status_data[35])&1<<7),
        'auto fast threshold locked': bool(ord(status_data[35])&1<<6),
        'MCA enabled': bool(ord(status_data[35])&1<<5),
        'preset counts reached': bool(ord(status_data[35])&1<<4),
        'GATE enabled': not bool(ord(status_data[35])&1<<3),
        'scope data ready': bool(ord(status_data[35])&1<<2),
        'unit is configured': bool(ord(status_data[35])&1<<2),
        'auto input offset searching': bool(ord(status_data[36])&1<<7),
        'MCS finished': bool(ord(status_data[36])&1<<6),
        'first packet since reboot': bool(ord(status_data[36])&1<<5),
        'FPGA clock freq (MHz)': [20, 80][(ord(status_data[36])&2)/2],
        'FPGA clock autoset': bool(ord(status_data[36])&1),
        'firmware build number': ord(status_data[37])&0b1111,
        'PC5 detected': bool(ord(status_data[38])&1<<7),
        'high voltage polarity': ['neg', 'pos'][(ord(status_data[38])&1<<6)/
                                                (1<<6)],
        'preamp voltage': [5., 8.5][(ord(status_data[38])&1<<5)/(1<<5)],
        'device type': ['DP5', 'PX5', 'DP5G', 'MCA8000D'][ord(
                                                          status_data[39])],
        'list-mode clock (us)': [0.1, 1.][(ord(status_data[43])&4)/4],
        'list-mode sync': ['INT', 'NOTIMETAG', 'EXT', 'FRAME'][
                                                 ord(status_data[43])&0b11],
        'AN_IN': byte2int(chr(ord(status_data[44])&0b11) + status_data[45],
                          little_endian=False)/419.7,
        'sequential buffering is running': bool(ord(status_data[46])&1<<1),
        'current sequential buffer': byte2int(chr(ord(status_data[46])&1) +
                                           chr(47))
    }


class StatusThread(threading.Thread):
    def __init__(self, det):
        super(StatusThread, self).__init__()
        self._stopper = threading.Event()
        self.det = det
        self.daemon = True

    def run(self):
        sets = ['PRET', 'MCAC', 'THSL', 'THFA', 'GAIN', 'TPEA', 'TECS']
        while not self._stopper.is_set():
            status = self.det.get_status()
            settings = self.det.get_settings_dict(sets)
            self.det.status_queue.put((status, settings))
            time.sleep(0.5)

    def stop(self):
        self._stopper.set()

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
