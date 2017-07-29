#!/usr/bin/env python3


"""
FILE: rwall.py

DISCLAIMER: Distributed under GPL3.0. There is NO warranty expressed or implied.

USAGE: rwall.py -h

DESCRIPTION: rWall randomizes backgrounds in GNOME 3 (GNOME Shell, Cinnamon,
Unity, MATE), KDE, Xfce, LXDE, Openbox, Mac OS X, and Windows 7 through 10.

rWall is useful for folks with large image libraries. If you haven't seen some
of your favorite images in a while, rWall will be a treat! Your background will
become a random or ordered flipbook or slideshow. Set the program file as
executable and assign the various options to keyboard shortcuts.

FEATURES:
* auto-detects and sets wallpaper for all supported desktop environments
* commandline options for up to five user-preset image directories
  or picks a random background from a commandline-supplied directory
* unified way to apply a specific or random wallpaper in all
  supported environments
* set a default image directory
* walks up and down alphabetically through the images in the last used directory
* slideshow from images in a directory
* filter images by standard aspect ratios or by the aspect ratio of the current
  display's aspect ratio.
* produces a separate profile for each desktop environment on a system, allowing
  rWall to remember your wallpaper preferences on a per-environment basis

TODO: explore OSX functionality
OPTIONS: type rwall.py -h in a terminal
REQUIREMENTS: Python3.2+, python3-pil, python3-tk, feh, xclip, and a supported
desktop environment.
BUGS: ---
NOTES: Feh is used for Openbox and any unknown environment. KDE users must click
Default Desktop Settings > Slideshow, apply "~/.config/rwall/kde-plasma", and
may have to logout/login.
AUTHOR: rockhazard, rockhazardz@gmail.com
ACKNOLEDGMENTS: xfconf shell string: Peter Levi (please go check out Variety!
http://peterlevi.com/variety/)
COMPANY: ---
VERSION: rWall 3.5q "Akira", by rockhazard (c)2016
CREATED: 09/13/2015
REVISION: 07/14/2016
LICENSE: GPL 3.0, no warranty expressed or implied
"""

__author__ = 'rockhazard'
import os, random, sys, imghdr, time, configparser, argparse, textwrap
import ctypes
from pathlib import Path
from fractions import Fraction
from subprocess import call

# doing in-script dependency checks, because absence of packages will reduce
# functionality but not break the script, therefore warn user, but proceed
depends = dict(xclip=['/usr/bin/xclip', True], feh=['/usr/bin/feh', True])
modules = dict(Pillow=None, Tkinter=None)

# python module dependencies
try:
    from PIL import Image
    modules['Pillow'] = True
except ImportError:
    modules['Pillow'] = False
try:
    import tkinter as tk
    modules['Tkinter'] = True
except ImportError:
    modules['Tkinter'] = False

# Linux dependencies
if 'APPDATA' not in os.environ:
    for package, path in depends.items():
        if not Path(path[0]).is_file():
            path[1] = False
            print('Please install:', Path(package).name)


