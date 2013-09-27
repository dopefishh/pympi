#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.etree import ElementTree
from time import localtime

class Eaf:
	"""Class to work with elan files"""
	
	html_escape_table = {'&':'&amp;', '"': '&quot;', '\'':'&apos;', '<':'&gt;', '>':'&lt;'}
	html_escape = lambda _, s: ''.join(c if c not in _.html_escape_table else _.html_escape_table[c] for c in s)

	#Document root data
#	annotationDocument = {}
	#File header
#	fileheader = ''
	#Header data
#	header = {}
#	media_descriptors, properties, linked_file_descriptors = [], [], []
	#Timeslot data {id -> time}
#	timeslots = {}
	#Tier data: {id -> (align, ref, attrib, num)}, 
	# align = {id -> (begin, end, value, svg_ref)}
	# ref   = {id -> (ref, value, previous, svg_ref)}
#	tiers = {}
	#Linguistic type data {id -> attrib}
#	linguistic_types = {}
	#Locale data [attrib]
#	locales = []
	#Constraint data {stereotype -> description}
#	constraints = {}
	#Controlled vocabulary data {id -> (description, entries)}
	# entry = {value -> description}
#	controlled_vocabularies = {}
	#External refs [id, type, value]
#	external_refs = []
	#Lexicon refs
#	lexicon_refs = []

	#new timeslot and annotation value
#	new_time, new_ann = 0, 0

