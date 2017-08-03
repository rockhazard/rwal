#!/usr/bin/env python3
"""Module for describing and parsing commandline arguments"""
import argparse, sys
from pathlib import Path
from textwrap import dedent


def build_args(desktop):
    """method for defining and parsing commandline options"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog=str(Path(sys.argv[0]).name),
        description=dedent("""\
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
        """.format(desktop)), epilog=dedent("""\
        rWall is developed by rockhazard and licensed under GPL3.0. There are no
        warranties expressed or implied.
        """))
    parser.add_argument('--version', help='print version info then exit',
                        version='rWall 3.5q "Akira", GPL3.0 (c) 2016, by rockhazard',
                        action='version')
    parser.add_argument('-v', '--verbose',
                        help='print detailed feedback on rWall functions',
                        action='store_true')
    parser.add_argument('-c', '--config',
                        help='edit the configuration file, set initially to the user\'s \
        default text editor', action='store_true')
    parser.add_argument('-a', '--filter', help='filter images by one of these aspect ratios: sd480, hd1050, hd1080, \
        dci4k, hd1050x2, hd1080x2, dci4kx2, and auto. Note that the notation \
        is designed for easy identification by popular sample resolution, but \
        multiple resolutions may be filtered per aspect ratio (such as 4k UHD \
        and 1080 HD, since both are 16:9 aspect ratio).', nargs=1, metavar=(
        'ASPECT_RATIO'))
    parser.add_argument('-t', '--present',
                        help='ignore images in subdirectories',
                        action='store_true')
    parser.add_argument('-d', '--directory',
                        help='random background from DIRECTORY, e.g. "%(prog)s -d ~/Pictures"',
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
    parser.add_argument(
        '-i', '--image',
        help='apply IMAGE as wallpaper: "%(prog)s -i /path/to/file"', nargs=1)
    parser.add_argument('-f', '--first',
                        help='first background from DIRECTORY, e.g. "%(prog)s -f ~/Pictures"',
                        nargs=1, metavar='DIRECTORY')
    parser.add_argument('-l', '--list',
                        help='Use a file of newline-separated image paths, instead of a directory',
                        nargs=1, metavar='FILE')
    parser.add_argument('-s', '--slideshow', help="""create a background slideshow by looping the background in
        DIRECTORY directory or list, every DELAY seconds, COUNT number of times,
        e.g. "%(prog)s -s ~/Pictures 5 10 random". DELAY must be greater than 0.\
        COUNT of 0 sets COUNT to number of images in given directory. SWITCH
        is either "random" or "alpha", and describes the order of the loop.
        DIRECTORY can also be 1 through 5, or directory1 through directory5.
        These are mapped to your preset directories in rwall.conf.""",
                        nargs=4,
                        metavar=('DIRECTORY', 'DELAY', 'COUNT', 'SWITCH'))
    parser.add_argument('-b', '--printbackground',
                        help='prints filename of last-applied background to stdout and clipboard',
                        action='store_true')
    parser.add_argument('-e', '--editbackground',
                        help='edit the current background, defaulted to the GIMP',
                        action='store_true')
    args = parser.parse_args()
    return args
