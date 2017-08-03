# README #

## rWall ##

## What is this repository for? ##

rWall is a wallpaper management program for all major (and some minor) desktop environments

## Features ##

* Auto-detects most environments, such as Windows and all common Linux desktop environments
* Randomly selects images from one of five user-preset directories, in addition to the default directory.
* Specify an image directory on the commandline.
* In addition to random selection, the user can apply a manually selected image.
* Walks through the list of images in the last used directory, turning your background into a flipbook/photo album.  This feature works with all the above features.
* A slideshow, using either random or alphabetical settings.
* Filter images by aspect ratio, so you never have to see a background that doesn't fit again.
* Edit the current background with a quick command.
* Lightweight and highly scriptable, rWall is designed to be used with shortcuts and other programs, in addition toe being tiny and highly portable.

## How do I get set up? ##

rWall mostly requires setup in Windows, KDE, and Openbox. KDE support requires some trivial setup via "Default Desktop Settings". Using the slideshow option, set "Change images every" to lowest, and select ~/.config/rwall/kde/mon1, then apply settings.  Openbox requires the installation of feh and the application of feh's background settings in autostart.sh.
### >> Dependencies: 
rWall requires Python 3.2+, feh, and one of the supported desktop environments (GNOME3, Cinnamon2, KDE 4.x, Xfce 4.10, or Openbox).  Image filtering requires Python3 Pillow and Tkinter libraries be installed, but not doing so won't break the script.  In Linux, rWall's only hard dependency is feh, if you are in Openbox or an undetected Linux environment.
### >> Debian/Ubuntu/Linux Mint: 
`sudo apt-get install python3-pil python3-tk xclip feh`
### >> Windows 7+: 
Windows users must install Python 3 and get the Pillow wheel from: http://www.lfd.uci.edu/~gohlke/pythonlibs/
Launch cmd.exe and run `pip install [name of Pillow file]` from Pillow's
directory.
### >> Configuration: 
rWall autoconfigures itself for the supported environments, for the most part.  A settings folder is created as `[home]/.config/rwall`.  Rwall.conf, background.conf, and images.txt files are created there. Use rwall.conf to set your image directories.
### >> Deployment instructions: 
Just download and run the script.  Setup shortcuts for rwall.py, rwall.py -n, and rwall.py -p to turn your background into a rapid photo album experience.

## Changelog ##

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

Contact me at ike.davis.net@gmail.com

### [rockhazard home](https://rockhazard.github.io/index.html)
