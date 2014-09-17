#!/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pympi import TextGrid
from pympi.Praat import TierNotFoundException, TierTypeException


class PraatTest(unittest.TestCase):
    def setUp(self):
        self.tg = TextGrid()

# Test all the Praat.TextGrid functions
    def test_add_tier(self):
        self.assertRaises(ValueError, self.tg.add_tier, 'a', number=-1)
        self.assertRaises(ValueError, self.tg.add_tier, 'a', number=10)

        self.tg.add_tier('tier1')
        self.assertEqual(len(self.tg.tiers), 1)
        self.assertEqual(self.tg.tiers[0].tier_type, 'IntervalTier')

        self.tg.add_tier('tier2', tier_type='TextTier')
        self.assertEqual(len(self.tg.tiers), 2)
        self.assertEqual(self.tg.tiers[1].tier_type, 'TextTier')

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
        self.assertRaises(TierNotFoundException, self.tg.remove_tier, -1)
        self.assertRaises(TierNotFoundException, self.tg.remove_tier, 'a')
        self.assertRaises(TierNotFoundException, self.tg.remove_tier, 10)

        self.tg.add_tier('tier1')
        self.tg.add_tier('tier2')
        self.tg.add_tier('tier3')
        self.tg.add_tier('tier4', number=2)

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

    def test_get_tier(self):
        self.assertRaises(TierNotFoundException, self.tg.get_tier, -1)
        self.assertRaises(TierNotFoundException, self.tg.get_tier, 'a')
        self.assertRaises(TierNotFoundException, self.tg.get_tier, 10)

        tier1 = self.tg.add_tier('tier1')
        tier2 = self.tg.add_tier('tier2')
        tier3 = self.tg.add_tier('tier3')

        self.assertEqual(tier1, self.tg.get_tier(tier1.name))
        self.assertEqual(tier1, self.tg.get_tier(tier1.number))
        self.assertEqual(tier3, self.tg.get_tier(tier3.name))
        self.assertEqual(tier3, self.tg.get_tier(tier3.number))

        self.assertEqual(self.tg.tiers[1], self.tg.get_tier(tier2.name))
        self.assertEqual(self.tg.tiers[1], self.tg.get_tier(tier2.number))

    def test_change_tier_name(self):
        self.assertRaises(TierNotFoundException,
                          self.tg.change_tier_name, -1, 'b')
        self.assertRaises(TierNotFoundException,
                          self.tg.change_tier_name, 'a', 'b')
        self.assertRaises(TierNotFoundException,
                          self.tg.change_tier_name, 10, 'b')

        self.tg.add_tier('tier1')
        tier2 = self.tg.add_tier('tier2')
        self.tg.add_tier('tier3')

        self.tg.change_tier_name('tier1', 'tier1a')
        self.assertEqual(['tier1a', 'tier2', 'tier3'],
                         [a.name for a in self.tg.tiers])
        self.tg.change_tier_name(tier2.number, 'tier2a')
        self.assertEqual(['tier1a', 'tier2a', 'tier3'],
                         [a.name for a in self.tg.tiers])
        self.tg.change_tier_name('tier1a', 'tier1')
        self.assertEqual(['tier1', 'tier2a', 'tier3'],
                         [a.name for a in self.tg.tiers])

    def test_get_tiers(self):
        self.tg.add_tier('tier1')
        self.tg.add_tier('tier2')
        self.tg.add_tier('tier3')
        self.assertEqual(self.tg.tiers,
                         list(self.tg.get_tiers()))

    def test_get_tier_name_num(self):
        self.tg.add_tier('tier1')
        self.tg.add_tier('tier2')
        self.tg.add_tier('tier3', number=2)
        self.assertEqual([(1, 'tier1'), (2, 'tier3'), (3, 'tier2')],
                         self.tg.get_tier_name_num())

    def test_to_file(self):
        pass

    def test_to_eaf(self):
        pass

