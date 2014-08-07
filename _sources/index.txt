.. pympi documentation master file, created by
   sphinx-quickstart on Mon Aug  4 11:37:37 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pympi's documentation!
=================================

API Documentation:

.. toctree::
   :maxdepth: 2

   Praat
   Elan
   EafIO
   
Installation
============
Run: ``# python setup.py install``

If you don't have right on your system to install in the default package
location for python you can specify your own package location:
``$ python setup.py install --prefix=/home/user/bin``

.. note:: You have to add 
          ``export PYTHONPATH=~/home/user/bin/lib/python2.7/site-packages``
          to your ``~/.bashrc``

Changelog
=========
+------------+---------+------------------------------------------------------+
| Date       | Version | Changelog                                            |
+============+=========+======================================================+
| 2014-08-06 | 0.91d   | New documentation format(sphinx) and github pages.   |
+------------+---------+------------------------------------------------------+
| 2014-07-17 | 0.91    | Controlled vocabularies (eaf file format 2.8) added  |
|            |         | and quickly tested.                                  |
+------------+---------+------------------------------------------------------+
| 2014-07-16 | 0.9     | Added support for licences(eaf file format 2.8) and  |
|            |         | planned extended controlled vocabulary support.      |
+------------+---------+------------------------------------------------------+
| 2014-07-09 | 0.7     | Changed the style to pep8 and thus some functions    |
|            |         | (read all) have changed name.                        |
+------------+---------+------------------------------------------------------+
| 2014-03-24 |         | Fixed a lot of TextGrid bugs and have written a      |
|            |         | better parser using more regexp.                     |
+------------+---------+------------------------------------------------------+
| 2014-02-17 |         | Started branching and fixed a few bugs.              |
+------------+---------+------------------------------------------------------+
| 2014-02-03 |         | Fixed the praat tofile function so that it writes    |
|            |         | silence intervals (that praat convention).           |
+------------+---------+------------------------------------------------------+
| 2014-01-27 |         | Added documentation via pdoc in html and cleaned up  |
|            |         | some documentation in EafIO.py.                      |
+------------+---------+------------------------------------------------------+
| 2013-12-02 |         | IO is now in a different file, the old tofile is     |
|            |         | removed because the new one is much better.          |
+------------+---------+------------------------------------------------------+
| 2013-11-15 |         | Rewritten the tofile function, the old function is a |
|            |         | bit faster but less reliable. The old function can   |
|            |         | still be used by using tofileOLD().                  |
+------------+---------+------------------------------------------------------+

Author
======
Mart Lubbers(``mart at martlubbers.net``)