###IO OPERATIONS
	def __init__(self, filePath=None):
		now = localtime()
		self.annotationDocument = {'AUTHOR':'Eaf.py', 'DATE':'%.4d-%.2d-%.2dT%.2d:%.2d:%.2d+%.2d:00' % (now[0], now[1], now[2], now[3], now[4], now[5], now[8]), 'VERSION':'2.7', 'FORMAT':'2.7'}
		self.fileheader = '<?xml version="1.0" encoding="UTF-8"?>\n'
		self.controlled_vocabularies, self.constraints, self.tiers, self.linguistic_types, self.header, self.timeslots = {}, {}, {}, {}, {}, {}
		self.external_refs, self.lexicon_refs, self.locales, self.media_descriptors, self.properties, self.linked_file_descriptors = [], [], [], [], [], []
		self.new_time, self.new_ann = 0, 0

		if filePath is None:
			self.addLinguisticType('default-lt', None)
		else:
			with open(filePath, 'r') as f:
				self.fileheader = f.readlines()[0]
			treeRoot = ElementTree.parse(filePath).getroot()
			self.annotationDocument.update(treeRoot.attrib)
			del(self.annotationDocument['{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation'])
			tierNumber = 0
			for elem in treeRoot:
				if elem.tag == 'HEADER':
					self.header.update(elem.attrib)
					for elem1 in elem:
						if elem1.tag == 'MEDIA_DESCRIPTOR':
							self.media_descriptors.append(elem1.attrib)
						elif elem1.tag == 'LINKED_FILE_DESCRIPTOR':
							self.linked_file_descriptors.append(elem1.attrib)
						elif elem1.tag == 'PROPERTY':
							self.properties.append((elem1.text, elem1.attrib))
				elif elem.tag == 'TIME_ORDER':
					for elem1 in elem:
						if int(elem1.attrib['TIME_SLOT_ID'][2:])>self.new_time:
							self.new_time = int(elem1.attrib['TIME_SLOT_ID'][2:])
						self.timeslots[elem1.attrib['TIME_SLOT_ID']] = int(elem1.attrib['TIME_VALUE'])
				elif elem.tag == 'TIER':
					tierId = elem.attrib['TIER_ID']
					align = {}
					ref = {}
					for elem1 in elem:
						if elem1.tag == 'ANNOTATION':
							for elem2 in elem1:
								if elem2.tag == 'ALIGNABLE_ANNOTATION':
									annotID = elem2.attrib['ANNOTATION_ID']
									if int(annotID[1:])>self.new_ann:
										self.new_ann = int(annotID[1:])
									annotStart = elem2.attrib['TIME_SLOT_REF1']
									annotEnd = elem2.attrib['TIME_SLOT_REF2']
									svg_ref = None if 'SVG_REF' not in elem2.attrib else elem2.attrib['SVG_REF']
									align[annotID] = (annotStart, annotEnd, '' if list(elem2)[0].text is None else self.html_escape(list(elem2)[0].text.encode('utf-8')), svg_ref)
								elif elem2.tag == 'REF_ANNOTATION':
									annotRef = elem2.attrib['ANNOTATION_REF']
									previous = None if 'PREVIOUS_ANNOTATION' not in elem2.attrib else elem2.attrib['PREVIOUS_ANNOTATION']
									annotId = elem2.attrib['ANNOTATION_ID']
									if int(annotID[1:])>self.new_ann:
										self.new_ann = int(annotID[1:])
									svg_ref = None if 'SVG_REF' not in elem2.attrib else elem2.attrib['SVG_REF']
									ref[annotId] = (annotRef, '' if list(elem2)[0].text is None else self.html_escape(list(elem2)[0].text.encode('utf-8')), previous, svg_ref) 
					self.tiers[tierId] = (align, ref, elem.attrib, tierNumber)
					tierNumber += 1
				elif elem.tag == 'LINGUISTIC_TYPE':
					self.linguistic_types[elem.attrib['LINGUISTIC_TYPE_ID']] = elem.attrib
				elif elem.tag == 'LOCALE':
					self.locales.append(elem.attrib)
				elif elem.tag == 'CONSTRAINT':
					self.constraints[elem.attrib['STEREOTYPE']] = elem.attrib['DESCRIPTION']
				elif elem.tag == 'CONTROLLED_VOCABULARY':
					vcId = elem.attrib['CV_ID']
					descr = elem.attrib['DESCRIPTION']
					entries = {}
					for elem1 in elem:
						if elem1.tag == 'CV_ENTRY':
							entries[elem1.text] = elem1.attrib['DESCRIPTION']
					self.controlled_vocabularies[vcId] = (descr, entries)
				elif elem.tag == 'LEXICON_REF':
					self.lexicon_refs.append(elem.attrib)
				elif elem.tag == 'EXTERNAL_REF':
					self.external_refs.append((elem.attrib['EXT_REF_ID'], elem.attrib['TYPE'], elem.attrib['VALUE']))
	
	def tofile(self, filePath):
		xmlFormat = lambda k, d: '' if d[k] is None else '%s="%s"' % (k, d[k])
		xmlPrint = lambda t, x, c: '<%s %s%s>' % (t, ' '.join([xmlFormat(key, x) for key in sorted(x.keys())]), c)
		tabs = 0
		with open(filePath, 'w') as f:
			f.write('%s%s' % ('    '*tabs, self.fileheader))
			f.write('%s<ANNOTATION_DOCUMENT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.mpi.nl/tools/elan/EAFv2.6.xsd"%s\n' % ('    '*tabs, xmlPrint('', self.annotationDocument, '')[1:]))
			#HEADER
			tabs += 1
			f.write('%s%s\n' % ('    '*tabs, xmlPrint('HEADER', self.header, '')))
			tabs += 1
			for m in self.media_descriptors:
				f.write('%s%s\n' % ('    '*tabs, xmlPrint('MEDIA_DESCRIPTOR', m, '/')))
			for m in self.properties:
				f.write('%s%s%s</PROPERTY>\n' % ('    '*tabs, xmlPrint('PROPERTY', m[1], ''), m[0]))
			for m in self.linked_file_descriptors:
				f.write('%s%s\n' % ('    '*tabs, xmlPrint('LINKED_FILE_DESCRIPTOR', m, '/')))
			tabs -= 1
			f.write('%s</HEADER>\n' % ('    '*tabs))
			#TIMESLOTS
			f.write('%s<TIME_ORDER>\n' % ('    '*tabs))
			tabs += 1
			for m in sorted(self.timeslots.keys(), key=lambda x: int(x[2:])):
				f.write('%s<TIME_SLOT TIME_SLOT_ID="%s" TIME_VALUE="%d"/>\n' % ('    '*tabs, m, self.timeslots[m]))
			tabs -= 1
			f.write('%s</TIME_ORDER>\n' % ('    '*tabs))
			#TIERS
			for m in sorted(self.tiers.keys(), key=lambda k:self.tiers[k][3]):
				curtier = self.tiers[m]
				if len(curtier[0]) == 0 and len(curtier[1]) == 0:
					f.write('%s%s\n' % ('    '*tabs, xmlPrint('TIER', (self.tiers[m])[2], '/')))
					continue
				f.write('%s%s\n' % ('    '*tabs, xmlPrint('TIER', (self.tiers[m])[2], '')))
				tabs += 1
				#ALIGNABLE ANNOTATIONS
				for n in curtier[0].keys():
					f.write('%s<ANNOTATION>\n' % ('    '*tabs))
					tabs += 1
					curann = curtier[0][n]
					f.write('%s<ALIGNABLE_ANNOTATION ANNOTATION_ID="%s" TIME_SLOT_REF1="%s" TIME_SLOT_REF2="%s"' % ('    '*tabs, n, curann[0], curann[1]))
					if curann[3] is not None: f.write('SVG_REF="%s"' % curann[3])
					f.write('>\n%s<ANNOTATION_VALUE>%s</ANNOTATION_VALUE>\n%s</ALIGNABLE_ANNOTATION>\n%s</ANNOTATION>\n' % ('    '*(tabs+1), curann[2], '    '*tabs, '    '*(tabs-1)))
					tabs -= 1
				#REF ANNOTATIONS
				for n in curtier[1].keys():
					f.write('%s<ANNOTATION>\n' % ('    '*tabs))
					tabs += 1
					curann = curtier[1][n]
					f.write('%s<REF_ANNOTATION ANNOTATION_ID="%s" ANNOTATION_REF="%s" ' % ('    '*tabs, n, curann[0]))
					if curann[1] is not None:
						f.write('PREVIOUS_ANNOTATION="%s" ' % curann[2])
					if curann[3] is not None:
						f.write('EXT_REF="%s"' % curann[3])
					f.write('>\n%s<ANNOTATION_VALUE>%s</ANNOTATION_VALUE>\n%s</REF_ANNOTATION>\n%s</ANNOTATION\n' % ('    '*(tabs+1), curann[1], '    '*tabs, '    '*(tabs-1)))
					tabs -= 1
				tabs -= 1
				f.write('%s</TIER>\n' % ('    '*tabs))
			#LINGUISTIC TYPES
			for m in self.linguistic_types:
				f.write('%s%s\n' % ('    '*tabs, xmlPrint('LINGUISTIC_TYPE', self.linguistic_types[m], '/')))
			#LOCALES
			for m in self.locales:
				f.write('%s%s\n' % ('    '*tabs, xmlPrint('LOCALE', m, '/')))
			#CONSTRAINTS
			for m in self.constraints:
				f.write('%s<CONSTRAINT STEREOTYPE="%s" DESCRIPTION="%s"/>\n' % ('    '*tabs, m, self.constraints[m]))
			#CONTROLLED VOCABULARIES
			for m in self.controlled_vocabularies.keys():
				curvoc = self.controlled_vocabularies[m]
				f.write('%s<CONTROLLED_VOCABULARY CV_ID="%s" DESCRIPTION="%s">\n' % ('    '*tabs, m, curvoc[0]))
				tabs += 1
				for n in curvoc[1].keys():
					f.write('%s<CV_ENTRY DESCRIPTION="%s">%s</CV_ENTRY>\n' % ('    '*tabs, curvoc[1][n], n))
				tabs -= 1
				f.write('%s</CONTROLLED_VOCABULARY>\n' % '    '*tabs)
			#EXTERNAL REFS
			for m in self.external_refs:
				f.write('%s<EXTERNAL_REF EXT_REF_ID="%s" TYPE="%s" VALUE="%s"/>\n' % ('    '*tabs, m[0], m[1], m[2]))
			#LEXICON REFS
			for m in self.lexicon_refs:
				f.write('%s%s\n' % ('    '*tabs, xmlPrint('LEXICON_REF', m, '/')))
			f.write('</ANNOTATION_DOCUMENT>')

	def toTextGrid(self, filePath, excludedTiers=[]):
		"""Converts the object to praat's TextGrid format and leaves the excludedTiers(optional) behind. (warning some data is lost because praat can hold less datatypes)"""
		try:
			from Praat import TextGrid
		except ImportError:
			print 'Please install the TextGrid module from the TextGrid.py file found at https://github.com/dopefishh/pympi'
			exit()
		tgout = TextGrid()
		for tier in [a for a in self.tiers.iterkeys() if a not in excludedTiers]:
			currentTier = tgout.addTier(tier)
			for interval in self.getAnnotationDataForTier(tier):
				currentTier.addInterval(interval[0]/1000.0, interval[1]/1000.0, interval[2])
		tgout.tofile(filePath)