# Test all the Praat.Tier functions
    def setup_tier(self):
        self.tier1 = self.tg.add_tier('tier1')
        self.tier2 = self.tg.add_tier('tier2', tier_type='TextTier')

    def test_add_point(self):
        self.setup_tier()
        self.assertRaises(TierTypeException, self.tier1.add_point, 5, 'a')
        self.tier2.add_point(5, 't')
        self.assertEquals([(5, 't')], self.tier2.intervals)
        self.assertRaises(Exception, self.tier2.add_point, 5, 'a')
        self.tier2.add_point(6, 'a')
        self.assertEquals([(5, 't'), (6, 'a')], self.tier2.intervals)
        self.tier2.add_point(5, 'a', False)

    def test_add_interval(self):
        self.setup_tier()
        self.assertRaises(TierTypeException,
                          self.tier2.add_interval, 5, 6, 'a')
        self.assertRaises(Exception, self.tier2.add_interval, 6, 5, 'a')

        self.tier1.add_interval(5, 6, 't')
        self.assertEquals([(5, 6, 't')], self.tier1.intervals)
        self.assertRaises(Exception, self.tier1.add_interval, 5.5, 6.5, 't')
        self.tier1.add_interval(6, 7, 'a')
        self.assertEquals([(5, 6, 't'), (6, 7, 'a')], self.tier1.intervals)

        self.tier1.add_interval(5.5, 6.5, 't', False)

    def test_remove_interval(self):
        self.setup_tier()
        self.assertRaises(TierTypeException, self.tier2.remove_interval, 5)
        self.tier1.add_interval(5, 6, 'a')
        self.tier1.add_interval(6, 7, 'b')
        self.tier1.add_interval(7, 8, 'c')
        self.tier1.remove_interval(5.5)
        self.assertEqual([(6, 7, 'b'), (7, 8, 'c')],
                         self.tier1.intervals)
        self.tier1.remove_interval(8)
        self.assertEqual([(6, 7, 'b')],
                         self.tier1.intervals)
        self.tier1.remove_interval(8)
        self.assertEqual([(6, 7, 'b')],
                         self.tier1.intervals)

    def test_remove_point(self):
        self.setup_tier()
        self.assertRaises(TierTypeException, self.tier1.remove_point, 5)
        self.tier2.add_point(5, 'a')
        self.tier2.add_point(6, 'b')
        self.tier2.add_point(7, 'c')
        self.tier2.remove_point(5)
        self.assertEqual([(6, 'b'), (7, 'c')],
                         self.tier2.intervals)
        self.tier2.remove_point(7)
        self.assertEqual([(6, 'b')],
                         self.tier2.intervals)
        self.tier2.remove_point(7)
        self.assertEqual([(6, 'b')],
                         self.tier2.intervals)

    def test_get_intervals(self):
        self.setup_tier()
        self.tier1.add_interval(5, 6, 'a')
        self.tier1.add_interval(7, 8, 'c')
        self.tier1.add_interval(6, 7, 'b')
        self.assertEqual([(5, 6, 'a'), (6, 7, 'b'), (7, 8, 'c')],
                         list(self.tier1.get_intervals()))
        self.tier2.add_point(5, 'a')
        self.tier2.add_point(7, 'c')
        self.tier2.add_point(6, 'b')
        self.assertEqual([(5, 'a'), (6, 'b'), (7, 'c')],
                         list(self.tier2.get_intervals()))

    def test_clear_intervals(self):
        self.setup_tier()
        self.tier1.add_interval(5, 6, 'a')
        self.tier1.add_interval(6, 7, 'b')
        self.tier1.add_interval(7, 8, 'c')
        self.tier1.clear_intervals()
        self.assertEqual([], self.tier1.intervals)

        self.tier2.add_point(5, 'a')
        self.tier2.add_point(6, 'b')
        self.tier2.add_point(7, 'c')
        self.tier2.clear_intervals()
        self.assertEqual([], self.tier2.intervals)

if __name__ == '__main__':
    unittest.main()
