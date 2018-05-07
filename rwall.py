#!/usr/bin/env python3


"""
FILE: rwall.py

DISCLAIMER: Distributed under GPL3.0. There is NO warranty expressed or implied.

USAGE: rwall.py -h

DESCRIPTION: rWall randomizes backgrounds in GNOME 3 (GNOME Shell, Cinnamon,
Unity, MATE), KDE, Xfce, LXDE, Openbox, Mac OS X, and Windows 7+.

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

TODO: ---
OPTIONS: type rwall.py -h in a terminal
REQUIREMENTS: Python3.2+, python3-pil, python3-tk, feh, xclip, and a supported
desktop environment.
BUGS: OSX innocuous error returned by Applescript, 'Duplicate Options' bug that
      requires deletion of background.conf
NOTES: Feh is used for Openbox and any unknown environment. KDE users must click
Default Desktop Settings > Slideshow, apply "~/.config/rwall/kde-plasma", and
may have to logout/login.
AUTHOR: Ike Davis, ike.davis.net@gmail.com
ACKNOWLEDGMENTS: xfconf shell string: Peter Levi (please go check out Variety!
http://peterlevi.com/variety/)
COMPANY: ---
VERSION: rWall 3.5q "Akira", by rockhazard (c)2016
CREATED: 09/13/2015
REVISION: 07/27/2017
LICENSE: GPL 3.0, no warranty expressed or implied
"""
import sys
from pathlib import Path
from state import State
from config import Config
from images import ImageCollector
from environment import Environment
from arguments import build_args
from slideshow import SlideShow

__author__ = 'Ike Davis'
config = Config()
state = State()
rimage = ImageCollector()
renv = Environment()


def set_background():
    # acquire image based on user options then apply to background
    renv.set_state('pic', rimage.select_image())
    renv.set_background()


def main(argv):
    config.set_config()
    config.set_bgconfig()
    args = build_args(renv.get_state('desktopSession'))
    state.set_state('verbose', args.verbose)

    if args.present:
        state.set_state('pwd', args.present)
    if args.filter:
        state.set_state('filter', args.filter[0])
    if args.list:
        state.set_state('list', args.list[0])
    elif args.reshuffle:
        rimage.change_directory('reshuffle')
    elif args.directory1:
        rimage.change_directory('directory1')
    elif args.directory2:
        rimage.change_directory('directory2')
    elif args.directory3:
        rimage.change_directory('directory3')
    elif args.directory4:
        rimage.change_directory('directory4')
    elif args.directory5:
        rimage.change_directory('directory5')
    elif args.next:
        state.set_state('image_action', 'next')
    elif args.previous:
        state.set_state('image_action', 'previous')
    elif args.image:
        state.set_state('image_action', 'commandline')
        state.set_state('directory', args.image[0])
    elif args.printbackground:
        sys.exit(rimage.get_record_background())
    elif args.editbackground:
        sys.exit(rimage.edit_background())
    elif args.slideshow:
        slide = SlideShow()
        state.set_state('slideshow', True)
        state.set_state('directory', args.slideshow[0])
        sys.exit(slide.start_slideshow(args.slideshow[0],
                                       args.slideshow[1],
                                       args.slideshow[2],
                                       args.slideshow[3]))
    elif args.directory:
        state.set_state('directory', args.directory[0])
        rimage.change_directory('directory')
    elif args.first:
        state.set_state('image_action', 'first')
        if Path(args.first[0]).is_dir():
            state.set_state('directory', args.first[0])
            rimage.change_directory('directory')
        else:
            sys.exit('Invalid directory! Check commandline argument.')
    elif args.config:
        sys.exit(config.edit_config())
    else:
        rimage.change_directory('default')

    set_background()

    if args.verbose:
        state.announce()


if __name__ == '__main__':
    # profiling test
    # import cProfile
    # cProfile.run("sys.exit(main(sys.argv[1:]))")
    sys.exit(main(sys.argv[1:]))
