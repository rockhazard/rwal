#!/usr/bin/env python3

import os, configparser
from pathlib import Path
from textwrap import dedent


class State:
    """monoState: distribute dictionary and getter/setter to child objects"""
    _state = dict(
        home=os.path.expanduser('~'),
        verbose=False,
        directory=None,
        filter=False,
        slideshow=False,
        list=False,
        pwd=False,
        image_action='random',
        mode=False,
        mode_error=dedent("""\
            WARNING: configuration fault detected
            check modes in rwall.conf
            fallback mode applied""")
    )

    def __init__(self):
        self.__dict__ = self._state

        # absence of packages reduces functionality but won't break script, so proceed
        self.depends = dict(xclip=['/usr/bin/xclip', True],
                            feh=['/usr/bin/feh', True])
        self.modules = dict(Pillow=None, Tkinter=None)

        # python module dependencies
        try:
            from PIL import Image
            self.modules['Pillow'] = True
        except ImportError:
            self.modules['Pillow'] = False
        try:
            import tkinter as tk
            self.modules['Tkinter'] = True
        except ImportError:
            self.modules['Tkinter'] = False

        # valid image types; to expand, use imghdr.what() values
        self.fileTypes = ('jpeg', 'png', 'bmp')

        # directory flags, used for argument test in start_slideshow()
        self.dirFlags = ('directory1', 'directory2', 'directory3', 'directory4',
                         'directory5', '1', '2', '3', '4', '5')

        # desktop environment flags for diff implementations
        self.gnomeEnv = ('cinnamon', 'gnome', 'ubuntu', 'unity')
        self.kdeEnv = ('kde-plasma', 'plasma', '/usr/share/xsessions/plasma')

        # configuration files
        self.desktopSession = os.environ.get('DESKTOP_SESSION')
        if self.desktopSession in self.kdeEnv:
            self.configDirectory = str(Path(self._state['home'],
                                            '.config/rwall/kde-plasma/'))
        else:
            self.configDirectory = str(Path(self._state['home'],
                                            '.config/rwall/{}'.format(
                                                self.desktopSession)))
        self.configFile = Path(self._state['home'], self.configDirectory,
                               'rwall.conf')
        self.bgFile = Path(self._state['home'], self.configDirectory,
                           'background.conf')
        # configuration file parser
        self.config = configparser.RawConfigParser(allow_no_value=True)
        # background config parser
        self.bgConfig = configparser.RawConfigParser(allow_no_value=True)

    def set_state(self, key, value):
        self._state[key] = value

    def get_state(self, key):
        return self._state.get(key, None)

    def read_config(self):
        return self.config.read(str(self.configFile))

    def get_config(self, section, subsection):
        self.read_config()
        return self.config.get(section, subsection)

    def read_bgConfig(self):
        return self.bgConfig.read(str(self.bgFile))

    def get_bgConfig(self, temp='Temp', background='Current Background'):
        self.read_bgConfig()
        return self.bgConfig.get(temp, background)

    def announce(self):
        """output to stdout if --verbose is True"""
        current_dir = self.bgConfig.get('Temp', 'Current Directory')
        if self._state['filter']:
            aspect_ratio = self._state['filter']
        else:
            aspect_ratio = self.config.get(
                'Wallpaper Modes', 'Aspect Ratio Filter', fallback='none')
        print('aspect ratio filter: {}'.format(aspect_ratio))
        print('{} wallpaper mode set to \'{}\'\
            '.format(self.desktopSession, self._state['mode']))
        print('{} wallpaper applied from:\
            \n{}'.format(self._state['image_action'], current_dir))
