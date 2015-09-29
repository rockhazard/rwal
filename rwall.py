#!/usr/bin/env python3


"""
FILE: rwall.py

DISCLAIMER: Distributed under GPL3.0. There is NO warranty expressed or implied.

USAGE: rwall.py [-h] [-v] [-c] [-i] [-d DIRECTORY] [-1] [-2] [-3] [-4] [-5] [-n] 
                [-p] [-l DIRECTORY DELAY COUNT next|random] [-b] [-e]

DESCRIPTION: rWall randomizes backgrounds in GNOME 3, Cinnamon 2, KDE 4-5, Mate,
Xfce 4.10, LXDE, Openbox (using feh), and Windows 7 - 10. rWall was developed 
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
BUGS: rwall.py --syncall breaks --next. Workaround: "rwall.py -r ; rwall.py -s"
NOTES: Users should run the script once without options, then modify 
~/.config/rwall/rwall.conf as desired; KDE requires setting desktop slideshow to 
"~/.config/rwall/kde/mon1". Openbox require feh to be installed and setup. 
Feh is also used as fallback for unrecognized environments.
AUTHOR: rockhazard, rockhazardz@gmail.com
ACKNOLEDGMENTS: xfconf shell string: Peter Levi (please go check out Variety!
http://peterlevi.com/variety/)
COMPANY: ---
VERSION: rWall 3.5m "Akira", by rockhazard (c)2015
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
depends = dict( xclip=( '/usr/bin/xclip', True ), feh=( '/usr/bin/feh', True ) )
modules = dict( Pillow=None )

try: # check for 3rd party modules
    from PIL import Image
    modules['Pillow'] = True
except ImportError:
    modules['Pillow'] = False

# check for Linux dependencies
if 'APPDATA' not in os.environ:
    for package, path in depends.items():
        if not Path(path[0]).is_file():
            path[1] = False
            print('Please install:', package)

# import search path appended for configuration and module files
# sys.path.append('{}/.config/rwall/'.format(os.expanduser('~')))

class Rwall:
    def __init__(self, switch='random'):  # classwide perams
        # User's home directory
        self.home = os.path.expanduser('~')

        # recognized desktop environments
        self.deList = (
            'cinnamon', 'gnome', 'ubuntu', 'unity', 'mate', 'plasma', 
            'kde-plasma', 'openbox', 'xfce', 'lxde')

        # directory flags, used for argument test in start_slideshow()
        self.dirFlags = ('directory1', 'directory2', 'directory3', 'directory4',
            'directory5', '1', '2', '3', '4', '5')

        # desktop environment detection variable
        self.desktopSession = os.environ.get('DESKTOP_SESSION')

        # wallpaper mode
        self.wallpaperMode = 'scaled'

        # display if modes settings wrong or missing
        self.wallpaperModeError = (
            'WARNING: configuration fault detected\n' + 
            'check modes in rwall.conf\n' + 'fallback mode applied')
        
        # valid image types; to expand, use imghdr.what() values
        self.fileTypes = ('jpeg', 'png')

        # configuration files
        self.configFile = Path(self.home, '.config/rwall/rwall.conf')
        self.bgFile = Path(self.home, '.config/rwall/background.conf')

        # image acquisition switch determines method of image selection: 
        # 'random', 'next', 'previous', 'commandline', 'first'
        self._state = switch

        # list of images to be randomized and/or sorted
        self.sourceImages = []

    """
    CONFIGURATION FUNCTIONS
    """

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
            self.config.set('Defaults','Announce', 'no')
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
            # sd480, hd1050, hd1080, hd1050x2, and hd1080x2
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
            self.announceBool = self.config.getboolean('Defaults','Announce')


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
            self.imageDirectory = str(sys.argv[2])
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
        if Path(self.imageDirectory).is_dir:
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
        else:
            sys.exit('Build image list failed: check directory.')

        # if aspect ratio filter is set, filter images
        self.image_filter(self.sourceImages)

        # prevent runaway append to images.txt during slideshow
        slideshowArgs = ['-l','--l','--loop']
        if not any(arg in sys.argv for arg in slideshowArgs):
            self.write_imagesListFile()
        return self.sourceImages

    def image_filter(self, *args):
        # allows filtering of images by aspect ration, as set in config file
        if modules['Pillow']:
            # container for final filtered list
            self.filteredImages = []
            # valid aspect ratios
            ratios = dict( sd480 = 4/3, hd1050 = 8/5, hd1080 = 16/9, 
                hd1050x2 = 16/5, hd1080x2 = 32/9 )
            # get config file setting
            aspectRatio = self.config.get(
            'Wallpaper Modes', 'Aspect Ratio Filter', fallback='none')
            if aspectRatio in ratios:
                if self.announceBool:
                    print(
                        'Selecting images with a', 
                        aspectRatio, 'aspect ratio.')
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
                'Invalid value. Check Aspect Ratio Filter in rwall.conf')
        else:
            print(
            'NOTICE: Image filtering disabled pending installation of Pillow.')


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
        slideshowArgs = ['-l','--l','--loop']
        if not any(i in sys.argv for i in slideshowArgs):
            self.get_source_images()
        self.randomImage = random.choice(self.sourceImages)
        return self.randomImage

    def select_firstImage(self):
        # target of self._state variable when assigned 'first'
        # does not trigger images.txt write if used in slideshow
        slideshowArgs = ['-l','--l','--loop']
        if not any(i in sys.argv for i in slideshowArgs):
            self.get_source_images()
        self.firstImage = self.sourceImages[0]
        return self.firstImage

    def select_cli_image(self, image=False):
        # target of self._state variable when assigned 'commandline'
        if image == False:
            image = str(sys.argv[2])
        try: # validate image, build list based on it, then return image var
            if imghdr.what(image) in self.fileTypes:
                self.imageDirectory = os.path.dirname(image)
                self.get_source_images(self.imageDirectory)
                self.commandlineImage = image
                return self.commandlineImage
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
        self.get_indexed_background()  # returns self.indexedBG
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
        self.get_indexed_background()  # returns self.indexedBG
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
        # can be used to automate the script:
        # "rwall.py -l <dir>|<dirFlag> n 0 next" is automated 'next'
        if Path(sys.argv[2]).is_dir():
            directory = 'directory'
        elif directory in self.dirFlags:
            directory = str(sys.argv[2])
        else:
            sys.exit('Invalid argument!')
        self.change_directory(directory)
        self.set_bgconfig()
        self.get_source_images()
        self.write_imagesListFile()
        if delay < 1:
            sys.exit('DELAY must be greater than 0.')
        try:
            # count=0 sets count to number of files in imagesList
            # starts slideshow from first images in list
            if count == 0:
                self.get_imagesList()
                count = len(self.imagesList)
                self.set_state('first')
                self.set_background()
            while count > 0:
                currentDir = self.bgconfig.get('Temp', 'Current Directory')
                self.set_state(switch)
                self.set_background()
                time.sleep(delay)
                count -= 1
                timeRemaining = round(float((count*delay)/60),2)
                call('clear', shell=True)
                print('{0} wallpaper changes remain over {1} minutes:\n{2}\
                    '.format(count,timeRemaining,currentDir),
                    '\nPress Ctrl-C to cancel.')
            else:
                call('reset', shell=True)
                print('rWall slideshow has ended.')           
        except KeyboardInterrupt:
            call('reset', shell=True)
            sys.exit('Slideshow terminated by user...')

    def set_state(self, switch):
        # accessor method for setting image acquisition option
        # 'random', 'next', 'previous', 'first', and 'commandline'
        self._state = switch

    def get_state(self):
        # accessor method for retrieving image acquisition option
        return self._state

    def indexed_background(self):
        # records current background image path and acts as position key for
        # next/previous functions
        self.set_bgconfig()
        # self.bgDir = os.path.dirname(self.selectedImage)
        self.bgconfig.set('Temp', 'Indexed Background', self.selectedImage)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgconfig.write(configfile)

    def current_background(self):
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
        if self._state == 'random':
            self.selectedImage = self.select_randomImage()
        elif self._state == 'first':
            self.selectedImage = self.select_firstImage()
        elif self._state == 'next':
            self.selectedImage = self.select_next_image()
        elif self._state == 'previous':
            self.selectedImage = self.select_previous_image()
        elif self._state == 'commandline':
            self.selectedImage = self.select_cli_image()
        elif self._state == 'sync':
            self.selectedImage = self.sync_background()

        # test for valid filetypes, then index background
        if imghdr.what(self.selectedImage) in self.fileTypes:
            # index for internal use: enables next/previous functions
            # even on fault; separate from finally applied background
            self.indexed_background()
        else:
            # index fault, and skip to next or last valid filename
            self.indexed_background()
            # if self.config.getboolean('Defaults','Announce'):
            print('rWall skipped:\n{}\nIt is a corrupted file.\
                '.format(self.get_indexed_background()))
            if self._state == 'next':
                self.selectedImage = self.select_next_image()
            elif self._state == 'previous':
                self.selectedImage = self.select_previous_image()
            self.indexed_background()

        # record newest image that has passed checks and filters
        # for use with get_current_background() and edit_background()
        self.current_background()

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
            self.wallpaperMode = imageConfig
        else:
            # self.wallpaperMode = 'scaled'
            print(self.wallpaperModeError)

        image = self.select_image()
        self.gnome3 = \
            'gsettings set org.gnome.desktop.background picture-options\
            {};'.format(self.wallpaperMode) + \
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
            self.wallpaperMode = imageConfig
        else:
            # self.wallpaperMode = 'scaled'
            print(self.wallpaperModeError)

        image = self.select_image()
        self.mate = \
            'gsettings set org.mate.background picture-options {0}; \
            gsettings set org.mate.background picture-filename \
            \'{1}\''.format(self.wallpaperMode,image)
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
            self.wallpaperMode = imageConfig
        else:
            # self.wallpaperMode = '4'
            print(self.wallpaperModeError)

        image = self.select_image()
        self.xfce = \
            """for i in $(xfconf-query -c xfce4-desktop -p /backdrop -l|egrep \
                -e "screen.*/monitor.*image-path$" \
                -e "screen.*/monitor.*/last-image$"); do
                    xfconf-query -c xfce4-desktop -p $i -n \
                    -t string -s "" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{0}" 2> /dev/null
                    xfconf-query -c xfce4-desktop -p $i -s "{1}" 2> /dev/null
            done""".format(self.wallpaperMode,image)
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
            self.wallpaperMode = imageConfig
        else:
            # self.wallpaperMode = 'scaled'
            print(self.wallpaperModeError)

        image = self.select_image()
        self.lxde = 'pcmanfm --set-wallpaper \'{}\' \
        --wallpaper-mode={}'.format(image,self.wallpaperMode)
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
                self.wallpaperMode = imageConfig
            else:
                # self.wallpaperMode = '--bg-max'
                print(self.wallpaperModeError)

            image = self.select_image()
            self.openbox = 'feh {} \'{}\''.format(self.wallpaperMode,image)
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

    def set_background(self, setall=False):
        # executes chosen desktop environment function to set wallpaper
        if 'APPDATA' in os.environ:
            return self.set_desktop_environment()
        elif setall:
            # sets all environs at once: doesn't work with LXDE, or Windows
            deSets = dict( Openbox=self.set_openbox(), Xfce=self.set_xfce(), 
                Mate=self.set_mate(), GNOME=self.set_gnome3(), 
                KDE=self.set_kde() )
            for DE, command in deSets.items():
                try:
                    call(command, shell=True)
                    print('Background set for', DE)
                except:
                    continue
            sys.exit('All available environs were set.')
        else:
            return call(self.set_desktop_environment(), shell=True)

    def get_indexed_background(self):
        # retrieves index for next/previous functions
        self.set_bgconfig()
        self.indexedBG = \
        self.bgconfig.get('Temp', 'Indexed Background')
        return self.indexedBG

    def get_current_background(self):
        # retrieves background for use in editing and clipboard
        self.set_bgconfig()
        self.appliedBG = \
        self.bgconfig.get('Temp', 'Current Background')
        # if in windows, don't use xclip
        if 'APPDATA' not in os.environ:
            if depends['xclip'][1]:
                # if not called on commandline, don't use xclip
                getBgArgs = ['-b','--b','--printbackground']
                if any(i in sys.argv for i in getBgArgs):
                    call('echo -n {} | \
                        xclip -selection clipboard'.format(self.appliedBG), 
                        shell=True)
        return self.appliedBG

    def sync_background(self):
        # selectively apply background from previous session to current DE
        self.set_bgconfig()
        image = self.bgconfig.get('Temp', 'Current Background')
        return self.select_cli_image(image)

    def edit_background(self):
        # uses the GIMP to edit current background; change editor in config file
        self.get_current_background()
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
        self.set_config()
        self.currentDir = self.bgconfig.get('Temp', 'Current Directory')
        self.get_state()
        aspectRatio = self.config.get(
            'Wallpaper Modes', 'Aspect Ratio Filter', fallback='none')
        if self.config.getboolean('Defaults','Announce'):
            print('aspect ratio filter: {}'.format(aspectRatio))
            if self.desktopSession in self.deList:
                announceDE = self.desktopSession
            elif 'APPDATA' in os.environ:
                announceDE = 'Windows'
            else:
                announceDE = 'feh'
            print('{} wallpaper mode set to \'{}\'\
                '.format(announceDE,self.wallpaperMode))
            print('{} wallpaper applied from:\
                \n{}'.format(self._state,self.currentDir))
            print('Don\'t want to see this message? ' +
                'Set "announce" to "no" in rwall.conf.')

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
        Cinnamon2, MATE, KDE 4 - 5, Xfce 4.10, Openbox, LXDE, and Windows7 - 10; 
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
    parser.add_argument('-v', '--version', 
        help='print rWall\'s version and exit', action='store_true')
    parser.add_argument('-c', '--config',
        help='edit the configuration file, set initially to the user\'s \
        default text editor' , action='store_true')
    parser.add_argument('-d', '--directory', help=
        'random background from DIRECTORY, e.g. "rwall.py -d ~/Pictures"',
        nargs=1, required=False)
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
        'apply IMAGE as wallpaper: "rwall.py -i /path/to/file"',
        nargs=1, required=False)
    parser.add_argument('-f', '--first', help=
        'first background from DIRECTORY, e.g. "rwall.py -f ~/Pictures"',
        nargs=1, metavar=('DIRECTORY'), required=False)
    parser.add_argument('-l', '--loop', help=
        """create a background slideshow by looping the background in 
        DIRECTORY directory, every DELAY seconds, COUNT number of times, 
        e.g. "rwall.py -l ~/Pictures 5 10". DELAY must be greater than 0.\
        COUNT of 0 sets COUNT to number of images in given directory. SWITCH
        is either "random" or "next", and describes the order of the loop.""", 
        nargs=4, metavar=('DIRECTORY', 'DELAY','COUNT', 'SWITCH'))
    parser.add_argument('-b', '--printbackground',
        help=
        'prints filename of last-applied background to stdout and clipboard', 
        action='store_true')
    parser.add_argument('-s', '--syncdesktop',
        help=
        'applies background from the last desktop environment in which rWall \
        was executed.  Used to selectively synchronize your desktop themes. \
        Doesn\'t work with Windows', action='store_true')
    parser.add_argument('-r', '--syncall',
        help=
        'sets all available desktop environments to the last image applied by \
        rWall.  Synchronizes all compatible desktops at once. \
        Doesn\'t work with LXDE or Windows.', action='store_true')
    parser.add_argument('-e', '--editbackground',
        help='edit the current background, defautled to the GIMP', 
        action='store_true')
    args = parser.parse_args()

    if args.version:
        sys.exit('rWall 3.5m "Akira", GPL3.0 (c) 2015, by rockhazard')
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
        rwall.set_state('next')
    elif args.previous:
        rwall.set_state('previous')
    elif args.image:
        rwall.set_state('commandline')
    elif args.printbackground:
        sys.exit(rwall.get_current_background())
    elif args.syncdesktop:
        rwall.set_state('sync')
        print('Background synced with previous session.')
    elif args.syncall:
        rwall.set_state('sync')
        rwall.set_background(True)
    elif args.editbackground:
        sys.exit(rwall.edit_background())
    elif args.loop:
        sys.exit(rwall.start_slideshow(str(sys.argv[2]), int(sys.argv[3]),
            int(sys.argv[4]), str(sys.argv[5])))
    elif args.directory:
        if  Path(sys.argv[2]).is_dir():
            rwall.change_directory('directory')
        else:
            sys.exit('Invalid directory! Check commandline argument.')
    elif args.first:
        rwall.set_state('first')
        if  Path(sys.argv[2]).is_dir():
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

    # display wallpaper info to stdout, if "announce" in config set to "yes"
    rwall.announce()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
