pympi version 0.6
2014-02-17


Contents
========
- ./pympi/Praat.py 
    - A python class to read, write, edit and create praat's TextGrid files.
- ./pympi/Elan.py 
	- A python class to edit and create ELAN's eaf files.
- ./pympi/EafIO.py 
	- A python class to write and read ELAN's eaf files.
- ./test/* 
	- In the test folder there is a case example of the fto function(gaps and overlaps)

Installation
============
Run:
`# python setup.py install`

Then you can just run for example:
```
>>> from pympi import Praat, Elan
>>> help(Elan.Eaf)
>>> help(Praat.TextGrid)
```

History
=======
- 2014-02-17
	- Started branching
	- Fixed a few bugs
- 2014-02-03
	- Fixed the praat tofile function so that it writes silence intervals (that praat convention)
- 2014-01-27
	- Added documentation via pdoc in html and cleaned up some documentation in EafIO.py
- 2013-12-02
	- IO is now in a different file, the old tofile is removed because the new one is much better.
- 2013-11-15
	- Rewritten the tofile function, the old function is a bit faster but less reliable. The old function can still be used by using tofileOLD().
