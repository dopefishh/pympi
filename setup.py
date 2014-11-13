#!/usr/bin/env python

from distutils.core import setup

licence = '"THE BEER-WARE LICENSE" (Revision 42)',
version = '1.2'

setup(name='pympi-ling',
      version=version,
      description=
      'A python module for processing ELAN and Praat annotation files',
      author='Mart Lubbers',
      long_description="""\
Documentation as well as a detailed changelog can be found on:
http://dopefishh.github.io/pympi/

Pympi is a package that allows you to interact with Elan[1] files and
TextGrid[2] files. You can create, edit and convert both formats into
eachother. It also includes a gaps and overlaps algorithm to calculate the
gaps, overlaps and pauses between annotations conform Heldner and Edlund's
method[3].

The development version can be found on github[4].

How to cite::

    @misc{{pympi-ling,
        author={{Lubbers, Mart and Torreira, Francisco}},
        title={{pympi-ling:\
a Python module for processing ELAN and Praat annotation files.}},
        howpublished={{\url{{https://pypi.python.org/pypi/pympi-ling}}}},
        year={{2013-2014}},
        note={{Version {}}}
    }}

1. https://tla.mpi.nl/tools/tla-tools/elan/
2. http://www.fon.hum.uva.nl/praat/
3. Heldner, M., & Edlund, J. (2010). Pauses, gaps and overlaps in
   conversations. Journal of Phonetics, 38(4), 555-568.
   doi:10.1016/j.wocn.2010.08.002
4. https://github.com/dopefishh/pympi""".format(version),
      author_email='mart@martlubbers.net',
      url='https://github.com/dopefishh/pympi',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Text Processing :: Linguistic'],
      packages=['pympi']
      )
