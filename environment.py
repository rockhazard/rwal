#!/usr/bin/env python3
"""
Library for detecting the host environment then building and executing wallpaper
commands
"""
import sys
import os
import subprocess
import ctypes
from state import State


class Environment(State):
    """ detect desktop environment and produce background command string"""

    def __init__(self):
        super(Environment, self).__init__()
        self.pic = None
        self.desktopSession = os.environ['DESKTOP_SESSION']
        # desktop environment flags for diff implementations
        self.gnomeEnv = ('cinnamon', 'gnome', 'ubuntu', 'unity')
        self.kdeEnv = ('kde-plasma', 'plasma', '/usr/share/xsessions/plasma')

    def set_desktop(self):
        """detect desktop environment to set appropriate desktop function"""
        if self.desktopSession in self.gnomeEnv:
            return self.set_gnome3()
        elif self.desktopSession in self.kdeEnv:
            return self.set_kde()
        elif self.desktopSession == 'LXDE':
            return self.set_lxde()
        elif self.desktopSession == 'mate':
            return self.set_mate()
        elif self.desktopSession == 'xfce':
            return self.set_xfce()
        elif self.desktopSession == 'openbox':
            return self.set_openbox()
        elif 'APPDATA' in os.environ:
            return self.set_windows()
        elif 'Apple_PubSub_Socket_Render' in os.environ:
            return self.set_mac()
        else:
            return self.set_openbox()

    """
    DESKTOP ENVIRONMENT COMMANDS
    """

    def get_mode(self, desktop):
        """check and apply user-defined mode format; use fallback if invalid"""
        gnomeMode = ('none', 'centered', 'scaled', 'spanned', 'stretched',
                     'wallpaper', 'zoom')
        if desktop == 'cinnamon':
            image_config = self.config.get(
                'Wallpaper Modes', 'Cinnamon', fallback='scaled')
            mode = gnomeMode
        elif desktop == 'gnome':
            image_config = self.config.get(
                'Wallpaper Modes', 'GNOME', fallback='scaled')
            mode = gnomeMode
        elif desktop == 'mate':
            image_config = self.config.get(
                'Wallpaper Modes', 'MATE', fallback='scaled')
            mode = gnomeMode
        elif desktop == 'xfce':
            image_config = self.config.get(
                'Wallpaper Modes', 'Xfce', fallback='4')
            mode = ('0', '1', '2', '3', '4', '5')
        elif desktop == 'lxde':
            image_config = self.config.get(
                'Wallpaper Modes', 'LXDE', fallback='scaled')
            mode = ('tiled', 'center', 'scaled', 'fit', 'stretch')
        else:
            image_config = self.config.get(
                'Wallpaper Modes', 'Openbox', fallback='--bg-max')
            mode = ('--bg-max', '--bg-scale', '--bg-tile', '--bg-fill',
                    '--bg-center')
        if image_config in mode:
            self._state['mode'] = image_config
            return self._state['mode']
        else:
            print(self._state['mode_error'])

    def set_gnome3(self):
        # set GNOME 3 background for Gnome Shell, Cinnamon, and Unity
        if os.environ.get('DESKTOP_SESSION') == 'cinnamon':
            self.get_mode('cinnamon')
        else:
            self.get_mode('gnome')
        gnome3 = \
            'gsettings set org.gnome.desktop.background picture-options\
            {};'.format(self._state['mode']) + \
            'gsettings set org.gnome.desktop.background picture-uri \
            \'file://{}\''.format(self.get_state('pic'))
        return gnome3

    def set_mate(self):
        self.get_mode('mate')
        mate = \
            'gsettings set org.mate.background picture-options {0}; \
            gsettings set org.mate.background picture-filename \
            \'{1}\''.format(self._state['mode'], self.get_state('pic'))
        return mate

    def set_kde(self):
        # set KDE4 & 5
        kde = \
            'rm $(find {1} -type f \
            -iregex ".*\.\(jpg\|png\|jpeg\)$") 2> /dev/null ;\
            cp {0} {1}/'.format(self.get_state('pic'), self.configDirectory)
        return kde

    def set_xfce(self):
        # Shell string by Peter Levi, http://peterlevi.com/variety/
        self.get_mode('xfce')
        xfce = \
            """for i in $(xfconf-query -c xfce4-desktop -p /backdrop -l|egrep \
                -e "screen.*/monitor.*image-path$" \
                -e "screen.*/monitor.*/last-image$"); do
                    xfconf-query -c xfce4-desktop -p $i -n \
                    -t string -s "" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{0}" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{1}" 2> /dev/null
            done""".format(self._state['mode'], self.get_state('pic'))
        return xfce

    def set_lxde(self):
        self.get_mode('lxde')
        lxde = 'pcmanfm --set-wallpaper \'{}\' \
        --wallpaper-mode={}'.format(self.get_state('pic'), self._state['mode'])
        return lxde

    def set_openbox(self):
        # Openbox and other *nix window managers
        if self.depends['feh'][1]:
            self.get_mode('openbox')
            openbox = 'feh {} \'{}\''.format(self._state['mode'],
                                             self.get_state('pic'))
            return openbox
        else:
            print('Openbox and any undetected environs require feh.')

    def set_windows(self):
        # Note: in Python3, strings passed to windll must be encoded as ascii
        windows = ctypes.windll.user32.SystemParametersInfoA(0x14, 0,
                                                             self.get_state(
                                                                 'pic').encode(
                                                                 'ascii'), 3)
        return windows

    def set_mac(self):
        applescript = """/usr/bin/osascript<<END
        tell application "Finder"
        set desktop picture to POSIX file "{}"
        end tell
        END""".format(self.get_state('pic'))
        return applescript

    def set_background(self):
        """executes appropriate environment command to set wallpaper"""
        if 'APPDATA' in os.environ:
            return self.set_desktop()
        else:
            return subprocess.call(self.set_desktop(), shell=True)


def main(argv):
    env = Environment()
    env.set_state('pic', '{}/Pictures/image.jpg'.format(env.get_state('home')))
    env.set_background()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
