"""This module defines tkinter widget classes for stage control by users."""

import Queue
import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
import blcontrol.stages.commands as com
from blcontrol.gui.misc import FloatValFrame

class SingleMotorWidget(FloatValFrame):
    """Base class for control widgets for a single motor.

    Attributes:
        motor (blcontrol.stages.Motor): The motor controlled by this widget.
        current_pos (tk.StringVar): A string variable containing the motor's
            current position with real units.
        goto (ttk.Entry): Input for position to which the motor will be moved.
        checkjob: An `after` loop to continually update the motor's position
            data.
    """
    
    def __init__(self, parent, motor, **options):
        FloatValFrame.__init__(self, parent, **options)
        self.motor = motor
        self.current_pos = StringVar()
        self.make_widgets()
        self.check_queue()
        
    def make_widgets(self):
        name = ttk.Label(self, text=self.motor.name, width=3)
        name.grid(column=0, row=0, sticky=E, padx=(5,1))
        pos = ttk.Label(self, textvariable=self.current_pos, width=11, anchor=E)
        pos.grid(column=1, row=0, padx=2)
        self.goto = ttk.Entry(self, width=7, justify=RIGHT, validate='key',
                              validatecommand=self.vcmd)
        self.goto.grid(column=2, row=0, padx=2)
        self.goto.bind('<KeyPress-KP_Enter>', self.move) #numpad Enter key
        self.goto.bind('<KeyPress-Return>', self.move)
        self.zerobutt = ttk.Button(self, text='Zero',
                                   command=self.motor.zero_here, width=5)
        self.zerobutt.grid(column=4, row=0, padx=5)

    def check_queue(self):
        """Loop to check the position queue for new data every 50ms."""
        try:
            newpos = self.motor.get_tracking_pos()
        except Queue.Empty:
            pass
        else:
            self.update_pos(newpos)
        self.checkjob = self.after(50, self.check_queue)

    def disable(self):
        """Adds home button and disables entry."""
        self.goto.configure(state='disabled')
        self.zerobutt.configure(text='Home', command=self.home_and_reenable)
        self.after_cancel(self.checkjob)
        self.current_pos.set('')

    def home_and_reenable(self):
        """Restores pos info and enables entry."""
        self.motor.send(com.HOME)
        self.motor.get_reply(com.HOME)
        self.goto.configure(state='normal')
        self.zerobutt.configure(text='Zero', command=self.motor.zero_here)
        self.motor.send(com.POS)
        self.check_queue()


class LinearStageWidget(SingleMotorWidget):
    """Class for linear stage control widgets."""
    
    def __init__(self, parent, motor, **options):
        SingleMotorWidget.__init__(self, parent, motor, **options)

    def update_pos(self, pos):
        """Updates the `self.current_pos` variable with a formatted string."""
        value = '{0:0.3f} mm'.format(pos)
        self.current_pos.set(value)

    def move(self, event=None):      #pylint: disable=unused-argument
        """Retrieves goto position from entry and sends move command to motor.
        
        `event` param is unused, but provides compatibility with key bindings.
        """
        pos_str = self.goto.get()
        if pos_str != '':
            goto_pos = float(self.goto.get())
            self.motor.start_move(goto_pos)
            self.goto.delete(0,END)


class RotaryStageWidget(SingleMotorWidget):
    """Class for rotary stage control widgets."""
    
    def __init__(self, parent, motor, **options):
        self._angle_mode = 'deg'
        SingleMotorWidget.__init__(self, parent, motor, **options)

    def update_pos(self, pos):
        """Updates the `self.current_pos` variable with a formatted string."""
        if self._angle_mode == 'deg':
            value = '{0:0.3f} deg'.format(pos)
        elif self._angle_mode == 'arcmin':
            value = "{0:0.3f}'".format(pos*60)
        self.current_pos.set(value)
        
    def move(self, event=None):      #pylint: disable=unused-argument
        """Retrieves goto position from entry and sends move command to motor.

        `event` param is unused, but provides compatibility with key bindings.
        """
        pos_str = self.goto.get()
        if pos_str != '':
            if self._angle_mode == 'deg':
                goto_pos = float(self.goto.get())
            elif self._angle_mode == 'arcmin':
                goto_pos = 60*float(self.goto.get())
            self.motor.start_move(goto_pos)
            self.goto.delete(0,END)

    def set_degree_mode(self):
        """Sets units to decimal degrees."""
        if self._angle_mode != 'deg':
            self._angle_mode = 'deg'
            self.motor.send(com.POS)
            
    def set_arcmin_mode(self):
        """Sets units to arcminutes."""
        if self._angle_mode != 'arcmin':
            self._angle_mode = 'arcmin'
            self.motor.send(com.POS)


class MotorFrame(ttk.Frame):
    """Class for a collection of motor control widgets.

    Attributes:
        sio (StageIO): stage assembly controller
        motor_dict (dict): maps motor names to corresponding widgets.
    """
    
    def __init__(self, parent, sio, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.sio = sio
        self.motor_dict = {}
        self.unhomed_motors = []
        self.make_widgets()
        self.check_for_errs()

    def make_widgets(self):
        title = ttk.Label(self, text='Motor Positioning', font='TkHeadingFont')
        title.pack(side=TOP, pady=7, expand=1)
        self.sio.send_all(com.POS)
        self.sio.send_all(com.GET, com.MODE)
        for motor_num, motor in self.sio.motors_by_num.iteritems():
            if not (1<<7 & motor.get_reply(com.MODE).data):
                self.unhomed_motors.append(motor)
            if motor.travel:
                self.motor_dict[motor.name] = LinearStageWidget(self, motor)
            else:
                self.motor_dict[motor.name] = RotaryStageWidget(self, motor)
            self.motor_dict[motor.name].pack(side=TOP, pady=1)
        stopbutt = ttk.Button(self, text='Stop All', command=self.sio.stop_all)
        stopbutt.pack(side=TOP, pady=2, expand=1)
        if self.unhomed_motors:
            self.unhomed_warn()

    def unhomed_warn(self):
        """Display warning message if some motors have not been homed."""
        for motor in self.unhomed_motors:
            self.motor_dict[motor.name].disable()
        if len(self.unhomed_motors) > 1:
            names = ''.join([', '+motor.name for motor in self.unhomed_motors[1:]])
        else:
            names = ''
        names = self.unhomed_motors[0].name + names
        message = 'Motor(s) {0} have not been homed'.format(names)
        self.after(300, lambda: messagebox.showwarning('Unhomed Motors',
                                                       message))
            
    def check_for_errs(self):
        """Loop to check error message queue for errors every 300ms."""
        try:
            error = self.sio.reader.error_queue.get_nowait()
        except Queue.Empty:
            pass
        else:
            motorname = self.sio.motors_by_num[error.device_number].name
            errornum = error.data
            message = 'Device `{0}` returned error code {1}:\n{2}'.format(
                motorname, errornum, com.ERRORDICT[errornum])
            messagebox.showwarning('Device Error', message)
        self.errjob = self.after(300, self.check_for_errs)

    def cancel_loops(self):
        """Cancels error checking loop and all children's pos checking loops."""
        self.after_cancel(self.errjob)
        for widget in self.motor_dict.values():
            widget.after_cancel(widget.checkjob)
