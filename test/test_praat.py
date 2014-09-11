#!/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pympi import TextGrid


class PraatTest(unittest.TestCase):
    def setUp(self):
        self.tg = TextGrid()

    def test_add_tier(self):
        self.tg.add_tier('tier1')
        self.assertEqual(len(self.tg.tiers), 1)

        self.tg.add_tier('tier2')
        self.assertEqual(len(self.tg.tiers), 2)

        self.tg.add_tier('tier3')
        self.assertEqual(len(self.tg.tiers), 3)

        self.assertEqual(['tier1', 'tier2', 'tier3'],
                         [a.name for a in self.tg.tiers])
        self.assertEqual([1, 2, 3], [a.number for a in self.tg.tiers])

        self.tg.add_tier('tier4', number=2)
        self.assertEqual(len(self.tg.tiers), 4)
        self.assertEqual('tier4', self.tg.tiers[3].name)
        self.assertEqual([1, 3, 4, 2], [a.number for a in self.tg.tiers])

    def test_remove_tier(self):
        self.test_add_tier()
        self.tg.remove_tier(3)
        self.assertEqual(len(self.tg.tiers), 3)
        self.assertEqual([1, 3, 2], [a.number for a in self.tg.tiers])
        self.assertEqual(['tier1', 'tier3', 'tier4'],
                         [a.name for a in self.tg.tiers])

        self.tg.remove_tier('tier1')
        self.assertEqual(len(self.tg.tiers), 2)
        self.assertEqual(['tier3', 'tier4'], [a.name for a in self.tg.tiers])
        self.assertEqual([2, 1], [a.number for a in self.tg.tiers])

        self.tg.remove_tier(2)
        self.assertEqual(len(self.tg.tiers), 1)
        self.assertEqual([1], [a.number for a in self.tg.tiers])
        self.assertEqual(['tier4'], [a.name for a in self.tg.tiers])

        self.tg.remove_tier('tier4')
        self.assertTrue(not self.tg.tiers)

    def get_tier(self):
        tier1 = self.tg.add_tier('tier1')
        tier2 = self.tg.add_tier('tier2')
        tier3 = self.tg.add_tier('tier3', number=2)

        self.assertEqual(tier1, self.tg.get_tier(tier1.name))
        self.assertEqual(tier1, self.tg.get_tier(tier1.number))
        self.assertEqual(tier3, self.tg.get_tier(tier3.name))
        self.assertEqual(tier3, self.tg.get_tier(tier3.number))

        self.assertEqual(self.tg.tiers[1], self.tg.get_tier(tier2.name))
        self.assertEqual(self.tg.tiers[1], self.tg.get_tier(tier2.number))

if __name__ == '__main__':
    unittest.main()
