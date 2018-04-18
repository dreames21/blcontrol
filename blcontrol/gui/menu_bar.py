import sys
if sys.version_info[0] < 3:
    from Tkinter import * #pylint: disable=wildcard-import, unused-wildcard-import
    import ttk
else:
    from tkinter import * #pylint: disable=import-error, wildcard-import

class BLMenuBar(Menu):
    def __init__(self, parent, **options):
        Menu.__init__(self, parent, **options)
        self.make_menus()

    def make_menus(self):
        self.file_menu = FileMenu(self)
        self.add_cascade(menu=self.file_menu, label='File')
        self.plot_menu = SettingsMenu(self)
        self.add_cascade(menu=self.plot_menu, label='Settings')


class BLMenuItem(Menu):
    def __init__(self, parent, **options):
        Menu.__init__(self, parent, **options)
        self.make_items()


class FileMenu(BLMenuItem):
    def make_items(self):
        self.add_command(label='Save As...', command=self.save_data)
        self.add_command(label='Exit', command=self.exit_program)
        
    def exit_program(self):
        self.master.master.terminate()

    def save_data(self):
        self.master.master.scancontrol.save_scan()


class SettingsMenu(BLMenuItem):
    def make_items(self):
        self.add_command(label='Detector', command=self.det_settings)
        self.add_command(label='Stages', command=self.stage_settings)
        self.add_command(label='Display', command=self.display_settings)

    def det_settings(self):
        pass

    def stage_settings(self):
        pass

    def display_settings(self):
        pass

