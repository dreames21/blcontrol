from blcontrol.gui.gui import BeamlineGUI
from blcontrol.utils import load_conf_file

if __name__ == '__main__':
    config = load_conf_file()
    gui = BeamlineGUI(config)
    gui.mainloop()
