#!/usr/bin/env python

from distutils.core import setup

licence = '"THE BEER-WARE LICENSE" (Revision 42)'
version = '1.49c'

setup(name='pympi-ling',
      version=version,
      description=
        'A python module for processing ELAN and Praat annotation files',
      author='Mart Lubbers',
      long_description=open('README.rst').read(),
      author_email='mart@martlubbers.net',
      url='https://github.com/dopefishh/pympi',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.4',
                   'Topic :: Text Processing :: Linguistic'],
      packages=['pympi'])
