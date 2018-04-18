import numpy as np
import threading
import time
import Queue
from scan_data import Spectrum, LinearScan, GridScan

class ScanThread(threading.Thread):
    """Base class for data acquisition threads.

    Attributes:
        det: Detector to use for data acquisition
        acctime: Accumulation time (seconds) for individual spectra
        plotqueue: Queue to hold data for plotting
        specqueue: Queue to hold spectrum data for display separate from data
            plot
        data: Acquired data from acquisition
    """
    def __init__(self, det, acctime):
        super(ScanThread, self).__init__()
        self.det = det
        self.acctime = acctime
        self._stopper = threading.Event()
        self.plotqueue = Queue.Queue()
        self.specqueue = Queue.Queue()
        self.data = None
        self.daemon = True
        self.name = "ScanThread"

    def stop(self):
        """Signal the thread to terminate after the current iteration."""
        self._stopper.set()
        self.det.disable_mca()

    @property
    def is_stopped(self):
        return self._stopper.is_set()


class SpectrumAcqThread(ScanThread):
    """Thread for acquiring a single spectrum."""
    def __init__(self, det, acctime, plotqueue, get_settings=True):
        super(SpectrumAcqThread, self).__init__(det, acctime)
        self.plotqueue = plotqueue
        self.get_settings = get_settings

    def run(self):
        scandata = Spectrum([], self.det.get_energies(), {}, time.asctime())
        self.det.begin_acq(self.acctime)
        mca_enabled = True
        if self.get_settings:
            scandata.settings = self.det.get_all_settings()
        while mca_enabled:
            scandata.counts, scandata.status = self.det.get_spectrum()
            mca_enabled = scandata.status['MCA enabled']
            self.plotqueue.put(scandata)
            time.sleep(0.5)
        self.data = scandata
        self.plotqueue.join()
        

class LinearScanThread(ScanThread):
    """Thread for acquring linear (single motor) scan data.

    Attributes:
        motor: Motor to move during acquisition
        locs: List of motor locations to collect spectra.
    """
    def __init__(self, det, motor, acctime, locs):
        super(LinearScanThread, self).__init__(det, acctime)
        self.motor = motor
        self.locs = locs
        self.name = "LinearScanThread"

    def run(self):
        scandata = LinearScan([], [], self.motor.name, time.asctime())
        for i, l in enumerate(self.locs):
            get_settings = not bool(i)
            if self.is_stopped:
                break
            else:
                mv_thread = self.motor.start_move(l)
                mv_thread.join()
                specthread = SpectrumAcqThread(self.det, self.acctime,
                                               self.specqueue, get_settings)
                specthread.start()
                specthread.join()
                spectrum = specthread.data
                scandata.locations.append(l)
                scandata.spectra.append(spectrum)
                self.plotqueue.put(scandata)
        settings = scandata.spectra[0].settings
        for spec in scandata.spectra:
            spec.settings = settings
        self.data = scandata
        self.plotqueue.join()


class GridScanThread(ScanThread):
    """Thread for acquiring grid scan data (motors dx and dy).

    Attributes:
        sio: StageIO object controlling motors
        xlocs: List of locations of motor `dx`
        ylocs: List of locations of motor `dy`
    """
    def __init__(self, det, sio, xlocs, ylocs, acctime):
        super(GridScanThread, self).__init__(det, acctime)
        self.xlocs = xlocs
        self.ylocs = ylocs
        self.dx = sio.motors['dx']
        self.dy = sio.motors['dy']
        self.name = "GridScanThread"
        
    def run(self):
        spectra = np.empty((len(self.xlocs), len(self.ylocs)), dtype=object)
        scandata = GridScan(self.xlocs, self.ylocs, spectra, time.asctime())
        xlocscopy = list(self.xlocs)
        self.plotqueue.put(scandata)
        for y in self.ylocs:
            for x in xlocscopy:
                if not self.is_stopped:
                    i, j = self.xlocs.index(x), self.ylocs.index(y)
                    y_thread = self.dy.start_move(y)
                    x_thread = self.dx.start_move(x)
                    y_thread.join()
                    x_thread.join()
                    get_settings = not bool(i+j)
                    specthread = SpectrumAcqThread(self.det, self.acctime,
                                                   self.specqueue, get_settings)
                    specthread.start()
                    specthread.join()
                    spectrum = specthread.data
                    scandata.spectra[i, j] = spectrum
                    spectrum.settings = scandata.spectra[0,0].settings
                    self.plotqueue.put(scandata)
            xlocscopy.reverse()
        self.data = scandata
        self.plotqueue.join()
