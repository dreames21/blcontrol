"""This module defines a tkinter widget to contain detector status info."""

import Queue
import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
    import tkMessageBox as messagebox
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

class DetectorStatus(ttk.Frame):
    """A widget that displays the detector's status in real time.

    Attributes:
        det (blcontrol.detector.DP5Device): The detector providing status data.
        stats (list of strs): A list of the status and setting names to be
            displayed.
        variables (dict): A mapping of stats to corresponding string variables.
        refreshjob: An `after` loop to continually update the status data.
    """

    def __init__(self, parent, queue, **options):
        ttk.Frame.__init__(self, parent, **options)
        self.queue = queue
        self.stats = ['Preset Time', 'Accum. Time', 'Real Time', 'Dead Time', 
            'MCA Enabled', 'MCA Channels', 'Slow Count', 'Fast Count',
            'Slow Threshold', 'Fast Threshold', 'Gain', 'Peaking Time',
            'Detector Temp', 'Set Point', 'Board Temp']
        self.variables = {name: StringVar() for name in self.stats}
        self.make_widgets()
        self.refresh_status()

    def make_widgets(self):
        title = ttk.Label(self, text="Detector Status", font='TkHeadingFont')
        title.grid(column=1, row=0, columnspan=2, pady=9)
        for i, stat in enumerate(self.stats):
            namelabel = ttk.Label(self, text=stat+':')
            vallabel = ttk.Label(self, textvariable=self.variables[stat])
            if i in (3, 11, 14):
                p = 7
            else:
                p = 0
            namelabel.grid(column=1, row=i+1, padx=3, pady=(0,p), sticky=E)
            vallabel.grid(column=2, row=i+1, padx=3, pady=(0,p), sticky=W)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(len(self.stats)+2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(3, weight=1)

    def refresh_status(self):
        """Reads status data from detector and sets corresponding variables.

        Sets up an `after` loop to request new status data from the detector
        and update variables every 500 ms.
        """
        try:
            status, settings = self.queue.get_nowait()
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

            values = [setting.split('=')[1] for setting in settings]
            self.variables['Preset Time'].set(values[0] + ' s')
            self.variables['MCA Channels'].set(values[1])
            self.variables['Slow Threshold'].set(values[2] +'%')
            self.variables['Fast Threshold'].set(values[3])
            self.variables['Gain'].set(values[4])
            self.variables['Peaking Time'].set(values[5] + ' us')
            self.variables['Set Point'].set(values[6] + ' K')
        finally:
            self.statusloop = self.after(250, self.refresh_status)

    def cancel_loops(self):
        """Cancels refresh loop so application can exit gracefully."""
        self.after_cancel(self.statusloop)
