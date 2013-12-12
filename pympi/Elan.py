#!/usr/bin/env python
# -*- coding: utf-8 -*-

import EafIO
from time import localtime
import warnings

class Eaf:
	"""Class to work with elan files
	Class variables
	---------------
	annotationDocument      - Dict of all annotationdocument TAG entries.
	fileheader              - String of the header(xml version etc).
	header                  - Dict of the header TAG entries.
	media_descriptors       - List of all linked files: [{attrib}]
	properties              - List of all properties: [(value, {attrib})]
	linked_file_descriptors - List of all secondary linked files: [{attrib}].
	timeslots               - Timeslot data: {TimslotID -> time(ms)}
	tiers                   - Tier data: {TierName -> (alignedAnnotations, referenceAnnotations, attributes, ordinal)}, 
								alignedAnnotations    : [{annotationId -> (beginTs, endTs, value, svg_ref)}]
								referenceAnnotations  : [{annotationId -> (reference, value, previous, svg_ref)}]
	linguistic_types        - Linguistic type data [{id -> attrib}]
	locales                 - List of locale data: [{attrib}]
	constraints             - Constraint data: {stereotype -> description}
	controlled_vocabularies - Controlled vocabulary data: {id -> (description, entries, ext_ref)}
								entry: {description -> (attrib, value)}
	external refs           - External refs [extref]
								extref: [id, type, value]
	lexicon_refs            - Lexicon refs [{attribs}]
	"""

###IO OPERATIONS
	def __init__(self, filePath=None, author='Elan.py', elan_new=True):
		"""Constructor, builds an elan object from file(if given) or an empty one, if elan_new is off then a true minimal file is created if it's on then default entries are added"""
		self.naiveGenAnn = False
		self.naiveGenTS = False
		now = localtime()
		self.annotationDocument = {
				'AUTHOR':author, 
				'DATE':'%.4d-%.2d-%.2dT%.2d:%.2d:%.2d+%.2d:00' % (now[0], now[1], now[2], now[3], now[4], now[5], now[8]), 
				'VERSION':'2.7', 
				'FORMAT':'2.7', 
				'xmlns:xsi':'http://www.w3.org/2001/XMLSchema-instance', 
				'xsi:noNamespaceSchemaLocation':'http://www.mpi.nl/tools/elan/EAFv2.7.xsd'}
		self.controlled_vocabularies, self.constraints, self.tiers, self.linguistic_types, self.header, self.timeslots = {}, {}, {}, {}, {}, {}
		self.external_refs, self.lexicon_refs, self.locales, self.media_descriptors, self.properties, self.linked_file_descriptors = [], [], [], [], [], []
		self.new_time, self.new_ann = 0, 0

		if filePath is None:
			self.addLinguisticType('default-lt', None)
			if elan_new:
				self.constraints["Time_Subdivision"] = "Time subdivision of parent annotation's time interval, no time gaps allowed within this interval"
				self.constraints["Symbolic_Subdivision"] = "Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered"
				self.constraints["Symbolic_Association"] = "1-1 association with a parent annotation"
				self.constraints["Included_In"] = "Time alignable annotations within the parent annotation's time interval, gaps are allowed"
				self.properties.append(('0', {'NAME': 'lastUsedAnnotation'}))
		else:
			EafIO.parseEaf(filePath, self)

	def tofile(self, filePath):
		"""Exports the eaf object to a file given by the path"""
		EafIO.toEaf(filePath, self)

	def toTextGrid(self, filePath, excludedTiers=[]):
		"""Converts the object to praat's TextGrid format and leaves the excludedTiers(optional) behind. returns 0 when succesfull"""
		try:
			from pympi.Praat import TextGrid
		except ImportError:
			warnings.warn('Please install the pympi.Praat module from the pympi module found at https://github.com/dopefishh/pympi')
			return 1
		tgout = TextGrid()
		for tier in [a for a in self.tiers.iterkeys() if a not in excludedTiers]:
			currentTier = tgout.addTier(tier)
			for interval in self.getAnnotationDataForTier(tier):
				currentTier.addInterval(interval[0]/1000.0, interval[1]/1000.0, interval[2])
		tgout.tofile(filePath)
		return 0

	def extract(self, start, end):
		"""Extracts a timeframe from the eaf file and returns it"""
		from copy import deepcopy
		eafOut = deepcopy(self)
		for tier in eafOut.tiers.itervalues():
			rems = []
			for ann in tier[0].iterkeys():
				if eafOut.timeslots[tier[0][ann][1]] > end or eafOut.timeslots[tier[0][ann][0]] < start:
					rems.append(ann)
			for r in rems:
				del tier[0][r]
		return eafOut