###MEDIA OPERATIONS
	def getVideo(self):
		"""Gives a list of all video files"""
		return [m for m in self.media_descriptors if 'video' in m['MIME_TYPE']]

	def getAudio(self):
		"""Gives a list of all audio files"""
		return [m for m in self.media_descriptors if 'video' in m['MIME_TYPE']]

###TIER OPERATIONS
	def addTier(self, idTier, tierType='default-lt', parent=None, defaultLocale=None, participant=None, annotator=None):
		"""Adds a tier giving a id and type and optional extra data"""
		self.tiers[idTier] = ({}, {}, {'TIER_ID':idTier, 'LINGUISTIC_TYPE_REF':tierType, 'PARENT_REF':parent, 'PARTICIPANT':participant, 'DEFAULT_LOCALE':defaultLocale, 'ANNOTATOR':annotator}, len(self.tiers))
	
	def removeTier(self, idTier):
		"""Removes a tier by id, if it doesn't exist nothing happens"""
		try:
			del(self.tiers[idTier])
			self.cleanTimeSlots()
		except:	pass

	def getTierNames(self):
		"""Returns a list of tiernames"""
		return self.tiers.keys()
	
	def getIndexOfTier(self, idTier):
		"""Returns the index of a given tier, -1 if tier doesn't exist"""
		return -1 if idTier not in self.tiers else self.tiers[3]

	def getParameterDictForTier(self, idTier):
		"""Returns a dictionary with all the parameters of the given tier, None if tier doesn't exist"""
		try:
			return self.tiers[idTier][2]
		except KeyError:
			return None

	def getIndexOfLastTier(self):
		"""Gives the index of the last tier"""
		return len(self.tiers)-1

	def appendRefAnnotationToTier(self, idTier, idAnn, strAnn, annRef, prevAnn=None, svg_ref=None):
		"""Adds a ref annotation to the given tier"""
		try:
			self.tiers[idTier][1][idAnn] = (annRef, strAnn, prevAnn, svg_ref)
		except KeyError: pass

	def childTiersFor(self, idTier):
		"""Returns a list of all the children of the given tier, None if the tier doesn't exist"""
		try:
			return [m for m in self.tiers.iterkeys() if 'PARENT_REF' in self.tiers[m][2] and self.tiers[m][2]['PARENT_REF']==idTier]
		except KeyError:
			return None

	def getLinguisticTypeForTier(self, idTier):
		"""Returns the locale of the given tier, '' if none and None if tier doesn't exist"""
		try:
			return self.tiers[idTier][2]['LINGUISTIC_TYPE_REF']
		except KeyError:
			return None

	def getLocaleForTier(self, idTier):
		"""Returns the locale of the given tier, '' if none and None if tier doesn't exist"""
		try:
			tier = self.tiers[idTier]
			try:
				return tier[2]['DEFAULT_LOCALE']
			except KeyError:
				return ''
		except KeyError:
			return None

	def getParticipantForTier(self, idTier):
		"""Returns the participant for the given tier, '' if none and None if tier doesn't exist"""
		try:
			tier = self.tiers[idTier]
			return '' if 'PARTICIPANT' not in tier[2] else tier[2]['PARTICIPANT']
		except KeyError:
			return None

