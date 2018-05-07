# README #

rWall Stable

### What is rWall? ###

rWall is a desktop wallpaper management application. It automatically detects the current user's environment then randomly selects and applies an image from a directory or list to the user's desktop background.  It supports GNOME3 (Gnome Shell, Unity, Cinnamon, Mate), KDE4 & 5, XFCE 4.10, LXDE, Openbox, OSX, and Windows 7+.

### Features ###

* Auto-detects most environments, such as Windows, OSX, and all common Linux desktop environments
* Randomly or alphabetically select images from one of five user-preset directories, in addition to the default directory.
* Specify an image directory on the commandline.
* Specify a list of images from a newline-separated text file.
* In addition to random selection, the user can apply a manually selected image.
* Walks through the list of images in the last used directory, turning your background into a flipbook/photo album.  This feature works with all the above features.
* A slideshow, using either random or alphabetical settings.
* Filter images by the aspect ratio of your screen (or choose from a number of manual alternatives), so you never have to see a background that doesn't fit again.
* Edit the current background with a quick command.
* Lightweight and highly scriptable, rWall is designed to be used with shortcuts and other programs, in addition toe being tiny and highly portable.

### How do I get set up? ###

* __GNOME and Xfce:__
These environments d not require any setup, but see _rwall.conf_ for customizations.

* __KDE:__
Setup via "Default Desktop Settings". Using the slideshow option, set "Change images every" to lowest, and select ~/.config/rwall/kde/mon1, then apply settings.  

* __Openbox:__
Install feh and apply feh's background settings in _autostart.sh_.

* __Windows 7+:__
In order to use the image filtering feature, Windows users must install Python 3 and get the Pillow wheel from:
http://www.lfd.uci.edu/~gohlke/pythonlibs/
Launch cmd.exe and run `pip install [name of Pillow file]` from Pillow's
directory.

#### Dependencies:

* Python 3.2+
* Python 3 Pillow and Tkinter
* feh (required for Openbox and other windows managers)
* xclip
* A supported environment (GNOME3, Cinnamon2x, KDE, Xfce, Openbox, Windows 7+, or MacOSX)

_Debian/Ubuntu/Linux Mint notes:_
`sudo apt-get install python3-pil python3-tk xclip feh`

#### Configuration:
On first run, rWall does _not_ set a wallpaper. Instead, a configuration folder is created as `[user]/.config/rwall`.  Rwall.conf, background.conf, and images.txt files are created there. Use rwall.conf to set your image directories and default config editor. Otherwise, rWall will use [user]/Pictures by default on its next execution.

#### Examples:
* To use the default image directory
`rwall.py`

* To specify a directory at the commandline
`rwall.py -d /path/to/directory`

* To specify the first of five predefined directoies
`rwall.py -1`

* To use a list of newline-separated image paths
`rwall.py -l /path/to/image/list`

* To specify a particular image
`rwall.py -i /path/to/image`


### Changelog ###

v3.6 "Blinky"

* optionally use newline-separated lists of image paths instead of directories
* '--reshuffle': random selection from current image's directory and below
* '--present': random selection from the present working directory, ignoring subdirectories

v3.5 "Akira"

* Config file
* Windows 7 function
* Addition of LXDE and KDE5 functions
* Improved Slideshow function
* Improved error handling and bugfixes
* Image filtering with Pillow

v3.0 "Scratchy"

* First Python3 version.
* Improved speed and image collection
* Enhanced features, like slideshow
* Next/Previous works in all environs now

v2.5 "Itchy"

* Final shell script version

### Contact ###

ike.davis.net@gmail.com
