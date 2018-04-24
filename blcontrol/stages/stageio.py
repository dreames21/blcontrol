"""This module defines classes for communication with beamline stages."""

import ConfigParser
import os
import Queue
import serial.tools.list_ports
import threading
import time
import zaber.serial as zb

import stages.commands as com

class StageIO(object):
    """Class for communication with motors.

    Attributes:
        config (ConfigParser): A configuration object with serial port and motor
            configuration information.
        motors (dict): Maps motor names to the corresponding Motor objects.
        motors_by_num (dict): Maps motor numbers to Motor objects.
        port (zaber.serial.BinarySerial): Represents the serial port to which
            the motor controllers are connected.
    """
    
    def __init__(self, config):
        """Inits StageIO using configuration parameters.

        Args:
            config (ConfigParser): Contains the serial port information and all
                necessary motor configuration parameters.
        """
        self.config = config
        self.zeroposconfig = ZeroPosConfig()
        self.motors = {}
        self.motors_by_num = {}
        self._find_port()
        self.port.timeout = self.config.getint('Stage Port', 'timeout')
        self.initialize_motors()
        
    def _find_port(self):
        """Find the USB port to which the devices are connected.
        
        Uses the serial number of the USB-to-serial converter found
        in self.config.  If not found, uses the serial port path found
        in self.config.
        """
        usbsnr = self.config.get('Stage Port', 'usbsn')
        matches = []
        for i in serial.tools.list_ports.grep(usbsnr):
            matches.append(i)
        if len(matches) == 0: # try serial if no usb found
            portpath = self.config.get('Stage Port', 'serialport')
        else:
            portpath = matches[0][0]
        baudrate = self.config.getint('Stage Port', 'baudrate')
        self.port = zb.BinarySerial(portpath, baud=baudrate,
                                    inter_char_timeout=None)
        self.port._ser.flushInput()

    def initialize_motors(self):
        """Populates `self.motors` with objects for each connected motor."""
        old_timeout = self.port.timeout  # Save previous timeout
        try:
            #Set timeout to 0.5 seconds.  The number of motors is
            #determined by how many replies are read before a timeout occurs.
            self.port.timeout = 0.5
            self.port._ser.reset_input_buffer()
            sernums = {}
            self.send_all(com.SERNUM)
            while True:
                try:
                    reply = self.port.read()
                    sernums[reply.device_number] = reply.data
                except zb.exceptions.TimeoutError:
                    break
            pos_queues = {}
            reply_queues = {}
            for motor_num, sernum in sernums.iteritems():
                motor = Motor(motor_num, self.port, self.config,
                              self.zeroposconfig)
                self.motors_by_num[motor_num] = motor
                pos_queues[motor_num] = motor.pos_queue
                reply_queues[motor_num] = motor.reply_queue
            self.reader = SerialPortReader(self.port, pos_queues, reply_queues)
            self.reader.start()
        finally:
            self.port.timeout = old_timeout # Restore previous timeout
        for motor in self.motors_by_num.values():
            motor.post_init()
        self.motors = {motor.name : motor for motor in self.motors_by_num.values()}
                
    def send_all(self, command_num, data=0):
        """Send a command to all connected motors."""
        self.port.write(0, command_num, data)

    def stop_all(self):
        """Send a stop command to all connected motors."""
        self.send_all(com.STOP)

    def enable_move_tracking(self):
        """Enables regular and manual move tracking for all motors."""
        self.send_all(com.GET, com.MODE)
        for motor in self.motors.values():
            current_mode = motor.get_reply(com.MODE).data
            move_tracking_bit = 1<<4
            man_mvt_disabled_bit = 1<<5
            delta = 0
            if not current_mode & move_tracking_bit:
                delta += move_tracking_bit
            if current_mode & man_mvt_disabled_bit:
                delta -= man_mvt_disabled_bit
            if delta:
                new_mode = current_mode + delta
                motor.send(com.MODE, new_mode)


