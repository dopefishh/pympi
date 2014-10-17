#!/bin/env python
# -*- coding: utf-8 -*-

import unittest
import io
from pympi import TextGrid
from pympi.Praat import TierNotFoundException, TierTypeException


class PraatTest(unittest.TestCase):
    def setUp(self):
        self.tg = TextGrid(xmax=20)

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
        for codec in ['ascii', 'utf-8', 'utf-16', 'latin_1', 'mac_roman']:
            self.tg = TextGrid(codec=codec, xmax=20)
            tier1 = self.tg.add_tier('tier')
            tier1.add_interval(1, 2, 'i1'.encode(codec))
            tier1.add_interval(2, 3, 'i2'.encode(codec))
            tier1.add_interval(4, 5, 'i3'.encode(codec))

            if codec != 'ascii':
                tier4 = self.tg.add_tier('tier')
                tier4.add_interval(1, 2, 'i1ü'.decode('utf-8').encode(codec))
                tier4.add_interval(2.0, 3, 'i2'.encode(codec))
                tier4.add_interval(4, 5.0, 'i3'.encode(codec))
                tier2 = self.tg.add_tier('tier2', tier_type='TextTier')
                tier2.add_point(1, 'p1ü'.decode('utf-8').encode(codec))
                tier2.add_point(2, 'p1'.encode(codec))
                tier2.add_point(3, 'p1'.encode(codec))

            tier3 = self.tg.add_tier('tier3', tier_type='TextTier')
            tier3.add_point(0.5, 'p1'.encode(codec))
            tier3.add_point(5, 'p1'.encode(codec))
            tier3.add_point(3.3, 'p1'.encode(codec))

            tgfile = io.StringIO()
            self.tg.to_stream(tgfile, codec=codec)
            tgfile.seek(0)
            tg1 = tgfile.read()
            tgfile.seek(0)

            self.tg = TextGrid(tgfile, codec=codec, stream=True)

            tgfile = io.StringIO()
            self.tg.to_stream(tgfile, codec=codec)
            tgfile.seek(0)
            tg2 = tgfile.read()
            tgfile.seek(0)

            self.assertEqual(tg2, tg1)

    def test_to_eaf(self):
        tier1 = self.tg.add_tier('tier1')
        tier2 = self.tg.add_tier('tier2', tier_type='TextTier')
        tier1.add_interval(0, 1, 'int1')
        tier1.add_interval(2, 3, 'int2')
        tier1.add_interval(4, 5, 'int3')
        tier2.add_point(1.5, 'point1')
        tier2.add_point(2.5, 'point2')
        tier2.add_point(3.5, 'point3')
        eaf = self.tg.to_eaf(0.03)
        self.assertRaises(ValueError, self.tg.to_eaf, -1)
        self.assertEquals(sorted(eaf.get_tier_names()),
                          sorted(['default', 'tier1', 'tier2']))
        self.assertEquals(sorted(eaf.get_annotation_data_for_tier('tier1')),
                          sorted([(0, 1000, 'int1'), (4000, 5000, 'int3'),
                                  (2000, 3000, 'int2')]))
        self.assertEquals(eaf.get_annotation_data_for_tier('tier2'),
                          [(2500, 2530, 'point2'), (1500, 1530, 'point1'),
                           (3500, 3530, 'point3')])

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
                         sorted(self.tier1.get_intervals()))
        self.tier2.add_point(5, 'a')
        self.tier2.add_point(7, 'c')
        self.tier2.add_point(6, 'b')
        self.assertEqual([(5, 'a'), (6, 'b'), (7, 'c')],
                         sorted(self.tier2.get_intervals()))

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
