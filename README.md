# README #

rWall Stable

### What is this repository for? ###

rWall is a desktop wallpaper management application. It automatically detects the current user's environment then optionally selects a random ordered image from a directory or list.  The script applies that image as a background. It supports GNOME3 (Gnome Shell, Unity, Cinnamon, Mate), KDE4 & 5, XFCE 4.10, LXDE, Openbox, OSX, and Windows 7+.

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

rWall mostly requires setup in Windows, KDE, and Openbox. KDE support requires some trivial setup via "Default Desktop Settings". Using the slideshow option, set "Change images every" to lowest, and select ~/.config/rwall/kde/mon1, then apply settings.  Openbox requires the installation of feh and the application of feh's background settings in autostart.sh.

* Dependencies:
rWall requires Python 3.2+, feh, and one of the supported desktop environments (GNOME3, Cinnamon2, KDE 4.x, Xfce 4.10, or Openbox).  Image filtering requires Python3 Pillow and Tkinter libraries be installed, but not doing so won't break the script.  In Linux, rWall's only hard dependency is feh, if you are in Openbox or an undetected Linux environment.

* Debian/Ubuntu/Linux Mint:
`sudo apt-get install python3-pil python3-tk xclip feh`

* Windows 7+:
In order to use the image filtering feature, Windows users must install Python 3 and get the Pillow wheel from:
http://www.lfd.uci.edu/~gohlke/pythonlibs/
Launch cmd.exe and run `pip install [name of Pillow file]` from Pillow's
directory.

* Configuration:
rWall autoconfigures itself for the supported environments, for the most part.  A settings folder is created as `[user_home]/.config/rwall`.  Rwall.conf, background.conf, and images.txt files are created there. Use rwall.conf to set your image directories and default config editor.

* Deployment instructions:
Just download and run the script.  Setup shortcuts for rwall.py, rwall.py -n, and rwall.py -p to turn your background into a rapid photo album experience.

### Changelog ###

v2.5 "Itchy"

* Last shell script version

v3.0 "Scratchy"

* First Python3 version.
* Improved speed and image collection
* Enhanced features, like slideshow
* Next/Previous works in all environs now

v3.5 "Akira"

* Config file
* Windows 7 function
* Addition of LXDE and KDE5 functions
* Improved Slideshow function
* Improved error handling and bugfixes
* Image filtering with Pillow

v3.6 "Blinky"

* Added list, reshuffle, and present (working directory) features

### Contribution guidelines ###

Contact me at rockhazardz@gmail.com