###MEDIA OPERATIONS
	def getTimeSeries(self):
		"""Gives a list of all time secondary linked txt files"""
		return [m for m in self.linked_file_descriptors if 'text/plain' in m['MIME_TYPE']]
	
	def getLinkedFiles(self):
		"""Gives a list of all media files"""
		return self.media_descriptors

	def addLinkedFile(self, filePath, relpath=None, mimetype=None, time_origin=None, exfrom=None):
		"""Adds the linked file, if the mimetype is not given it tries to find it(only words for mpg and wav"""
		if mimetype is None:
			mimes = {'wav':'audio/x-wav', 'mpg':'video/mpeg', 'mpeg':'video/mpg'}
			mimetype = mimes[filePath.split('.')[-1]]
		self.media_descriptors.append({'MEDIA_URL':filepath, 'RELATIVE_MEDIA_URL':relpath, 'MIME_TYPE':mimetype, 'TIME_ORIGIN':time_origin, 'EXTRACTED_FROM':exfrom})

###TIER OPERATIONS
	def copyTier(self, eafObj, tierName):
		"""Copies the tier from this object to the given object, if the tier is present it removes it. Returns 0 if succesfull"""
		eafObj.removeTier(tierName)
		try:
			t = self.tiers[tierName][3]
			eafObj.addTier(tierName, tierDict=self.tiers[tierName][3])
			for ann in self.getAnnotationDataForTier(tierName):
				eafObj.insertAnnotation(tierName, ann[0], ann[1], ann[2])
			return 0
		except KeyError:
			warnings.warn('copyTier: Tier non existent!')
			return 1

	def addTier(self, tierId, ling='default-lt', parent=None, locale=None, part=None, ann=None, tierDict=None):
		"""Adds a tier giving a id and type and optional extra data"""
		if tierDict is None:
			self.tiers[tierId] = ({}, {}, {'TIER_ID':tierId, 'LINGUISTIC_TYPE_REF':ling, 'PARENT_REF':parent, 'PARTICIPANT':part, 'DEFAULT_LOCALE':locale, 'ANNOTATOR':ann}, len(self.tiers))
		else:
			self.tiers[tierId] = ({}, {}, tierDict, len(self.tiers))

	def removeTiers(self, tiers):
		"""Removes the given tiers"""
		for a in tiers:
			self.removeTier(a, check=False, clean=False)
		self.cleanTimeSlots()

	def removeTier(self, idTier, check=False, clean=True):
		"""Removes a tier by id, returns 0 if succesfull"""
		try:
			del(self.tiers[idTier])
			if clean: 
				self.cleanTimeSlots()
			return 0
		except KeyError:	
			if check: warnings.warn('removeTier: Tier non existent!\n' + 'looking for: ' + idTier)
			return 1

	def getTierNames(self):
		"""Returns a list of tiernames"""
		return self.tiers.keys()

	def getIndexOfTier(self, idTier):
		"""Returns the index of a given tier, -1 if tier doesn't exist"""
		try:
			return self.tiers[idTier][3]
		except KeyError:
			warnings.warn('getIndexOfTier: Tier non existent!')
			return -1

	def getParameterDictForTier(self, idTier):
		"""Returns a dictionary with all the parameters of the given tier, None if tier doesn't exist"""
		try:
			return self.tiers[idTier][2]
		except KeyError:
			warnings.warn('getParameterDictForTier: Tier non existent!')
			return None

	def childTiersFor(self, idTier):
		"""Returns a list of all the children of the given tier, None if the tier doesn't exist"""
		try:
			return [m for m in self.tiers.iterkeys() if 'PARENT_REF' in self.tiers[m][2] and self.tiers[m][2]['PARENT_REF']==idTier]
		except KeyError:
			warnings.warn('childTierFor: Tier non existent!')
			return None

	def getLinguisticTypeForTier(self, idTier):
		"""Returns the locale of the given tier, '' if none and None if tier doesn't exist"""
		try:
			return self.tiers[idTier][2]['LINGUISTIC_TYPE_REF']
		except KeyError:
			warnings.warn('getLinguisticTypeForTier: Tier non existent!')
			return None

	def getLocaleForTier(self, idTier):
		"""Returns the locale of the given tier, '' if none and None if tier doesn't exist"""
		try:
			tier = self.tiers[idTier]
			return '' if 'DEFAULT_LOCALE' not in tier[2] else tier[2]['DEFAULT_LOCALE']
		except KeyError:
			warnings.warn('getLocaleForTier: Tier non existent!')
			return None

	def getParticipantForTier(self, idTier):
		"""Returns the participant for the given tier, '' if none and None if tier doesn't exist"""
		try:
			tier = self.tiers[idTier]
			return '' if 'PARTICIPANT' not in tier[2] else tier[2]['PARTICIPANT']
		except KeyError:
			warnings.warn('getParticipantForTier: Tier non existent')
			return None

