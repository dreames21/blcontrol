"""This module defines classes for communication with beamline stages."""

import Queue
import serial.tools.list_ports
import threading
import time
import zaber.serial as zb
import blcontrol.stages.commands as com

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
        self.port = zb.BinarySerial(portpath)

    def initialize_motors(self):
        """Populates `self.motors` with objects for each connected motor."""
        old_timeout = self.port.timeout  # Save previous timeout
        try:
            #Set timeout to 0.5 seconds.  The number of motors is
            #determined by how many replies are read before a timeout occurs.
            self.port.timeout = 0.5
            self.send_all(com.SERNUM)
            pos_queues = {}
            reply_queues = {}
            try:
                while True:
                    reply = self.port.read()
                    motor_num = reply.device_number
                    motor = Motor(motor_num, self.port, self.config, reply.data)
                    self.motors[motor.name] = motor
                    self.motors_by_num[motor_num] = motor
                    pos_queues[motor_num] = motor.pos_queue
                    reply_queues[motor_num] = motor.reply_queue
            except zb.exceptions.TimeoutError:
                pass
            self.send_all(com.GET, com.MICRORES)
            for _ in self.motors:
                reply = self.port.read()
                motor_num = reply.device_number
                motor = self.motors_by_num[motor_num]
                stepres = self.config.getfloat('Motor Res', motor.name)
                motor.resolution = stepres/reply.data
            self.reader = SerialPortReader(self.port, pos_queues, reply_queues)
            self.reader.start()
        finally:
            self.port.timeout = old_timeout  # Restore previous timeout

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
    
    def __init__(self, number, port, config, sernum):
        """Initializes the Motor object.

        `resolution` should be overwritten after creation of Motor object,
        either directly or by using the built-in methods to determine these
        values.
        """
        self.number = number
        self.port = port
        self.config = config
        self.sernum = sernum
        self._zeropos = 0
        self.reply_queue = Queue.Queue()
        self.pos_queue = Queue.Queue(maxsize=1)
        self.resolution = None
    
    def send(self, commandnum, data=0):
        """Send a command to the motor controller."""
        self.port.write(self.number, commandnum, data)

    def get_reply(self, commandnum=None):
        """Read a reply from the motor controller.

        Args:
            commandnum (int, optional): If provided, this method will return
                only a reply with this command number.

        Raises:
            Timeout Error: A reply (optionally with the specified command
                number) was not received within the serial port's timeout.

        Returns (zaber.serial.BinaryReply):
            The reply received from the motor controller.
        """
        try:
            reply = self.reply_queue.get(self.port.timeout)
            if commandnum is not None:
                while (reply.command_number != commandnum):
                    reply = self.reply_queue.get(self.port.timeout)
        except Queue.Empty:
            raise TimeoutError('Read timed out.')
        return reply

    def get_reply_notimeout(self, commandnum=None):
        """Read a reply from the motor controller.

        Note: Blocks until a valid reply is received.

        Args:
            commandnum (int, optional): If provided, this method will return
                only a reply with this command number.

        Returns (zaber.serial.BinaryReply):
            The reply received from the motor controller.
        """
        reply = self.reply_queue.get()
        if commandnum is not None:
            while (reply.command_number != commandnum):
                reply = self.reply_queue.get(self.port.timeout)
            
    def stepdata2pos(self, stepdata):
        """Converts steps to real units based on resolution and zero position."""
        return round((stepdata - self._zeropos)*self.resolution, 4)

    def pos2stepdata(self, pos):
        """Converts real units to steps based on resolution and zero position."""
        return int(pos/self.resolution + self._zeropos)

    def get_tracking_pos(self):
        """Reads latest position from position tracking queue.  Blocks
        until tracking data is received."""
        return self.stepdata2pos(self.pos_queue.get_nowait())
        
    def is_in_range(self, position):
        """Returns True if the given position is in the range of the
        stage's travel, False otherwise.  Always True for rotation stages."""
        return (not self.travel or ((position + self._zeropos >= 0)
                    and (position + self._zeropos <= self.travel)))

    def start_move(self, position):
        """Signals the motor to begin moving to `position`."""
        self.send(com.MVABS, self.pos2stepdata(position))

    def finish_move(self):
        """Returns position when motor has finished moving."""
        stepdata = self.get_reply_notimeout(com.MVABS)
        return stepdata2pos(stepdata)

    def get_status(self):
        """Returns a string summarizing the status of the motor."""
        self.send(com.STATUS)
        reply = self.get_reply(com.STATUS)
        return com.STATUSDICT[reply.data]

    def zero_here(self):
        """Sets the zero of the motor to its current position."""
        self.send(com.POS)
        self._zeropos = self.get_reply(com.POS).data
       
    def set_resolution(self):
        """Sets `self.resolution` based on info from controller and config."""
        self.send(com.GET, com.MICRORES)
        microstep_res = self.get_reply(com.MICRORES).data
        stepres = self.config.getfloat('Motor Res', self.name)
        self.resolution = stepres/microstep_res

    @property
    def is_homed(self):
        """Returns True if device has valid home position, False otherwise."""
        self.send(com.GET, com.MODE)
        return bool(self.get_reply(com.MODE).data & 1<<7)
    
    @property
    def name(self):
        """Returns device's user defined name from `self.config`."""
        return self.config.get('Motor Names', str(self.sernum))
        
    @property
    def travel(self):
        """Returns device's travel, or None for rotary stages."""
        travelstring = self.config.get('Travel', self.name)
        if travelstring:
            return float(travelstring)
        else:
            return None


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
        
    def _read(self):
        try:
            return self.port.read()
        except zb.TimeoutError:
            return None

    def run(self):
        """Continuously reads from `self.port` and sorts inputs into Queues."""
        while True:
            time.sleep(0.2)
            reply = self._read()
            if reply is not None:
                motor_num = reply.device_number
                if reply.command_number in (com.MTRACK, com.MANMTRACK,
                                            com.MANMV, com.POS, com.MVABS,
                                            com.STOP):
                    if self.pos_queues[motor_num].full():
                        self.pos_queues[motor_num].get()
                    self.pos_queues[motor_num].put(reply.data)
                if reply.command_number not in (com.MTRACK, com.MANMTRACK,
                                                com.MANMV, com.ERROR):
                    self.reply_queues[motor_num].put(reply)
                if reply.command_number == com.ERROR:
                    self.error_queue.put(reply)


class TimeoutError(Exception):
    """Exception raised when a reply is not received before port timeout."""
    pass
