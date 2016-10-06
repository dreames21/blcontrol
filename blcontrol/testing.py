import random

class FakeDet(object):
    """Representation of a detector with dummy data for testing."""
    def get_status(self):
        return {'accumulation time': 30.0,
                'real time': 33.0,
                'MCA enabled': True,
                'slow count': 45678,
                'fast count': 54322,
                'detector temperature (K)': round(219.5 + random.random(), 1),
                'board temperature (C)': round(35.0 + random.random(), 1)
                }
    def get_setting(self, *args):
        return ['PRET=30.0', 'MCAC=2048', 'THSL=8.034', 'THFA=113',
                'GAIN=12.045', 'TPEA=3.200', 'TECS=220.0']
                
    def begin_acq(self, acqtime):
        pass

    def get_spectrum(self):
        return [random.randint(0,5000) for _ in range(256)]

    def chan2energy(self, chan):
        return chan*0.1
