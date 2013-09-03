import xml.etree.ElementTree as ET
from time import localtime as now
import pdb

class Eaf:
	"""Class to work with elan files"""
	
	html_escape_table = {'&':'&amp;', '"': 'quot;', '\'':'&apos;', '<':'&gt;', '>':'%lt;'}
	html_escape = lambda _, s: ''.join(c if c not in _.html_escape_table else _.html_escape_table[c] for c in s)

	#Root data
	annotationDocument = {'AUTHOR':'Eaf.py', 'DATE':'%.4d-%.2d-%.2dT%.2d:%.2d:%.2d+%.2d:00' % (now()[0], now()[1], now()[2], now()[3], now()[4], now()[5], now()[8]), 'VERSION':'2.7', 'FORMAT':'2.7'}
	#File header
	fileheader = '<?xml version="1.0" encoding="UTF-8"?>\n'
	#Header data
	header = {}
	media_descriptors, properties, linked_file_descriptors = [], [], []
	#Timeslot data {id -> time}
	timeslots = {}
	#Tier data: {id -> (align, ref, attrib, num)}, 
	# align = {id -> (begin, end, value, svg_ref)}
	# ref   = {id -> (ref, value, previous, svg_ref)}
	tiers = {}
	#Linguistic type data {id -> attrib}
	linguistic_types = {}
	#Locale data [attrib]
	locales = []
	#Constraint data {stereotype -> description}
	constraints = {}
	#Controlled vocabulary data {id -> (description, entries)}
	# entry = {value -> description}
	controlled_vocabularies = {}
	#External refs [id, type, value]
	external_refs = []
	#Lexicon refs
	lexicon_refs = []

	#new timeslot and annotation value
	new_time, new_ann = 0, 0

###IO OPERATIONS
	def __init__(self, filePath=None):
		if filePath is not None:
			with open(filePath, 'r') as f:
				self.fileheader = f.readlines()[0]
			treeRoot = ET.parse(filePath).getroot()
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

###MEDIA OPERATIONS
	def getMediaForMimeType(self, mime):
		"""Gives a list of media attachments containing mime in mime_type"""
		return [m for m in self.media_descriptors if mime in m['MIME_TYPE']]

	def getVideo(self):
		"""Gives a list of all video files"""
		return self.getMediaForMimeType('video')

	def getVideoTimeOrigin(self):
		"""Gives a list of all video time origins"""
		return [0 if 'TIME_ORIGIN' not in m else m['TIME_ORIGIN'] for m in self.getMediaForMimeType('video')]

	def getAudio(self):
		"""Gives a list of all audio files"""
		return self.getMediaForMimeType('audio')

	def getAudioTimeOrigin(self):
		"""Gives a list of all audio time origins"""
		return [0 if 'TIME_ORIGIN' not in m else m['TIME_ORIGIN'] for m in self.getMediaForMimeType('audio')]

###TIER OPERATIONS
	def addTier(self, idTier, tierType='default-lt', parent=None, defaultLocale=None, participant=None, annotator=None):
		"""Adds a tier giving a id and type and optional extra data"""
		data = {'TIER_ID':idTier, 'LINGUISTIC_TYPE_REF':tierType, 'PARENT_REF':parent, 'PARTICIPANT':participant,
				'DEFAULT_LOCALE':defaultLocale, 'ANNOTATOR':annotator}
		self.tiers[idTier] = ({}, {}, data, len(self.tiers))
	
	def removeTier(self, idTier):
		"""Removes a tier by id, if it doesn't exist nothing happens"""
		if idTier in self.tiers:
			del(self.tiers[idTier])
			self.cleanTimeSlots()
	
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
		except KeyError:
			pass

	def childTiersFor(self, idTier):
		"""Returns a list of all the children of the given tier, None if the tier doesn't exist"""
		try:
			return [m for m in self.tiers.keys() if 'PARENT_REF' in self.tiers[m][2] and self.tiers[m][2]['PARENT_REF']==idTier]
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
			try:
				return tier[2]['PARTICIPANT']
			except KeyError:
				return ''
		except KeyError:
			return None