###ANNOTATION OPERATIONS
	def getAnnotationDataForTier(self, idTier):
		"""Returns the annotation data for the given tier in the format: (start, end, value)  None if the tier doesn't exist"""
		try:
			a = self.tiers[idTier][0]
			return [(self.timeslots[a[b][0]], self.timeslots[a[b][1]], a[b][2]) for b in a.iterkeys()]
		except KeyError:
			warnings.warn('getAnnotationDataForTier: Tier non existent!')
			return None

	def getAnnotationDataAtTime(self, idTier, time):
		"""Returns an annotation at time in the given tier, None if the tier doesn't exist"""
		try:
			anns = self.tiers[idTier][0]
			return sorted([(self.timeslots[m[0]], self.timeslots[m[1]], m[2]) for m in anns.itervalues() if self.timeslots[m[0]]<=time and self.timeslots[m[1]]>=time])
		except KeyError:
			warnings.warn('getAnnotationDataAtTime: Tier non existent!')
			return None

	def getAnnotationDatasBetweenTimes(self, idTier, start, end):
		"""Returns all the annotations overlapping with the given interval in the given tier, None if the tier doesn't exist"""
		try:
			anns = self.tiers[idTier][0]
			return sorted([(self.timeslots[m[0]], self.timeslots[m[1]], m[2]) for m in anns.itervalues() if self.timeslots[m[1]]>=start and self.timeslots[m[0]]<=end])
		except KeyError:
			warnings.warn('getAnnotationDatasBetweenTimes: Tier non existent!')
			return None

	def removeAllAnnotationsFromTier(self, idTier):
		"""Removes all the annotations from the given tier, returns 0 if succesfull"""
		try:
			self.tiers[idTier][0], self.tiers[idTier][1] = {}, {}
			self.cleanTimeSlots()
			return 0
		except KeyError: 
			warnings.warn('removeAllAnnotationsFromTier: Tier non existent!')
			return 1

	def insertAnnotation(self, idTier, start, end, value='', svg_ref=None):
		"""Add an annotation in the given tier, returns 0 if succesfull"""
		try:
			startTs = self.generateTsId(start)
			endTs = self.generateTsId(end)
			self.tiers[idTier][0][self.generateAnnotationId()] = (startTs, endTs, value, svg_ref)
			return 0
		except KeyError:
			warnings.warn('insertAnnotation: Tier non existent')
			return 1
	
	def removeAnnotation(self, time, tier, clean=True):
		"""Removes an annotation at the given time point in the given tier, returns 0 if succesfull"""
		try:
			for b in [a for a in self.tiers[tier][0].iteritems() if a[1][0]>=time and a[1][1]<=time]:
				del(self.tiers[tier][0][b[0]])
				return 0
		except KeyError:
			warnings.warn('removeAnnotation: Tier non existent')
		return 1

	def insertRefAnnotation(self, idTier, ref, value, prev, svg_ref=None):
		"""Adds a reference annotation to the given tier, 0 if succesfull"""
		try:
			self.tiers[idTier][1][self.generateAnnotationId()] = (ref, value, prev, svg_ref)
			return 0
		except KeyError:
			warnings.warn('insertRefAnnotation: Tier non existent')
			return 1

	def getRefAnnotationDataForTier(self, idTier):
		"""Returns all the ref annotation for a given tier in the form: (id->(ref, value, prev, svg_ref), None if the tier doesn't exist"""
		try:
			return self.tiers[idTier][1]
		except KeyError:
			warnings.warn('getRefAnnotationDataForTier: Tier non existent!')
			return None

