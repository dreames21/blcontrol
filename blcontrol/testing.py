import numpy as np
import random
import threading

class FakeDet(object):
    """Representation of a detector with dummy data for testing."""
    def __init__(self, *args):
        self.mca = False
        self.spectrum = 256*[0]
        
    def begin_acq(self, acqtime):
        self.mca = True
        timer = threading.Timer(acqtime, self.disable_mca)
        timer.start()

    def disable_mca(self):
        self.mca = False
        self.spectrum = 256*[0]
    
    def get_status(self):
        return {'accumulation time': 30.0,
                'real time': 33.0,
                'MCA enabled': self.mca,
                'slow count': 45678,
                'fast count': 54322,
                'detector temperature (K)': round(219.5 + random.random(), 1),
                'board temperature (C)': round(35.0 + random.random(), 1)
                }
    def get_setting(self, *args):
        return ['PRET=30.0', 'MCAC=1024', 'THSL=8.034', 'THFA=113',
                'GAIN=12.045', 'TPEA=3.200', 'TECS=220.0']

    def get_spectrum(self):
        new = [i + int(200*np.exp(-1*(i-50)**2) + 100*random.random())
                for i in self.get_energies()]
        self.spectrum = [self.spectrum[i] + n for i, n in enumerate(new)]
        return self.spectrum, self.get_status()

    def chan2energy(self, chan):
        return chan*0.3

    def set_setting(self, *args):
        pass

    def get_energies(self):
        return [self.chan2energy(i) for i in range(256)]