###ANNOTATION OPERATIONS
	def getAnnotationDataForTier(self, idTier):
		"""Returns the annotation data for the given tier in the format: (start, end, value)  None if the tier doesn't exist"""
		try:
			a = self.tiers[idTier][0]
			return [(self.timeslots[a[b][0]], self.timeslots[a[b][1]], a[b][2]) for b in a.iterkeys()]
		except KeyError:
			return None

	def getAnnotationDataAtTime(self, idTier, time):
		"""Returns an annotation at time in the given tier, None if the tier doesn't exist"""
		try:
			anns = self.tiers[idTier][0]
			return sorted([(self.timeslots[m[0]], self.timeslots[m[1]], m[2]) for m in anns.itervalues() if self.timeslots[m[0]]<=time and self.timeslots[m[1]]>=time])
		except KeyError:
			return None

	def getAnnotationDatasBetweenTimes(self, idTier, start, end):
		"""Returns all the annotations overlapping with the given interval in the given tier, None if the tier doesn't exist"""
		try:
			anns = self.tiers[idTier][0]
			return sorted([(self.timeslots[m[0]], self.timeslots[m[1]], m[2]) for m in anns.itervalues() if self.timeslots[m[1]]>=start and self.timeslots[m[0]]<=end])
		except KeyError:
			return None

	def removeAllAnnotationsFromTier(self, idTier):
		"""Removes all the annotations from the given tier, when the tier doesn't exist nothing happens"""
		try:
			self.tiers[idTier][0], self.tiers[idTier][1] = {}, {}
			self.cleanTimeSlots()
		except KeyError: pass
	
	def updatePrevAnnotationForAnnotation(self, idTier, idAnn, idPrevAnn=None):
		"""Updates the previous annotation value in an annotation in the given tier, nothing happens if they don't exist"""
		try:
			self.tiers[idTier][1][idAnn][2] = idPrevAnn
		except KeyError: pass

	def insertAnnotation(self, idTier, start, end, value='', svg_ref=None):
		"""Add an annotation in the given tier, if the tiers doesn't exist nothing happens"""
		try:
			startTs, endTs = self.generateTsId(), self.generateTsId()
			self.timeslots[startTs], self.timeslots[endTs] = start, end
			self.tiers[idTier][0][self.generateAnnotationId()] = (startTs, endTs, value, svg_ref)
		except KeyError: pass

	def getRefAnnotationDataForTier(self, idTier):
		"""Returns all the ref annotation for a given tier in the form: (id->(ref, value, prev, svg_ref), None if the tier doesn't exist"""
		try:
			return self.tiers[idTier][1]
		except KeyError:
			return None