class Motor(object):
    """Class representing a motor controller on the beamline.

    Attributes:
        number (int): The motor number assigned by controller firmware according
            to distance from the computer, with 1 being closest.
        port (zaber.serial.BinarySerial): The port to which the motor controller
            is connected.
        config (ConfigParser): A configuration object containing the name,
            travel, and resolution information for the motor.
        reply_queue (Queue): Holds replies from the motor controller.
        pos_queue (Queue): Holds position information from the controller.
        resolution (float): The motor's resolution in steps/mm or steps/degree.
        sernum (int): Serial number of the motor.
        name (str): The name of the motor, user-defined in `self.config`.
        travel (float): The stage's total travel in mm, or None for rotary
            stages.
    """
    
    def __init__(self, number, port, config, zeroposconfig):
        """Initializes the Motor object."""
        self.number = number
        self.port = port
        self.config = config
        self.zeroposconfig = zeroposconfig
        self.reply_queue = Queue.Queue()
        self.pos_queue = SingleValQueue()

    def post_init(self):
        self.set_name()
        self.set_resolution()
        
    def send(self, commandnum, data=0):
        """Send a command to the motor controller."""
        self.port.write(self.number, commandnum, data)

    def get_reply(self, commandnum=None, blocking=True, timeout=False):
        """Read a reply from the motor controller.

        Args:
            commandnum (int, optional): If provided, this method will return
                only a reply with this command number.

        Raises:
            Timeout Error: A reply (optionally with the specified command
                number) was not received within the serial port's timeout, if
                blocking.

        Returns (zaber.serial.BinaryReply):
            The reply received from the motor controller.
        """
        if timeout:
            to = self.port.timeout
        else:
            to = None
        try:
            reply = self.reply_queue.get(block=blocking, timeout=to)
            if commandnum is not None:
                while (reply.command_number != commandnum):
                    reply = self.reply_queue.get(block=blocking, timeout=to)
        except Queue.Empty:
            raise zb.exceptions.TimeoutError('Read timed out.')
        return reply
            
    def stepdata2pos(self, stepdata):
        """Converts steps to real units based on resolution and zero position."""
        return round((stepdata - self.zeropos)*self.resolution, 4)

    def pos2stepdata(self, pos):
        """Converts real units to steps based on resolution and zero position."""
        return int(pos/self.resolution + self.zeropos)

    def get_tracking_pos(self):
        """Reads latest position from position tracking queue.  Blocks
        until tracking data is received."""
        return self.stepdata2pos(self.pos_queue.get_nowait())
        
    def is_in_range(self, position):
        """Returns True if the given position is in the range of the
        stage's travel, False otherwise.  Always True for rotation stages."""
        zp = self.zeropos*self.resolution
        return (not self.travel or ((position + zp >= 0)
                    and (position + zp <= self.travel)))

    def start_move(self, position):
        """Signals the motor to begin moving to `position`."""
        thread = MoveThread(self, position)
        thread.start()
        return thread

    def get_status(self):
        """Returns a string summarizing the status of the motor."""
        self.send(com.STATUS)
        reply = self.get_reply(com.STATUS)
        return com.STATUSDICT[reply.data]

    def zero_here(self):
        """Sets the zero of the motor to its current position."""
        self.send(com.POS)
        self.zeropos = self.get_reply(com.POS).data
       
    def set_resolution(self):
        """Sets `self.resolution` based on info from controller and config."""
        self.send(com.GET, com.MICRORES)
        microstep_res = self.get_reply(com.MICRORES).data
        stepres = self.config.getfloat('Motor Res', self.name)
        self.resolution = stepres/microstep_res

    def set_name(self):
        self.send(com.SERNUM)
        sernum = self.get_reply(com.SERNUM).data
        self.name = self.config.get('Motor Names', str(sernum))

    @property
    def zeropos(self):
        return self.zeroposconfig.getzero('Zero Positions', self.name)

    @zeropos.setter
    def zeropos(self, value):
        self.zeroposconfig.set('Zero Positions', self.name, str(value))
        self.zeroposconfig.write_file()

    @property
    def is_homed(self):
        """Returns True if device has valid home position, False otherwise."""
        self.send(com.GET, com.MODE)
        return bool(self.get_reply(com.MODE).data & 1<<7)
        
    @property
    def travel(self):
        """Returns device's travel, or None for rotary stages."""
        travelstring = self.config.get('Travel', self.name)
        if travelstring:
            return float(travelstring)
        else:
            return None

    @property
    def pos(self):
        """Returns device's current position."""
        self.send(com.POS)
        stepdata = self.get_reply(com.POS).data
        return self.stepdata2pos(stepdata)

    @property
    def max_current(self):
        return self.config.getfloat('Max Current', self.name)