###CONTROLLED VOCABULARY OPERATIONS
	def addControlledVocabularyToLinguisticType(self, linguisticType, cvId):
		"""Adds a controlled vocabulary to a linguistic type, returns 0 if succesfull"""
		try:
			self.linguistic_types[linguisticType]['CONTROLLED_VOCABULARY_REF'] = cvId
			return 0
		except KeyError:
			warnings.warn('addControlledVocabularyToLinguisticType: Linguistic type non existent!')
			return 1

	def removeControlledVocabulary(self, cv):
		"""Removes a controlled vocabulary, returns 0 if succesfull"""
		try:
			del(self.controlled_vocabularies[cv])
			return 0
		except KeyError:
			warnings.warn('removeControlledVocabulary: Controlled vocabulary non existent!')
			return 1

###HELPER FUNCTIONS
	def generateAnnotationId(self):
		"""Helper function to generate the newest annotation id"""
		if self.naiveGenAnn:
			new = self.lastAnn+1
			self.lastAnn = new
		else:
			new = 1
			anns = {int(ann[1:]) for tier in self.tiers.itervalues() for ann in tier[0].iterkeys()}
			if len(anns) > 0:
				newann = set(xrange(1, max(anns))).difference(anns)
				if len(newann) == 0:
					new = max(anns)+1
					self.naiveGenAnn = True
					self.lastAnn = new
				else:
					new = sorted(newann)[0]
		return 'a%d' % new

	def generateTsId(self, time=None):
		"""Helper function te generate the newest timeslot id"""
		if self.naiveGenTS:
			new = self.lastTS+1
			self.lastTS = new
		else:
			new = 1
			tss = {int(x[2:]) for x in self.timeslots.iterkeys()}
			if len(tss) > 0:
				newts = set(xrange(1, max(tss))).difference(tss)
				if len(newts) == 0:
					new = max(tss)+1
					self.naiveGenTS = True
					self.lastTS = new
				else:
					new = sorted(newts)[0]
		ts = 'ts%d' % new
		self.timeslots[ts] = time
		return ts

	def cleanTimeSlots(self):
		"""Removes all the unused timeslots"""
		tsInTier = set(sum([a[0:2] for tier in self.tiers.itervalues() for a in tier[0].itervalues()], ()))
		tsAvail = set(self.timeslots.iterkeys())
		for a in tsInTier.symmetric_difference(tsAvail):
			del(self.timeslots[a])
		self.naiveGenTS = False
		self.naiveGenAnn = False

