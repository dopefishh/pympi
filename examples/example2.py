#!/bin/env python
# -*- coding: utf-8 -*-

import pympi    # Import pympi to work with elan files

# Specify the file path
elan_file_path = '/home/frobnicator/corpus/sign/file1.eaf'

# Initialize the elan file
eaf = pympi.Elan.Eaf(elan_file_path)
# Merge both hands for speaker 1
eaf.merge_tiers(['spk1L', 'spk1R'], 'spk1', 80)
# Merge both hands for speaker 2
eaf.merge_tiers(['spk2L', 'spk2R'], 'spk2', 80)
# Create gaps and overlaps tier called ftos with a maximum length of 5000ms and
# using the fast method
eaf.create_gaps_and_overlaps_tier('spk1', 'spk2', 'ftos', 5000, True)
# Write the results to file with the _fto suffix
eaf.to_file(elan_file_path.replace('.eaf', '_fto.eaf'))