## need exceptions to prevent setting currents > max current

    @property
    def hold_current(self):
	"""Gives the holding current of the motor in Amps."""
        self.send(com.GET, com.HOLDCURR)
        data = self.get_reply(com.HOLDCURR).data
        return data*0.02 #data is in 20 mA increments

    @hold_current.setter
    def hold_current(self, value):
        data = value/0.02
        self.send(com.HOLDCURR, data)
	self.get_reply(com.HOLDCURR)

    @property
    def run_current(self):
        """Gives the RMS running current of the motor in Amps"""
        self.send(com.GET, com.RUNCURR)
	data = self.get_reply(com.RUNCURR).data
        return data*0.014 #data is in increments of 14.1 mA RMS (20 mA peak)

    @run_current.setter
    def run_current(self, value):
        data = value/0.014
        self.send(com.RUNCURR, data)
        self.get_reply(com.RUNCURR)
        


class SerialPortReader(threading.Thread):
    """A thread to monitor the serial port and parse input.

    Attributes:
        port (zaber.serial.BinarySerial): The serial port to read.
        pos_queues (dict): Maps motor numbers to Queues that contain position
            data for that motor.
        reply_queues (dict): Maps motor numbers to Queues that contain replies
            from that motor (excluding position tracking data).
        error_queue (Queue): Contains error messages received from all motors.
    """
    
    def __init__(self, port, pos_queues, reply_queues):
        self.port = port
        self.pos_queues = pos_queues
        self.reply_queues = reply_queues
        self.error_queue = Queue.Queue()
        super(SerialPortReader, self).__init__()
        self.daemon = True
        self.name = "SerialPortReader"
        
    def _read(self):
        try:
            return self.port.read()
        except zb.TimeoutError:
            pass

    def run(self):
        """Continuously reads from `self.port` and sorts inputs into Queues."""
        while True:
            time.sleep(0.05)
            reply = self._read()
            if reply is not None:
                motor_num = reply.device_number
                if reply.command_number in (com.MTRACK, com.MANMTRACK,
                                            com.MANMV, com.POS, com.MVABS,
                                            com.STOP):
                    self.pos_queues[motor_num].put(reply.data)
                if reply.command_number not in (com.MTRACK, com.MANMTRACK,
                                                com.MANMV, com.ERROR):
                    self.reply_queues[motor_num].put(reply)
                if reply.command_number == com.ERROR:
                    self.error_queue.put(reply)


class MoveThread(threading.Thread):
    """Commands the motor to move and lives until move is complete."""
    def __init__(self, motor, destination):
        super(MoveThread, self).__init__()
        self.daemon = True
        self.motor = motor
        self.name = "MoveThread"
        self.destination = destination

    def run(self):
        """Sends move command, and reads replies until move is completed.

        Move is completed when the motor returns either a `move absolute`
        command, indicating that it has reached the destination, or a `stop`
        command, indicating that it was commanded to stop before the destination
        was reached."""
        reply_com = None
        step_dest = self.motor.pos2stepdata(self.destination)
        self.motor.send(com.MVABS, step_dest)
        while reply_com not in (com.MVABS, com.STOP):
            reply = self.motor.get_reply(timeout=None)
            reply_com = reply.command_number

class SingleValQueue(Queue.Queue):
    """Implements a queue that holds only a single value."""
    def __init__(self):
        Queue.Queue.__init__(self, maxsize=1)

    def put(self, item):
        """If queue has an object, delete it before putting in a new one."""
        if self.full():
            self.get()
        Queue.Queue.put(self, item)


module_dir = os.path.dirname(__file__)
cfg_full_path = os.path.join(module_dir, '..','..','config','bldata.txt')

class ZeroPosConfig(ConfigParser.SafeConfigParser):
    """Implements a config file to hold the zero positions of the motors."""
    def __init__(self, filepath=cfg_full_path):
        ConfigParser.SafeConfigParser.__init__(self)
        self.filepath = filepath
        self.read(self.filepath)
                
    def getzero(self, *args):
        section, option = args[0:2]
        if not self.has_option(section, option):
            self.set(section, option, '0')
            self.write_file()
        return ConfigParser.SafeConfigParser.getfloat(self, *args)

    def write_file(self):
        with open(self.filepath, 'w') as datafile:
            self.write(datafile)
        
