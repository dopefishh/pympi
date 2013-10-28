pympi version 0.5
2013-09-19
=====

CONTENTS
========
./pympi/Praat.py
	A python class to read, write, edit and create praat's TextGrid files.
./pympi/Elan.py
	A python class to read, write, edit and create ELAN's eaf files.
./PhonetizerSpanish.py
	A class that converts spanish words to phone representation.
./test/*
	In the test folder there is a case example of the fto function(gaps and overlaps)

INSTALLATION PYMPI PACKAGE
==========================
Run:
# python setup.py -install 

Then you can just run for example:
>>> from pympi import Praat, Elan
>>> help(Elan.Eaf)
>>> help(Praat.TextGrid)

TODO
====
- clean timeslots function is too slow(disabled for now)
- add warnings when a function failed(right now only return code)

KNOWM BUGS
==========
Sometimes the media descriptor gets copied, still don't know how that happens.

