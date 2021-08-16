#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

licence = 'MIT Licence'
version = '1.70.2'

setup(name='pympi-ling',
      version=version,
      description=
        'A python module for processing ELAN and Praat annotation files',
      author='Mart Lubbers',
      long_description=r"""
pympi version 1.70.2
====================

Introduction
------------

Pympi is a package that allows you to interact with `Elan`_ files and
`TextGrid`_ files. You can create, edit and convert both formats into
each other. It includes besides all the basic functions also functions
for: - Calculating gaps and overlaps between speakers conform `Heldner
and Edlund’s method`_. (Could be used to calculate floor transfers) -
Shift annotations in both directions (Could be used when due to an error
all annotations are misaligned). - Import from CLAN’s chat files. -
Merge and or filter tiers (Could be used to combine hands in gesture
coding) - Move tiers between elan files. - Etc.

Requirements
------------

None

Optional requirements
---------------------

-  `lxml`_ is used for testing.

Documentation and downloads
---------------------------

Full api documentation of the current and old versions can be found on
`here`_.

Pypi repository location can be found
`here <https://pypi.python.org/pypi/pympi-ling/>`__.

Installation
------------

Automatic
~~~~~~~~~

-  From a shell run with administrator rights:

   .. code:: shell

       pip install pympi-ling

-  Or alternatively run with administrator rights:

   .. code:: shell

       easy_install pympi-ling

*NOTE: on windows the executable might not be in $PATH.*

Manual
~~~~~~

1. Download the latest version from `pypi`_
2. Untar the file
3. From that directory run with administrator rights

   .. code:: shell

       python setup.py install

How to cite
-----------

.. code:: tex

    @misc{pympi-1.70,
        author={Lubbers, Mart and Torreira, Francisco},
        title={pympi-ling: a Python module for processing ELANs EAF and Praats TextGrid annotation files.},
        howpublished={\url{https://pypi.python.org/pypi/pympi-ling}},
        year={2013-2021},
        note={Version 1.70}
    }

Authors
-------

Mart Lubbers (mart at martlubbers.net)
and 
Francisco Toreirra (francisco.torreira at mpi.nl)

and with contributions from:
sarpu, hadware, thomaskisler, mome, mimrock and xrotwang

.. _Elan: https://tla.mpi.nl/tools/tla-tools/elan/
.. _TextGrid: http://www.fon.hum.uva.nl/praat/
.. _Heldner and Edlund’s method: http://www.sciencedirect.com/science/article/pii/S0095447010000628
.. _lxml: http://lxml.de/
.. _here: http://dopefishh.github.io/pympi/
.. _pypi: http://dopefishh.github.io/pympi/""",
      author_email='mart@martlubbers.net',
      url='https://github.com/dopefishh/pympi',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'Programming Language :: Python :: 3.8',
                   'Programming Language :: Python :: 3.9',
                   'Topic :: Text Processing :: Linguistic'],
      packages=['pympi'],
      extras_require={
        'test': [
            'pytest>=5',
            'pytest-mock',
            'pytest-cov',
            'coverage>=4.2',
            'lxml',
        ],
      })