###CONTROLLED VOCABULARY OPERATIONS
	def addControlledVocabularyToLinguisticType(self, linguisticType, cvId):
		"""Adds a controlled vocabulary to a linguistic type, when the lingtype doesn't exist nothing happens"""
		try:
			self.linguistic_types[linguisticType]['CONTROLLED_VOCABULARY_REF'] = cvId
		except KeyError: pass

	def removeControlledVocabulary(self, cv):
		"""Removes a controlled vocabulary, when the cv doesn't exist nothing happens"""
		try:
			del(self.controlled_vocabularies[cv])
		except KeyError: pass

###HELPER FUNCTIONS
	def generateAnnotationId(self):
		"""Helper function to generate the newest annotation id"""
		self.new_ann += 1
		return 'a%d' % (self.new_ann) 

	def generateTsId(self):
		"""Helper function te generate the newest timeslot id"""
		self.new_time += 1
		return 'ts%d' % (self.new_time)

	def cleanTimeSlots(self):
		"""Removes all the unused timeslots"""
		tsInTier = []
		for t in self.tiers.itervalues():
			for an in t[0].itervalues():
				del(self.timeslots[an[0]])
				del(self.timeslots[an[1]])
	
###GAP AND OVERLAP FUNCTIONS
	def glueAnnotationsInTier(self, tier, tierName=None, treshhold=30):
		"""Glues all the continues annotations together"""
		if tierName is None: tierName = '%s_glued' % tier
		self.removeTier(tierName)
		self.addTier(tierName)

		tierData = sorted(self.getAnnotationDataForTier(tier), key=lambda a: a[0])
		currentAnn = None
		for i in xrange(0, len(tierData)):
			if currentAnn is None:
				currentAnn = (tierData[i][0], tierData[i][1], tierData[i][2])
			elif tierData[i][0]-currentAnn[1]<treshhold:
				currentAnn = (currentAnn[0], tierData[i][1], '%s_%s' % (currentAnn[2], tierData[i][2]))
			else:
				self.insertAnnotation(tierName, currentAnn[0], currentAnn[1], currentAnn[2])
				currentAnn = tierData[i]
		if currentAnn is not None:
			self.insertAnnotation(tierName, currentAnn[0], tierData[len(tierData)-1][1], currentAnn[2])

	def getFullTimeInterval(self):
		"""Returns a tuple (start, end) of the full time frame. optional tier"""
		return (min(self.timeslots.itervalues()), max(self.timeslots.itervalues()))

	def createGapsAndOverlapsTier(self, tier1, tier2, tierName=None, tierType=None):
		"""Creates a tier out of the gaps and overlap between two tiers, returns the fto data"""
		if tierName is None:
			tierName = '%s_%s_go' % (tier1, tier2)
		if tierType is None:
			tierType = self.linguistic_types.keys()[0]
		self.removeTier(tierName)
		self.addTier(tierName, tierType)
		ftos = self.getGapsAndOverlapsDuration(tier1, tier2)
		for fto in ftos:
			self.insertAnnotation(tierName, fto[1], fto[2], fto[0])
		return ftos

	def getGapsAndOverlapsDuration(self, tier1, tier2, progressbar=False):
		"""Gives the gaps and overlaps between tiers in the format: (type, start, end), None if one of the tiers don't exist."""
		if tier1 not in self.tiers or tier2 not in self.tiers: return None
		spkr1anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]]) for a in self.tiers[tier1][0].values())
		spkr2anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]]) for a in self.tiers[tier2][0].values())
		line1 = []
		isin = lambda x, lst: False if len([i for i in lst if i[0]<=x and i[1]>=x])==0 else True
		minmax = (min(spkr1anns[0][0], spkr2anns[0][0]), max(spkr1anns[-1][1], spkr2anns[-1][1]))
		last = (1, minmax[0])
		lastP = 0
		for ts in xrange(*minmax):
			in1, in2 = isin(ts, spkr1anns), isin(ts, spkr2anns)
			if in1 and in2:		#Both speaking
				if last[0] == 'B': continue
				ty = 'B'
			elif in1:			#Only 1 speaking
				if last[0] == '1': continue
				ty = '2'
			elif in2:			#Only 2 speaking
				if last[0] == '2': continue
				ty = '2'
			else:				#None speaking
				if last[0] == 'N': continue
				ty = 'N'
			line1.append( (last[0], last[1], ts) )
			last = (ty, ts)
			if progressbar and int((ts*1.0/minmax[1])*100) > lastP:
				lastP = int((ts*1.0/minmax[1])*100)
				print '%d%%' % lastP
		line1.append((last[0], last[1], minmax[1]))
		ftos = []
		for i in xrange(len(line1)):
			if line1[i][0] == 'N':
				if i!=0 and i<len(line1)-1 and line1[i-1][0] != line1[i+1][0]:
					ftos.append(('G12_%s_%s' % (tier1, tier2) if line1[i-1][0]=='1' else 'G21_%s_%s' % (tier2, tier1), line1[i][1], line1[i][2]))
				else:
					ftos.append(('P_%s' % tier1 if line1[i-1][0]=='1' else tier2, line1[i][1], line1[i][2]))
			elif line1[i][0] == 'B':
				if i!=0 and i<len(line1)-1 and line1[i-1][0] != line1[i+1][0]:
					ftos.append(('O12_%s_%s' % (tier1, tier2)  if line1[i-1][0] else 'O21_%s_%s' % (tier2, tier1), line1[i][1], line1[i][2]))
				else:
					ftos.append(('B_%s' % tier1 if line1[i-1][0]=='1' else tier2, line1[i][1], line1[i][2]))
		return ftos