###ANNOTATION OPERATIONS
	def getRefAnnotationIdsForTier(self, idTier):
		"""Returns a list of ref annotation ids within a tier, None if tier doesn't exist"""
		try:
			return [m for m in self.tiers[idTier][1].keys()]
		except KeyError:
			return None

	def getAnnotationIdsForTier(self, idTier, startTime=None, endTime=None):
		"""Returns a list of annotation ids within a tier, None if tier doesn't exist"""
		try:
			return [m for m in self.tiers[idTier][0]]
		except KeyError:
			return None
	
	def getAnnotationIdAtTime(self, idTier, time):
		"""Returns a list of annotation ids that match the given time, returns None if tier doesn't exist"""
		try:
			anns = self.tiers[idTier][0]
			return [m for m in anns.keys() if self.timeslots[anns[m][0]]<=time and self.timeslots[anns[m][1]]>=time]
		except KeyError:
			return None
	
	def getAnnotationIdsInOverlap(self, idTier, begin, end):
		"""Returns all the annotation ids with overlap with the given interval, None if tier doesn't exist"""
		try:
			anns = self.tiers[idTier][0]
			return [m for m in anns.keys() if begin<=self.timeslots[anns[m][1]] and self.timeslots[anns[m][0]]<=end]
		except KeyError:
			return None

	def getAnnotationValueAtTime(self, idTier, time):
		"""Returns the annotation value at the given time in the given tier, None if tier or annotation doesn't exist"""
		try:
			return self.tiers[idTier][0][self.getAnnotationIdAtTime(idTier, time, False)]		
		except KeyError:
			return None

	def getAnnotationValueForAnnotation(self, idTier, idAnn):
		"""Returns the value for the annotation id, None if the annotation and tier don't exist"""
		try:
			return self.tiers[idTier][0][idAnn][2]
		except KeyError:
			return None

	def getEndTimeForAnnotation(self, idTier, idAnn):
		"""Returns end time for annotation id, None if the annotation and tier don't exist"""
		try:
			return timeslots[self.getEndTsForAnnotation(idTier, idAnn)]
		except KeyError:
			return None

	def getEndTsForAnnotation(self, idTier, idAnn):
		"""Returns the end timeslot for annotation id, None if the annotation and tier don't exist"""
		try:
			return self.tiers[idTier][0][idAnn][1]
		except KeyError:
			return None

	def getStartTimeForAnnotation(self, idTier, idAnn):
		"""Returns the start time for annotation id, None if the annotation or tier don't exist"""
		try:
			return timeslots[self.getStartTsForAnnotation(idTier, idAnn)]
		except KeyError:
			return None

	def getStartTsForAnnotation(self, idTier, idAnn):
		"""Returns the start timeslot for annotation id, None if the annotation or tier don't exist"""
		try:
			return self.tiers[idTier][0][idAnn][0]
		except KeyError:
			return None

	def removeAllAnnotationsFromTier(self, idTier):
		"""Removes all the annotations from the given tier, when the tier doesn't exist nothing happens"""
		try:
			self.tiers[idTier][0] = {}
			self.tiers[idTier][1] = {}
			self.cleanTimeSlots()
		except KeyError:
			pass

	def removeAnnotationWithId(self, idTier, idAnn):
		"""Removes the annotation with the id from the tier, when they don't exist nothing happens"""
		try:
			del(self.tiers[idTier][0][idAnn])
		except KeyError:
			pass
		try:
			del(self.tiers[idTier][1][idAnn])
		except KeyError:
			pass
		self.cleanTimeSlots()

	def removeAnnotationsWithRef(self, idTier, idRefAnn):
		"""Removes all the annotations are reffed by the annotation given, when they don't exist nothing happens"""
		try:
			for a in [an for an in self.tiers[idTier][1].keys() if self.tiers[idTier][1][an] == idRefAnn]:
				del(self.tiers[idTier][1][a])
		except KeyError:
			pass

	def setAnnotationValueForAnnotation(self, idTier, idAnn, strAnn):
		"""Set the annotation value for an annotation in a given tier, if the they don't exist nothing happens"""
		try:
			self.tiers[idTier][0][idAnn][2] = strAnn
		except KeyError:
			pass
		try:
			self.tiers[idTier][1][idAnn][1] = strAnn
		except KeyError:
			pass

	def updatePrevAnnotationForAnnotation(self, idTier, idAnn, idPrevAnn=None):
		"""Updates the previous annotation value in an annotation in the given tier, nothing happens if they don't exist"""
		try:
			self.tiers[idTier][1][idAnn][2] = idPrevAnn
		except KeyError:
			pass

	def insertAnnotation(self, idTier, start, end, value='', svg_ref=None):
		"""Add an annotation in the given tier, if the tiers doesn't exist nothing happens"""
		if idTier in self.tiers:
			startTs = self.generateTsId()
			endTs = self.generateTsId()
			self.timeslots[startTs] = start
			self.timeslots[endTs] = end
			self.tiers[idTier][0][self.generateAnnotationId()] = (startTs, endTs, value, svg_ref)

	def getRefAnnotationIdForAnnotation(self, idTier, idAnn):
		"""Returns all the ref annotations pointing to the given annotation in the given tier, None if the tier or annotation doesn't exist"""
		try:
			return [i for i in self.tiers[idTier][1].keys() if self.tiers[idTier][1][i][0]==idAnn]
		except KeyError:
			return None
		
	def getRefAnnotationIdsForTier(self, idTier):
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
		except KeyError:
			pass

	def removeControlledVocabulary(self, cv):
		"""Removes a controlled vocabulary, when the cv doesn't exist nothing happens"""
		try:
			del(self.controlled_vocabularies[cv])
		except KeyError:
			pass

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
			for an in t.itervalues():
				del(self.timeslots[an[0]])
				del(self.timeslots[an[1]])
	
	def extract(self, begin, end, file_name, margin=0):
		"""TODO"""
		pass

