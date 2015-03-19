#!/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree
from pympi import Eaf
import tempfile
import unittest


class Elan(unittest.TestCase):
    def setUp(self):
        self.eaf = Eaf()

    def test_add_linked_file(self):
        self.eaf.add_linked_file('/some/file/path/test.wav')
        self.assertEqual(self.eaf.media_descriptors[0]['MIME_TYPE'],
                         'audio/x-wav')
        self.eaf.add_linked_file('/some/file/path/test.mpg',
                                 './test.mpg', time_origin=5, ex_from='ef')
        self.assertEqual(self.eaf.media_descriptors[1]['MIME_TYPE'],
                         'video/mpeg')
        self.assertEqual(self.eaf.media_descriptors[1]['RELATIVE_MEDIA_URL'],
                         './test.mpg')
        self.assertEqual(self.eaf.media_descriptors[1]['TIME_ORIGIN'], 5)
        self.assertEqual(self.eaf.media_descriptors[1]['EXTRACTED_FROM'], 'ef')

        self.eaf.add_linked_file('/some/file/path/test.wierd',
                                 mimetype='none/wierd')
        self.assertEqual(self.eaf.media_descriptors[2]['MIME_TYPE'],
                         'none/wierd')

        self.assertRaises(KeyError, self.eaf.add_linked_file, '/test.wierd')

    def test_remove_linked_files(self):
        self.eaf.add_linked_file('/some/file/path/test.wav',
                                 './test.wav', time_origin=5, ex_from='ef1')
        self.eaf.add_linked_file('/some/file/path/test2.wav',
                                 './test2.wav', time_origin=10, ex_from='ef2')
        self.eaf.add_linked_file('/some/file/path/test3.mpg',
                                 './test3.mpg', time_origin=15, ex_from='ef3')
        self.eaf.add_linked_file('/some/file/path/test4.mpg',
                                 './test4.mpg', time_origin=20, ex_from='ef3')
        self.eaf.remove_linked_files(mimetype='audio/x-wav')
        self.assertEqual(len(self.eaf.get_linked_files()), 2)
        self.eaf.remove_linked_files(ex_from='ef1')
        self.assertEqual(len(self.eaf.get_linked_files()), 2)
        self.eaf.remove_linked_files(file_path='/some/file/path/test4.mpg')
        self.assertEqual(len(self.eaf.get_linked_files()), 1)
        self.eaf.remove_linked_files(relpath='./test3.mpg')
        self.assertEqual(self.eaf.get_linked_files(), [])

    def test_remove_secondary_linked_files(self):
        self.eaf.add_secondary_linked_file(
            '/some/file/path/test.wav', './test.wav', time_origin=5,
            assoc_with='ef1')
        self.eaf.add_secondary_linked_file(
            '/some/file/path/test2.wav', './test2.wav', time_origin=10,
            assoc_with='ef2')
        self.eaf.add_secondary_linked_file(
            '/some/file/path/test3.mpg', './test3.mpg', time_origin=15,
            assoc_with='ef3')
        self.eaf.add_secondary_linked_file(
            '/some/file/path/test4.mpg', './test4.mpg', time_origin=20,
            assoc_with='ef3')
        self.eaf.remove_secondary_linked_files(mimetype='audio/x-wav')
        self.assertEqual(len(self.eaf.get_secondary_linked_files()), 2)
        self.eaf.remove_secondary_linked_files(assoc_with='ef1')
        self.assertEqual(len(self.eaf.get_secondary_linked_files()), 2)
        self.eaf.remove_secondary_linked_files(
            file_path='/some/file/path/test4.mpg')
        self.assertEqual(len(self.eaf.get_secondary_linked_files()), 1)
        self.eaf.remove_secondary_linked_files(relpath='./test3.mpg')
        self.assertEqual(self.eaf.get_secondary_linked_files(), [])

    def test_add_secondary_linked_file(self):
        self.eaf.add_secondary_linked_file('/some/file/path/test.wav')
        self.assertEqual(self.eaf.linked_file_descriptors[0]['MIME_TYPE'],
                         'audio/x-wav')
        self.eaf.add_secondary_linked_file(
            '/some/file/path/test.mpg', './test.mpg',
            time_origin=5, assoc_with='ef')
        self.assertEqual(self.eaf.linked_file_descriptors[1]['MIME_TYPE'],
                         'video/mpeg')
        self.assertEqual(
            self.eaf.linked_file_descriptors[1]['RELATIVE_LINK_URL'],
            './test.mpg')
        self.assertEqual(self.eaf.linked_file_descriptors[1]['TIME_ORIGIN'], 5)
        self.assertEqual(
            self.eaf.linked_file_descriptors[1]['ASSOCIATED_WITH'], 'ef')

        self.eaf.add_secondary_linked_file('/some/file/path/test.wierd',
                                           mimetype='none/wierd')
        self.assertEqual(self.eaf.linked_file_descriptors[2]['MIME_TYPE'],
                         'none/wierd')

        self.assertRaises(KeyError,
                          self.eaf.add_secondary_linked_file, '/test.wierd')

    def test_get_linked_files(self):
        self.eaf.add_linked_file('/some/file/path/test.wav')
        self.eaf.add_linked_file('/some/file/path/test.mpg', './test.mpg',
                                 time_origin=5, ex_from='ef')
        self.assertEqual(self.eaf.get_linked_files(),
                         self.eaf.media_descriptors)

    def test_get_secondary_linked_files(self):
        self.eaf.add_secondary_linked_file('/some/file/path/test.wav')
        self.eaf.add_secondary_linked_file(
            '/some/file/path/test.mpg', './test.mpg', time_origin=5,
            assoc_with='ef')
        self.assertEqual(self.eaf.get_secondary_linked_files(),
                         self.eaf.linked_file_descriptors)

    def test_add_tier(self):
        self.eaf.add_locale('ru')
        self.eaf.add_language('RUS')
        self.assertEqual(len(self.eaf.get_tier_names()), 1)
        self.eaf.add_tier('tier1', 'default-lt', locale='ru', language='RUS')
        self.assertEqual(len(self.eaf.get_tier_names()), 2)
        self.assertEqual(
            self.eaf.get_parameters_for_tier('tier1')['LINGUISTIC_TYPE_REF'],
            'default-lt')
        self.assertEqual(
            self.eaf.get_parameters_for_tier('tier1')['DEFAULT_LOCALE'],
            'ru')
        self.assertEqual(
            self.eaf.get_parameters_for_tier('tier1')['LANG_REF'], 'RUS')

        self.eaf.add_tier('tier2', 'non-existing-linguistic-type')
        self.assertEqual(len(self.eaf.get_tier_names()), 3)
        self.assertEqual(
            self.eaf.get_parameters_for_tier('tier2')['LINGUISTIC_TYPE_REF'],
            'default-lt')
        self.assertEqual(['default', 'tier1', 'tier2'],
                         sorted(self.eaf.get_tier_names()))

        self.eaf.add_tier('tier3', None, 'tier1', 'en', 'person', 'person2')
        self.assertEqual(self.eaf.get_parameters_for_tier('tier3'), {
            'ANNOTATOR': 'person2', 'DEFAULT_LOCALE': None,
            'LINGUISTIC_TYPE_REF': 'default-lt', 'PARENT_REF': 'tier1',
            'LANG_REF': None, 'PARTICIPANT': 'person', 'TIER_ID': 'tier3'})

        self.eaf.add_tier('tier4', tier_dict={
            'ANNOTATOR': 'person2', 'DEFAULT_LOCALE': 'en',
            'LINGUISTIC_TYPE_REF': 'default-lt', 'PARENT_REF': 'tier1',
            'PARTICIPANT': 'person', 'TIER_ID': 'tier4', 'LANG_ID': 'RUS'})
        self.assertEqual(self.eaf.get_parameters_for_tier('tier4'), {
            'ANNOTATOR': 'person2', 'DEFAULT_LOCALE': 'en',
            'LINGUISTIC_TYPE_REF': 'default-lt', 'PARENT_REF': 'tier1',
            'PARTICIPANT': 'person', 'TIER_ID': 'tier4', 'LANG_ID': 'RUS'})

        for tier in ['tier1', 'tier2', 'tier3']:
            self.assertEqual(self.eaf.tiers[tier][0], {})
            self.assertEqual(self.eaf.tiers[tier][1], {})

        self.assertRaises(ValueError, self.eaf.add_tier, '')

    def test_remove_tiers(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_tier('tier2')
        self.eaf.add_tier('tier3')
        self.eaf.add_tier('tier4')
        self.eaf.remove_tiers(['default', 'tier4', 'tier1'])
        self.assertEqual(sorted(self.eaf.get_tier_names()), ['tier2', 'tier3'])
        self.assertRaises(KeyError, self.eaf.remove_tiers, ['tier1'])
        self.eaf.remove_tiers(['tier2', 'tier3'])
        self.assertEqual(sorted(self.eaf.get_tier_names()), [])

    def test_remove_tier(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_tier('tier2')
        self.eaf.add_tier('tier3')
        self.eaf.add_tier('tier4')
        self.eaf.remove_tier('tier1')
        self.assertEqual(sorted(self.eaf.get_tier_names()),
                         ['default', 'tier2', 'tier3', 'tier4'])
        self.assertRaises(KeyError, self.eaf.remove_tier, 'tier1')

    def test_get_tier_names(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_tier('tier2')
        self.eaf.add_tier('tier3')
        self.eaf.add_tier('tier4')
        self.assertEqual(sorted(self.eaf.get_tier_names()),
                         ['default', 'tier1', 'tier2', 'tier3', 'tier4'])

    def test_get_parameters_for_tier(self):
        self.eaf.add_tier('tier1', 'default-lt', 'tier1', None, 'person',
                          'person2')
        self.eaf.add_tier('tier2')
        self.assertEqual(self.eaf.get_parameters_for_tier('tier1'), {
            'ANNOTATOR': 'person2', 'DEFAULT_LOCALE': None, 'LANG_REF': None,
            'LINGUISTIC_TYPE_REF': 'default-lt', 'PARENT_REF': 'tier1',
            'PARTICIPANT': 'person', 'TIER_ID': 'tier1'})
        self.assertEqual(self.eaf.get_parameters_for_tier('tier2'), {
            'PARTICIPANT': None, 'DEFAULT_LOCALE': None,
            'LINGUISTIC_TYPE_REF': 'default-lt', 'ANNOTATOR': None,
            'LANG_REF': None, 'PARENT_REF': None, 'TIER_ID': 'tier2'})

    def test_child_tiers_for(self):
        self.eaf.add_tier('parent1')
        self.eaf.add_tier('parent2')
        self.eaf.add_tier('child11', parent='parent1')
        self.eaf.add_tier('child12', parent='parent1')
        self.eaf.add_tier('child13', parent='parent1')
        self.eaf.add_tier('orphan21')
        self.eaf.add_tier('orphan22')
        self.eaf.add_tier('orphan23')
        self.assertEqual(sorted(self.eaf.child_tiers_for('parent1')),
                         ['child11', 'child12', 'child13'])
        self.assertEqual(sorted(self.eaf.child_tiers_for('parent2')), [])
        self.assertRaises(KeyError, self.eaf.child_tiers_for, 'parent3')

    def test_get_annotation_data_for_tier(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1000, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a1')
        self.eaf.add_annotation('tier1', 2000, 3000, 'a1')
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1')),
            sorted([(0, 1000, 'a1'), (2000, 3000, 'a1'), (1000, 2000, 'a1')]))
        self.assertRaises(KeyError,
                          self.eaf.get_annotation_data_for_tier, 'tier2')

    def test_get_annotation_data_at_time(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1000, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a2')
        self.eaf.add_annotation('tier1', 2000, 3000, 'a3')
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_at_time('tier1', 500)),
            [(0, 1000, 'a1')])
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_at_time('tier1', 1000)),
            sorted([(0, 1000, 'a1'), (1000, 2000, 'a2')]))
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_at_time('tier1', 3001)), [])
        self.assertRaises(KeyError,
                          self.eaf.get_annotation_data_at_time, 'tier2', 0)

    def test_get_annotation_data_between_times(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1000, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a2')
        self.eaf.add_annotation('tier1', 2000, 3000, 'a3')
        self.eaf.add_annotation('tier1', 3000, 4000, 'a4')
        self.assertEqual(sorted(self.eaf.get_annotation_data_between_times(
            'tier1', 1500, 2500)), [(1000, 2000, 'a2'), (2000, 3000, 'a3')])
        self.assertEqual(sorted(self.eaf.get_annotation_data_between_times(
            'tier1', 1000, 2000)), [(0, 1000, 'a1'),
                                    (1000, 2000, 'a2'), (2000, 3000, 'a3')])
        self.assertEqual(sorted(self.eaf.get_annotation_data_between_times(
            'tier1', 4001, 30000)), [])
        self.assertRaises(
            KeyError, self.eaf.get_annotation_data_between_times, 'ter1', 0, 1)

    def test_remove_all_annotations_from_tier(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1000, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a2')
        self.eaf.add_annotation('tier1', 2000, 3000, 'a3')
        self.eaf.add_annotation('tier1', 3000, 4000, 'a4')
        self.eaf.remove_all_annotations_from_tier('tier1')
        self.assertEqual(self.eaf.get_annotation_data_for_tier('tier1'), [])

    def test_add_annotation(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1')),
            [(0, 1, '')])
        self.eaf.add_annotation('tier1', 1, 2, 'abc')
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1')),
            sorted([(0, 1, ''), (1, 2, 'abc')]))
        self.assertRaises(KeyError, self.eaf.add_annotation, 't1', 0, 0)
        self.assertRaises(ValueError,
                          self.eaf.add_annotation, 'tier1', 1, 1)
        self.assertRaises(ValueError,
                          self.eaf.add_annotation, 'tier1', 2, 1)
        self.assertRaises(ValueError,
                          self.eaf.add_annotation, 'tier1', -1, 1)
        self.eaf.add_tier('tier2')
        self.eaf.add_ref_annotation('tier2', 'tier1', 0, 'r1')
        self.assertRaises(ValueError,
                          self.eaf.add_annotation, 'tier2', 0, 1)

    def test_remove_annotation(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1000, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a2')
        self.eaf.add_annotation('tier1', 2000, 3000, 'a3')
        self.eaf.add_annotation('tier1', 3000, 4000, 'a4')
        self.assertEqual(self.eaf.remove_annotation('tier1', 500), 1)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1')),
            sorted([(1000, 2000, 'a2'), (2000, 3000, 'a3'),
                    (3000, 4000, 'a4')]))

        self.assertEqual(self.eaf.remove_annotation('tier1', 2000), 2)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1')),
            sorted([(3000, 4000, 'a4')]))
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1')),
            sorted([(3000, 4000, 'a4')]))
        self.assertRaises(KeyError, self.eaf.remove_annotation, 'tier2', 0)

    def test_clean_time_slots(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_tier('tier2')
        self.eaf.add_annotation('tier1', 0, 1, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a2')
        self.eaf.add_annotation('tier1', 2000, 3000, 'a3')
        self.eaf.add_annotation('tier1', 3000, 4000, 'a4')
        ts = [x for x in self.eaf.timeslots]
        self.eaf.remove_annotation('tier1', 1500, False)
        self.assertEqual(len(ts), len(self.eaf.timeslots))
        self.eaf.clean_time_slots()
        self.assertEqual(len(ts)-2, len(self.eaf.timeslots))

    def test_merge_tiers(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_tier('tier2')
        self.eaf.add_tier('tier3')
        # Overlap
        self.eaf.add_annotation('tier1', 0, 1000, 'a1')
        self.eaf.add_annotation('tier2', 500, 1500, 'b1')

        # Gap
        self.eaf.add_annotation('tier1', 2000, 2500, 'a2')
        self.eaf.add_annotation('tier2', 3000, 4000, 'b2')

        # Within
        self.eaf.add_annotation('tier1', 5000, 6000, 'a3')
        self.eaf.add_annotation('tier2', 5100, 5900, 'b3')

        # Three
        self.eaf.add_annotation('tier1', 6050, 6250, 'c')
        self.eaf.add_annotation('tier1', 6250, 6500, 'c')
        self.eaf.add_annotation('tier1', 6500, 6750, 'c')
        self.eaf.add_annotation('tier3', 6100, 6800, 'd')

        # Gap of 5 ms
        self.eaf.add_annotation('tier1', 7000, 7995, 'a4')
        self.eaf.add_annotation('tier2', 8000, 9000, 'b4')

        self.eaf.merge_tiers(['tier1', 'tier2'], 'm_0')
        self.eaf.merge_tiers(['tier1'], 'm_a', 5)
        self.eaf.merge_tiers(['tier1', 'tier2'], 'm_5', 5)
        self.eaf.merge_tiers(['tier1', 'tier2'], 'm_6', 6)
        self.eaf.merge_tiers(['tier1', 'tier2', 'tier3'], 'mm')

        m0 = [(0, 1500, 'a1_b1'), (2000, 2500, 'a2'), (3000, 4000, 'b2'),
              (5000, 6000, 'a3_b3'), (6050, 6250, 'c'), (6250, 6500, 'c'),
              (6500, 6750, 'c'), (7000, 7995, 'a4'), (8000, 9000, 'b4')]
        m5 = [(0, 1500, 'a1_b1'), (2000, 2500, 'a2'), (3000, 4000, 'b2'),
              (5000, 6000, 'a3_b3'), (6050, 6750, 'c_c_c'), (7000, 7995, 'a4'),
              (8000, 9000, 'b4')]
        m6 = [(0, 1500, 'a1_b1'), (2000, 2500, 'a2'), (3000, 4000, 'b2'),
              (5000, 6000, 'a3_b3'), (6050, 6750, 'c_c_c'),
              (7000, 9000, 'a4_b4')]
        mm = [(0, 1500, 'a1_b1'), (2000, 2500, 'a2'), (3000, 4000, 'b2'),
              (5000, 6000, 'a3_b3'), (6050, 6800, 'c_d_c_c'),
              (7000, 7995, 'a4'), (8000, 9000, 'b4')]
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('m_0')), m0)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('m_5')), m5)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('m_6')), m6)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('mm')), mm)
        self.assertRaises(KeyError, self.eaf.merge_tiers, ['a', 'b'])

    def test_shift_annotations(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_tier('tier2')
        # Overlap
        self.eaf.add_annotation('tier1', 0, 100, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a2')
        self.eaf.add_annotation('tier2', 500, 1500, 'b1')
        self.eaf.add_annotation('tier2', 0, 150, 'b1')
        d1 = self.eaf.get_annotation_data_for_tier('tier1')
        d2 = self.eaf.get_annotation_data_for_tier('tier2')
        self.eaf.shift_annotations(0)
        self.assertEqual(d1, self.eaf.get_annotation_data_for_tier('tier1'))
        self.assertEqual(d2, self.eaf.get_annotation_data_for_tier('tier2'))

        self.eaf.shift_annotations(100)
        self.assertEqual(self.eaf.get_annotation_data_for_tier('tier1'),
                         [(x+100, y+100, v) for x, y, v in d1])
        self.assertEqual(self.eaf.get_annotation_data_for_tier('tier2'),
                         [(x+100, y+100, v) for x, y, v in d2])
        self.assertEqual(self.eaf.shift_annotations(-200),
                         ([('tier2', 100, 250, 'b1')],
                          [('tier1', 100, 200, 'a1')]))

    def test_filter_annotations(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1, '1')
        self.eaf.add_annotation('tier1', 1, 2, '2')
        self.eaf.add_annotation('tier1', 2, 3, '3')
        self.eaf.add_annotation('tier1', 3, 4, '4')
        self.eaf.add_annotation('tier1', 4, 5, 'a')
        self.eaf.add_annotation('tier1', 5, 6, 'b')
        self.eaf.add_annotation('tier1', 6, 7, 'c')
        self.eaf.add_annotation('tier1', 7, 8, 'd')

        # No in or exclude
        self.eaf.filter_annotations('tier1')
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1_filter')),
            sorted(self.eaf.get_annotation_data_for_tier('tier1')))

        # Inclusion
        self.eaf.filter_annotations('tier1', filtin=['1', '2', '3'])
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1_filter')),
            sorted([(0, 1, '1'), (2, 3, '3'), (1, 2, '2')]))
        self.eaf.filter_annotations('tier1', filtin=['[123]'], regex=True)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1_filter')),
            sorted([(0, 1, '1'), (2, 3, '3'), (1, 2, '2')]))

        # Exclusion
        self.eaf.filter_annotations('tier1', filtex=['1', '2', '3', '4'])
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1_filter')),
            sorted([(4, 5, 'a'), (6, 7, 'c'), (5, 6, 'b'), (7, 8, 'd')]))
        self.eaf.filter_annotations('tier1', filtex=['[1234]'], regex=True)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1_filter')),
            sorted([(4, 5, 'a'), (6, 7, 'c'), (5, 6, 'b'), (7, 8, 'd')]))

        # Combination
        self.eaf.filter_annotations('tier1', filtin=['1', '2', '3', '4'],
                                    filtex=['1', '2'])
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tier1_filter')),
            sorted([(2, 3, '3'), (3, 4, '4')]))
        self.eaf.filter_annotations('tier1', tier_name='t', filtin=['[1234]'],
                                    filtex=['[12]'], regex=True)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('t')),
            sorted([(2, 3, '3'), (3, 4, '4')]))

        self.assertRaises(KeyError, self.eaf.filter_annotations, 'a')

    def test_get_full_time_interval(self):
        self.assertEqual(self.eaf.get_full_time_interval(), (0, 0))
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 100, 500, 'a')
        self.eaf.add_annotation('tier1', 500, 1000, 'b')
        self.assertEqual(self.eaf.get_full_time_interval(), (100, 1000))

    def test_create_gaps_and_overlaps_tier(self):
        self.eaf.add_tier('t1')
        self.eaf.add_tier('t2')
        # Pause
        self.eaf.add_annotation('t1', 0, 1000)
        self.eaf.add_annotation('t1', 1200, 2000)
        # Gap
        self.eaf.add_annotation('t2', 2200, 3000)
        # Overlap
        self.eaf.add_annotation('t1', 2800, 4000)
        # Exact fto
        self.eaf.add_annotation('t2', 4000, 5000)
        # Within overlap
        self.eaf.add_annotation('t1', 4200, 4800)
        # Long pause
        self.eaf.add_annotation('t2', 14800, 15000)
        # Long gap
        self.eaf.add_annotation('t1', 20000, 20500)
        self.eaf.create_gaps_and_overlaps_tier('t1', 't2')
        self.eaf.create_gaps_and_overlaps_tier('t1', 't2', 'tt', 3000)
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('t1_t2_ftos')),
            [(1001, 1199, 'P1_t1'), (2001, 2199, 'G12_t1_t2'),
             (2800, 3000, 'O21_t2_t1'), (4200, 4800, 'W21_t2_t1'),
             (5001, 14799, 'P2_t2'), (15001, 19999, 'G21_t2_t1')])
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tt')),
            [(1001, 1199, 'P1_t1'), (2001, 2199, 'G12_t1_t2'),
             (2800, 3000, 'O21_t2_t1'), (4200, 4800, 'W21_t2_t1')])
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('t1_t2_ftos') +
                   [(4000, 4000, 'O12_t1_t2')]),
            list(self.eaf.get_gaps_and_overlaps('t1', 't2')))
        self.assertEqual(
            sorted(self.eaf.get_annotation_data_for_tier('tt') +
                   [(4000, 4000, 'O12_t1_t2')]),
            list(self.eaf.get_gaps_and_overlaps('t1', 't2', 3000)))

    def test_get_gaps_and_overlaps(self):
        pass
        # This is a placeholder, the real testing happens in:
        #   def test_create_gaps_and_overlaps_tier(self):

    def test_get_gaps_and_overlaps2(self):
        self.eaf.add_tier('t1')
        self.eaf.add_tier('t2')
        # Pause
        self.eaf.add_annotation('t1', 0, 1000)
        self.eaf.add_annotation('t1', 1200, 2000)
        # Gap
        self.eaf.add_annotation('t2', 2200, 3000)
        # Overlap
        self.eaf.add_annotation('t1', 2800, 4000)
        # Exact fto
        self.eaf.add_annotation('t2', 4000, 5000)
        # Within overlap
        self.eaf.add_annotation('t1', 4200, 4800)
        # Long pause
        self.eaf.add_annotation('t2', 14800, 15000)
        # Long gap
        self.eaf.add_annotation('t1', 20000, 20500)
        g1 = self.eaf.get_gaps_and_overlaps2('t1', 't2')
        g2 = self.eaf.get_gaps_and_overlaps2('t1', 't2', 3000)
        self.assertEqual(sorted(g1), [
            (1000, 1200, 'P1'), (2000, 2200, 'G12'), (2800, 3000, 'O21'),
            (4200, 4800, 'W21'), (5000, 14800, 'P2'), (15000, 20000, 'G21')])
        self.assertEqual(sorted(g2), [
            (1000, 1200, 'P1'), (2000, 2200, 'G12'),
            (2800, 3000, 'O21'), (4200, 4800, 'W21')])
        self.assertRaises(KeyError, list,
                          self.eaf.get_gaps_and_overlaps2('2', '3'))

    def test_get_tier_ids_for_linguistic_type(self):
        self.eaf.add_linguistic_type('l1')
        self.eaf.add_linguistic_type('l2')
        self.eaf.add_tier('t1', 'l1')
        self.eaf.add_tier('t2', 'l2')
        self.eaf.add_tier('t3', 'l2')
        self.eaf.add_tier('t4', parent='t1')
        self.eaf.add_tier('t5', 'l1', parent='t1')
        self.eaf.add_tier('t6')
        self.assertEqual(sorted(self.eaf.get_tier_ids_for_linguistic_type(
                         'l1')), ['t1', 't5'])
        self.assertEqual(sorted(self.eaf.get_tier_ids_for_linguistic_type(
                                'l2')), ['t2', 't3'])
        self.assertEqual(sorted(self.eaf.get_tier_ids_for_linguistic_type(
                                'default-lt', 't1')), ['t4'])

    def test_remove_linguistic_type(self):
        self.eaf.add_linguistic_type('l1')
        self.eaf.add_linguistic_type('l2')
        self.eaf.add_linguistic_type('l3')
        self.eaf.remove_linguistic_type('l2')
        self.assertEqual(sorted(self.eaf.get_linguistic_type_names()),
                         ['default-lt', 'l1', 'l3'])
        self.assertRaises(KeyError, self.eaf.remove_linguistic_type, 'a')

    def test_add_linguistic_type(self):
        self.eaf.add_linguistic_type('l1')
        self.eaf.add_linguistic_type('l2', 'Time_Subdivision', False, True)
        self.assertEqual(
            self.eaf.linguistic_types['l1'], {
                'CONSTRAINTS': None, 'TIME_ALIGNABLE': 'true',
                'LINGUISTIC_TYPE_ID': 'l1', 'GRAPHIC_REFERENCES': 'false'})
        self.assertEqual(
            self.eaf.linguistic_types['l2'], {
                'CONSTRAINTS': 'Time_Subdivision', 'TIME_ALIGNABLE': 'false',
                'LINGUISTIC_TYPE_ID': 'l2', 'GRAPHIC_REFERENCES': 'true'})
        self.eaf.add_linguistic_type('l3', param_dict={
            'CONSTRAINTS': 'Time_Subdivision', 'TIME_ALIGNABLE': 'false',
            'LINGUISTIC_TYPE_ID': 'l2', 'GRAPHIC_REFERENCES': 'true'})
        self.assertEqual(self.eaf.get_parameters_for_linguistic_type('l3'), {
            'CONSTRAINTS': 'Time_Subdivision', 'TIME_ALIGNABLE': 'false',
            'LINGUISTIC_TYPE_ID': 'l2', 'GRAPHIC_REFERENCES': 'true'})

        self.assertRaises(KeyError, self.eaf.add_linguistic_type, 'l2', 'a')

    def test_get_linguistic_types_names(self):
        self.assertEqual(sorted(self.eaf.get_linguistic_type_names()),
                         ['default-lt'])
        self.eaf.add_linguistic_type('l1')
        self.eaf.add_linguistic_type('l2')
        self.eaf.add_linguistic_type('l3')
        self.assertEqual(sorted(self.eaf.get_linguistic_type_names()),
                         ['default-lt', 'l1', 'l2', 'l3'])

    def test_get_parameters_for_linguistic_type(self):
        self.eaf.add_tier('tier2')
        self.eaf.add_linguistic_type('l2', 'Time_Subdivision', False, True)
        self.assertEqual(self.eaf.get_parameters_for_linguistic_type('l2'), {
            'CONSTRAINTS': 'Time_Subdivision', 'TIME_ALIGNABLE': 'false',
            'LINGUISTIC_TYPE_ID': 'l2', 'GRAPHIC_REFERENCES': 'true'})

    def test_to_textgrid(self):
        self.eaf.remove_tier('default')
        tg = self.eaf.to_textgrid()
        self.assertEqual(list(tg.get_tier_name_num()), [])
        self.eaf.add_tier('t1')
        self.eaf.add_annotation('t1', 0, 100, 'a11')
        self.eaf.add_annotation('t1', 100, 200, 'a21')
        self.eaf.add_annotation('t1', 200, 300, 'a31')
        self.eaf.add_annotation('t1', 300, 400, 'a41')
        self.eaf.add_tier('t2')
        self.eaf.add_annotation('t2', 0, 100, 'a12')
        self.eaf.add_annotation('t2', 100, 200, 'a22')
        self.eaf.add_annotation('t2', 200, 300, 'a32')
        self.eaf.add_annotation('t2', 300, 400, 'a42')
        self.eaf.add_tier('t3')
        self.eaf.add_annotation('t3', 0, 100, 'a13')
        self.eaf.add_annotation('t3', 100, 200, 'a23')
        self.eaf.add_annotation('t3', 200, 300, 'a33')
        self.eaf.add_annotation('t3', 300, 400, 'a43')
        self.eaf.add_tier('t4')
        self.eaf.add_annotation('t4', 0, 100, 'a14')
        self.eaf.add_annotation('t4', 100, 200, 'a24')
        self.eaf.add_annotation('t4', 200, 300, 'a34')
        self.eaf.add_annotation('t4', 300, 400, 'a44')
        self.eaf.add_tier('t5')
        self.eaf.add_annotation('t5', 0, 100, 'a15')
        self.eaf.add_annotation('t5', 100, 200, 'a25')
        self.eaf.add_annotation('t5', 200, 300, 'a35')
        self.eaf.add_annotation('t5', 300, 400, 'a45')
        self.eaf.add_tier('t6')
        self.eaf.add_annotation('t6', 0, 100, 'a16')
        self.eaf.add_annotation('t6', 100, 200, 'a26')
        self.eaf.add_annotation('t6', 200, 300, 'a36')
        self.eaf.add_annotation('t6', 300, 400, 'a46')
        tg = self.eaf.to_textgrid()
        self.assertEqual(sorted(a[1] for a in tg.get_tier_name_num()),
                         ['t1', 't2', 't3', 't4', 't5', 't6'])
        tg = self.eaf.to_textgrid(filtin=['t1', 't2', 't3'])
        self.assertEqual(sorted(a[1] for a in tg.get_tier_name_num()),
                         ['t1', 't2', 't3'])
        tg = self.eaf.to_textgrid(filtex=['t1', 't2', 't3'])
        self.assertEqual(sorted(a[1] for a in tg.get_tier_name_num()),
                         ['t4', 't5', 't6'])
        tg = self.eaf.to_textgrid(filtin=['t[123]'], regex=True)
        self.assertEqual(sorted(a[1] for a in tg.get_tier_name_num()),
                         ['t1', 't2', 't3'])
        tg = self.eaf.to_textgrid(filtex=['t[123]'], regex=True)
        self.assertEqual(sorted(a[1] for a in tg.get_tier_name_num()),
                         ['t4', 't5', 't6'])
        self.eaf.add_tier('t7')
        tg = self.eaf.to_textgrid()
        self.assertEqual(sorted(a[1] for a in tg.get_tier_name_num()),
                         ['t1', 't2', 't3', 't4', 't5', 't6', 't7'])
        self.assertEqual(list(tg.get_tier('t1').get_intervals(sort=True)),
                         [(0.0, 0.1, 'a11'), (0.1, 0.2, 'a21'),
                          (0.2, 0.3, 'a31'), (0.3, 0.4, 'a41')])
        self.assertEqual(list(tg.get_tier('t7').get_intervals()), [])

    def test_extract(self):
        self.eaf.add_tier('tier1')
        self.eaf.add_annotation('tier1', 0, 1000, 'a1')
        self.eaf.add_annotation('tier1', 1000, 2000, 'a2')
        self.eaf.add_annotation('tier1', 2000, 3000, 'a3')
        self.eaf.add_annotation('tier1', 3000, 4000, 'a4')
        self.eaf.add_tier('tier2')
        e1 = self.eaf.extract(1500, 2500)
        self.assertEqual(e1.adocument, self.eaf.adocument)
        self.assertEqual(e1.licenses, self.eaf.licenses)
        self.assertEqual(e1.header, self.eaf.header)
        self.assertEqual(e1.media_descriptors, self.eaf.media_descriptors)
        self.assertEqual(e1.linked_file_descriptors,
                         self.eaf.linked_file_descriptors)
        self.assertEqual(e1.linguistic_types, self.eaf.linguistic_types)
        self.assertEqual(e1.locales, self.eaf.locales)
        self.assertEqual(e1.constraints, self.eaf.constraints)
        self.assertEqual(e1.controlled_vocabularies,
                         self.eaf.controlled_vocabularies)
        self.assertEqual(e1.external_refs, self.eaf.external_refs)
        self.assertEqual(e1.lexicon_refs, self.eaf.lexicon_refs)
        self.assertEqual(e1.get_tier_names(), self.eaf.get_tier_names())
        self.assertEqual(sorted(e1.get_annotation_data_between_times(
            'tier1', 1500, 2500)), [(1000, 2000, 'a2'), (2000, 3000, 'a3')])
        e1 = self.eaf.extract(1000, 2000)
        self.assertEqual(sorted(e1.get_annotation_data_between_times(
            'tier1', 1000, 2000)),
            [(0, 1000, 'a1'), (1000, 2000, 'a2'), (2000, 3000, 'a3')])
        e1 = self.eaf.extract(4001, 30000)
        self.assertEqual(sorted(e1.get_annotation_data_between_times(
            'tier1', 4001, 30000)), [])

    def test_get_ref_annotation_at_time(self):
        self.eaf.add_tier('p1')
        self.eaf.add_linguistic_type('c', 'Symbolic_Association')
        self.eaf.add_tier('a1', 'c', 'p1')
        self.eaf.add_annotation('p1', 0, 1000, 'a1')
        self.eaf.add_annotation('p1', 1000, 2000, 'a2')
        self.eaf.add_annotation('p1', 3000, 4000, 'a3')
        self.eaf.add_ref_annotation('a1', 'p1', 500, 'ref1')
        self.eaf.add_ref_annotation('a1', 'p1', 3000, 'ref2')
        self.assertEqual(self.eaf.get_ref_annotation_at_time('a1', 500),
                         [(0, 1000, 'ref1', 'a1')])
        self.assertEqual(self.eaf.get_ref_annotation_at_time('p1', 2500), [])
        self.assertRaises(KeyError,
                          self.eaf.get_ref_annotation_at_time, 'eau', 0)

    def test_add_ref_annotation(self):
        self.eaf.add_tier('p1')
        self.eaf.add_linguistic_type('c', 'Symbolic_Association')
        self.eaf.add_tier('a1', 'c', 'p1')
        self.eaf.add_annotation('p1', 0, 1000, 'a1')
        self.eaf.add_annotation('p1', 1000, 2000, 'a2')
        self.eaf.add_annotation('p1', 3000, 4000, 'a3')
        self.eaf.add_ref_annotation('a1', 'p1', 500, 'ref1')
        self.eaf.add_ref_annotation('a1', 'p1', 3000)
        self.assertEqual(
            sorted([(3000, 4000, '', 'a3'), (0, 1000, 'ref1', 'a1')]),
            sorted(self.eaf.get_ref_annotation_data_for_tier('a1')))

        self.assertRaises(ValueError,
                          self.eaf.add_ref_annotation, 'p1', 'a1', 0, 'r1')
        self.assertRaises(ValueError, self.eaf.add_ref_annotation, 'a1',
                          'p1', 2500, 'r')
        self.assertRaises(KeyError,
                          self.eaf.add_ref_annotation, 'aa', 'bb', 0, 'r1')

    def test_get_ref_annotation_data_for_tier(self):
        self.eaf.add_tier('p1')
        self.eaf.add_linguistic_type('c', 'Symbolic_Association')
        self.eaf.add_tier('a1', 'c', 'p1')
        self.eaf.add_annotation('p1', 0, 1000, 'a1')
        self.eaf.add_annotation('p1', 1000, 2000, 'a2')
        self.eaf.add_annotation('p1', 3000, 4000, 'a3')
        self.eaf.add_ref_annotation('a1', 'p1', 500, 'ref1')
        self.eaf.add_ref_annotation('a1', 'p1', 3000)
        self.assertEqual(
            sorted([(3000, 4000, '', 'a3'), (0, 1000, 'ref1', 'a1')]),
            sorted(self.eaf.get_ref_annotation_data_for_tier('a1')))
        self.assertRaises(KeyError,
                          self.eaf.get_ref_annotation_data_for_tier, 'aaa')
        self.assertEqual(self.eaf.get_ref_annotation_data_for_tier('p1'), [])

    def test_add_locale(self):
        self.eaf.add_locale('ru', 'RUS', 'YAWERTY (Phonetic)')
        self.eaf.add_locale('en')
        self.assertEqual(
            self.eaf.get_locales(),
            {'ru': ('RUS', 'YAWERTY (Phonetic)'), 'en': (None, None)})

    def test_remove_locale(self):
        self.eaf.add_locale('ru', 'RUS', 'YAWERTY (Phonetic)')
        self.eaf.add_locale('en')
        self.eaf.remove_locale('ru')
        self.assertEqual(self.eaf.get_locales(), {'en': (None, None)})
        self.assertRaises(KeyError, self.eaf.remove_locale, 'ru')

    def test_get_locales(self):
        self.eaf.add_locale('ru', 'RUS', 'YAWERTY (Phonetic)')
        self.eaf.add_locale('en')
        self.assertEqual(
            self.eaf.get_locales(),
            {'ru': ('RUS', 'YAWERTY (Phonetic)'), 'en': (None, None)})

    def test_add_language(self):
        self.eaf.add_language('ru', 'RUS', 'YAWERTY (Phonetic)')
        self.eaf.add_language('en')
        self.assertEqual(
            self.eaf.get_languages(),
            {'ru': ('RUS', 'YAWERTY (Phonetic)'), 'en': (None, None)})

    def test_remove_language(self):
        self.eaf.add_language('ru', 'RUS', 'YAWERTY (Phonetic)')
        self.eaf.add_language('en')
        self.eaf.remove_language('ru')
        self.assertEqual(self.eaf.get_languages(), {'en': (None, None)})
        self.assertRaises(KeyError, self.eaf.remove_language, 'ru')

    def test_get_languages(self):
        self.eaf.add_language('ru', 'RUS', 'YAWERTY (Phonetic)')
        self.eaf.add_language('en')
        self.assertEqual(
            self.eaf.get_languages(),
            {'ru': ('RUS', 'YAWERTY (Phonetic)'), 'en': (None, None)})

    def test_add_property(self):
        self.eaf.add_property('k1', 'v1')
        self.eaf.add_property('k2', 'v2')
        self.assertEqual(self.eaf.get_properties(), [
            ('lastUsedAnnotation', 0), ('k1', 'v1'), ('k2', 'v2')])

    def test_remove_property(self):
        self.eaf.add_property('k1', 'v1')
        self.eaf.add_property('k2', 'v2')
        self.eaf.add_property('k3', 'v3')
        self.eaf.add_property('k4', 'v4')
        self.eaf.add_property('k4', 'v5')
        self.eaf.remove_property('a1')
        self.assertEqual(self.eaf.get_properties(), [
            ('lastUsedAnnotation', 0), ('k1', 'v1'), ('k2', 'v2'),
            ('k3', 'v3'), ('k4', 'v4'), ('k4', 'v5')])
        self.eaf.remove_property('k1')
        self.assertEqual(self.eaf.get_properties(), [
            ('lastUsedAnnotation', 0), ('k2', 'v2'), ('k3', 'v3'),
            ('k4', 'v4'), ('k4', 'v5')])
        self.eaf.remove_property(value='v2')
        self.assertEqual(self.eaf.get_properties(), [
            ('lastUsedAnnotation', 0), ('k3', 'v3'), ('k4', 'v4'),
            ('k4', 'v5')])
        self.eaf.remove_property('k4')
        self.assertEqual(self.eaf.get_properties(), [
            ('lastUsedAnnotation', 0), ('k3', 'v3')])
        self.eaf.remove_property()
        self.assertEqual(self.eaf.get_properties(), [])

    def test_get_properties(self):
        self.eaf.add_property('k1', 'v1')
        self.eaf.add_property('k2', 'v2')
        self.eaf.add_property('k3', 'v3')
        self.eaf.add_property('k4', 'v4')
        self.eaf.add_property('k4', 'v5')
        self.assertEqual(self.eaf.get_properties(), [
            ('lastUsedAnnotation', 0), ('k1', 'v1'), ('k2', 'v2'),
            ('k3', 'v3'), ('k4', 'v4'), ('k4', 'v5')])

    def test_add_license(self):
        self.eaf.add_license('k1', 'v1')
        self.eaf.add_license('k2', 'v2')
        self.assertEqual(self.eaf.get_licenses(), [
            ('k1', 'v1'), ('k2', 'v2')])

    def test_remove_license(self):
        self.eaf.add_license('k1', 'v1')
        self.eaf.add_license('k2', 'v2')
        self.eaf.add_license('k3', 'v3')
        self.eaf.add_license('k4', 'v4')
        self.eaf.add_license('k4', 'v5')
        self.eaf.remove_license('a1')
        self.assertEqual(self.eaf.get_licenses(), [
            ('k1', 'v1'), ('k2', 'v2'), ('k3', 'v3'), ('k4', 'v4'),
            ('k4', 'v5')])
        self.eaf.remove_license('k1')
        self.assertEqual(self.eaf.get_licenses(), [
            ('k2', 'v2'), ('k3', 'v3'), ('k4', 'v4'), ('k4', 'v5')])
        self.eaf.remove_license(url='v2')
        self.assertEqual(self.eaf.get_licenses(), [
            ('k3', 'v3'), ('k4', 'v4'), ('k4', 'v5')])
        self.eaf.remove_license('k4')
        self.assertEqual(self.eaf.get_licenses(), [('k3', 'v3')])
        self.eaf.remove_license()
        self.assertEqual(self.eaf.get_licenses(), [])

    def test_get_licenses(self):
        self.eaf.add_license('k1', 'v1')
        self.eaf.add_license('k2', 'v2')
        self.eaf.add_license('k3', 'v3')
        self.eaf.add_license('k4', 'v4')
        self.eaf.add_license('k4', 'v5')
        self.assertEqual(self.eaf.get_licenses(), [
            ('k1', 'v1'), ('k2', 'v2'), ('k3', 'v3'), ('k4', 'v4'),
            ('k4', 'v5')])

    def test_rename_tier(self):
        self.eaf.add_tier('child', parent='default')
        self.eaf.add_tier('test1')
        self.eaf.add_tier('test2')
        self.eaf.add_tier('test3')
        self.eaf.add_tier('test4')
        self.eaf.rename_tier('test1', 'test1a')
        self.eaf.rename_tier('default', 'test5')
        self.assertEqual(sorted(self.eaf.get_tier_names()), sorted([
            'child', 'test1a', 'test2', 'test3', 'test4', 'test5']))
        self.assertEqual(sorted(self.eaf.child_tiers_for('test5')),
                         sorted(['child']))

    def test_copy_tier(self):
        self.eaf.add_tier('test1')
        self.eaf.add_annotation('test1', 0, 100, 'a')
        self.eaf.add_annotation('test1', 100, 200, 'a')
        self.eaf.add_tier('test2')
        self.eaf.add_annotation('test2', 0, 100, 'a')
        self.eaf.add_annotation('test2', 100, 200, 'a')
        target = Eaf()
        self.eaf.copy_tier(target, 'test2')
        self.assertEqual(sorted(target.get_parameters_for_tier('test2')),
                         sorted(self.eaf.get_parameters_for_tier('test2')))
        self.assertEqual(
            sorted(target.get_annotation_data_for_tier('test2')),
            sorted(self.eaf.get_annotation_data_for_tier('test2')))

    def test_add_controlled_vocabulary(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_controlled_vocabulary('cv2')
        self.eaf.add_controlled_vocabulary('cv3', 'er1')
        self.assertEqual(sorted(self.eaf.get_controlled_vocabulary_names()),
                         ['cv1', 'cv2', 'cv3'])

    def test_add_cv_entry(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_language('eng')
        self.eaf.add_language('nld')
        self.eaf.add_cv_entry(
            'cv1', 'cve1', [('H', 'eng', 'hold'), ('H', 'nld', None)])
        self.assertEqual(self.eaf.get_cv_entries('cv1'), {
            'cve1': ([('H', 'eng', 'hold'), ('H', 'nld', None)], None)})
        self.eaf.add_cv_entry(
            'cv1', 'cve2', [('S', 'eng', 'stroke'), ('S', 'nld', None)])
        self.assertEqual(self.eaf.get_cv_entries('cv1'), {
            'cve1': ([('H', 'eng', 'hold'), ('H', 'nld', None)], None),
            'cve2': ([('S', 'eng', 'stroke'), ('S', 'nld', None)], None)})
        self.assertRaises(KeyError, self.eaf.add_cv_entry, 'cv2', 'cve1', [])
        self.assertRaises(ValueError, self.eaf.add_cv_entry, 'cv1', 'cve1',
                          [('H', 'spa', None)])

    def test_add_cv_description(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_language('eng')
        self.eaf.add_language('nld')
        self.eaf.add_cv_description('cv1', 'eng', 'Gesture Phases')
        self.eaf.add_cv_description('cv1', 'nld', None)
        self.assertEqual(self.eaf.get_cv_descriptions('cv1'), [
            ('eng', 'Gesture Phases'), ('nld', None)])
        self.assertRaises(KeyError, self.eaf.add_cv_description, 'cv2', 'eng')
        self.assertRaises(ValueError,
                          self.eaf.add_cv_description, 'cv1', 'spa', None)

    def test_get_controlled_vocabulary_names(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_controlled_vocabulary('cv2')
        self.eaf.add_controlled_vocabulary('cv3', 'er1')
        self.assertEqual(sorted(self.eaf.get_controlled_vocabulary_names()),
                         ['cv1', 'cv2', 'cv3'])

    def test_get_cv_entry(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_language('eng')
        self.eaf.add_language('nld')
        self.eaf.add_cv_entry(
            'cv1', 'cve1', [('H', 'eng', 'hold'), ('H', 'nld', None)])
        self.assertEqual(self.eaf.get_cv_entries('cv1'), {
            'cve1': ([('H', 'eng', 'hold'), ('H', 'nld', None)], None)})
        self.eaf.add_cv_entry(
            'cv1', 'cve2', [('S', 'eng', 'stroke'), ('S', 'nld', None)])
        self.assertEqual(self.eaf.get_cv_entries('cv1'), {
            'cve1': ([('H', 'eng', 'hold'), ('H', 'nld', None)], None),
            'cve2': ([('S', 'eng', 'stroke'), ('S', 'nld', None)], None)})
        self.assertRaises(KeyError, self.eaf.get_cv_entries, 'cv2')

    def test_get_cv_descriptions(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_language('eng')
        self.eaf.add_language('nld')
        self.eaf.add_cv_description('cv1', 'eng', 'Gesture Phases')
        self.eaf.add_cv_description('cv1', 'nld', None)
        self.assertEqual(self.eaf.get_cv_descriptions('cv1'), [
            ('eng', 'Gesture Phases'), ('nld', None)])
        self.assertRaises(KeyError, self.eaf.get_cv_descriptions, 'cv2')

    def test_remove_controlled_vocabulary(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_controlled_vocabulary('cv2')
        self.eaf.add_controlled_vocabulary('cv3', 'er1')
        self.eaf.remove_controlled_vocabulary('cv3')
        self.assertEqual(sorted(self.eaf.get_controlled_vocabulary_names()),
                         ['cv1', 'cv2'])
        self.eaf.remove_controlled_vocabulary('cv1')
        self.assertEqual(sorted(self.eaf.get_controlled_vocabulary_names()),
                         ['cv2'])
        self.assertRaises(KeyError, self.eaf.remove_controlled_vocabulary, 'c')

    def test_remove_cv_entry(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_language('eng')
        self.eaf.add_language('nld')
        self.eaf.add_cv_entry(
            'cv1', 'cve1', [('H', 'eng', 'hold'), ('H', 'nld', None)])
        self.eaf.add_cv_entry(
            'cv1', 'cve2', [('S', 'eng', 'stroke'), ('S', 'nld', None)])
        self.eaf.remove_cv_entry('cv1', 'cve1')
        self.assertEqual(self.eaf.get_cv_entries('cv1'), {
            'cve2': ([('S', 'eng', 'stroke'), ('S', 'nld', None)], None)})
        self.assertRaises(KeyError, self.eaf.remove_cv_entry, 'cv2', 'c')
        self.assertRaises(KeyError, self.eaf.remove_cv_entry, 'cv1', 'c')

    def test_remove_cv_description(self):
        self.eaf.add_controlled_vocabulary('cv1')
        self.eaf.add_language('eng')
        self.eaf.add_language('nld')
        self.eaf.add_cv_description('cv1', 'eng', 'Gesture Phases')
        self.eaf.add_cv_description('cv1', 'nld', None)
        self.assertEqual(self.eaf.get_cv_descriptions('cv1'), [
            ('eng', 'Gesture Phases'), ('nld', None)])
        self.assertRaises(KeyError, self.eaf.get_cv_descriptions, 'cv2')

    def test_add_external_ref(self):
        self.eaf.add_external_ref('er1', 'ecv', 'location')
        self.eaf.add_external_ref('er2', 'lexen_id', 'location2')
        self.assertEqual(sorted(self.eaf.get_external_ref_names()),
                         ['er1', 'er2'])
        self.assertRaises(KeyError, self.eaf.add_external_ref, 'er1', 'a', '')

    def test_get_external_ref_names(self):
        self.assertEqual(sorted(self.eaf.get_external_ref_names()),
                         [])
        self.eaf.add_external_ref('er1', 'ecv', 'location')
        self.eaf.add_external_ref('er2', 'lexen_id', 'location2')
        self.assertEqual(sorted(self.eaf.get_external_ref_names()),
                         ['er1', 'er2'])

    def test_get_external_ref(self):
        self.eaf.add_external_ref('er1', 'ecv', 'location')
        self.eaf.add_external_ref('er2', 'lexen_id', 'location2')
        self.assertEqual(self.eaf.get_external_ref('er1'), ('ecv', 'location'))
        self.assertRaises(KeyError, self.eaf.get_external_ref, 'er3')

    def test_remove_external_ref(self):
        self.eaf.add_external_ref('er1', 'ecv', 'location')
        self.eaf.add_external_ref('er2', 'lexen_id', 'location2')
        self.eaf.remove_external_ref('er1')
        self.assertEqual(sorted(self.eaf.get_external_ref_names()), ['er2'])

    def test_add_lexicon_ref(self):
        self.eaf.add_lexicon_ref('id1', 'long name', 't1', 'url1', 'lid1',
                                 'lname1')
        self.eaf.add_lexicon_ref('id2', 'long name', 't2', 'url1', 'lid1',
                                 'lname1', 'dc1', 'dc1')
        self.assertEqual(sorted(self.eaf.get_lexicon_ref_names()),
                         ['id1', 'id2'])
        self.assertEqual(self.eaf.get_lexicon_ref('id1'), {
            'DATCAT_ID': None, 'NAME': 'long name', 'DATCAT_NAME': None, 'URL':
            'url1', 'LEX_REF_ID': 'id1', 'LEXICON_NAME': 'lname1', 'TYPE':
            't1', 'LEXICON_ID': 'lid1'})
        self.assertEqual(self.eaf.get_lexicon_ref('id2'), {
            'DATCAT_ID': 'dc1', 'NAME': 'long name', 'DATCAT_NAME': 'dc1',
            'URL': 'url1', 'LEX_REF_ID': 'id2', 'LEXICON_NAME': 'lname1',
            'TYPE': 't2', 'LEXICON_ID': 'lid1'})

    def test_remove_lexicon_ref(self):
        self.eaf.add_lexicon_ref('id1', 'long name', 't1', 'url1', 'lid1',
                                 'lname1')
        self.eaf.add_lexicon_ref('id2', 'long name', 't2', 'url1', 'lid1',
                                 'lname1', 'dc1', 'dc1')
        self.eaf.remove_lexicon_ref('id1')
        self.assertEqual(sorted(self.eaf.get_lexicon_ref_names()),
                         ['id2'])
        self.assertRaises(KeyError, self.eaf.remove_lexicon_ref, 'i')

    def test_get_lexicon_ref_names(self):
        self.assertEqual(sorted(self.eaf.get_lexicon_ref_names()), [])
        self.eaf.add_lexicon_ref('id1', 'long name', 't1', 'url1', 'lid1',
                                 'lname1')
        self.eaf.add_lexicon_ref('id2', 'long name', 't2', 'url1', 'lid1',
                                 'lname1', 'dc1', 'dc1')
        self.assertEqual(sorted(self.eaf.get_lexicon_ref_names()),
                         ['id1', 'id2'])

    def test_get_lexicon_ref(self):
        self.eaf.add_lexicon_ref('id1', 'long name', 't1', 'url1', 'lid1',
                                 'lname1')
        self.eaf.add_lexicon_ref('id2', 'long name', 't2', 'url1', 'lid1',
                                 'lname1', 'dc1', 'dc1')
        self.assertEqual(self.eaf.get_lexicon_ref('id1'), {
            'DATCAT_ID': None, 'NAME': 'long name', 'DATCAT_NAME': None, 'URL':
            'url1', 'LEX_REF_ID': 'id1', 'LEXICON_NAME': 'lname1', 'TYPE':
            't1', 'LEXICON_ID': 'lid1'})
        self.assertEqual(self.eaf.get_lexicon_ref('id2'), {
            'DATCAT_ID': 'dc1', 'NAME': 'long name', 'DATCAT_NAME': 'dc1',
            'URL': 'url1', 'LEX_REF_ID': 'id2', 'LEXICON_NAME': 'lname1',
            'TYPE': 't2', 'LEXICON_ID': 'lid1'})
        self.assertRaises(KeyError, self.eaf.get_lexicon_ref, 'id3')

    def test_to_file_to_eaf(self):
        x, filepath = tempfile.mkstemp()
        self.eaf = Eaf('./test/sample_2.8.eaf')

        self.eaf.to_file(filepath)

        with open('./test/EAFv2.8.xsd', 'r') as scheme_in:
            scheme_root = etree.XML(scheme_in.read())
        schema = etree.XMLSchema(scheme_root)
        xmlparser = etree.XMLParser(schema=schema)
        etree.parse(filepath, xmlparser)

    def test_parse_eaf(self):
        pass

    def test_eaf_from_chat(self):
        pass

if __name__ == '__main__':
    unittest.main()
