# pympi version 0.9d, 2014-07-09

Contents
========
Full API documentation at: http://dopefishh.github.io/pympi/
- ./pympi/Praat.py 
    - A python class to read, write, edit and create praat's TextGrid files.
- ./pympi/Elan.py 
    - A python class to edit and create ELAN's eaf files.
- ./pympi/EafIO.py 
    - A python class to write and read ELAN's eaf files.

Installation
============
##\*nix(linux, mac ...)
Run: `# python setup.py install`

If you don't have super user right you can install it in your home directory by
running: `$ python setup.py install --prefix=/home/user/bin`

and then add `export PYTHONPATH=~/home/user/bin/lib/python2.7/site-packages` to
your ~/.bashrc

##Windows
This package is not tested on windows, it should work on windows because the
package doesn't use os exclusive functions as far as we know...

TODO
====
- Make the class faster and more usable by using iterators for certain functions
- Maybe integration with [praatalign]{https://github.com/dopefishh/praatalign}
  so forced phonetic alignment is also added to the library.
