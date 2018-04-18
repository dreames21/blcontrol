"""This module defines a tkinter widget to contain detector status info."""

import Queue
import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import
from det_settings_window import DetSettingsWindow


STATS =['Preset Time', 'Accum. Time', 'Real Time', 'Dead Time', 'MCA Enabled',
        'MCA Channels', 'Slow Count', 'Fast Count', 'Slow Threshold',
        'Fast Threshold', 'Gain', 'Peaking Time', 'Detector Temp', 'Set Point',
        'Board Temp']

class DetectorStatus(ttk.Frame):
    """A widget that displays the detector's status in real time.

    Attributes:
        det (blcontrol.detector.DP5Device): The detector providing status data.
        stats (list of strs): A list of the status and setting names to be
            displayed.
        variables (dict): A mapping of stats to corresponding string variables.
        refreshjob: An `after` loop to continually update the status data.
    """

    def __init__(self, parent, det, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.det = det
        self.variables = {name: StringVar() for name in STATS}
        self.make_widgets()

        self.refresh_status()

    def make_widgets(self):
        title = ttk.Label(self, text="Detector Control", font='TkHeadingFont')
        title.grid(column=0, row=0, columnspan=4, pady=7)
        for i, stat in enumerate(STATS):
            namelabel = ttk.Label(self, text=stat+':')
            vallabel = ttk.Label(self, textvariable=self.variables[stat])
            if i in (3, 11, 14):
                p = 7
            else:
                p = 0
            namelabel.grid(column=1, row=i+1, padx=3, pady=(0,p), sticky=E)
            vallabel.grid(column=2, row=i+1, padx=3, pady=(0,p), sticky=W)

        self.conn_button = ttk.Button(self, text='Connect',
                                      command=self.det.reconnect)
        self.conn_button.grid(row=len(STATS)+2, column=1, pady=15)
        
        self.disc_button = ttk.Button(self, text='Disconnect',
                                     command=self.det.disconnect, state=DISABLED)
        self.disc_button.grid(row=len(STATS)+2, column=2, pady=15)

        settings_button = ttk.Button(self, text='Settings',
                                     command=self.open_settings_window)
        settings_button.grid(row=len(STATS)+3, column=1, columnspan=2)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(len(STATS)+4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(3, weight=1)
        

    def refresh_status(self):
        """Reads status data from detector and sets corresponding variables.

        Sets up an `after` loop to request new status data from the detector
        and update variables every 500 ms.
        """
        if self.det.is_connected:
            self.conn_button['state'] = DISABLED
            self.disc_button['state'] = NORMAL
        else:
            self.conn_button['state'] = NORMAL
            self.disc_button['state'] = DISABLED
            
        try:
            status, settings = self.det.status_queue.get_nowait()
        except Queue.Empty:
            pass
        else:
            acc_time = status['accumulation time']
            self.variables['Accum. Time'].set(str(acc_time) + ' s')
            real_time = status['real time']
            self.variables['Real Time'].set(str(real_time) + ' s')
            if real_time:
                dead_time = round(100*(real_time - acc_time)/real_time, 1)
            else:
                dead_time = 0.
            self.variables['Dead Time'].set(str(dead_time) + '%')
            self.variables['MCA Enabled'].set(str(status['MCA enabled']))
            self.variables['Slow Count'].set(str(status['slow count']))
            self.variables['Fast Count'].set(str(status['fast count']))
            self.variables['Detector Temp'].set(str(
                status['detector temperature (K)']) + ' K')
            self.variables['Board Temp'].set(str(status['board temperature (C)']) +
                                             ' C')

            self.variables['Preset Time'].set(settings['PRET'] + ' s')
            self.variables['MCA Channels'].set(settings['MCAC'])
            self.variables['Slow Threshold'].set(settings['THSL'] +'%')
            self.variables['Fast Threshold'].set(settings['THFA'])
            self.variables['Gain'].set(settings['GAIN'])
            self.variables['Peaking Time'].set(settings['TPEA'] + ' us')
            self.variables['Set Point'].set(settings['TECS'] + ' K')
        finally:
            self.statusloop = self.after(250, self.refresh_status)

    def open_settings_window(self):
        setwin = DetSettingsWindow(self, self.det)
        setwin.grab_set()

    def cancel_loops(self):
        """Cancels refresh loop so application can exit gracefully."""
        self.after_cancel(self.statusloop)