###ADVANCED FUNCTIONS
	def generateAnnotationConcat(self, tiers, start, end):
		"""Generates a general value combining all the unique values within the tiers given"""
		return '_'.join(set(d[2] for t in tiers if t in self.tiers for d in self.getAnnotationDatasBetweenTimes(t, start, end)))

	def mergeTiers(self, tiers, tiernew=None, gaptresh=1):
		"""Merges the given tiers together in the new tier, returns 0 if succesfull"""
		if len([t for t in tiers if t not in self.tiers]) > 0:
			warnings.warn('mergeTiers: One or more tiers non existent!')
			return 1        
		if tiernew is None: 
			tiernew = '%s_Merged' % '_'.join(tiers)
		self.removeTier(tiernew)
		self.addTier(tiernew)
		try:
			timepts = sorted(set.union(\
			*[set(j for j in xrange(d[0], d[1])) for d in\
			[ann for tier in tiers for ann in self.getAnnotationDataForTier(tier)]]))
		except TypeError:
			warnings.warn('mergeTiers: No annotations found!')
			return 1
		if len(timepts) > 1:
			start = timepts[0]
			for i in xrange(1, len(timepts)):
				if timepts[i]-timepts[i-1] > gaptresh:
					self.insertAnnotation(tiernew, start, timepts[i-1], self.generateAnnotationConcat(tiers, start, timepts[i-1]))
					start = timepts[i]
			self.insertAnnotation(tiernew, start, timepts[i-1], self.generateAnnotationConcat(tiers, start, timepts[i-1]))
		return 0

	def shiftAnnotations(self, time):
		"""Returns a copy of the object with the timeshift of the desired ms (negative for right shift, positive for left shift)"""
		e = self.extract(-1*time, self.getFullTimeInterval()[1]) if time < 0 else self.extract(0, self.getFullTimeInterval()[1]-time)
		for tier in e.tiers.itervalues():
			for ann in tier[0].itervalues():
				e.timeslots[ann[0]],e.timeslots[ann[1]] = e.timeslots[ann[0]]+offset, e.timeslots[ann[1]]+offset
		e.cleanTimeSlots()
		return e

	def filterAnnotations(self, tier, tierName=None, filtin=None, filtex=None):
		"""Filters the tier, retuns 0 when succesfull"""
		if tier not in self.tiers:
			warnings.warn('filterAnnotations: Tier non existent!' + tier)
			return 1
		if tierName is None:
			tierName = '%s_filter' % tier1
		self.removeTier(tierName)
		self.addTier(tierName)
		for a in [b for b in self.getAnnotationDataForTier(tier) if (filtex is None or b[2] not in filtex) and (filtin is None or b[2] in filtin)]:
			self.insertAnnotation(tierName, a[0], a[1], a[2])
		return 0

	def glueAnnotationsInTier(self, tier, tierName=None, treshhold=85, filtin=None, filtex=None):
		"""Glues all the continues annotations together, returns 0 if succesfull"""
		if tier not in self.tiers:
			warnings.warn('glueAnnotationsInTier: Tier non existent!')
			return 1
		if tierName is None: 
			tierName = '%s_glued' % tier
		self.removeTier(tierName)
		self.addTier(tierName)
		tierData = sorted(self.getAnnotationDataForTier(tier), key=lambda a: a[0])
		tierData = [t for t in tierData if (filtin is None or t[2] in filtin) and (filtex is None or t[2] not in filtex)]
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
		return 0

	def getFullTimeInterval(self):
		"""Returns a tuple (start, end) of the full time frame"""
		return (min(self.timeslots.itervalues()), max(self.timeslots.itervalues()))

	def createGapsAndOverlapsTier(self, tier1, tier2, tierName=None, maxlen=-1, tierType=None):
		"""Creates a tier out of the gaps and overlap between two tiers, returns the fto data, returns None if one of the tiers doesn't exist"""
		if tier1 not in self.tiers or tier2 not in self.tiers:
			warnings.warn('createGapsAndOverlapsTier: One or more tiers non existent!')
			return None
		if tierName is None:
			tierName = '%s_%s_ftos' % (tier1, tier2)
		self.removeTier(tierName)
		self.addTier(tierName)
		ftos = self.getGapsAndOverlapsDuration(tier1, tier2, maxlen)
		for fto in ftos:
			self.insertAnnotation(tierName, fto[1], fto[2], fto[0])
		return ftos

	def getGapsAndOverlapsDuration(self, tier1, tier2, maxlen=-1, progressbar=False):
		"""Gives the gaps and overlaps between tiers in the format: (type, start, end), None if one of the tiers don't exist."""
		if tier1 not in self.tiers or tier2 not in self.tiers: 
			warnings.warn('getGapsAndOverlapsDuration: One or more tiers non existent!')
			return None
		spkr1anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]]) for a in self.tiers[tier1][0].values())
		spkr2anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]]) for a in self.tiers[tier2][0].values())
		line1 = []
		isin = lambda x, lst: False if len([i for i in lst if i[0]<=x and i[1]>=x])==0 else True
		try:
			minmax = (min(spkr1anns[0][0], spkr2anns[0][0]), max(spkr1anns[-1][1], spkr2anns[-1][1]))
		except IndexError:
			warnings.warn('getGapsAndOverlapsDuration: No annotations found...')
			return []
		last = (1, minmax[0])
		lastP = 0
		for ts in xrange(*minmax):
			in1, in2 = isin(ts, spkr1anns), isin(ts, spkr2anns)
			if in1 and in2:		#Both speaking
				if last[0] == 'B': continue
				ty = 'B'
			elif in1:			#Only 1 speaking
				if last[0] == '1': continue
				ty = '1'
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
					ftos.append(('P_%s' % (tier1 if line1[i-1][0]=='1' else tier2), line1[i][1], line1[i][2]))
			elif line1[i][0] == 'B':
				if i!=0 and i<len(line1)-1 and line1[i-1][0] != line1[i+1][0]:
					ftos.append(('O12_%s_%s' % ((tier1, tier2) if line1[i-1][0] else 'O21_%s_%s' % (tier2, tier1)), line1[i][1], line1[i][2]))
				else:
					ftos.append(('B_%s_%s' % ((tier1, tier2) if line1[i-1][0]=='1' else (tier2, tier1)), line1[i][1], line1[i][2]))
		return [f for f in ftos if maxlen==-1 or abs(f[2]-f[1])<maxlen]

