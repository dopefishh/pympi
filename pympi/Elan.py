#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.etree import ElementTree
from time import localtime
import warnings

class Eaf:
	"""Class to work with elan files"""

	html_escape_table = {'&':'&amp;', '"': '&quot;', '\'':'&apos;', '<':'&gt;', '>':'&lt;'}
	html_escape = lambda _, s: ''.join(c if c not in _.html_escape_table else _.html_escape_table[c] for c in s)

	"""
	All the class variables present:
	annotationDocument      - Dict of all annotationdocument TAG entries.
	fileheader              - String of the header(xml version etc).
	header                  - Dict of the header TAG entries.
	media_descriptors       - List of all linked files: [{attributes}]
	properties              - List of all properties: [{attributes}]
	linked_file_descriptors - List of all secondary linked files: [{attributes}].
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
	lexicon_refs            - Lexicon refs [attribs]
	"""

###IO OPERATIONS
	def __init__(self, filePath=None, deflingtype='default-lt'):
		"""Constructor, builds an elan object from file(if given) or an empty one"""
		now = localtime()
		self.annotationDocument = {'AUTHOR':'Elan.py', 'DATE':'%.4d-%.2d-%.2dT%.2d:%.2d:%.2d+%.2d:00' % (now[0], now[1], now[2], now[3], now[4], now[5], now[8]), 'VERSION':'2.7', 'FORMAT':'2.7'}
		self.fileheader = '<?xml version="1.0" encoding="UTF-8"?>\n'
		self.controlled_vocabularies, self.constraints, self.tiers, self.linguistic_types, self.header, self.timeslots = {}, {}, {}, {}, {}, {}
		self.external_refs, self.lexicon_refs, self.locales, self.media_descriptors, self.properties, self.linked_file_descriptors = [], [], [], [], [], []
		self.new_time, self.new_ann = 0, 0

		if filePath is None:
			self.addLinguisticType(deflingtype, None)
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
					ext_ref = None if 'EXT_REF' not in elem.attrib else elem.attrib['EXT_REF']
					entries = {}
					for elem1 in elem:
						if elem1.tag == 'CV_ENTRY':
							entries[elem1.attrib['DESCRIPTION']] = (elem1.attrib, elem1.text)
					self.controlled_vocabularies[vcId] = (descr, entries, ext_ref)
				elif elem.tag == 'LEXICON_REF':
					self.lexicon_refs.append(elem.attrib)
				elif elem.tag == 'EXTERNAL_REF':
					self.external_refs.append((elem.attrib['EXT_REF_ID'], elem.attrib['TYPE'], elem.attrib['VALUE']))

	
	def tofile(self, filepath):
		"""Exports the eaf object to a file given by the path"""
		rmNone = lambda x: dict((k, str(v).decode('UTF-8')) for k, v in x.iteritems() if v is not None)
		ANNOTATION_DOCUMENT = ElementTree.Element('ANNOTATION_DOCUMENT', self.annotationDocument)
		
		HEADER = ElementTree.SubElement(ANNOTATION_DOCUMENT, 'HEADER', self.header)
		for m in self.media_descriptors:
			ElementTree.SubElement(HEADER, 'MEDIA_DESCRIPTOR', rmNone(m))
		for m in self.properties:
			ElementTree.SubElement(HEADER, 'PROPERTY', rmNone(m[1])).text = str(m[0]).decode('UTF-8')
		for m in self.linked_file_descriptors:
			ElementTree.SubElement(HEADER, 'LINKED_FILE_DESCRIPTOR', rmNone(m))

		TIME_ORDER = ElementTree.SubElement(ANNOTATION_DOCUMENT, 'TIME_ORDER')
		for t in self.timeslots.iteritems():
			ElementTree.SubElement(TIME_ORDER, 'TIME_SLOT', rmNone({'TIME_SLOT_ID': t[0], 'TIME_VALUE': t[1]}))

		for t in self.tiers.iteritems():
			tier = ElementTree.SubElement(ANNOTATION_DOCUMENT, 'TIER', rmNone(t[1][2]))
			for a in t[1][0].iteritems():
				ann = ElementTree.SubElement(tier, 'ANNOTATION')
				alan = ElementTree.SubElement(ann, 'ALIGNABLE_ANNOTATION', rmNone({'ANNOTATION_ID': a[0], 'TIME_SLOT_REF1': a[1][0], 'TIME_SLOT_REF2': a[1][1], 'SVG_REF': a[1][3]}))
				ElementTree.SubElement(alan, 'ANNOTATION_VALUE').text = str(a[1][2]).decode('UTF-8')
			for a in t[1][1].iteritems():
				ann = ElementTree.SubElement(tier, 'ANNOTATION')
				rean = ElementTree.SubElement(ann, 'REF_ANNOTATION', rmNone({'ANNOTATION_ID': a[0], 'ANNOTATION_REF': a[1][0], 'PREVIOUS_ANNOTATION': a[1][2], 'SVG_REF': a[1][3]}))
				ElementTree.SubElement(rean, 'ANNOTATION_VALUE').text = str(a[1][1]).decode('UTF-8')

		for l in self.linguistic_types.itervalues():
			ElementTree.SubElement(ANNOTATION_DOCUMENT, 'LINGUISTIC_TYPE', rmNone(l))
		
		for l in self.constraints.iteritems():
			ElementTree.SubElement(ANNOTATION_DOCUMENT, 'CONSTRAINT', rmNone({'STEREOTYPE':l[0], 'DESCRIPTION':l[1]}))

		for l in self.controlled_vocabularies.iteritems():
			cv = ElementTree.SubElement(ANNOTATION_DOCUMENT, 'CONTROLLED_VOCABULARY', rmNone({'CV_ID':l[0], 'DESCRIPTION':l[1][0], 'EXT_REF':l[1][2]}))
			for c in l[1][1].itervalues():
				ElementTree.SubElement(cv, 'CV_ENTRY', rmNone(c[0])).text = str(c[1]).decode('UTF-8')
		
		for r in self.external_refs:
			ElementTree.SubElement(ANNOTATION_DOCUMENT, 'EXTERNAL_REF', rmNone({'EXT_REF_ID':r[0], 'TYPE':r[1], 'VALUE':r[2]}))

		for l in self.locales:
			ElementTree.SubElement(ANNOTATION_DOCUMENT, 'LOCALE', l)
		
		for l in self.lexicon_refs:
			ElementTree.SubElement(ANNOTATION_DOCUMENT, 'LEXICON_REF', l)
	
		def indent(el, level=0):
			i = "\n" + level*"\t"
			if len(el):
				if not el.text or not el.text.strip():
					el.text = i+"\t"
				if not el.tail or not el.tail.strip():
					el.tail = i
				for elem in el:
					indent(elem, level+1)
				if not el.tail or not el.tail.strip():
					el.tail = i
			else:
				if level and (not el.tail or not el.tail.strip()):
					el.tail = i

		indent(ANNOTATION_DOCUMENT)
		ElementTree.ElementTree(ANNOTATION_DOCUMENT).write(filepath, xml_declaration=True, encoding='UTF-8')	

	def tofileOLD(self, filePath):
		"""Exports the eaf object to a file give by the path"""
		xmlFormat = lambda k, d: '' if d[k] is None else '%s="%s"' % (self.html_escape(k), self.html_escape(d[k]))
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

	def updatePrevAnnotationForAnnotation(self, idTier, idAnn, idPrevAnn=None):
		"""Updates the previous annotation value in an annotation in the given tier, returns 0 if succesfull"""
		try:
			self.tiers[idTier][1][idAnn][2] = idPrevAnn
			return 0
		except KeyError: 
			warnings.warn('updatePrevAnnotationForAnnotation: Tier or annotation non existent!')
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
		new = 1
		anns = {int(ann[1:]) for tier in self.tiers.itervalues() for ann in tier[0].iterkeys()}
		if len(anns) > 0:
			newann = set(xrange(1, max(anns))).difference(anns)
			new = max(anns)+1 if len(newann)==0 else sorted(newann)[0]
		return 'a%d' % new

	def generateTsId(self, time=None):
		"""Helper function te generate the newest timeslot id"""
		new = 1
		tss = {int(x[2:]) for x in self.timeslots.iterkeys()}
		if len(tss) > 0:
			newts = set(xrange(1, max(tss))).difference(tss)
			new = max(tss)+1 if len(newts)==0 else sorted(newts)[0]
		ts = 'ts%d' % new
		self.timeslots[ts] = time
		return ts

	def cleanTimeSlots(self):
		"""Removes all the unused timeslots"""
		tsInTier = set(sum([a[0:2] for tier in self.tiers.itervalues() for a in tier[0].itervalues()], ()))
		tsAvail = set(self.timeslots.iterkeys())
		for a in tsInTier.symmetric_difference(tsAvail):
			del(self.timeslots[a])

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
		if tierType is None:
			tierType = self.linguistic_types.keys()[0]
		self.removeTier(tierName)
		self.addTier(tierName, tierType)
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

	def addLinguisticType(self, lingtype, constraints, timealignable=False, graphicreferences=False, extref=None):
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
