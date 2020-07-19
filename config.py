#!/usr/bin/env python3
"""Module for writing and reading the rwal configuration files"""
import os, sys, subprocess
from state import State
from pathlib import Path
from textwrap import dedent


class Config(State):
    """program-wide configuration"""

    def __init__(self):
        super(Config, self).__init__()

    def set_config(self):
        """create configuration directory and file if absent, read if present"""
        default = str(Path(self._state['home'], 'Pictures'))

        # check for existence of config directory, create if absent
        if not Path(self.configDirectory).is_dir():
            os.makedirs(self.configDirectory)
            print('created configuration directory')

        # uncomment next line to make config case-sensitive
        self.config.optionxform = lambda option: option

        # check for existence of config file, create if absent
        if not self.configFile.is_file():
            self.config.add_section('rwal Configuration')
            self.config.set('rwal Configuration',
                            dedent("""\
            # Please modify this file to change rWall\'s behavior.
            # If you make a mistake, a clue will print to the terminal.
            # If all else fails just delete this file and run rwal.py.
            # A fresh working default config file will be created for you.
            # Thanks for using rWall. Have fun!"""))

            # default settings
            self.config.add_section('Defaults')
            # announce wallpaper application and image/environment stats
            # self.config.set('Defaults','Announce', 'no')
            # replace 'editor' with user's default text editor
            if 'APPDATA' in os.environ:
                self.config.set('Defaults', 'Default Config Editor',
                                'notepad.exe')
            else:
                self.config.set('Defaults', 'Default Config Editor', 'editor')
            self.config.set('Defaults', 'Default Background Editor', 'gimp')
            self.config.set('Defaults', 'Default Directory',
                            '{}'.format(default))

            # wallpaper mode settings
            self.config.add_section('Wallpaper Modes')

            # wallpaper mode presets
            self.config.set('Wallpaper Modes',
                            dedent("""\
            # Aspect Ratio Filter Options:
            # sd480, hd1050, hd1080, hd1050x2, hd1080x2, and auto"""))
            self.config.set('Wallpaper Modes', 'Aspect Ratio Filter', 'none')
            self.config.set('Wallpaper Modes',
                            dedent("""\n\
            # Wallpaper Mode Settings by Environment:
            # KDE modes must be selected within KDE\'s slideshow options"""))
            self.config.set('Wallpaper Modes',
                            dedent("""\n\
            # GNOME3 (GNOME Shell, Cinnamon, Unity, and MATE):
            # none, centered, scaled, spanned, stretched, wallpaper, zoom"""))
            self.config.set('Wallpaper Modes', 'Cinnamon', 'scaled')
            self.config.set('Wallpaper Modes', 'GNOME', 'scaled')
            self.config.set('Wallpaper Modes', 'MATE', 'scaled')
            self.config.set('Wallpaper Modes',
                            dedent("""\n\
            # Xfce:
            # 0-Auto, 1-Centered, 2-Tiled, 3-Stretched, 4-Scaled, 5-Zoomed"""))
            self.config.set('Wallpaper Modes', 'Xfce', '4')
            self.config.set('Wallpaper Modes',
                            dedent("""\n\
            # Openbox (or any use of feh):
            # --bg-max,--bg-scale,--bg-tile,--bg-fill,--bg-center"""))
            self.config.set('Wallpaper Modes', 'Openbox', '--bg-max')
            self.config.set('Wallpaper Modes',
                            dedent("""\n\
            # Lxde:
            # tiled, center, scaled, fit, stretch"""))
            self.config.set('Wallpaper Modes', 'LXDE', 'scaled')

            # preset image directory defaults
            self.config.add_section('Preset Image Directories')
            self.config.set('Preset Image Directories', 'Directory1',
                            '{}'.format(default))
            self.config.set('Preset Image Directories', 'Directory2',
                            '{}'.format(default))
            self.config.set('Preset Image Directories', 'Directory3',
                            '{}'.format(default))
            self.config.set('Preset Image Directories', 'Directory4',
                            '{}'.format(default))
            self.config.set('Preset Image Directories', 'Directory5',
                            '{}'.format(default))
            with open(str(self.configFile), 'w') as configfile:
                self.config.write(configfile)

            print('Default configuration initialized.')
            print('Configuration file: {}\nuse rwal.py -c to edit file\
                '.format(str(self.configFile)))
            print('Default image directory is set to {}'.format(default))
            sys.exit(dedent("""\
                Please run rwal.py again to select and apply a background.
                If you need help, type rwal.py -h in a terminal."""))
        else:
            # open config file for reading if it already exists
            self.config.read(str(self.configFile))
            # config getter vars assigned here when used more than once

    def set_bgconfig(self):
        """create or read file used by get_background and next/previous
        functions"""

        # check for existence of background config file, create if absent
        if not self.bgFile.is_file():
            # for process use
            self.bgConfig.add_section('Temp')
            self.bgConfig.set('Temp', 'Current Directory', '')
            self.bgConfig.set('Temp', 'Current Background', '')
            self.bgConfig.set('Temp', 'Indexed Background', '')
            with open(str(self.bgFile), 'w') as configfile:
                # open bgconfig file for reading if it already exists
                self.bgConfig.write(configfile)
                # bgconfig accessors assigned vars here when used more than
                # once

            print(
                'created background configuration file: {}'.format(self.bgFile))
        else:
            self.bgConfig.read(str(self.bgFile))

    def edit_config(self):
        self.set_config()
        edit_conf = self.config.get('Defaults', 'Default Config Editor')
        return subprocess.run(
            '{} {}/rwall.conf'.format(edit_conf, self.configDirectory),
            shell=True)
