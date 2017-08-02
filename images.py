#!/usr/bin/env python3

import sys, os, random, imghdr, subprocess
from PIL import Image
from textwrap import dedent
import tkinter as tk
from fractions import Fraction
from pathlib import Path
from state import State


class ImageCollector(State):
    """image acquisition library employed by environment module"""

    def __init__(self):
        super(ImageCollector, self).__init__()
        # self.selector = ImageSelector()
        self.sourceImages = []
        self.selectedImage = None

    def change_directory(self, directory):
        """reads config or commandline for directories, then checks path
        validity"""
        if directory in self.dirFlags[0:5]:  # formatted Directory1 ... 5
            self.imageDirectory = self.get_config('Preset Image Directories',
                                                  directory.title())
        elif directory in self.dirFlags[5:]:  # formatted 1 ... 5
            self.imageDirectory = self.get_config('Preset Image Directories',
                                                  'Directory{}'.format(
                                                      directory))
        elif directory == 'directory':  # commandline-supplied directory
            self.imageDirectory = self._state['directory']
        elif directory == 'reshuffle':
            self.read_bgConfig()
            self.imageDirectory = \
                self.bgConfig.get('Temp', 'Current Directory')
        elif directory == 'default':
            self.imageDirectory = \
                self.get_config('Defaults', 'Default Directory')

        # check path validity, then return path for processing
        if Path(self.imageDirectory).is_dir():
            return self.imageDirectory
        else:
            sys.exit('Invalid directory!')

    def record_dir(self):
        """records background image path to background.conf"""
        self.read_bgConfig()
        self.bgConfig.set('Temp', 'Current Directory', self.imageDirectory)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgConfig.write(configfile)

    """
    IMAGE ACQUISITION FUNCTIONS
    """

    def get_source_images(self):
        """create list of images from given directory or images list file"""
        # list files recursively, or only in target directory
        extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        if self._state['list']:  # grab from user-provided list
            rawList = self.get_imagesList()
            for line in rawList:
                if line.endswith(extensions):
                    self.sourceImages.append(line)
        elif self._state['pwd']:  # do no search subdirectories
            for file in Path(self.imageDirectory).iterdir():
                candidate = str(file)
                if candidate.endswith(extensions):
                    self.sourceImages.append(candidate)
        else:  # default case, grab from subdirectories
            for root, dirnames, filenames in os.walk(self.imageDirectory):
                for file in filenames:
                    candidate = str(Path(root, file))
                    if candidate.endswith(extensions):
                        self.sourceImages.append(candidate)

        # check if images list is empty
        try:
            if self.sourceImages[0]:
                if self._state['verbose']:
                    if len(self.sourceImages) > 1:
                        print('Success: found {} valid images.'.format(
                            len(self.sourceImages)))
                    else:
                        print('Success: found 1 valid source image.')
        except IndexError:
            sys.exit('No valid images found in "{}"'.format(
                self.imageDirectory))

        if self.modules['Pillow']:
            self.image_filter()
        else:
            print('NOTICE: Pillow not installed. Image filtering disabled.')

        # prevent runaway append to images.txt during slideshow
        if not self._state['slideshow']:
            self.write_images_list_file()
        return self.sourceImages

    def get_screen_rez(self):
        if self.modules['Tkinter']:
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            return screen_width / screen_height
        elif self._state['filter'] == 'auto':
            print(dedent("""\
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
        elif aspect_ratio not in ['None', 'NONE', 'no', 'none', 'N', 'n', '']:
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
            if self._state['list']:
                listSource = self._state['list']
            else:
                listSource = '{}/images.txt'.format(self.configDirectory)
            with open(listSource) as images:
                # strip duplicate file locations to prevent next/previous
                # freeze
                imagesSet = set(images.read().splitlines())
                self.imagesList = sorted(list(imagesSet))
        except FileNotFoundError:
            sys.exit(dedent('No images file. Point rwall.py at a '
                            'directory containing images using -d.'))
        return self.imagesList

    def index_background(self):
        """allows next/previous to move passed corrupted images"""
        self.read_bgConfig()
        self.bgConfig.set('Temp', 'Indexed Background', self.selectedImage)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgConfig.write(configfile)

    def record_background(self):
        """records applied background"""
        self.read_bgConfig()
        bg_dir = os.path.dirname(self.selectedImage)
        self.bgConfig.set('Temp', 'Current Directory', bg_dir)
        self.bgConfig.set('Temp', 'Current Background', self.selectedImage)
        with open(str(self.bgFile), 'w') as configfile:
            self.bgConfig.write(configfile)

    def skip_image(self):
        selector = ImageSelector()
        self.index_background()
        print('rWall skipped:\n{}\nIt is a corrupted or missing file.\
              '.format(self.get_index_background()))
        if self._state['image_action'] == 'next':
            self.selectedImage = selector.get_pic('next')
        elif self._state['image_action'] == 'previous':
            self.selectedImage = selector.get_pic('previous')
        self.index_background()

    def select_image(self, action=None):
        """select, validate, and index image"""
        selector = ImageSelector()
        if action is None:
            self.selectedImage = selector.get_pic()
        else:
            self.selectedImage = selector.get_pic(action)

        # skip corrupted and missing files
        try:
            if imghdr.what(self.selectedImage) in self.fileTypes:
                self.index_background()
            else:
                self.skip_image()
        except FileNotFoundError:
            self.skip_image()

        # used with get_record_background() and edit_background()
        self.record_background()

        return self.selectedImage

    def get_index_background(self):
        """"retrieves index for next/previous functions"""
        self.read_bgConfig()
        self.indexedBG = self.bgConfig.get('Temp', 'Indexed Background')
        return self.indexedBG

    def get_record_background(self):
        """retrieves background for use in editing and clipboard"""
        self.read_bgConfig()
        applied_bg = self.bgConfig.get('Temp', 'Current Background')
        # if in windows, don't use xclip; if in MacOS us pbcopy
        if 'APPDATA' not in os.environ:
            if self.depends['xclip'][1]:
                subprocess.call('echo -n "{}" | \
                     xclip -selection clipboard'.format(applied_bg), shell=True)
        elif 'Apple_PubSub_Socket_Render' in os.environ:
            subprocess.call(
                'echo -n {} | pbcopy'.format(applied_bg), shell=True)
        return applied_bg

    def edit_background(self):
        self.read_config()
        applied_bg = self.get_record_background()
        edit_bg = self.config.get('Defaults', 'Default Background Editor')
        return subprocess.call('{} \'{}\''.format(edit_bg, applied_bg),
                               shell=True)


class ImageSelector(State):
    """"add image selection methods here then add corresponding string values to
     _state['image_action'] in get_pic method, arguments.py, and rwall.py"""

    def __init__(self):
        super(ImageSelector, self).__init__()
        self.images = ImageCollector()

    def select_random_image(self):
        """default image value"""
        self.images.get_source_images()
        random_image = random.choice(self.images.sourceImages)
        return random_image

    def select_first_image(self):
        """select first image in directory"""
        self.images.get_source_images()
        first_image = self.images.sourceImages[0]
        return first_image

    def select_cli_image(self):
        """select image from commandline"""
        self.images.imageDirectory = os.path.dirname(self._state['directory'])
        commandline_image = self._state['directory']
        try:  # validate
            if imghdr.what(commandline_image) in self.fileTypes:
                self.images.get_source_images()
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
        self.images.get_imagesList()
        self.images.get_index_background()
        # retrieve index of current background in image list
        image_index = self.images.imagesList.index(self.images.indexedBG)
        try:
            if self.images.indexedBG in self.images.imagesList:
                next_image = self.images.imagesList[image_index + 1]
        except IndexError:
            next_image = self.images.imagesList[0]
            print('Reached end of list: applying first image in list!')
        if self._state['verbose']:
            print('Background {} in a list of {} applied.'.format(
                image_index + 1, len(self.images.imagesList)))
        return next_image

    def select_previous_image(self):
        """step to previous image in imagesList"""
        # target of self._state when assigned 'previous'
        self.images.get_imagesList()
        self.images.get_index_background()
        # retrieve index of current background in image list
        image_index = self.images.imagesList.index(self.images.indexedBG)
        try:
            if self.images.indexedBG in self.images.imagesList:
                last_image = self.images.imagesList[image_index - 1]
        except IndexError:
            last_image = self.images.imagesList[-1]
            print('Reached beginning of list: applying last image in list!')
        if self._state['verbose']:
            print('Background {} in a list of {} applied.'.format(
                image_index - 1, len(self.images.imagesList)))
        return last_image

    def get_pic(self, action=None):
        """"choose method of getting image by action flag"""""
        _actions = ('random', 'first', 'commandline', 'next', 'previous')
        if not action:
            action = self.get_state('image_action')
        if action == 'random':
            return self.select_random_image()
        elif action == 'first':
            return self.select_first_image()
        elif action == 'commandline':
            return self.select_cli_image()
        elif action == 'next':
            return self.select_next_image()
        elif action == 'previous':
            return self.select_previous_image()
        elif action not in _actions:
            raise ValueError('get_pic passed unhandled value '
                             '\'{}\' of type {}'.format(action,
                                                        type(action)))
