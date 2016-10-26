import copy
import numpy as np
import threading
import time
import Queue
from blcontrol.scan_data import Spectrum, LinearScan, GridScan

class SpectrumAcqThread(threading.Thread):
    def __init__(self, det, acctime, plotqueue):
        super(SpectrumAcqThread, self).__init__()
        self.det = det
        self.acctime = acctime
        self.plotqueue = plotqueue
        self.data = Spectrum([], self.det.get_energies(), {}, '')
        self.daemon = True

    def run(self):
        self.data.timestamp = time.asctime()
        self.det.begin_acq(self.acctime)
        mca_enabled = True
        while mca_enabled:
            self.data.counts, self.data.status = self.det.get_spectrum()
            mca_enabled = self.data.status['MCA enabled']
            if not mca_enabled:
                self.data.settings = self.det.get_settings_dict()
            self.plotqueue.put(copy.deepcopy(self.data))
            print 'put spec'
            time.sleep(0.5)
        self.plotqueue.join()

    def stop(self):
        self.det.disable_mca()


class LinearScanThread(threading.Thread):
    def __init__(self, det, motor, acctime, locs):
        super(LinearScanThread, self).__init__()
        self.det = det
        self.motor = motor
        self.acctime = acctime
        self.locs = locs
        self.stopper = threading.Event()
        self.plotqueue = Queue.Queue()
        self.specqueue = Queue.Queue()
        self.data = None
        self.daemon = True

    def run(self):
        self.data = LinearScan([], [], self.motor.name, time.asctime())
        for l in self.locs:
            if self.stopper.is_set():
                break
            else:
                mv_thread = self.motor.start_move(l)
                mv_thread.join()
                specthread = SpectrumAcqThread(self.det, self.acctime,
                                               self.specqueue)
                specthread.start()
                specthread.join()
                spectrum = specthread.data
                self.data.locations.append(l)
                self.data.spectra.append(spectrum)
                self.plotqueue.put(copy.deepcopy(self.data))
        self.plotqueue.join()

    def stop(self):
        self.stopper.set()
        self.det.disable_mca()


class GridScanThread(threading.Thread):
    def __init__(self, det, sio, xlocs, ylocs, acctime):
        self.det = det
        self.acctime = acctime
        self.xlocs = xlocs
        self.ylocs = ylocs
        self.dx = sio.motors['dx']
        self.dy = sio.motors['dy']
        self.stopper = threading.Event()
        self.plotqueue = Queue.Queue()
        self.specqueue = Queue.Queue()
        spectra = np.empty((len(xlocs), len(ylocs)), dtype=object)
        self.data = GridScan(xlocs, ylocs, spectra, time.asctime())
        super(GridScanThread, self).__init__()
        self.daemon = True

    def run(self):
        spectra = np.empty((len(self.xlocs), len(self.ylocs)), dtype=object)
        self.data = GridScan(self.xlocs, self.ylocs, spectra,
                                  time.asctime())
        xlocscopy = list(self.xlocs)
        self.plotqueue.put(copy.deepcopy(self.data))
        for y in self.ylocs:
            for x in xlocscopy:
                if not self.stopper.is_set():
                    y_thread = self.dy.start_move(y)
                    x_thread = self.dx.start_move(x)
                    y_thread.join()
                    x_thread.join()
                    specthread = SpectrumAcqThread(self.det, self.acctime,
                                                   self.specqueue)
                    specthread.start()
                    specthread.join()
                    spectrum = specthread.data
                    i, j = self.xlocs.index(x), self.ylocs.index(y)
                    self.data.spectra[i, j] = spectrum
                    self.plotqueue.put(copy.deepcopy(self.data))
            xlocscopy.reverse()
        self.plotqueue.join()

    def stop(self):
        self.stopper.set()
        self.det.disable_mca()
