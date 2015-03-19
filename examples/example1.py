#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob     # Import glob to easily loop over files
import pympi    # Import pympi to work with elan files
import string   # Import string to get the punctuation data

# Define some variables for later use
corpus_root = '/home/frobnicator/corpora/corpus_1'
output_file = '{}/word_frequencies.txt'.format(corpus_root)
ort_tier_names = ['spkA', 'spkB', 'spkC']

# Initialize the frequency dictionary
frequency_dict = {}

# Loop over all elan files the corpusroot subdirectory called eaf
for file_path in glob.glob('{}/eaf/*.eaf'.format(corpus_root)):
    # Initialize the elan file
    eafob = pympi.Elan.Eaf(file_path)
    # Loop over all the defined tiers that contain orthography
    for ort_tier in ort_tier_names:
        # If the tier is not present in the elan file spew an error and
        # continue. This is done to avoid possible KeyErrors
        if ort_tier not in eafob.get_tier_names():
            print 'WARNING!!!'
            print 'One of the ortography tiers is not present in the elan file'
            print 'namely: {}. skipping this one...'.format(ort_tier)
        # If the tier is present we can loop through the annotation data
        else:
            for annotation in eafob.get_annotation_data_for_tier(ort_tier):
                # We are only interested in the utterance
                utterance = annotation[2]
                # Split, by default, splits on whitespace thus separating words
                words = utterance.split()
                # For every word increment the frequency
                for word in words:
                    # Remove the possible punctuation
                    for char in string.punctuation:
                        word = word.replace(char, '')
                    # Convert to lowercase
                    word = word.lower()
                    # Increment the frequency, using the get method we can
                    # avoid KeyErrors and make sure the word is added when it
                    # wasn't present in the frequency dictionary
                    frequency_dict[word] = frequency_dict.get(word, 0) + 1

# Open an output file to write the data to
with open(output_file, 'w') as output_file:
    # Loop throught the words with their frequencies, we do this sorted because
    # the file will then be more easily searchable
    for word, frequency in sorted(frequency_dict.items()):
        # We write the output separated by tabs
        output_file.write('{}\t{}\n'.format(word, frequency))
