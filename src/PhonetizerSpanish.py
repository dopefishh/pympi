#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to phonetize spanish words and place them in a optional dictionary
wordToPron.acronymMap : Dictionary of single letters and their pronunciation
"""

from unicodedata import category as cat, normalize as norm
from re import sub
import codecs
import pdb

#The map for individual letter pronunciations
acronymMap = {	'A':'a', 'B':'be', 'C':'Te', 'D':'de', 'E':'e', 'F':'efe', 
	 			'G':'xe', 'H':'atSe', 'I':'i', 'J':'xota', 'K':'ka', 
				'L':'ele', 'M':'eme', 'N':'ene', 'O':'o', 'P':'p', 
				'Q':'ku', 'R':'erre', 'S':'ese', 'T':'te', 'U':'u', 
				'V':'ubu', 'W':'ubudoble', 'X':'ekis', 'Y':'igriega', 'Z':'Teta'}

#Special annotation characters for truncation, foreign language and non spoken sounds
annotationSpecials = '[]<>()&'

def wordToPron(word, dictionary=None):
	"""	Spanish word to phoneme mapping the word should be in Unicode ex. u'sabes', the dictionary is optional it could be used for fast lookup"""
	#Remove all the punctuation except the standard annotation items
	word = sub('\(.*\)', '', ''.join(ch for ch in word if cat(ch).startswith('L') or ch in annotationSpecials))

	#Count uppercases to categorize the word
	uppercases = len([ch for ch in word if cat(ch).startswith('Lu')])
		
	if not word:
		print "Empty word!"
		return "#"	

	#Check sounds and foreign language. ex &nth&, [langEnglish]Hello, <ehh>
	if word[0] =='&' or word[0]=='<' or '[lang' in word:
		print 'Non word character or foreign language, please add manually: ' + word
		exit()
	
	#Allocate the map
	phoneMap = []
	
	#Acronyms
	if uppercases>1:
		phoneMap = [acronymMap[i] for i in word]
	#Normal words
	else:
		originalWord = word
		word = word.lower()
		skip = 0 
		for i in xrange(len(word)):
			ch = word[i]
			if skip>0: 
				skip -= 1
				continue
			if ch=='c':
				if i+1<len(word) and word[i+1] in 'ei':
					phoneMap.append('T')
				elif i+1<len(word) and word[i+1]=='h':
					phoneMap.append('tS')
					skip += 1 
				else: phoneMap.append('k')
			elif ch=='g':
				if i+1<len(word) and word[i+1]=='ü'.decode('utf-8'):
					phoneMap.append('gu')
					skip += 1		  
				elif i+1<len(word) and word[i+1]=='u':
					phoneMap.append('g')
					skip += 1 
				elif i+1<len(word) and word[i+1] in 'ei':
					phoneMap.append('x')
			elif ch=='j':
				phoneMap.append('x')
			elif ch=='ñ'.decode('utf-8'):
				phoneMap.append('J')
			elif ch=='l':
				if i+1<len(word) and word[i+1]=='l':
					phoneMap.append('jj')
					skip += 1 
				else:
					phoneMap.append(ch)
			elif ch=='q':
				if i+1<len(word) and word[i+1]=='u':
					phoneMap.append('k')
					skip += 1 
				else:
					print 'warning q without proceeding u'
					phoneMap.append('k')
			elif ch=='r' and i is 0 or word[i-1] in 'nlsm': 
				phoneMap.append('r')
			elif ch=='r':
				phoneMap.append('r')
			elif ch=='u': 
				phoneMap.append('u')
			elif ch=='v' or ch=='w': 
				phoneMap.append('b')
			elif ch=='y': 
				phoneMap.append('jj')
			elif ch=='z': 
				phoneMap.append('T')
			else: 
				phoneMap.append(str(norm('NFKD', ch).encode('ascii', 'ignore')))
		word = originalWord
	
	#Rejoin all the phonemes
	phoneMap = ''.join(phoneMap)
	
	#If a dictionary is given add it to the dictionary	
	if dictionary is not None:
		with codecs.open(dictionary, 'a', 'utf-8') as f:
			f.write('%s\t%s\n' % (word, phoneMap))
			print word + ' added...'
	return phoneMap
