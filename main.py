import ConfigParser
import os
from blcontrol.gui.gui import BeamlineGUI

def load_conf_file(conf_path='~/.blconf'):
    xconfpath = os.path.expanduser(conf_path)
    config = ConfigParser.SafeConfigParser()
    configfile = open(xconfpath, 'r')
    config.readfp(configfile)
    configfile.close()
    return config

if __name__ == '__main__':
    config = load_conf_file()
    gui = BeamlineGUI(config)
    gui.mainloop()
