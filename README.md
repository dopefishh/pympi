# pympi version 0.99a, 2014-09-26

WARNING
=======
This version is already updated for Eaf file format 2.8. If you need the class
for the older 2.7 format please go to the branch ```eaf_file_2.7```.

NOTE ON VERSION
===============
From version 1 the api will not change anymore. This is currently on version
0.99 not yet the case. The TextGrid module is already finalized and will always
ensure compatibility with newer versions.

Contents
========
Full API documentation at: http://dopefishh.github.io/pympi/
- ./pympi/Praat.py 
    - A python class to read, write, edit and create praat's TextGrid files.
- ./pympi/Elan.py 
    - A python class to edit and create ELAN's eaf files.

Installation
============
##\*nix(linux, mac ...)
Run: `# python setup.py install`

If you don't have super user right you can install it in your home directory by
running: `$ python setup.py install --prefix=/home/user/bin`

and then add `export PYTHONPATH=~/home/user/bin/lib/python2.7/site-packages` to
your `~/.bashrc`(or equivalent in mac)

##Windows
Run command prompt(possibly with adminstrative privileges...) and type:
``cd C:\directory\where\you\extracted\the\zip
	python setup.py install``