###LINGUISTIC TYPE FUNCTIONS
	def createControlledVocabulary(self, cvEntries, cvId, description=''):
		"""Adds a controlled vocabulary with the given cvEntiries{value->description}, id and optional description"""
		self.controlledvocabularies[cvId] = (description, cvEntries)

	def getTierIdsForLinguisticType(self, lingType, parent=None):
		"""Returns all the tier id's with the given linguistic type"""
		return [t for t in self.tiers.iterkeys() if self.tiers[t][2]['LINGUISTIC_TYPE_REF']==lingType and (parent is None or self.tiers[t][2]['PARENT_REF']==parent)]

	def removeLinguisticType(self, lingType):
		"""Removes a linguistic type, if the lingtype doesn't exist nothing happens"""
		try:
			del(self.linguistic_types[lingType])
		except KeyError: pass

	def addLinguisticType(self, lingtype, constraints, timealignable=False, graphicreferences=False, extref=None):
		"""Adds a linguistic type"""
		self.linguistic_types[lingtype] = {'LINGUISTIC_TYPE_ID':lingtype, 'TIME_ALIGNABLE':str(timealignable).lower(), 'GRAPHIC_REFERENCES':str(graphicreferences).lower(), 'CONSTRAINTS':constraints}
		if extref is not None:
			self.linguistic_types[lingtype]['EXT_REF'] = extref

	def getConstraintForLinguisticType(self, lingid):
		"""Returns the constraints for the linguistic type. None if the type doesn't exist"""
		try:
			return self.linguistic_types[lingid]['CONSTRAINTS']
		except KeyError:
			return None

	def getParameterDictForLinguisticType(self, lingid):
		"""Returns all the info of a lingtype in a dictionary, None if type doesn't exist"""
		try:
			return self.linguistic_types[lingid]
		except KeyError:
			return None

	def hasLinguisticType(self, lingtype):
		"""Returns if the given type is in the linguistic types"""
		return lingtype in self.linguistic_types

	def linguisticTypeIsTimeAlignable(self, lingid):
		"""Returns if the given type is time alignable, None if the type doesn't exist"""
		try:
			return self.linguistic_types[lingid]['TIME_ALIGNABLE']
		except KeyError:
			return None
