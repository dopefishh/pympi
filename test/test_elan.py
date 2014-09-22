#!/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pympi import Eaf


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

    def test_get_linked_files(self):
        self.eaf.add_linked_file('/some/file/path/test.wav')
        self.eaf.add_linked_file('/some/file/path/test.mpg', './test.mpg',
                                 time_origin=5, ex_from='ef')
        self.assertEqual(self.eaf.get_linked_files(),
                         self.eaf.media_descriptors)

    def test_add_tier(self):
        self.assertEqual(len(self.eaf.tiers), 1)
        self.eaf.add_tier('tier1', 'default-lt')
        self.assertEqual(len(self.eaf.tiers), 2)
        self.assertEqual(self.eaf.tiers['tier1'][2]['LINGUISTIC_TYPE_REF'],
                         'default-lt')

        self.eaf.add_tier('tier2', 'non-existing-linguistic-type')
        self.assertEqual(len(self.eaf.tiers), 3)
        self.assertEqual(self.eaf.tiers['tier2'][2]['LINGUISTIC_TYPE_REF'],
                         'default-lt')
        self.assertEqual(['default', 'tier1', 'tier2'], self.eaf.tiers.keys())

        self.eaf.add_tier('tier3', None, 'tier1', 'en', 'person', 'person2')
        self.assertEqual(self.eaf.tiers['tier3'][2], {
            'ANNOTATOR': 'person2', 'DEFAULT_LOCALE': 'en',
            'LINGUISTIC_TYPE_REF': 'default-lt', 'PARENT_REF': 'tier1',
            'PARTICIPANT': 'person', 'TIER_ID': 'tier3'})

        self.eaf.add_tier('tier4', tier_dict={
            'ANNOTATOR': 'person2', 'DEFAULT_LOCALE': 'en',
            'LINGUISTIC_TYPE_REF': 'default-lt', 'PARENT_REF': 'tier1',
            'PARTICIPANT': 'person', 'TIER_ID': 'tier4'})
        self.assertEqual(self.eaf.tiers['tier4'][2], {
            'ANNOTATOR': 'person2', 'DEFAULT_LOCALE': 'en',
            'LINGUISTIC_TYPE_REF': 'default-lt', 'PARENT_REF': 'tier1',
            'PARTICIPANT': 'person', 'TIER_ID': 'tier4'})

        for tier in ['tier1', 'tier2', 'tier3']:
            self.assertEqual(self.eaf.tiers[tier][0], {})
            self.assertEqual(self.eaf.tiers[tier][1], {})

    def test_remove_tiers(self):
    #    self.eaf.add_tier('tier1')
    #    self.eaf.add_tier('tier2')
    #    self.eaf.add_tier('tier3')
    #    self.eaf.add_tier('tier4')
        pass


    def test_copy_tier(self):
        pass

    def test_extract(self):
        pass

    def test_to_textgrid(self):
        pass

    def test_to_file(self):
        pass


if __name__ == '__main__':
    unittest.main()