class Rwall:
    """Randomizes wallpaper under multiple environments"""
    def __init__(self, **kwargs):  # classwide perams
        # User's home directory
        self.home = os.path.expanduser('~')

        # directory flags, used for argument test in start_slideshow()
        self.dirFlags = ('directory1', 'directory2', 'directory3', 'directory4',
                         'directory5', '1', '2', '3', '4', '5')

        # desktop environment flags for diff implementations
        self.gnomeEnv = ('cinnamon', 'gnome', 'ubuntu', 'unity')
        self.kdeEnv = ('kde-plasma', 'plasma', '/usr/share/xsessions/plasma')

        # desktop environment detection variable
        if os.environ.get('DESKTOP_SESSION'):
            self.desktopSession = os.environ.get('DESKTOP_SESSION')
        if 'DESKTOP_SESSION' not in os.environ:
            try:
                self.desktopSession = os.environ['OS']
            except KeyError:
                self.desktopSession = 'Unknown'

        # final environment command
        self.desktopEnvironment = None

        # valid image types; to expand, use imghdr.what() values
        self.fileTypes = ('jpeg', 'png')

        # configuration files
        if self.desktopSession in self.kdeEnv:
            self.configDirectory = str(Path(self.home,
                                            '.config/rwall/kde-plasma/'))
        else:
            self.configDirectory = str(Path(self.home,
                                            '.config/rwall/{}'.format(
                                                self.desktopSession)))
        self.configFile = Path(self.home, self.configDirectory, 'rwall.conf')
        self.bgFile = Path(self.home, self.configDirectory, 'background.conf')
        # configuration file parser
        self.config = configparser.RawConfigParser(allow_no_value=True)
        # background config parser
        self.bgConfig = configparser.RawConfigParser(allow_no_value=True)

        # class-wide dictionary and its defaults
        self._state = kwargs
        self._state['verbose'] = False
        self._state['directory'] = None
        self._state['filter'] = False
        self._state['slideshow'] = False
        self._state['parent'] = False
        # values are 'random', 'next', 'previous', 'commandline', and 'first'
        self._state['image'] = 'random'
        # display if modes settings wrong or missing
        self._state['mode_error'] = textwrap.dedent("""\
            WARNING: configuration fault detected
            check modes in rwall.conf
            fallback mode applied""")

        # fallback wallpaper modes
        if 'openbox' in self.desktopSession:
            self._state['mode'] = '--bg-max'
        elif 'xfce' in self.desktopSession:
            self._state['mode'] = '4'
        else:
            self._state['mode'] = 'scaled'

        self.sourceImages = []
        self.imagesList = None
        self.selectedImage = None

    """
    CONFIGURATION FUNCTIONS
    """
    def set_state(self, key, value):
        self._state[key] = value

    def get_state(self, key):
        return self._state.get(key, None)

    def set_config(self):
        """create configuration directory and file if absent, read if present"""
        default = str(Path(self.home, 'Pictures'))

        # check for existence of config directory, create if absent
        if not Path(self.configDirectory).is_dir():
            os.makedirs(self.configDirectory)
            print('created configuration directory')

        # uncomment next line to make config case-sensitive
        self.config.optionxform = lambda option: option

        # check for existence of config file, create if absent
        if not self.configFile.is_file():
            self.config.add_section('rWall Configuration')
            self.config.set('rWall Configuration',
                            textwrap.dedent("""\
            # Please modify this file to change rWall\'s behavior.
            # If you make a mistake, a clue will print to the terminal.
            # If all else fails just delete this file and run rwall.py.
            # A fresh working default config file will be created for you.
            # Thanks for using rWall. Have fun!"""))

            # default settings
            self.config.add_section('Defaults')
            # announce wallpaper application and image/environment stats
            # self.config.set('Defaults','Announce', 'no')
            # replace 'editor' with user's default text editor
            self.config.set('Defaults', 'Default Config Editor', 'editor')
            self.config.set('Defaults', 'Default Background Editor', 'gimp')
            self.config.set('Defaults', 'Default Directory',
                            '{}'.format(default))

            # wallpaper mode settings
            self.config.add_section('Wallpaper Modes')

            # wallpaper mode presets
            self.config.set('Wallpaper Modes',
                            textwrap.dedent("""\
            # Aspect Ratio Filter Options:
            # sd480, hd1050, hd1080, hd1050x2, hd1080x2, and auto"""))
            self.config.set('Wallpaper Modes', 'Aspect Ratio Filter', 'none')
            self.config.set('Wallpaper Modes',
                            textwrap.dedent("""\n\
            # Wallpaper Mode Settings by Environment:
            # KDE modes must be selected within KDE\'s slideshow options"""))
            self.config.set('Wallpaper Modes',
                            textwrap.dedent("""\n\
            # GNOME3 (GNOME Shell, Cinnamon, Unity, and MATE):
            # none, centered, scaled, spanned, stretched, wallpaper, zoom"""))
            self.config.set('Wallpaper Modes', 'Cinnamon', 'scaled')
            self.config.set('Wallpaper Modes', 'GNOME', 'scaled')
            self.config.set('Wallpaper Modes', 'MATE', 'scaled')
            self.config.set('Wallpaper Modes',
                            textwrap.dedent("""\n\
            # Xfce:
            # 0-Auto, 1-Centered, 2-Tiled, 3-Stretched, 4-Scaled, 5-Zoomed"""))
            self.config.set('Wallpaper Modes', 'Xfce', '4')
            self.config.set('Wallpaper Modes',
                            textwrap.dedent("""\n\
            # Openbox (or any use of feh):
            # --bg-max,--bg-scale,--bg-tile,--bg-fill,--bg-center"""))
            self.config.set('Wallpaper Modes', 'Openbox', '--bg-max')
            self.config.set('Wallpaper Modes',
                            textwrap.dedent("""\n\
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
            print('Configuration file: {}\nuse rwall.py -c to edit file\
                '.format(str(self.configFile)))
            print('Default image directory is set to {}'.format(default))
            sys.exit(textwrap.dedent("""\
                Please run rwall.py again to select and apply a background.
                If you need help, type rwall.py -h in a terminal."""))
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
                # bgconfig accessors assigned vars here when used more than once

            print(
                'created background configuration file: {}'.format(self.bgFile))
        else:
            self.bgConfig.read(str(self.bgFile))

    """
    DIRECTORY AND ENVIRONMENT FUNCTIONS
    """
    def clear_screen(self, com='clear'):
        if 'APPDATA' not in os.environ:
            call(com, shell=True)
        else:
            call('cls', shell=True)

    def change_directory(self, directory):
        """reads config or commandline for directories, then checks path
        validity"""
        if directory in self.dirFlags[0:5]:
            self.imageDirectory = self.config.get('Preset Image Directories',
                                                  directory.title())
        elif directory in self.dirFlags[5:]:
            self.imageDirectory = self.config.get('Preset Image Directories',
                                                'Directory{}'.format(directory))
        elif directory == 'directory':  # commandline-supplied directory
            self.imageDirectory = self._state['directory']
        elif directory == 'reshuffle':
            self.set_bgconfig()
            self.imageDirectory = \
                self.bgConfig.get('Temp', 'Current Directory')
        elif directory == 'default':
            self.imageDirectory = \
                self.config.get('Defaults', 'Default Directory')

        # check path validity, then return path for processing
        if Path(self.imageDirectory).is_dir():
            return self.imageDirectory
        else:
            sys.exit('Invalid directory!')

    def record_dir(self):
        """records background image path to background.conf"""
        self.set_bgconfig()
        self.bgConfig.set('Temp', 'Current Directory', self.imageDirectory)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgConfig.write(configfile)

    def set_desktop_environment(self):
        """detect desktop environment to set appropriate desktop function"""
        if self.desktopSession in self.gnomeEnv:
            self.desktopEnvironment = self.set_gnome3()
        elif self.desktopSession in self.kdeEnv:
            self.desktopEnvironment = self.set_kde()
        elif self.desktopSession == 'LXDE':
            self.desktopEnvironment = self.set_lxde()
        elif self.desktopSession == 'mate':
            self.desktopEnvironment = self.set_mate()
        elif self.desktopSession == 'xfce':
            self.desktopEnvironment = self.set_xfce()
        elif self.desktopSession == 'openbox':
            self.desktopEnvironment = self.set_openbox()
        elif 'APPDATA' in os.environ:
            self.desktopEnvironment = self.set_windows()
        elif 'Apple_PubSub_Socket_Render' in os.environ:
            self.desktopEnvironment = self.set_mac()
        else:
            self.desktopEnvironment = self.set_openbox()
        return self.desktopEnvironment

    """
    IMAGE ACQUISITION FUNCTIONS
    """
    def get_source_images(self):
        """create list of images from given directory"""
        # list files recursively, or only in target directory
        extensions = ('.jpg', '.jpeg', '.png')
        if not self._state['parent']:
            for root, dirnames, filenames in os.walk(self.imageDirectory):
                for file in filenames:
                    candidate = str(Path(root, file))
                    if candidate.endswith(extensions):
                        self.sourceImages.append(candidate)
        else:
            for file in Path(self.imageDirectory).iterdir():
                candidate = str(file)
                if candidate.endswith(extensions):
                    self.sourceImages.append(candidate)

        # check if images list is empty
        try:
            if self.sourceImages[0]:
                if self._state['verbose']:
                    print('Image list build successful!')
        except IndexError:
            sys.exit('No valid images in "{}"'.format(self.imageDirectory))

        if modules['Pillow']:
            self.image_filter()
        else:
            print('NOTICE: Pillow not installed. Image filtering disabled.')

        # prevent runaway append to images.txt during slideshow
        if not self._state['slideshow']:
            self.write_images_list_file()
        return self.sourceImages

    def get_screen_rez(self):
        if modules['Tkinter']:
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            return screen_width / screen_height
        elif self._state['filter'] == 'auto':
            print(textwrap.dedent("""\
                Automatic aspect ratio detection disabled.
                Please install python3-tk package."""))

    def image_filter(self):
        """optionally filters images by aspect ratio"""
        # container for final filtered list
        filtered_images = []
        ratios = dict(sd480=4 / 3, hd1050=8 / 5, hd1080=16 / 9,
                      dci4k=256 / 135, hd1050x2=16 / 5, hd1080x2=32 / 9,
                      dci4kx2=512 / 135, auto=self.get_screen_rez())
        # commandline overrides config file filter setting
        if self._state['filter']:
            aspect_ratio = self._state['filter']
        else:
            aspect_ratio = self.config.get(
                'Wallpaper Modes', 'Aspect Ratio Filter', fallback='none')
        if aspect_ratio in ratios:
            for pic in self.sourceImages:
                # get image's aspect ratio, then match against filter
                try:
                    im = Image.open(pic)
                    x, y = im.size
                    image_dimensions = Fraction(x, y)
                    im_x = image_dimensions.numerator
                    im_y = image_dimensions.denominator
                    if im_x / im_y == ratios[aspect_ratio]:
                        filtered_images.append(pic)
                except IOError:  # skip on corrupt image
                    continue
            if not filtered_images:
                sys.exit('No {} images found.'.format(aspect_ratio))
            else:
                self.sourceImages = filtered_images
                return self.sourceImages
        elif aspect_ratio not in ['None', 'NONE', 'no', 'none', '']:
            print('Invalid value. Check image filter setting.')

    def write_images_list_file(self):
        """produce images file for next/previous across user sessions therefore
        this file is not temporary"""
        with open('{}/images.txt'.format(self.configDirectory), 'w') \
                as images_list_file:
            for line in self.sourceImages:
                print(line, file=images_list_file, end='\n')

    def get_imagesList(self):
        """sorted list from images.txt for next/previous"""
        try:
            with open('{}/images.txt'.format(self.configDirectory)) as images:
                self.imagesList = sorted(images.read().splitlines())
        except FileNotFoundError:
            sys.exit(textwrap.dedent('No images file. Point rwall.py at a '
                                     'directory containing images using -d.'))
        return self.imagesList

    def select_random_image(self):
        """default image value"""
        # do not trigger images.txt write if in slideshow
        if not self._state['slideshow']:
            self.get_source_images()
        random_image = random.choice(self.sourceImages)
        return random_image

    def select_first_image(self):
        """select first image in directory"""
        # does not trigger images.txt write if used in slideshow
        if not self._state['slideshow']:
            self.get_source_images()
        first_image = self.sourceImages[0]
        return first_image

    def select_cli_image(self):
        """select image from commandline"""
        self.imageDirectory = os.path.dirname(self._state['directory'])
        commandline_image = self._state['directory']
        try:  # validate
            if imghdr.what(commandline_image) in self.fileTypes:
                self.get_source_images()
                return commandline_image
            else:
                return sys.exit('Invalid filetype!')
        except IsADirectoryError:
            return sys.exit('That\'s a directory, not a filename!')
        except FileNotFoundError:
            return sys.exit('No such file!')

    def select_next_image(self):
        """step to next image in imagesList"""
        # target of self._state when assigned 'next'
        self.get_imagesList()
        self.get_index_background()
        # retrieve index of current background in image list
        image_index = self.imagesList.index(self.indexedBG)
        try:
            if self.indexedBG in self.imagesList:
                next_image = self.imagesList[image_index + 1]
        except IndexError:
            next_image = self.imagesList[0]
            print('Reached end of list: applying first image in list!')
        if self._state['verbose']:
            print('Background {} in a list of {} applied.'.format(
                image_index + 1, len(self.imagesList)))
        return next_image

    def select_previous_image(self):
        """step to previous image in imagesList"""
        # target of self._state when assigned 'previous'
        self.get_imagesList()
        self.get_index_background()
        # retrieve index of current background in image list
        image_index = self.imagesList.index(self.indexedBG)
        try:
            if self.indexedBG in self.imagesList:
                last_image = self.imagesList[image_index - 1]
        except IndexError:
            last_image = self.imagesList[-1]
            print('Reached beginning of list: applying last image in list!')
        if self._state['verbose']:
            print('Background {} in a list of {} applied.'.format(
                image_index - 1, len(self.imagesList)))
        return last_image

    def start_slideshow(self, directory='directory', delay=10, count=10,
                        switch='random'):
        # check directory to match forms '1' through '5' and
        # 'directory1' through 'directory5', or path
        if Path(self._state['directory']).is_dir():
            directory = 'directory'
        elif directory in self.dirFlags:
            directory = self._state['directory']
        else:
            sys.exit('Invalid directory!')
        if delay < 1:
            sys.exit('DELAY must be greater than 0.')
        if switch not in ('next', 'random'):
            sys.exit('Error: SWITCH must be either "random" or "next"')
        self.change_directory(directory)
        self.set_bgconfig()
        self.get_source_images()
        self.write_images_list_file()
        self.selectedImage = self.sourceImages[0]
        self.index_background()
        try:
            # count=0 sets count to number of files in imagesList
            # starts slideshow from first images in list
            if count == 0:
                print('COUNT set to number of images in directory')
                self.get_imagesList()
                count = len(self.imagesList)
                self.set_state('image', 'first')
                self.set_background()
            while count > 0:
                self.set_state('image', switch)
                self.set_background()
                time.sleep(delay)
                count -= 1
                self.clear_screen()
                if self._state['verbose']:
                    current_dir = self.bgConfig.get('Temp', 'Current Directory')
                    time_remaining = round(float((count * delay) / 60), 2)
                    print('{0} wallpaper changes remain over {1} minutes:\n{2}\
                        '.format(count, time_remaining, current_dir),
                          '\nPress Ctrl-C to cancel.')
                else:
                    print('rWall Slideshow\nPress Ctrl-C to cancel.')
            else:
                self.clear_screen('reset')
                print('rWall slideshow has ended.')
        except KeyboardInterrupt:
            self.clear_screen('reset')
            sys.exit('Slideshow terminated by user...')

    def index_background(self):
        """allows next/previous to move passed corrupted images"""
        self.set_bgconfig()
        self.bgConfig.set('Temp', 'Indexed Background', self.selectedImage)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgConfig.write(configfile)

    def record_background(self):
        """records applied background"""
        self.set_bgconfig()
        bg_dir = os.path.dirname(self.selectedImage)
        self.bgConfig.set('Temp', 'Current Directory', bg_dir)
        self.bgConfig.set('Temp', 'Current Background', self.selectedImage)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgConfig.write(configfile)

    def skip_image(self):
        self.index_background()
        print('rWall skipped:\n{}\nIt is a corrupted or missing file.\
              '.format(self.get_index_background()))
        if self._state['image'] == 'next':
            self.selectedImage = self.select_next_image()
        elif self._state['image'] == 'previous':
            self.selectedImage = self.select_previous_image()
        self.index_background()

    def select_image(self):
        """trigger image selection function according to image value and send
        the final image to desktop environment command"""
        if self._state['image'] == 'random':
            self.selectedImage = self.select_random_image()
        elif self._state['image'] == 'first':
            self.selectedImage = self.select_first_image()
        elif self._state['image'] == 'next':
            self.selectedImage = self.select_next_image()
        elif self._state['image'] == 'previous':
            self.selectedImage = self.select_previous_image()
        elif self._state['image'] == 'commandline':
            self.selectedImage = self.select_cli_image()

        # test for valid filetypes, then index background
        try:
            if imghdr.what(self.selectedImage) in self.fileTypes:
                # index for internal use: enables next/previous functions
                # even on fault; separate from finally applied background
                self.index_background()
            else:  # index fault, and skip to next or last file
                self.skip_image()
        except FileNotFoundError:
            self.skip_image()

        # used with get_record_background() and edit_background()
        self.record_background()

        return self.selectedImage

    """
    DESKTOP ENVIRONMENT COMMANDS
    """
    def get_mode(self, environment):
        """check and apply user-defined mode format; use fallback if corrupt"""
        if environment == 'cinnamon':
            image_config = self.config.get(
                'Wallpaper Modes', 'Cinnamon', fallback='scaled')
            mode = ('none', 'centered', 'scaled', 'spanned', 'stretched',
                    'wallpaper', 'zoom')
        elif environment == 'gnome':
            image_config = self.config.get(
                'Wallpaper Modes', 'GNOME', fallback='scaled')
            mode = ('none', 'centered', 'scaled', 'spanned', 'stretched',
                    'wallpaper', 'zoom')
        elif environment == 'mate':
            image_config = self.config.get(
                'Wallpaper Modes', 'MATE', fallback='scaled')
            mode = ('none', 'centered', 'scaled', 'spanned', 'stretched',
                    'wallpaper', 'zoom')
        elif environment == 'xfce':
            image_config = self.config.get(
                'Wallpaper Modes', 'Xfce', fallback='4')
            mode = ('0', '1', '2', '3', '4', '5')
        elif environment == 'lxde':
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
        image = self.select_image()
        gnome3 = \
            'gsettings set org.gnome.desktop.background picture-options\
            {};'.format(self._state['mode']) + \
            'gsettings set org.gnome.desktop.background picture-uri \
            \'file://{}\''.format(image)
        return gnome3

    def set_mate(self):
        self.get_mode('mate')
        image = self.select_image()
        mate = \
            'gsettings set org.mate.background picture-options {0}; \
            gsettings set org.mate.background picture-filename \
            \'{1}\''.format(self._state['mode'], image)
        return mate

    def set_kde(self):
        # set KDE4 & 5
        image = self.select_image()
        kde = \
            'rm $(find {1} -type f \
            -iregex ".*\.\(jpg\|png\|jpeg\)$") 2> /dev/null ;\
            cp {0} {1}/'.format(image, self.configDirectory)
        return kde

    def set_xfce(self):
        # Shell string by Peter Levi, http://peterlevi.com/variety/
        self.get_mode('xfce')
        image = self.select_image()
        xfce = \
            """for i in $(xfconf-query -c xfce4-desktop -p /backdrop -l|egrep \
                -e "screen.*/monitor.*image-path$" \
                -e "screen.*/monitor.*/last-image$"); do
                    xfconf-query -c xfce4-desktop -p $i -n \
                    -t string -s "" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{0}" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{1}" 2> /dev/null
            done""".format(self._state['mode'], image)
        return xfce

    def set_lxde(self):
        self.get_mode('lxde')
        image = self.select_image()
        lxde = 'pcmanfm --set-wallpaper \'{}\' \
        --wallpaper-mode={}'.format(image, self._state['mode'])
        return lxde

    def set_openbox(self):
        # Openbox and other *nix window managers
        if depends['feh'][1]:
            self.get_mode('openbox')
            image = self.select_image()
            openbox = 'feh {} \'{}\''.format(self._state['mode'], image)
            return openbox
        else:
            print('Openbox and any undetected environs require feh.')

    def set_windows(self):
        # Note: in Python3, strings passed to windll must be encoded as ascii
        image = self.select_image()
        windows = ctypes.windll.user32.SystemParametersInfoA(0x14, 0,
            image.encode('ascii'), 3)
        return windows

    def set_mac(self):
        image = self.select_image()
        applescript = """/usr/bin/osascript<<END
        tell application "Finder"
        set desktop picture to POSIX file "{}"
        end tell
        END""".format(image)
        return applescript

    """
    BACKGROUND FUNCTIONS
    """
    def set_background(self):
        """executes appropriate environment command to set wallpaper"""
        if 'APPDATA' in os.environ:
            return self.set_desktop_environment()
        else:
            return call(self.set_desktop_environment(), shell=True)

    def get_index_background(self):
        """"retrieves index for next/previous functions"""
        self.set_bgconfig()
        self.indexedBG = self.bgConfig.get('Temp', 'Indexed Background')
        return self.indexedBG

    def get_record_background(self):
        """retrieves background for use in editing and clipboard"""
        self.set_bgconfig()
        applied_bg = self.bgConfig.get('Temp', 'Current Background')
        # if in windows, don't use xclip; if in MacOS us pbcopy
        if 'APPDATA' not in os.environ:
            if depends['xclip'][1]:
                call('echo -n "{}" | \
                     xclip -selection clipboard'.format(applied_bg), shell=True)
        elif 'Apple_PubSub_Socket_Render' in os.environ:
            call('echo -n {} | pbcopy'.format(applied_bg), shell=True)
        return applied_bg

    def edit_background(self):
        applied_bg = self.get_record_background()
        edit_bg = self.config.get('Defaults', 'Default Background Editor')
        return call('{} \'{}\''.format(edit_bg, applied_bg), shell=True)

    def edit_config(self):
        self.set_config()
        edit_conf = self.config.get('Defaults', 'Default Config Editor')
        return call('{} {}/rwall.conf'.format(edit_conf, self.configDirectory),
                    shell=True)

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
            \n{}'.format(self._state['image'], current_dir))


def main(argv):
    rwall = Rwall()
    rwall.set_config()

    """
    COMMANDLINE OPTIONS
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog=str(Path(sys.argv[0]).name),
        description=textwrap.dedent("""\
        DESCRIPTION:
        rWall randomizes your desktop background image in GNOME3, Cinnamon,
        MATE, KDE 4 & 5, Xfce, Openbox, LXDE, Mac OS X, and Windows 7 and newer;
        if none of these environments are detected, then rWall attempts
        to use feh to set your background.

        SETUP:
        Choose various background image source directories, then edit rwall.conf
        in "~/.config/rwall/{}" accordingly. You may
        use "%(prog)s -c" to edit this file, if you like. For KDE usage
        set KDE's desktop slideshow feature to "~/.config/rwall/kde-plasma".
        rWall requires feh for Openbox and unidentified desktop environs.  See
        your desktop environment's documentation for help setting up feh.
        """.format(rwall.desktopSession)), epilog=textwrap.dedent("""\
        rWall is developed by rockhazard and licensed under GPL3.0. There are no
        warranties expressed or implied.
        """))
    parser.add_argument('--version', help='print version info then exit',
        version='rWall 3.5q "Akira", GPL3.0 (c) 2016, by rockhazard',
        action='version')
    parser.add_argument('-v', '--verbose',
        help='print detailed feedback on rWall functions', action='store_true')
    parser.add_argument('-c', '--config',
        help='edit the configuration file, set initially to the user\'s \
        default text editor', action='store_true')
    parser.add_argument('-a', '--filter', help=
        'filter images by one of these aspect ratios: sd480, hd1050, hd1080, \
        dci4k, hd1050x2, hd1080x2, dci4kx2, and auto. Note that the notation \
        is designed for easy identification by popular sample resolution, but \
        multiple resolutions may be filtered per aspect ratio (such as 4k UHD \
        and 1080 HD, since both are 16:9 aspect ratio).', nargs=1, metavar=(
        'ASPECT_RATIO'))
    parser.add_argument('-t', '--parent',
        help='ignore images in subdirectories',
        action='store_true')
    parser.add_argument('-d', '--directory', help=
        'random background from DIRECTORY, e.g. "%(prog)s -d ~/Pictures"',
        nargs=1)
    parser.add_argument('-r', '--reshuffle',
        help='random background from current directory',
        action='store_true')
    parser.add_argument('-1', '--directory1',
        help='random background from images in first preset directory',
        action='store_true')
    parser.add_argument('-2', '--directory2',
        help='random background from images in second preset directory',
        action='store_true')
    parser.add_argument('-3', '--directory3',
        help='random background from images in third preset directory',
        action='store_true')
    parser.add_argument('-4', '--directory4',
        help='random background from images in fourth preset directory',
        action='store_true')
    parser.add_argument('-5', '--directory5',
        help='random background from images in fifth preset directory',
        action='store_true')
    parser.add_argument('-n', '--next',
        help='applies next background alphabetically from the current\
            image directory', action='store_true')
    parser.add_argument('-p', '--previous',
        help='applies previous background alphabetically from the current\
            image directory', action='store_true')
    parser.add_argument('-i', '--image', help=
        'apply IMAGE as wallpaper: "%(prog)s -i /path/to/file"', nargs=1)
    parser.add_argument('-f', '--first', help=
        'first background from DIRECTORY, e.g. "%(prog)s -f ~/Pictures"',
        nargs=1, metavar='DIRECTORY')
    parser.add_argument('-s', '--slideshow', help=
        """create a background slideshow by looping the background in
        DIRECTORY directory, every DELAY seconds, COUNT number of times,
        e.g. "%(prog)s -s ~/Pictures 5 10". DELAY must be greater than 0.\
        COUNT of 0 sets COUNT to number of images in given directory. SWITCH
        is either "random" or "next", and describes the order of the loop.
        DIRECTORY can also be 1 through 5, or directory1 through directory5.
        These are mapped to your preset directories in rwall.conf.""",
        nargs=4,  metavar=('DIRECTORY', 'DELAY', 'COUNT', 'SWITCH'))
    parser.add_argument('-b', '--printbackground',
        help=
        'prints filename of last-applied background to stdout and clipboard',
        action='store_true')
    parser.add_argument('-e', '--editbackground',
        help='edit the current background, defaulted to the GIMP',
        action='store_true')
    args = parser.parse_args()
    rwall.set_state('verbose', args.verbose)

    if args.parent:
        rwall.set_state('parent', args.parent)
    if args.filter:
        rwall.set_state('filter', args.filter[0])
    if args.reshuffle:
        rwall.change_directory('reshuffle')
    elif args.directory1:
        rwall.change_directory('directory1')
    elif args.directory2:
        rwall.change_directory('directory2')
    elif args.directory3:
        rwall.change_directory('directory3')
    elif args.directory4:
        rwall.change_directory('directory4')
    elif args.directory5:
        rwall.change_directory('directory5')
    elif args.next:
        rwall.set_state('image', 'next')
    elif args.previous:
        rwall.set_state('image', 'previous')
    elif args.image:
        rwall.set_state('image', 'commandline')
        rwall.set_state('directory', args.image[0])
    elif args.printbackground:
        print(rwall.get_record_background())
        sys.exit()
    elif args.editbackground:
        sys.exit(rwall.edit_background())
    elif args.slideshow:
        rwall.set_state('slideshow', True)
        rwall.set_state('directory', args.slideshow[0])
        sys.exit(rwall.start_slideshow(args.slideshow[0],
                int(args.slideshow[1]),
                int(args.slideshow[2]),
                args.slideshow[3]))
    elif args.directory:
        if Path(args.directory[0]).is_dir():
            rwall.set_state('directory', args.directory[0])
            rwall.change_directory('directory')
        else:
            sys.exit('Invalid directory! Check commandline argument.')
    elif args.first:
        rwall.set_state('image', 'first')
        if Path(args.first[0]).is_dir():
            rwall.set_state('directory', args.first[0])
            rwall.change_directory('directory')
        else:
            sys.exit('Invalid directory! Check commandline argument.')
    elif args.config:
        sys.exit(rwall.edit_config())
    else:
        rwall.change_directory('default')

    rwall.set_background()

    if args.verbose:
        rwall.announce()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
