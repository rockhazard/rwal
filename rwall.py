#!/usr/bin/env python3


"""
FILE: rwall.py

DISCLAIMER: Distributed under GPL3.0. There is NO warranty expressed or implied.

USAGE: rwall.py -h

DESCRIPTION: rWall randomizes backgrounds in GNOME 3, Cinnamon 2, KDE 4-5, Mate,
Xfce 4.10, LXDE, Openbox (using feh), and Windows 7-10. rWall was developed 
primarily in Linux Mint, but has been shown to work in many distributions. 
This program was originally ported from a bash script with the same name and 
author.

rWall is useful for folks with large image libraries. If you haven't seen some 
of your favorite images in a while, rWall will be a treat!

FEATURES: 
* auto-detects and sets wallpaper for all supported desktop environments
* commandline options for up to five user-preset image directories
* default directory setting 
* picks a random background from a commandline-supplied directory
* walks up and down alphabetically through the images in the last used directory
* slideshow from images in a commandline-supplied directory
* filter images by the aspect ratio of many standard display sizes.

TODO: explore OSX functionality, persist image list between dif DEs
OPTIONS: type rwall.py -h in a terminal
REQUIREMENTS: Python3.2+, feh, python3-pil, xclip, and a supported desktop 
environment.
BUGS: ---
NOTES: Users should run the script once without options, then modify 
~/.config/rwall/rwall.conf as desired; KDE requires setting desktop slideshow to 
"~/.config/rwall/kde/mon1". Openbox require feh to be installed and setup. 
Feh is also used as fallback for unrecognized environments.
AUTHOR: rockhazard, rockhazardz@gmail.com
ACKNOLEDGMENTS: xfconf shell string: Peter Levi (please go check out Variety!
http://peterlevi.com/variety/)
COMPANY: ---
VERSION: rWall 3.5n "Akira", by rockhazard (c)2015
CREATED: 09/13/2015
REVISION: 15
LICENSE: GPL 3.0, no warranty expressed or implied
CHANGELOG: 3.0 First implementation in Python3, 3.5 KDE5 and configuration file
"""

__author__ = 'rockhazard'
import os, glob, re, random, sys, imghdr, time, configparser, argparse, textwrap
import ctypes
from pathlib import Path
from fractions import Fraction
from subprocess import call

# doing in-script dependency checks, because absence of packages will reduce 
# functionality but not break the script, therefore warn user, but proceed
depends = dict( xclip=[ '/usr/bin/xclip', True ], feh=[ '/usr/bin/feh', True ] )
modules = dict( Pillow=None, Tkinter=None )

try: # check for 3rd party modules
    from PIL import Image
    modules['Pillow'] = True
except ImportError:
    modules['Pillow'] = False
try: # check for 3rd party modules
    import tkinter as tk
    modules['Tkinter'] = True
except ImportError:
    modules['Tkinter'] = False

# check for Linux dependencies
if 'APPDATA' not in os.environ:
    for package, path in depends.items():
        if not Path(path[0]).is_file():
            path[1] = False
            print('Please install:', Path(package).name)

# import search path appended for configuration and module files
# sys.path.append('{}/.config/rwall/'.format(os.path.expanduser('~')))

