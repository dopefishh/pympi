pympi version 0.5
2013-09-19
=====

CONTENTS
========
Praat.py
	A python class to read, write, edit and create praat's TextGrid files.
Elan.py
	A python class to read, write, edit and create ELAN's eaf files.
PhonetizerSpanish.py
	A class that converts spanish words to phone representation.

In the test folder there is a case example of the fto function(gaps and overlaps)

INSTALLATION
============
Run:
# python setup.py -install 

Then you can just run for example:
>>> from pympi import Praat, Elan
>>> help(Elan.Eaf)
>>> help(Praat.TextGrid)

The phonetizer can be used by putting it in the same folder as your script.

TODO
====
- Add time series to Elan files
