#!/usr/bin/env python3
"""A module that turns the user background into a slideshow."""

import sys, os, time, subprocess
from state import State
from images import ImageCollector
from environment import Environment
from pathlib import Path


class SlideShow(State):
    def __init__(self):
        super(SlideShow, self).__init__()
        self.images = ImageCollector()
        self.env = Environment()

    def start_slideshow(self, directory, delay, count, switch):
        listExt = ('.txt', '.list')

        def slides_setup():
            if not self.get_state('list'):
                self.images.change_directory(directory)
            self.images.get_source_images()
            self.images.write_images_list_file()

        if switch == 'alpha':
            switch = 'next'

        delay = int(delay)
        count = int(count)
        # check directory to match forms '1' through '5' and
        # 'directory1' through 'directory5', or path
        print(self._state['directory'])
        if Path(self._state['directory']).is_dir():
            directory = 'directory'
        # setup list-based slideshow
        elif Path(self._state['directory']).name.endswith(listExt):
            self.set_state('list', self.get_state('directory'))
            slides_setup()
        elif directory in self.dirFlags:
            directory = self._state['directory']
        else:
            sys.exit('Invalid directory or image path list!')
        if delay < 1:
            sys.exit('DELAY must be greater than 0.')
        if switch not in ('next', 'random'):
            sys.exit('Error: SWITCH must be either "random" or "next"')

        # setup images for directory-based slideshow
        if not Path(self._state['directory']).name.endswith('txt'):
            slides_setup()
        # required for 'next' switch
        self.images.selectedImage = self.images.sourceImages[0]
        self.images.index_background()

        try:
            # count=0 sets count to number of files in imagesList
            # starts slideshow from first images in list
            if count <= 0:
                print('COUNT set to number of images in directory')
                self.images.get_imagesList()
                count = len(self.images.imagesList)
                self.set_state('pic', self.images.select_image('first'))
                self.env.set_background()
                self.images.index_background()
            while count > 0:
                self.set_state('pic', self.images.select_image(switch))
                self.env.set_background()
                time.sleep(delay)
                count -= 1
                self.clear_screen()

                if self._state['verbose']:
                    # current_dir not working with ImageSelector
                    current_dir = self.bgConfig.get(
                        'Temp', 'Current Directory')
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

    def clear_screen(self, com='clear'):
        if 'APPDATA' not in os.environ:
            subprocess.call(com, shell=True)
        else:
            subprocess.call('cls', shell=True)