class Rwall:
    def __init__(self, switch='random', **kwargs):  # classwide perams
        # User's home directory
        self.home = os.path.expanduser('~')

        # directory flags, used for argument test in start_slideshow()
        self.dirFlags = ('directory1', 'directory2', 'directory3', 'directory4',
            'directory5', '1', '2', '3', '4', '5')

        # desktop environment detection variable
        self.desktopSession = os.environ.get('DESKTOP_SESSION')
        if 'DESKTOP_SESSION' not in os.environ:
            self.desktopSession = os.environ['OS']
        if self.desktopSession == None:
            self.desktopSession = 'Unknown'

        # valid image types; to expand, use imghdr.what() values
        self.fileTypes = ('jpeg', 'png')

        # configuration files
        self.configFile = Path(self.home, '.config/rwall/rwall.conf')
        self.bgFile = Path(self.home, '.config/rwall/background.conf')

        # class-wide dictionary and its defaults
        self._state = kwargs

        # directory default
        self._state['directory'] = None

        # default image filter state
        self._state['filter'] = False

        # slideshow active?
        self._state['slideshow'] = False

        # image switch determines method of image selection: 
        # 'random', 'next', 'previous', 'commandline', 'first', and 'sync'
        self._state['image'] = switch

        # fallback wallpaper modes
        if 'openbox' in self.desktopSession:
            self._state['mode'] = '--bg-max'
        elif 'xfce' in self.desktopSession:
            self._state['mode'] = '4'
        else:
            self._state['mode'] = 'scaled'

        # display if modes settings wrong or missing
        self._state['mode_error'] = textwrap.dedent("""\
            WARNING: configuration fault detected
            check modes in rwall.conf
            fallback mode applied""")

        # list of images to be randomized and/or sorted
        self.sourceImages = []

    """
    CONFIGURATION FUNCTIONS
    """

    def set_state(self, key, value):
        # accessor method
        self._state[key] = value

    def get_state(self, key):
        # accessor method
        return self._state.get(key, None)

    def set_config(self):
        """
        create configuration directory and file if absent, read if present
        """
        default = str(Path(self.home, 'Pictures'))

        # check for existence of config directory, create if absent
        configDirectory = Path(self.home, '.config/rwall/kde/mon1/')
        if not configDirectory.is_dir():
            os.makedirs(str(configDirectory))
            print('created configuration directory')

        # configuration file parser
        self.config = configparser.RawConfigParser(allow_no_value = True)
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
            # use $EDITOR variable to execute user's default text editor
            self.config.set('Defaults','Default Config Editor', 'editor')
            self.config.set('Defaults','Default Background Editor', 'gimp')
            self.config.set('Defaults','Default Directory', 
                '{}'.format(default))

            # wallpaper mode settings
            self.config.add_section('Wallpaper Modes')
            self.config.set('Wallpaper Modes',
            textwrap.dedent("""\
            # Aspect Ratio Filter Options:
            # sd480, hd1050, hd1080, hd1050x2, hd1080x2, and auto
            #
            # Wallpaper Mode Settings by Environment:
            # KDE modes must be sellected within KDE\'s slideshow options
            # GNOME3 (Cinnamon2.x, MATE, and Ubuntu/Unity): 
            # none, centered, scaled, spanned, stretched, wallpaper, zoom
            # Xfce: 
            # 0-Auto, 1-Centered, 2-Tiled, 3-Stretched, 4-Scaled, 5-Zoomed
            # Openbox (or any use of feh): 
            # --bg-max,--bg-scale,--bg-tile,--bg-fill,--bg-center
            # Lxde: 
            # tiled, center, scaled, fit, stretch \n"""))

            # wallpaper mode presets
            self.config.set('Wallpaper Modes','Aspect Ratio Filter', 'none')
            self.config.set('Wallpaper Modes','Cinnamon', 'scaled')
            self.config.set('Wallpaper Modes','GNOME', 'scaled')
            self.config.set('Wallpaper Modes','MATE', 'scaled')
            self.config.set('Wallpaper Modes','Xfce', '4')
            self.config.set('Wallpaper Modes','Openbox', '--bg-max')
            self.config.set('Wallpaper Modes','LXDE', 'scaled')

            # preset image directory defaults
            self.config.add_section('Preset Image Directories')
            self.config.set('Preset Image Directories','Directory1', 
                '{}'.format(default))
            self.config.set('Preset Image Directories','Directory2', 
                '{}'.format(default))
            self.config.set('Preset Image Directories','Directory3', 
                '{}'.format(default))
            self.config.set('Preset Image Directories','Directory4', 
                '{}'.format(default))
            self.config.set('Preset Image Directories','Directory5', 
                '{}'.format(default))
            with open(str(self.configFile), 'w') as configfile:
                self.config.write(configfile)

            print('created configuration file: {}\nuse rwall.py -c to edit file\
                '.format(str(self.configFile)))
        else:
            # open config file for reading if it already exists
            self.config.read(str(self.configFile))
            # config getter vars assigned here when used more than once

    def set_bgconfig(self):
        # file used by get_background and next/previous functions

        # background config parser
        self.bgconfig = configparser.RawConfigParser(allow_no_value = True)

        # check for existence of background config file, create if absent
        if not self.bgFile.is_file():
            # for process use
            self.bgconfig.add_section('Temp')
            self.bgconfig.set('Temp', 'Current Directory', '')
            self.bgconfig.set('Temp', 'Current Background', '')
            self.bgconfig.set('Temp', 'Indexed Background', '')
            with open(str(self.bgFile), 'w') as configfile:
                # open bgconfig file for reading if it already exists
                self.bgconfig.write(configfile)
                # bgconfig accessors assigned vars here when used more than once

            print(
                'created background configuration file: {}'.format(self.bgFile))
        else:
            self.bgconfig.read(str(self.bgFile))

    """
    DIRECTORY AND ENVIRONMENT FUNCTIONS
    """

    def change_directory(self, directory):
        """
        USER IMAGE DIRECTORIES
        reads config or commandline for directories, then checks if chosen path 
        is valid; edit configuration file (~/.config/rwall/rwall.conf) to set 
        these directories: default directory only used without cli options
        """
        if ('1' or 'directory1') in directory:
            self.imageDirectory = \
                self.config.get('Preset Image Directories','Directory1')
        elif ('2' or 'directory2') in directory:
            self.imageDirectory = \
                self.config.get('Preset Image Directories','Directory2')
        elif ('3' or 'directory3') in directory:
            self.imageDirectory = \
                self.config.get('Preset Image Directories','Directory3')
        elif ('4' or 'directory4') in directory:
            self.imageDirectory = \
                self.config.get('Preset Image Directories','Directory4')
        elif ('5' or 'directory5') in directory:
            self.imageDirectory = \
                self.config.get('Preset Image Directories','Directory5')
        elif directory == 'directory': # commandline-supplied directory
            self.imageDirectory = self._state['directory']
        elif directory == 'default':
            self.imageDirectory = \
                self.config.get('Defaults','Default Directory')

        # check dir validity, then return path for processing
        if Path(self.imageDirectory).is_dir():
            return self.imageDirectory
        else:
            sys.exit('Invalid directory!')

    def record_dir(self,*args):
        # records background image source path to background.conf
        self.set_bgconfig()
        self.bgconfig.set('Temp', 'Current Directory', self.imageDirectory)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgconfig.write(configfile)


    def set_desktop_environment(self):
        """
        auto-detect desktop environment then set appropriate desktop function
        """
        self.gnome = ('cinnamon', 'gnome', 'ubuntu', 'unity')
        self.kde = ('kde-plasma', 'plasma')
        if self.desktopSession in self.gnome:
            self.desktopEnvironment = self.set_gnome3()
        elif self.desktopSession in self.kde:
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
        else:
            self.desktopEnvironment = self.set_openbox()
        return self.desktopEnvironment

    """
    IMAGE ACQUISITION FUNCTIONS
    """

    def get_source_images(self, *args):
        """
        create list of image files from given directory
        """
        # regex pattern matches "*.jpg|jpeg|png"
        imagePattern = re.compile(r'(.+\.(png|jpg|jpeg)$)')
        for root,dirnames,filenames in os.walk(self.imageDirectory):
            for file in filenames:
                path = str(Path(root, file))
                try:
                    self.sourceImages.append(
                        imagePattern.match(path).group())
                except:
                    continue

        # check if image list is empty
        try:
            if self.sourceImages[0]:
                if self._state['verbose']:
                    print('Image list build successful!')
        except IndexError:
            sys.exit('No valid images in "{}"'.format(self.imageDirectory))

        # if aspect ratio filter is set, filter images
        if modules['Pillow']:
            self.image_filter(self.sourceImages)
        else:
            print(
            'NOTICE: Image filtering disabled pending installation of Pillow.')

        # prevent runaway append to images.txt during slideshow
        if not self._state['slideshow']:
            self.write_imagesListFile()
        return self.sourceImages

    def get_screen_rez(self):
        if modules['Tkinter']:
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            return screen_width/screen_height
        elif self._state['filter'] == 'auto':
            print(textwrap.dedent("""\
                Automatic aspect ratio detection disabled.
                Please install python3-tk package."""))

    def image_filter(self, *args):
        # allows filtering of images by aspect ration, as set in config file
        # container for final filtered list
        self.filteredImages = []
        # valid aspect ratios
        ratios = dict( sd480 = 4/3, hd1050 = 8/5, hd1080 = 16/9, 
            hd1050x2 = 16/5, hd1080x2 = 32/9, auto = self.get_screen_rez() )
        if self._state['filter']:
            # get aspect ratio filter setting from commandline
            aspectRatio = self._state['filter']
        else:
            # get config file setting
            aspectRatio = self.config.get(
            'Wallpaper Modes', 'Aspect Ratio Filter', fallback='none')
        if aspectRatio in ratios:
            for pic in self.sourceImages:
                # get image's aspect ratio, then match against filter
                try:
                    im = Image.open(pic)
                    x, y = im.size
                    imagef = Fraction(x,y)
                    im_x = imagef.numerator
                    im_y = imagef.denominator
                    if im_x/im_y == ratios[aspectRatio]:
                        self.filteredImages.append(pic)
                except IOError: # skip on corrupt image
                    continue
            if self.filteredImages == []:
                sys.exit(
                'No {} aspect ratio images found.'.format(aspectRatio))
            else:
                self.sourceImages = self.filteredImages
                return self.sourceImages
        elif aspectRatio not in ['None', 'NONE', 'no', 'none','']:
            print(
            'Invalid value. Check the image filter setting.')

    def write_imagesListFile(self):
        """
        produce images file for use with next/previous across desktop sessions
        therefore this file is not temporary
        """
        self.imagesListFile = open(
            '{}/.config/rwall/images.txt'.format(self.home), 'w')
        for line in self.sourceImages:
            print(line, file = self.imagesListFile, end = '\n')
        self.imagesListFile.close()
        return self.sourceImages

    def get_imagesList(self):
        # produces sorted list from images.txt for indexing in next/previous
        images = open(
            '{}/.config/rwall/images.txt'.format(self.home)).read().splitlines()
        self.imagesList = sorted(images)
        return self.imagesList

    def select_randomImage(self):
        # default, target of self._state value when set to 'random'
        # do not trigger images.txt write if in slideshow
        if not self._state['slideshow']:
            self.get_source_images()
        self.randomImage = random.choice(self.sourceImages)
        return self.randomImage

    def select_firstImage(self):
        # target of self._state variable when assigned 'first'
        # does not trigger images.txt write if used in slideshow
        if not self._state['slideshow']:
            self.get_source_images()
        self.firstImage = self.sourceImages[0]
        return self.firstImage

    def select_cli_image(self):
        # target of self._state variable when assigned 'commandline'
        self.imageDirectory = os.path.dirname(self._state['directory'])
        self.commandlineImage = self._state['directory']
        try: # validate 
            if imghdr.what(self.commandlineImage) in self.fileTypes:
                self.get_source_images(self.imageDirectory)
                return self.commandlineImage
            else:
                return sys.exit('Invalid filetype!')
        except IsADirectoryError:
            return sys.exit('That\'s a directory, not a filename!')
        except FileNotFoundError:
            return sys.exit('No such file!')

    def select_synced_image(self):
        # selectively apply background from previous session to current DE
        self.set_bgconfig()
        image = self.bgconfig.get('Temp', 'Current Background')
        try: # validate image, build list based on it, then return image var
            if imghdr.what(image) in self.fileTypes:
                self.imageDirectory = os.path.dirname(image)
                self.get_source_images(self.imageDirectory)
                self.syncedImage = image
                return self.syncedImage
            else:
                return sys.exit('Invalid filetype!')
        except IsADirectoryError:
            return sys.exit('That\'s a directory, not a filename!')
        except FileNotFoundError:
            return sys.exit('No such file!')


    def select_next_image(self):
        # step to next image in imagesList array
        # target of self._state when assigned 'next'
        self.get_imagesList()  # returns self.imagesList
        self.get_index_background()  # returns self.indexedBG
        # retrieve index of current background in image list
        self.imageIndex = self.imagesList.index(self.indexedBG)
        try:
            if self.indexedBG in self.imagesList:
                self.nextImage = self.imagesList[self.imageIndex + 1]
        except IndexError:
            self.nextImage = self.imagesList[0]
            print('Reached end of list: applying first image in list!')
        return self.nextImage

    def select_previous_image(self):
        # step to previous image in imagesList array
        # target of self._state when assigned 'previous'
        self.get_imagesList()  # returns self.imagesList
        self.get_index_background()  # returns self.indexedBG
        # retrieve index of current background in image list
        self.imageIndex = self.imagesList.index(self.indexedBG)
        try:
            if self.indexedBG in self.imagesList:
                self.lastImage = self.imagesList[self.imageIndex - 1]
        except IndexError:
            self.lastImage = self.imagesList[-1]
            print('Reached beginning of list: applying last image in list!')
        return self.lastImage

    def start_slideshow(self, directory='directory', delay=10, count=10, 
            switch='random'):
        # check parameters before starting slideshow
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
        self.write_imagesListFile()
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
                currentDir = self.bgconfig.get('Temp', 'Current Directory')
                self.set_state('image', switch)
                self.set_background()
                time.sleep(delay)
                count -= 1
                timeRemaining = round(float((count*delay)/60),2)
                call('clear', shell=True)
                if self._state['verbose']:
                    print('{0} wallpaper changes remain over {1} minutes:\n{2}\
                        '.format(count,timeRemaining,currentDir),
                        '\nPress Ctrl-C to cancel.')
                else:
                    print('rWall Slideshow\nPress Ctrl-C to cancel.')
            else:
                call('reset', shell=True)
                print('rWall slideshow has ended.')           
        except KeyboardInterrupt:
            call('reset', shell=True)
            sys.exit('Slideshow terminated by user...')

    def index_background(self):
        # records current background image path and acts as position key for
        # next/previous functions
        self.set_bgconfig()
        # self.bgDir = os.path.dirname(self.selectedImage)
        self.bgconfig.set('Temp', 'Indexed Background', self.selectedImage)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgconfig.write(configfile)

    def record_background(self):
        # records actual background, regardless of image filters or state
        self.set_bgconfig()
        self.bgDir = os.path.dirname(self.selectedImage)
        self.bgconfig.set('Temp', 'Current Directory', self.bgDir)
        self.bgconfig.set('Temp', 'Current Background', self.selectedImage)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgconfig.write(configfile)


    def select_image(self):
        """
        centralized function for processing image options; reads self._state
        flag and assigns image acquisition function to self.selectedImage
        accordingly, which is then sent to detected desktop environment command
        """
        if self._state['image'] == 'random':
            self.selectedImage = self.select_randomImage()
        elif self._state['image'] == 'first':
            self.selectedImage = self.select_firstImage()
        elif self._state['image'] == 'next':
            self.selectedImage = self.select_next_image()
        elif self._state['image'] == 'previous':
            self.selectedImage = self.select_previous_image()
        elif self._state['image'] == 'commandline':
            self.selectedImage = self.select_cli_image()
        elif self._state['image'] == 'sync':
            self.selectedImage = self.select_synced_image()

        # test for valid filetypes, then index background
        if imghdr.what(self.selectedImage) in self.fileTypes:
            # index for internal use: enables next/previous functions
            # even on fault; separate from finally applied background
            self.index_background()
        else:
            # index fault, and skip to next or last valid filename
            self.index_background()
            # if self.config.getboolean('Defaults','Announce'):
            print('rWall skipped:\n{}\nIt is a corrupted file.\
                '.format(self.get_index_background()))
            if self._state['image'] == 'next':
                self.selectedImage = self.select_next_image()
            elif self._state['image'] == 'previous':
                self.selectedImage = self.select_previous_image()
            self.index_background()

        # record newest image that has passed checks and filters
        # for use with get_record_background() and edit_background()
        self.record_background()

        return self.selectedImage

    """
    DESKTOP ENVIRONMENT COMMAND STRINGS
    """

    def set_gnome3(self):
        """
        set GNOME 3 background for Gnome Shell, Cinnamon, and Unity
        modes: none, centered, scaled, spanned, stretched, wallpaper, 
        zoom
        """

        # retrieve the appropriate settings for the detected DE
        if os.environ.get('DESKTOP_SESSION') == 'cinnamon':
            imageConfig = self.config.get(
                'Wallpaper Modes','Cinnamon', fallback='scaled')
        else:
            imageConfig = self.config.get('Wallpaper Modes','GNOME')
        gnomeMode = ('none', 'centered', 'scaled', 'spanned', 'stretched', 
            'wallpaper', 'zoom')

        # fallback in case of user error or missing/corrupted config file
        if imageConfig in gnomeMode:
            self._state['mode'] = imageConfig
        else:
            print(self._state['mode_error'])

        image = self.select_image()
        self.gnome3 = \
            'gsettings set org.gnome.desktop.background picture-options\
            {};'.format(self._state['mode']) + \
            'gsettings set org.gnome.desktop.background picture-uri \
            \'file://{}\''.format(image)
        return self.gnome3

    def set_mate(self):
        """
        set Mate background
        modes: none, centered, scaled, spanned, stretched, wallpaper, 
        zoom
        """
        imageConfig = self.config.get(
            'Wallpaper Modes','MATE', fallback='scaled')
        mateMode = ('none', 'centered', 'scaled', 'spanned', 'stretched', 
            'wallpaper', 'zoom')

        # fallback in case of user error or missing/corrupted config file
        if imageConfig in mateMode:
            self._state['mode'] = imageConfig
        else:
            print(self._state['mode_error'])

        image = self.select_image()
        self.mate = \
            'gsettings set org.mate.background picture-options {0}; \
            gsettings set org.mate.background picture-filename \
            \'{1}\''.format(self._state['mode'],image)
        return self.mate

    def set_kde(self):
        """
        set KDE4 & 5 background mappings must be set manually in KDE desktop 
        slideshow settings
        """
        image = self.select_image()
        self.kde = \
            'rm {1}/.config/rwall/kde/mon1/*;\
            cp {0} {1}/.config/rwall/kde/mon1/'.format(image,self.home)
        return self.kde

    def set_xfce(self):
        """
        set Xfce background
        modes: 0 - Auto, 1 - Centered, 2 - Tiled, 3 - Stretched, 4 - Scaled, 
        5 - Zoomed
        Credit for shell string: Peter Levi (please go check out Variety!
        http://peterlevi.com/variety/)
        """
        imageConfig = self.config.get('Wallpaper Modes','Xfce', fallback='4')
        xfceMode = ('0', '1', '2', '3', '4', '5')

        # fallback in case of user error or missing/corrupted config file
        if imageConfig in xfceMode:
            self._state['mode'] = imageConfig
        else:
            print(self._state['mode_error'])

        image = self.select_image()
        self.xfce = \
            """for i in $(xfconf-query -c xfce4-desktop -p /backdrop -l|egrep \
                -e "screen.*/monitor.*image-path$" \
                -e "screen.*/monitor.*/last-image$"); do
                    xfconf-query -c xfce4-desktop -p $i -n \
                    -t string -s "" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{0}" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{1}" 2> /dev/null
            done""".format(self._state['mode'],image)
        return self.xfce

    def set_lxde(self):
        """
        set LXDE background using Pcmanfm
        modes: 'tiled', 'center', 'scaled', 'fit', 'stretch'
        """
        imageConfig = self.config.get(
            'Wallpaper Modes','LXDE', fallback='scaled')
        lxdeMode = ('tiled', 'center', 'scaled', 'fit', 'stretch')

        # fallback in case of user error or missing/corrupted config file
        if imageConfig in lxdeMode:
            self._state['mode'] = imageConfig
        else:
            print(self._state['mode_error'])

        image = self.select_image()
        self.lxde = 'pcmanfm --set-wallpaper \'{}\' \
        --wallpaper-mode={}'.format(image,self._state['mode'])
        return self.lxde

    def set_openbox(self):
        """
        set Openbox and other window manager backgrounds
        modes: --bg-max,--bg-scale,--bg-tile,--bg-fill,--bg-center
        """
        # check if feh is installed
        if depends['feh'][1]:
            imageConfig = self.config.get(
                'Wallpaper Modes','Openbox', fallback='--bg-max')
            openboxMode = ('--bg-max', '--bg-scale', '--bg-tile', '--bg-fill', 
                '--bg-center')

            # fallback in case of user error or missing/corrupted config file
            if imageConfig in openboxMode:
                self._state['mode'] = imageConfig
            else:
                print(self._state['mode_error'])

            image = self.select_image()
            self.openbox = 'feh {} \'{}\''.format(self._state['mode'],image)
            return self.openbox
        else:
            print('Openbox and any undetected environs require feh.')

    def set_windows(self):
        # Note: in Python3, strings passed to windll must be encoded as ascii
        image = self.select_image()
        self.windows = ctypes.windll.user32.SystemParametersInfoA(0x14, 0, 
            str(image).encode('ascii') , 3)
        return self.windows

        

    """
    BACKGROUND FUNCTIONS
    """

    def set_background(self):
        # executes chosen desktop environment function to set wallpaper
        if 'APPDATA' in os.environ:
            return self.set_desktop_environment()
        else:
            return call(self.set_desktop_environment(), shell=True)

    def get_index_background(self):
        # retrieves index for next/previous functions
        self.set_bgconfig()
        self.indexedBG = self.bgconfig.get('Temp', 'Indexed Background')
        return self.indexedBG

    def get_record_background(self):
        # retrieves background for use in editing and clipboard
        self.set_bgconfig()
        self.appliedBG = self.bgconfig.get('Temp', 'Current Background')
        # if in windows, don't use xclip
        if 'APPDATA' not in os.environ:
            if depends['xclip'][1]:
                # if not called on commandline, don't use xclip
                if self._state['printbackground']:
                    call('echo -n {} | \
                        xclip -selection clipboard'.format(self.appliedBG), 
                        shell=True)
        return self.appliedBG

    def edit_background(self):
        # uses the GIMP to edit current background; change editor in config file
        self.get_record_background()
        editBG = self.config.get('Defaults','Default Background Editor')
        return call('{} \'{}\''.format(editBG,self.appliedBG), 
            shell=True)

    def edit_config(self):
        # uses $EDITOR to edit config file; change editor in config file
        self.set_config()
        edit_conf = self.config.get('Defaults','Default Config Editor')
        return call(
            '{} {}/.config/rwall/rwall.conf'.format(edit_conf,self.home), 
            shell=True)

    def announce(self):
        # stdout messages to user; silence by setting config "announce" to "no"
        self.currentDir = self.bgconfig.get('Temp', 'Current Directory')
        if self._state['filter']:
            aspectRatio = self._state['filter']
        else:
            aspectRatio = self.config.get(
            'Wallpaper Modes', 'Aspect Ratio Filter', fallback='none')
        print('aspect ratio filter: {}'.format(aspectRatio))
        print('{} wallpaper mode set to \'{}\'\
            '.format(self.desktopSession, self._state['mode']))
        print('{} wallpaper applied from:\
            \n{}'.format(self._state['image'], self.currentDir))