###GAP AND OVERLAP FUNCTIONS
	def createGapsAndOverlapsTier(self, tier1, tier2, tierName=None, tierType=None):
		"""Creates a tier out of the gaps and overlap between two tiers"""
		if tierName is None:
			tierName = '%s_%s_go' % (tier1, tier2)
		if tierType is None:
			tierType = self.linguistic_types.keys()[0]
		self.removeTier(tierName)
		self.addTier(tierName, tierType)
		for go in self.getGapsAndOverlapsDuration(tier1, tier2):
			self.insertAnnotation(tierName, go[1], go[2], go[0])

	def getGapsAndOverlapsDuration(self, tier1, tier2, withinOnly=False):
		"""Gives the gaps and overlaps between tiers in the format: (type, start, end), None if one of the tiers don't exist. If the withinOnly flag is true the pauses and betweenspeaker overlaps are not included"""
		if tier1 not in self.tiers or tier2 not in self.tiers:
			return None
		spkr1anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]]) for a in self.tiers[tier1][0].values())
		spkr2anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]]) for a in self.tiers[tier2][0].values())
		line1 = []
		isin = lambda x, lst: False if len([i for i in lst if i[0]<=x and i[1]>=x])==0 else True
		minmax = (min(spkr1anns[0][0], spkr2anns[0][0]), max(spkr1anns[-1][1], spkr2anns[-1][1]))
		last = (1, minmax[0])
		for ts in xrange(*minmax):
			in1, in2 = isin(ts, spkr1anns), isin(ts, spkr2anns)
			if in1 and in2:		#Both speaking
				if last[0] == 'B': continue
				line1.append((last[0], last[1], ts))
				last = ('B', ts)
			elif in1:			#Only 1 speaking
				if last[0] == '1': continue
				line1.append((last[0], last[1], ts))
				last = ('1', ts)
			elif in2:			#Only 2 speaking
				if last[0] == '2': continue
				line1.append((last[0], last[1], ts))
				last = ('2', ts)
			else:				#None speaking
				if last[0] == 'N': continue
				line1.append((last[0], last[1], ts))
				last = ('N', ts)
		line1.append((last[0], last[1], minmax[1]))
		gando = []
		for i in xrange(len(line1)):
			if line1[i][0] == 'N':
				if i!=0 and i<len(line1)-1 and line1[i-1][0] != line1[i+1][0]:
					gando.append(('Gap', line1[i][1], line1[i][2]))
				elif not withinOnly:
					gando.append(('Pause', line1[i][1], line1[i][2]))
			elif line1[i][0] == 'B':
				if i!=0 and i<len(line1)-1 and line1[i-1][0] != line1[i+1][0]:
					gando.append(('Overlap_W', line1[i][1], line1[i][2]))
				elif not withinOnly:
					gando.append(('Overlap_B', line1[i][1], line1[i][2]))
		return gando

###LINGUISTIC TYPE FUNCTIONS
	def createControlledVocabulary(self, cvEntries, cvID, description=''):
		pass
	def getTierIdsForLinguisticType(self, lingType, parent=None):
		pass
	def removeLinguisticType(self, lingType):
		pass
	def addLinguisticType(self, lingtype, constraints, timealignable=False, graphicreferences=False, extref=None):
		pass
	def getConstraintForLinguisticType(self, lingid):
		pass
	def getIndexOfLastLinguisticType(self):
		pass
	def getParameterDictForLinguisticType(self, lingid):
		pass
	def hasLinguisticType(self, lingtype):
		pass
	def linguisticTypeIsTimeAlignable(self, lingid):
		pass