###LINGUISTIC TYPE FUNCTIONS
	def createControlledVocabulary(self, cvEntries, cvId, description=''):
		"""Adds a controlled vocabulary with the given cvEntiries{value->description}, id and optional description"""
		self.controlledvocabularies[cvId] = (description, cvEntries)

	def getTierIdsForLinguisticType(self, lingType, parent=None):
		"""Returns all the tier id's with the given linguistic type"""
		return [t for t in self.tiers.iterkeys() if self.tiers[t][2]['LINGUISTIC_TYPE_REF']==lingType and (parent is None or self.tiers[t][2]['PARENT_REF']==parent)]

	def removeLinguisticType(self, lingType):
		"""Removes a linguistic type, returns 0 if succesfull"""
		try:
			del(self.linguistic_types[lingType])
			return 0
		except KeyError:
			warnings.warn('removeLinguisticType: Linguistic type non existent!')
			return 1

	def addLinguisticType(self, lingtype, constraints, timealignable=True, graphicreferences=False, extref=None):
		"""Adds a linguistic type, if it already exists the ling type is updated"""
		self.linguistic_types[lingtype] = {'LINGUISTIC_TYPE_ID':lingtype, 'TIME_ALIGNABLE':str(timealignable).lower(), 'GRAPHIC_REFERENCES':str(graphicreferences).lower(), 'CONSTRAINTS':constraints}
		if extref is not None:
			self.linguistic_types[lingtype]['EXT_REF'] = extref

	def getParameterDictForLinguisticType(self, lingid):
		"""Returns all the info of a lingtype in a dictionary, None if type doesn't exist"""
		try:
			return self.linguistic_types[lingid]
		except KeyError:
			warnings.warn('getParameterDictForLinguisticType: Linguistic type non existent!')
			return None

	def hasLinguisticType(self, lingtype):
		"""Returns if the given type is in the linguistic types"""
		return lingtype in self.linguistic_types