def main(argv):
    rwall = Rwall()
           
    # create config file if absent, read if present
    rwall.set_config()

    """
    COMMANDLINE OPTIONS
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        rWall randomizes your desktop background image in GNOME3,
        Cinnamon2, MATE, KDE 4 & 5, Xfce 4.10, Openbox, LXDE, and Windows 7-10; 
        if none of these environs are detected, then rWall attempts to use feh 
        to set your background.
        
        Choose various background image source directories, then edit the
        configuration file in ~/.config/rwall/rwall.conf accordingly. You can
        use "rwall.py -c" to edit this file, if you like. KDE usage
        requires setting the slideshow feature to ~/.config/rwall/kde/mon1.
        rWall requires feh for Openbox and unidentified desktop environs.  See
        your desktop environment's documentation for help setting up feh.
        """), epilog=textwrap.dedent("""\
        rWall, developed by rockhazard and licensed under GPL3.0. There are no 
        warranties expressed or implied.
        """))
    parser.add_argument('--version', help='print version info then exit', 
        version='rWall 3.5n "Akira", GPL3.0 (c) 2015, by rockhazard',
        action='version')
    parser.add_argument('-v', '--verbose',
        help='print detailed feedback on rWall functions' , action='store_true')
    parser.add_argument('-c', '--config',
        help='edit the configuration file, set initially to the user\'s \
        default text editor' , action='store_true')
    parser.add_argument('-a', '--filter', help=
        'filter images by one of these aspect ratios: sd480, hd1050, hd1080, \
        hd1050x2, hd1080x2, and auto', nargs=1, metavar=('ASPECT_RATIO'))
    parser.add_argument('-d', '--directory', help=
        'random background from DIRECTORY, e.g. "rwall.py -d ~/Pictures"',
        nargs=1)
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
        'apply IMAGE as wallpaper: "rwall.py -i /path/to/file"', nargs=1)
    parser.add_argument('-f', '--first', help=
        'first background from DIRECTORY, e.g. "rwall.py -f ~/Pictures"',
        nargs=1, metavar=('DIRECTORY'))
    parser.add_argument('-s', '--sync', help=
        'synchronize wallpaper with last execution of rWall.', 
        action='store_true')
    parser.add_argument('-l', '--loop', help=
        """create a background slideshow by looping the background in 
        DIRECTORY directory, every DELAY seconds, COUNT number of times, 
        e.g. "rwall.py -l ~/Pictures 5 10". DELAY must be greater than 0.\
        COUNT of 0 sets COUNT to number of images in given directory. SWITCH
        is either "random" or "next", and describes the order of the loop.
        DIRECTORY can also be 1 through 5, or directory1 through directory5.
        These are mapped to your preset directories in rwall.conf.""", 
        nargs=4, metavar=('DIRECTORY', 'DELAY','COUNT', 'SWITCH'))
    parser.add_argument('-b', '--printbackground',
        help=
        'prints filename of last-applied background to stdout and clipboard', 
        action='store_true')
    parser.add_argument('-e', '--editbackground',
        help='edit the current background, defaulted to the GIMP', 
        action='store_true')
    args = parser.parse_args()

    rwall.set_state('verbose', args.verbose)
    if args.filter:
        rwall.set_state('filter', args.filter[0])
    if args.sync:
        rwall.set_state('image', 'sync')
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
        rwall.set_state('printbackground', True)
        sys.exit(rwall.get_record_background())
    elif args.editbackground:
        sys.exit(rwall.edit_background())
    elif args.loop:
        rwall.set_state('slideshow', True)
        rwall.set_state('directory', args.loop[0])
        sys.exit(rwall.start_slideshow(args.loop[0], int(args.loop[1]),
            int(args.loop[2]), args.loop[3]))
    elif args.directory:
        if  Path(args.directory[0]).is_dir():
            rwall.set_state('directory', args.directory[0])
            rwall.change_directory('directory')
        else:
            sys.exit('Invalid directory! Check commandline argument.')
    elif args.first:
        rwall.set_state('image', 'first')
        if  Path(args.first[0]).is_dir():
            rwall.set_state('directory', args.first[0])
            rwall.change_directory('directory')
        else:
            sys.exit('Invalid directory! Check commandline argument.')
    elif args.config:
        sys.exit(rwall.edit_config())
    else:
        rwall.change_directory('default')

    # check imageList creation
    # print(rwall.get_imagesList())

    # apply background
    rwall.set_background()

    if args.verbose:
        # display wallpaper info to stdout
        rwall.set_state('verbose', True)
        rwall.announce()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
