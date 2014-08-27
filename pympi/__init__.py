# Import the packages
from Praat import TextGrid
from Elan import Eaf

# Prevent EafIO to be loaded automatically with import *
__all__ = ['Praat', 'Elan']
