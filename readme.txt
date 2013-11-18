pympi version 0.5
2013-11-18
==========

CONTENTS
========
./pympi/Praat.py
	A python class to read, write, edit and create praat's TextGrid files.
./pympi/Elan.py
	A python class to read, write, edit and create ELAN's eaf files.
./test/*
	In the test folder there is a case example of the fto function(gaps and overlaps)

INSTALLATION
============
Run:
# python setup.py install 

Then you can just run for example:
>>> from pympi import Praat, Elan
>>> help(Elan.Eaf)
>>> help(Praat.TextGrid)

KNOWN BUGS
==========

HISTORY
=======
2013-11-15
	- Rewritten the tofile function, the old function is a bit faster but less reliable. The old function can still be used by using tofileOLD()
