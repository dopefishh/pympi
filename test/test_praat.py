#!/bin/env python
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from pympi.Praat import TextGrid


class PraatTest(unittest.TestCase):
    def setUp(self):
        self.tg = TextGrid(xmax=20)
        self.maxdiff = None

# Test all the Praat.TextGrid functions
    def test_sort_tiers(self):
        self.tg.add_tier('t2')
        self.tg.add_tier('t1')
        self.tg.add_tier('t3')
        self.tg.add_tier('t6')
        self.tg.add_tier('t4')
        self.tg.add_tier('t5')

        tiernames = ['t1', 't2', 't3', 't4', 't5', 't6']
        self.tg.sort_tiers()
        self.assertEqual([a[1] for a in self.tg.get_tier_name_num()],
                         tiernames)
        self.tg.sort_tiers(lambda x: list(reversed(tiernames)).index(x.name))
        self.assertEqual([a[1] for a in self.tg.get_tier_name_num()],
                         list(reversed(tiernames)))

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

        self.tg.add_tier('tier4', number=2)
        self.assertEqual(len(self.tg.tiers), 4)
        self.assertEqual(4, len(self.tg.tiers))

    def test_remove_tier(self):
        self.assertRaises(Exception, self.tg.remove_tier, -1)
        self.assertRaises(Exception, self.tg.remove_tier, 10)

        self.tg.add_tier('tier1')
        self.tg.add_tier('tier2')
        self.tg.add_tier('tier3')
        self.tg.add_tier('tier4', number=2)

        self.tg.remove_tier(3)
        self.assertEqual(len(self.tg.tiers), 3)
        self.assertEqual(['tier1', 'tier3', 'tier4'],
                         sorted(a.name for a in self.tg.tiers))

        self.tg.remove_tier('tier1')
        self.assertEqual(len(self.tg.tiers), 2)
        self.assertEqual(['tier3', 'tier4'],
                         sorted(a.name for a in self.tg.tiers))

        self.tg.remove_tier(2)
        self.assertEqual(len(self.tg.tiers), 1)
        self.assertEqual(['tier4'], [a.name for a in self.tg.tiers])

        self.tg.remove_tier('tier4')
        self.assertTrue(not self.tg.tiers)

    def test_get_tier(self):
        self.assertRaises(Exception, self.tg.get_tier, -1)
        self.assertRaises(Exception, self.tg.get_tier, 'a')
        self.assertRaises(Exception, self.tg.get_tier, 10)

        tier1 = self.tg.add_tier('tier1')
        tier2 = self.tg.add_tier('tier2')
        tier3 = self.tg.add_tier('tier3')

        self.assertEqual(tier1, self.tg.get_tier(tier1.name))
        self.assertEqual(tier3, self.tg.get_tier(tier3.name))

        self.assertEqual(self.tg.tiers[1], self.tg.get_tier(tier2.name))

    def test_change_tier_name(self):
        self.assertRaises(Exception,
                          self.tg.change_tier_name, -1, 'b')
        self.assertRaises(Exception,
                          self.tg.change_tier_name, 'a', 'b')
        self.assertRaises(Exception,
                          self.tg.change_tier_name, 10, 'b')
        self.tg.add_tier('tier1')
        tier2 = self.tg.add_tier('tier2')
        self.tg.add_tier('tier3')

        self.tg.change_tier_name('tier1', 'tier1a')
        self.assertEqual(['tier1a', 'tier2', 'tier3'],
                         [a.name for a in self.tg.tiers])
        self.tg.change_tier_name(self.tg.tiers.index(tier2)+1, 'tier2a')
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
                         list(self.tg.get_tier_name_num()))

    def test_to_file(self):
        for codec in ['utf-8', 'latin_1', 'mac_roman']:
            self.tg = TextGrid(xmax=20)
            tier1 = self.tg.add_tier('tier')
            tier1.add_interval(1, 2, 'i1')
            tier1.add_interval(2, 3, 'i2')
            tier1.add_interval(4, 5, 'i3')

            tier4 = self.tg.add_tier('tier')
            tier4.add_interval(1, 2, u'i1ü')
            tier4.add_interval(2.0, 3, 'i2')
            tier4.add_interval(4, 5.0, 'i3')

            tier2 = self.tg.add_tier('tier2', tier_type='TextTier')
            tier2.add_point(1, u'p1ü')
            tier2.add_point(2, 'p1')
            tier2.add_point(3, 'p1')

            tempf = tempfile.mkstemp()[1]

# Normal mode
            self.tg.to_file(tempf, codec=codec)
            TextGrid(tempf, codec=codec)
# Short mode
            self.tg.to_file(tempf, codec=codec, mode='s')
            TextGrid(tempf, codec=codec)
# Binary mode
            self.tg.to_file(tempf, mode='b')
            TextGrid(tempf)

            os.remove(tempf)

    def test_to_eaf(self):
        tier1 = self.tg.add_tier('tier1')
        tier2 = self.tg.add_tier('tier2', tier_type='TextTier')
        tier1.add_interval(0, 1, 'int1')
        tier1.add_interval(2, 3, 'int2')
        tier1.add_interval(5, 6, 'int3')
        tier2.add_point(1.5, 'point1')
        tier2.add_point(2.5, 'point2')
        tier2.add_point(3.5, 'point3')
        eaf = self.tg.to_eaf(True, 0.03)
        self.assertRaises(ValueError, self.tg.to_eaf, pointlength=-1)
        self.assertEqual(sorted(eaf.get_tier_names()),
                         sorted(['default', 'tier1', 'tier2']))
        self.assertEqual(sorted(eaf.get_annotation_data_for_tier('tier1')),
                         sorted([(0, 1000, 'int1'), (5000, 6000, 'int3'),
                                 (2000, 3000, 'int2')]))
        self.assertEqual(sorted(eaf.get_annotation_data_for_tier('tier2')),
                         sorted([(2500, 2530, 'point2'),
                                 (1500, 1530, 'point1'),
                                 (3500, 3530, 'point3')]))

# Test all the Praat.Tier functions
    def setup_tier(self):
        self.tier1 = self.tg.add_tier('tier1')
        self.tier2 = self.tg.add_tier('tier2', tier_type='TextTier')

    def test_add_point(self):
        self.setup_tier()
        self.assertRaises(Exception, self.tier1.add_point, 5, 'a')
        self.tier2.add_point(5, 't')
        self.assertEqual([(5, 't')], self.tier2.intervals)
        self.assertRaises(Exception, self.tier2.add_point, 5, 'a')
        self.tier2.add_point(6, 'a')
        self.assertEqual([(5, 't'), (6, 'a')], self.tier2.intervals)
        self.tier2.add_point(5, 'a', False)

    def test_add_interval(self):
        self.setup_tier()
        self.assertRaises(Exception,
                          self.tier2.add_interval, 5, 6, 'a')
        self.assertRaises(Exception, self.tier2.add_interval, 6, 5, 'a')

        self.tier1.add_interval(5, 6, 't')
        self.assertEqual([(5, 6, 't')], self.tier1.intervals)
        self.assertRaises(Exception, self.tier1.add_interval, 5.5, 6.5, 't')
        self.tier1.add_interval(6, 7, 'a')
        self.assertEqual([(5, 6, 't'), (6, 7, 'a')], self.tier1.intervals)

        self.tier1.add_interval(5.5, 6.5, 't', False)

    def test_remove_interval(self):
        self.setup_tier()
        self.assertRaises(Exception, self.tier2.remove_interval, 5)
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
        self.assertRaises(Exception, self.tier1.remove_point, 5)
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
