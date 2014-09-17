#!/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pympi import Eaf


class Elan(unittest.TestCase):
    def setUp(self):
        self.eaf = Eaf()

if __name__ == '__main__':
    unittest.main()
