#! /usr/bin/env python

import ConfigParser
import os
from gui.gui import load_conf_file, BeamlineGUI

def main():
    config = load_conf_file()
    gui = BeamlineGUI(config)
    gui.mainloop()

if __name__ == '__main__':
    main()
