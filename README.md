# pympi version 0.9, 2014-07-09

Contents
========
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

History
=======
- 2014-07-17
	- Controlled vocabularies (eaf file format 2.8) added and quickly tested.
- 2014-07-16
	- Added support for licences(eaf file format 2.8) and planned extended
	  controlled vocabulary support
- 2014-07-09
	- Changed the style to pep8 and thus some functions(read all) have changed
	  name
- 2014-03-24
	- Fixed a lot of TextGrid bugs and have written a better parser using more
	  regexp
- 2014-02-17
	- Started branching
	- Fixed a few bugs
- 2014-02-03
	- Fixed the praat tofile function so that it writes silence intervals (that
	  praat convention)
- 2014-01-27
	- Added documentation via pdoc in html and cleaned up some documentation in
	  EafIO.py
- 2013-12-02
	- IO is now in a different file, the old tofile is removed because the new
	  one is much better.
- 2013-11-15
	- Rewritten the tofile function, the old function is a bit faster but less
	  reliable. The old function can still be used by using tofileOLD().
