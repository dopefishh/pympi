# -*- coding: utf-8 -*-
# (C) 2011 copyright by Peter Bouda
"""This module contains classes to access Elan data.

The class Eaf is a low level API to .eaf files.

EafGlossTree, EafPosTree, etc. are the classes to access the data via 
tree, which also contains the original .eaf IDs. Because of this
EafTrees are read-/writeable. 

"""

import os, glob, re
import pyannotation.data

from copy import deepcopy
from xml.dom.minidom import parse,parseString
import lxml.etree
from lxml import etree as ET
from lxml.etree import Element
from xml.parsers import expat
import sys
import pdb

############################################# Builders

class EafAnnotationFileObject(pyannotation.data.AnnotationFileObject):

	def __init__(self, filepath):
		pyannotation.data.AnnotationFileObject.__init__(self, filepath)
		self.setFilepath(filepath)

	def getFile(self):
		return self.file

	def getFilepath(self):
		return self.filepath

	def setFilepath(self, filepath):
		self.filepath = filepath
		self.file = Eaf(self.filepath)

	def createTierHandler(self):
		if self.tierHandler == None:
			self.tierHandler = EafAnnotationFileTierHandler(self)
		return self.tierHandler

	def createParser(self):
		if self.parser == None:
			self.parser = EafAnnotationFileParser(self, self.createTierHandler())
		return self.parser

	def createParserWords(self):
		if self.parser == None:
			self.parser = EafAnnotationFileParserWords(self, self.createTierHandler())
		return self.parser

	def createParserPos(self):
		if self.parser == None:
			self.parser = EafAnnotationFileParserPos(self, self.createTierHandler())
		return self.parser


class EafFromToolboxAnnotationFileObject(pyannotation.data.AnnotationFileObject):

	def __init__(self, filepath):
		pyannotation.data.AnnotationFileObject.__init__(self, filepath)
		self.setFilepath(filepath)

	def getFile(self):
		return self.file

	def getFilepath(self):
		return self.filepath

	def setFilepath(self, filepath):
		self.filepath = filepath
		self.file = EafPythonic(self.filepath)

	def createTierHandler(self):
		if self.tierHandler == None:
			self.tierHandler = EafAnnotationFileTierHandler(self)
			self.tierHandler.setUtterancetierType("tx")
			self.tierHandler.setWordtierType("mo")
			self.tierHandler.setMorphemetierType("mo")
			self.tierHandler.setGlosstierType("gl")
			self.tierHandler.setTranslationtierType(["ft", "ot"])
		return self.tierHandler

	def createParser(self):
		if self.parser == None:
			self.parser = EafFromToolboxAnnotationFileParser(self, self.createTierHandler())
		return self.parser


class EafAnnotationFileTierHandler(pyannotation.data.AnnotationFileTierHandler):

	def __init__(self, annotationFileObject):
		pyannotation.data.AnnotationFileTierHandler.__init__(self, annotationFileObject)
		self.eaf = annotationFileObject.getFile()
		self.UTTERANCETIER_TYPEREFS = [ "utterance", "utterances", u"Äußerung", u"Äußerungen" ]
		self.WORDTIER_TYPEREFS = [ "words", "word", "Wort", "Worte", u"Wörter" ]
		self.MORPHEMETIER_TYPEREFS = [ "morpheme", "morphemes",  "Morphem", "Morpheme" ]
		self.GLOSSTIER_TYPEREFS = [ "glosses", "gloss", "Glossen", "Gloss", "Glosse" ]
		self.POSTIER_TYPEREFS = [ "part of speech", "parts of speech", "Wortart", "Wortarten" ]
		self.TRANSLATIONTIER_TYPEREFS = [ "translation", "translations", u"Übersetzung",  u"Übersetzungen" ]

	def setUtterancetierType(self, type):
		if isinstance(type, list):
			self.UTTERANCETIER_TYPEREFS = type
		else:
			self.UTTERANCETIER_TYPEREFS = [type]

	def setWordtierType(self, type):
		if isinstance(type, list):
			self.WORDTIER_TYPEREFS = type
		else:
			self.WORDTIER_TYPEREFS = [type]

	def setMorphemetierType(self, type):
		if isinstance(type, list):
			self.MORPHEMETIER_TYPEREFS = type
		else:
			self.MORPHEMETIER_TYPEREFS = [type]

	def setGlosstierType(self, type):
		if isinstance(type, list):
			self.GLOSSTIER_TYPEREFS = type
		else:
			self.GLOSSTIER_TYPEREFS = [type]

	def setPostierType(self, type):
		if isinstance(type, list):
			self.POSTIER_TYPEREFS = type
		else:
			self.POSTIER_TYPEREFS = [type]

	def setTranslationtierType(self, type):
		if isinstance(type, list):
			self.TRANSLATIONTIER_TYPEREFS = type
		else:
			self.TRANSLATIONTIER_TYPEREFS = [type]

	def getUtterancetierIds(self, parent = None):
		ret = []
		for type in self.UTTERANCETIER_TYPEREFS:
			ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
		return ret

	def getWordtierIds(self, parent = None):
		ret = []
		for type in self.WORDTIER_TYPEREFS:
			ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
		return ret

	def getMorphemetierIds(self, parent = None):
		ret = []
		for type in self.MORPHEMETIER_TYPEREFS:
			ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
		return ret

	def getGlosstierIds(self, parent = None):
		ret = []
		for type in self.GLOSSTIER_TYPEREFS:
			ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
		return ret

	def getPostierIds(self, parent = None):
		ret = []
		for type in self.POSTIER_TYPEREFS:
			ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
		return ret

	def getTranslationtierIds(self, parent = None):
		ret = []
		for type in self.TRANSLATIONTIER_TYPEREFS:
			ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
		return ret

	def addTier(self, tierId, tierType, tierTypeConstraint, parentTier, tierDefaultLocale, tierParticipant):
		self.eaf.addTier(tierId, tierType, parentTier, tierDefaultLocale, tierParticipant)
		if not self.eaf.hasLinguisticType(tierType):
			self.eaf.addLinguisticType(tierType, tierTypeConstraint)

	def getLocaleForTier(self, idTier):
		return self.eaf.getLocaleForTier(idTier)

	def getParticipantForTier(self, idTier):
		return self.eaf.getParticipantForTier(idTier)


class EafAnnotationFileParser(pyannotation.data.AnnotationFileParser):

	def __init__(self, annotationFileObject, annotationFileTiers):
		pyannotation.data.AnnotationFileParser.__init__(self, annotationFileObject, annotationFileTiers)
		self.tierBuilder = annotationFileTiers
		self.eaf = annotationFileObject.getFile()
		self.lastUsedAnnotationId = self.eaf.getLastUsedAnnotationId()
		self.emptyIlElement = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

	def setFile(self, file):
		self.file = file

	def getNextAnnotationId(self):
		self.lastUsedAnnotationId = self.lastUsedAnnotationId + 1
		return self.lastUsedAnnotationId

	def parse(self):
		tree = []
		self.utteranceTierIds = self.tierBuilder.getUtterancetierIds()
		if self.utteranceTierIds != []:
			for uTier in self.utteranceTierIds:
				utterancesIds = self.eaf.getAlignableAnnotationIdsForTier(uTier) + self.eaf.getRefAnnotationIdsForTier(uTier)
				for uId in utterancesIds:
					utterance = self.eaf.getAnnotationValueForAnnotation(uTier, uId)
					translations = []
					ilElements = []
					locale = self.eaf.getLocaleForTier(uTier)
					participant = self.eaf.getParticipantForTier(uTier)
					translationTierIds = self.tierBuilder.getTranslationtierIds(uTier)
					for tTier in translationTierIds:
						transIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(uId, uTier, tTier)
						for transId in transIds:
							trans = self.eaf.getAnnotationValueForAnnotation(tTier, transId)
							if trans != '':
								translations.append([transId, trans])
					wordTierIds = self.tierBuilder.getWordtierIds(uTier)
					for wTier in wordTierIds:
						wordsIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(uId, uTier, wTier)
						for wordId in wordsIds:
							ilElements.append(self.getIlElementForWordId(wordId, wTier))
						if len(ilElements) == 0:
							ilElements = self.emptyIlElement
					tree.append([ uId,  utterance,  ilElements, translations, locale, participant, uTier ])
		else: # if self.utterancesTiers != []
			for wTier in self.tierBuilder.getWordtierIds():
				translations = []
				locale = self.eaf.getLocaleForTier(wTier)
				participant = self.eaf.getParticipantForTier(wTier)
				wordsIds = self.eaf.getAnnotationIdsForTier(wTier)
				for wordId in wordsIds:
					ilElements.append(self.getIlElementForWordId(wordId, wTier))   
				if len(ilElements) == 0:
					ilElements = self.emptyIlElement
				tree.append([ '',  '',  ilElements, translations, locale, participant, '' ])
		return tree

	def getIlElementForWordId(self, id, wTier):
		ilElement = []
		word = self.eaf.getAnnotationValueForAnnotation(wTier, id)
		ilElement.append(id)
		ilElement.append(word)
		morphElements = []
		morphemeTierIds = self.tierBuilder.getMorphemetierIds(wTier)
		for mTier in morphemeTierIds:
			morphIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(id, wTier, mTier)
			for morphId in morphIds:
				morphElements.append(self.getFuncElementForMorphemeId(morphId, mTier))
		if len(morphElements) == 0:
			ilElement.append([[ '',  '',  [ ['',  ''] ]]])
		else:
			ilElement.append(morphElements)
		return ilElement

	def getFuncElementForMorphemeId(self, morphId, mTier):
		ilElement = []
		morpheme = self.eaf.getAnnotationValueForAnnotation(mTier, morphId)
		morpheme = re.sub(r'^-', '', morpheme)
		morpheme = re.sub(r'-$', '', morpheme)
		ilElement.append(morphId)
		ilElement.append(morpheme)
		funcElements = []
		glossTierIds = self.tierBuilder.getGlosstierIds(mTier)
		for gTier in glossTierIds:
			funcIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(morphId, mTier, gTier)
			for funcId in funcIds:
				function = self.eaf.getAnnotationValueForAnnotation(gTier, funcId)
				function = re.sub(r'^-', '', function)
				morpheme = re.sub(r'-$', '', function)
				e = [funcId, function]
				funcElements.append(e)
		if len(funcElements) == 0:
			ilElement.append([['',  '']])
		else:
			ilElement.append(funcElements)
		return ilElement

	def removeAnnotationWithId(self, idAnnotation):
		self.eaf.removeAnnotationWithId(idAnnotation)

	def removeAnnotationsWithRef(self, idRefAnn):
		self.eaf.removeAnnotationsWithRef(idRefAnn)

	def updatePrevAnnotationForAnnotation(self, idAnnotation, idPrevAnn = None):
		self.eaf.updatePrevAnnotationForAnnotation(idAnnotation, idPrevAnn)

	def getAsEafXml(self, tree, tierUtterances, tierWords, tierMorphemes, tierGlosses, tierTranslations):
		# make local copy of eaf
		eaf2 = deepcopy(self.eaf)
		utterances = [[u[0], u[1]] for u in tree if u[6] == tierUtterances]
		translations = [[u[3], u[0]] for u in tree if u[6] == tierUtterances and len(u[3])>=1]
		words = [[w[0], w[1]] for u in tree if u[6] == tierUtterances for w in u[2]]
		ilelements = [u[2] for u in tree if u[6] == tierUtterances]
		# save utterances
		for u in utterances:
			eaf2.setAnnotationValueForAnnotation(tierUtterances, u[0], u[1])
		# save translations
		for t1 in translations:
			for t in t1[0]:
				if t[1] != "":
					if not eaf2.setAnnotationValueForAnnotation(tierTranslations, t[0], t[1]):
						eaf2.appendRefAnnotationToTier(tierTranslations, t[0], t[1], t1[1])
		# save words
		for w in words:
			eaf2.setAnnotationValueForAnnotation(tierWords, w[0], w[1])
		#save morphemes
		eaf2.removeAllAnnotationsFromTier(tierMorphemes)
		eaf2.removeAllAnnotationsFromTier(tierGlosses)
		for i in ilelements:
			for w in i:
				if len(w) >= 3:
					refAnnMorph = w[0]
					prevAnnMorph = None
					for m in w[2]:
						if len(m) >= 3:
							if m[0] != "" and m[1] != "" and refAnnMorph != "":
								eaf2.appendRefAnnotationToTier(tierMorphemes, m[0], m[1], refAnnMorph, prevAnnMorph)
							prevAnnMorph = m[0]
							refAnnGloss = m[0]
							prevAnnGloss = None
							for g in m[2]:
								if len(g) >= 2:
									if g[0] != "" and g[1] != "" and refAnnGloss != "":
										eaf2.appendRefAnnotationToTier(tierGlosses, g[0], g[1], refAnnGloss, prevAnnGloss)
									prevAnnGloss = g[0]
		return eaf2.tostring()


class EafAnnotationFileParserPos(EafAnnotationFileParser):

	def __init__(self, annotationFileObject, annotationFileTiers):
		EafTree.__init__(self, annotationFileObject, annotationFileTiers)

	def getIlElementForWordId(self, id, wTier):
		ilElement = []
		word = self.eaf.getAnnotationValueForAnnotation(wTier, id)
		ilElement.append(id)
		ilElement.append(word)
		posElements = []
		posTierIds = self.tierBuilder.getPostierIds(wTier)
		for pTier in posTierIds:
			posIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(id, wTier, pTier)
			for posId in posIds:
				pos = self.eaf.getAnnotationValueForAnnotation(pTier, posId)
				posElements.append((posId, pos))
		ilElement.append(posElements)
		return ilElement
	

class EafAnnotationFileParserWords(EafAnnotationFileParser):

	def __init__(self, annotationFileObject, annotationFileTiers):
		EafTree.__init__(self, annotationFileObject, annotationFileTiers)

	def getIlElementForWordId(self, id, wTier):
		ilElement = []
		word = self.eaf.getAnnotationValueForAnnotation(wTier, wordId)
		ilElement = [wordId, word]
		return ilElement


class EafFromToolboxAnnotationFileParser(pyannotation.data.AnnotationFileParser):

	def __init__(self, annotationFileObject, annotationFileTiers):
		pyannotation.data.AnnotationFileParser.__init__(self, annotationFileObject, annotationFileTiers, wordSep = r"[ \n\t\r]+", morphemeSep = r"[-]", glossSep = r"[:]")
		self.tierBuilder = annotationFileTiers
		self.eaf = annotationFileObject.getFile()
		self.lastUsedAnnotationId = self.eaf.getLastUsedAnnotationId()
		self.emptyIlElement = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

	def setFile(self, file):
		self.file = file

	def getNextAnnotationId(self):
		self.lastUsedAnnotationId = self.lastUsedAnnotationId + 1
		return self.lastUsedAnnotationId

	def parse(self):
		tree = []
		self.utteranceTierIds = self.tierBuilder.getUtterancetierIds()
		for uTier in self.utteranceTierIds:
			utterancesIds = self.eaf.getAlignableAnnotationIdsForTier(uTier) + self.eaf.getRefAnnotationIdsForTier(uTier)
			for uId in utterancesIds:
				utterance = self.eaf.getAnnotationValueForAnnotation(uTier, uId)
				utterance = re.sub(r" +", " ", utterance)

				refId = self.eaf.getRefAnnotationIdForAnnotationId(uTier, uId)
				toolboxId = self.eaf.getAnnotationValueForAnnotation("ref", refId)

				translations = []
				ilElements = []
				locale = self.eaf.getLocaleForTier(uTier)
				participant = self.eaf.getParticipantForTier(uTier)
				translationTierIds = self.tierBuilder.getTranslationtierIds("ref")
				for tTier in translationTierIds:
					transIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(refId, "ref", tTier)
					for transId in transIds:
						trans = self.eaf.getAnnotationValueForAnnotation(tTier, transId)
						if trans != '':
							translations.append([transId, trans])
				
				arrTextWords = re.split(self.WORD_BOUNDARY_PARSE, utterance)
				arrTextWords = filter(lambda i: i != '', arrTextWords)
				
				arrMorphWords = []
				arrGlossWords = []
				wordTierIds = self.tierBuilder.getWordtierIds("ref")
				for wTier in wordTierIds:
					wordsIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(refId, "ref", wTier)
					for wordId in wordsIds:
						word = self.eaf.getAnnotationValueForAnnotation(wTier, wordId)
						arrMorphWords.append(word)
						glossTierIds = self.tierBuilder.getGlosstierIds(wTier)
						for gTier in glossTierIds:
							glossIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(wordId, wTier, gTier)
							for glossId in glossIds:
								gloss = self.eaf.getAnnotationValueForAnnotation(gTier, glossId)
								arrGlossWords.append(gloss)

				for i,word in enumerate(arrTextWords):
					morphemes = ""
					glosses = ""
					if i < len(arrMorphWords):
						morphemes = arrMorphWords[i]
					if i < len(arrGlossWords):
						glosses = arrGlossWords[i]
					ilElement = self.ilElementForString("%s %s %s" % (word, morphemes, glosses))
					
					ilElements.append(ilElement)
				if len(ilElements) == 0:
					ilElements = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

				tree.append([ toolboxId,  utterance,  ilElements, translations, locale, participant, uTier ])
		return tree

####################################### Files

class Eaf(object):

	def __init__(self, file):
		self.tree = ET.parse(file)

	def tostring(self):
		return ET.tostring(self.tree.getroot(), pretty_print=True, encoding="utf-8")

	def tiers(self):
		# returns tiers as dictionary: id -> type
		ret = {}
		for tier in self.tree.findall('TIER'):
			ret[tier.attrib['TIER_ID']] = tier.attrib['LINGUISTIC_TYPE_REF']
		return ret
		
	def childTiersFor(self,  id):
		ret = {}
		childTiers = self.tree.findall("TIER[@PARENT_REF='%s']" % id)
		for tier in childTiers:
			child_id = tier.attrib['TIER_ID']
			if child_id not in ret.keys():
				ret2 = self.childTiersFor(child_id)
				for k,  v in ret2.items():
					ret[k] = v
			ret[child_id] = tier.attrib['LINGUISTIC_TYPE_REF']
		return ret

	def getIndexOfTier(self, id):
		ret = None
		i = 0
		for node in self.tree.getroot():
			if node.tag == 'TIER' and 'TIER_ID' in node.attrib and node.attrib['TIER_ID'] == id:
				ret = i
			i = i + 1
		return ret

	def getIndexOfLastTier(self):
		ret = None
		i = 0
		for node in self.tree.getroot():
			if node.tag == 'TIER':
				ret = i
			i = i + 1
		if ret == None:
			ret = i
		return ret

	def getLastUsedAnnotationId(self):
		strId = self.tree.findtext("HEADER/PROPERTY[@NAME='lastUsedAnnotationId']")
		lastId = 0
		if strId != None:
			lastId = int(strId)
		else:
			annotations = self.tree.findall("TIER/ANNOTATION/ALIGNABLE_ANNOTATION")
			for a in annotations:
				i = a.attrib['ANNOTATION_ID']
				i = int(re.sub(r"\D", "", i))
				if i > lastId:
					lastId = i
			annotations = self.tree.findall("TIER/ANNOTATION/REF_ANNOTATION")
			for a in annotations:
				i = a.attrib['ANNOTATION_ID']
				i = int(re.sub(r"\D", "", i))
				if i > lastId:
					lastId = i
		return lastId

	def getTierIdsForLinguisticType(self, type, parent = None):
		ret = []
		if parent == None:
			tiers = self.tree.findall("TIER[@LINGUISTIC_TYPE_REF='%s']" % type) #.decode('utf-8')
		else:
			tiers = self.tree.findall("TIER[@LINGUISTIC_TYPE_REF='%s'][@PARENT_REF='%s']" % (type, parent)) #.decode('utf-8')
		for tier in tiers:
			ret.append(tier.attrib['TIER_ID'])
		return ret

	def getParameterDictForTier(self, id):
		tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
		return tier.attrib
		
	def getParameterDictForLinguisticType(self, id):
		tier = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % id)
		return tier.attrib

	def getLinguisticTypeForTier(self, id):
		tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
		if 'LINGUISTIC_TYPE_REF' in tier.attrib:
			return tier.attrib['LINGUISTIC_TYPE_REF']
		return None
		
	def getConstraintForLinguisticType(self, id):
		tier = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % id)
		if 'CONSTRAINTS' in tier.attrib:
			return tier.attrib['CONSTRAINTS']
		return None
		
	def linguisticTypeIsTimeAlignable(self, id):
		tier = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % id)
		if 'TIME_ALIGNABLE' in tier.attrib:
			if tier.attrib['TIME_ALIGNABLE'] == 'true':
				return True
			else:
				return False
		return None

	def getIndexOfLastLinguisticType(self):
		ret = None
		i = 0
		for node in self.tree.getroot():
			if node.tag == 'LINGUISTIC_TYPE':
				ret = i
			i = i + 1
		if ret == None:
			ret = i
		return ret

	def getLocaleForTier(self, id):
		locale = ''
		tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
		if 'DEFAULT_LOCALE' in tier.attrib:
			locale = tier.attrib['DEFAULT_LOCALE']
			if locale == None:
				locale = ''
		return locale
		
	def getParticipantForTier(self, id):
		participant = ''
		tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
		if 'PARTICIPANT' in tier.attrib:
			participant = tier.attrib['PARTICIPANT']
			if participant == None:
				participant = ''
		participant = participant
		return participant

	def addLinguisticType(self, type, constraints, timeAlignable = False, graphicReferences = False, extRef = None):
		newtype = Element("LINGUISTIC_TYPE")
		newtype.attrib['LINGUISTIC_TYPE_ID'] = type
		newtype.attrib['CONSTRAINTS'] = constraints
		if timeAlignable:
			newtype.attrib['TIME_ALIGNABLE'] = 'true'
		else:
			newtype.attrib['TIME_ALIGNABLE'] = 'false'
		if graphicReferences:
			newtype.attrib['GRAPHIC_REFERENCES'] = 'true'
		else:
			newtype.attrib['GRAPHIC_REFERENCES'] = 'false'
		if extRef != None:
			newtype.attrib['EXT_REF'] = extRef
		newIndex = self.getIndexOfLastLinguisticType()
		self.tree.getroot().insert(newIndex, newtype)

	def hasLinguisticType(self, type):
		node = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % type)
		if node == None:
			return False
		else:
			return True

	def addTier(self,  id,  type,  parent = None, defaultLocale = None,  participant = ''):
		newtier = Element("TIER")
		newtier.attrib['TIER_ID'] = id
		newtier.attrib['LINGUISTIC_TYPE_REF'] = type				   
		if parent != None:
			newtier.attrib['PARENT_REF'] = parent
		if defaultLocale != None:
			newtier.attrib['DEFAULT_LOCALE'] = defaultLocale
		newtier.attrib['PARTICIPANT'] = participant
		newIndex = self.getIndexOfLastTier()
		if parent != None:
			i = self.getIndexOfTier(parent)
			if i != None:
				newIndex = i
		self.tree.getroot().insert(newIndex, newtier)				

	def getStartTsForAnnotation(self,  idTier,  idAnnotation):
		a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
		ret = a.attrib['TIME_SLOT_REF1']	  
		return ret

	def getEndTsForAnnotation(self,  idTier,  idAnnotation):	
		a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
		ret = a.attrib['TIME_SLOT_REF2']	   
		return ret

	def getSubAnnotationIdsForAnnotationInTier(self, idAnn, idTier, idSubTier):
		type = self.getLinguisticTypeForTier(idSubTier)
		ret = []
		if self.linguisticTypeIsTimeAlignable(type):
			startTs = self.getStartTsForAnnotation(idTier, idAnn)
			endTs = self.getEndTsForAnnotation(idTier, idAnn)
			ret = self.getAlignableAnnotationIdsForTier(idSubTier, startTs, endTs)
		else:
			ret = self.getRefAnnotationIdsForTier(idSubTier, idAnn)
		return ret

	def getAnnotationIdsForTier(self, idTier):
		type = self.getLinguisticTypeForTier(idTier)
		ret = []	   
		if self.linguisticTypeIsTimeAlignable(type):
			ret = self.getAlignableAnnotationIdsForTier(idTier)
		else:
			ret = self.getRefAnnotationIdsForTier(idTier)
		return ret

	def getRefAnnotationIdForAnnotationId(self, idTier, idAnnotation):
		a = self.tree.find( "TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier, idAnnotation) )
		if a is not None:
			return a.attrib["ANNOTATION_REF"]
		else:
			return None
		
	def getRefAnnotationIdsForTier(self, idTier, annRef = None,  prevAnn = None):
		ret = []
		foundann = []
		prevs = {}
		if annRef == None:
			allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION" % idTier)
			for a in allAnnotations:
				ret.append(a.attrib['ANNOTATION_ID'])
		else:
			if prevAnn == None:
				allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % (idTier, annRef))
			else:
				allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s'][@PREVIOUS_ANNOTATION='%s']" % (idTier, annRef, prevAnn))
			for a in allAnnotations:
				if prevAnn == None and 'PREVIOUS_ANNOTATION' in a.attrib:
					continue
				ret.append(a.attrib['ANNOTATION_ID'])
				foundann.append(a.attrib['ANNOTATION_ID'])
			for id in foundann:
				ret.extend(self.getRefAnnotationIdsForTier(idTier, annRef,  id))
		return ret

	def appendRefAnnotationToTier(self, idTier, idAnnotation, strAnnotation, annRef, prevAnn = None):
		t = self.tree.find("TIER[@TIER_ID='%s']" % idTier)
		if t == None:
			return False
		eAnnotation = Element("ANNOTATION")
		if prevAnn == None:
			eRefAnn = ET.SubElement(eAnnotation, "REF_ANNOTATION", ANNOTATION_ID=idAnnotation, ANNOTATION_REF=annRef)
		else:
			eRefAnn = ET.SubElement(eAnnotation, "REF_ANNOTATION", ANNOTATION_ID=idAnnotation, ANNOTATION_REF=annRef, PREVIOUS_ANNOTATION=prevAnn)
		eAnnVal = ET.SubElement(eRefAnn, "ANNOTATION_VALUE")
		eAnnVal.text = strAnnotation
		t.append(eAnnotation)
		return True

	def getAlignableAnnotationIdsForTier(self, id, startTs = None,  endTs = None):
		ret = []
		ts = {}
		if startTs != None and endTs != None:
			iStartTs = int(re.sub(r"\D", '', startTs))
			iEndTs = int(re.sub(r"\D", '', endTs))
		allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION" % id)
		for a in allAnnotations:
			aStartTs = a.attrib['TIME_SLOT_REF1']
			aEndTs = a.attrib['TIME_SLOT_REF2']
			iAStartTs = int(re.sub(r"\D", '', aStartTs))
			iAEndTs = int(re.sub(r"\D", '', aEndTs))
			if startTs != None and endTs != None:
				if iStartTs > iAStartTs or iEndTs < iAEndTs:
					continue
			id = None
			v = []
			id = a.attrib['ANNOTATION_ID']
			if id:
				ts[id] = iAStartTs
		# sort ids via start timestamp
		alist = sorted(ts.iteritems(), key=lambda (k,v): (v,k))
		for k, v in alist:
			ret.append(k)
		return ret

	def removeAllAnnotationsFromTier(self, idTier):
		t = self.tree.find("TIER[@TIER_ID='%s']" % idTier)
		annotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION" % idTier)
		if t == None or annotations == None:
			return False
		for a in annotations:
			t.remove(a)
		return True

	def removeAnnotationWithId(self, idAnnotation):
		a = self.tree.find("TIER/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % idAnnotation)
		if a != None:
			a.getparent().getparent().remove(a.getparent())
		else:
			a = self.tree.find("TIER/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % idAnnotation)
			if a != None:
				a.getparent().getparent().remove(a.getparent())

	def removeAnnotationsWithRef(self, idRefAnn):
		allAnnotations = self.tree.findall("TIER/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % idRefAnn)
		for a in allAnnotations:
			a.getparent().getparent().remove(a.getparent())

	def getAnnotationValueForAnnotation(self, idTier, idAnnotation):
		type = self.getLinguisticTypeForTier(idTier)
		ret = ''
		if self.linguisticTypeIsTimeAlignable(type):
			a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
			ret = a.findtext('ANNOTATION_VALUE')
		else:
			a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
			ret = a.findtext('ANNOTATION_VALUE')
		if ret == None:
			ret = ''
		return ret

	def setAnnotationValueForAnnotation(self, idTier, idAnnotation, strAnnotation):
		type = self.getLinguisticTypeForTier(idTier)
		ret = ''
		a = None
		if self.linguisticTypeIsTimeAlignable(type):
			a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % (idTier,  idAnnotation))
		else:
			a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % (idTier,  idAnnotation))
		if a == None:
			return False
		a.text = strAnnotation
		return True

	def updatePrevAnnotationForAnnotation(self, idAnnotation, idPrevAnn = None):
		# this will just do nothing for time-aligned tiers
		# if idPrevAnn is None, then the attribute will be removed
		a = self.tree.find("TIER/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % idAnnotation)
		if a != None:
			if idPrevAnn == None:
				del(a.attrib['PREVIOUS_ANNOTATION'])
			else:
				a.attrib['PREVIOUS_ANNOTATION'] = idPrevAnn


class EafPythonic(Eaf):
	"""Class for handling with EAF files the pythonic way"""

	def __init__(self, filename):
		"""Constructor"""
		self.tiersDict = {}
		self.alignableAnnotationsDict = {}
		self.refAnnotationsDict = {}
		self.refAnnotationsDictByTierAndAnnRef = {}
		self.linguistictypesDict = {}
		self.tree = ET.parse(filename)
		self.dictionary = {}
		self.timeSlots = {}
		##dom object created for minidom xml parsing
		##minidom parser can copy xml tags 
		self.dom=parse(filename)

		parser = Xml2Obj()
		rootElement = parser.parse(filename)

		for ltElement in rootElement.getElements("LINGUISTIC_TYPE"):
			ta = False
			idLt = ltElement.getAttribute("LINGUISTIC_TYPE_ID")
			if ltElement.getAttribute("TIME_ALIGNABLE") == "true":
				ta = True
			self.linguistictypesDict[idLt] = ta		   

		#added
		for item in self.tree.findall("TIME_ORDER/TIME_SLOT"):  
			self.timeSlots[item.attrib['TIME_SLOT_ID']] = item.attrib['TIME_VALUE']
			self.largestTimeSlot = item.attrib['TIME_SLOT_ID']

		## added
		for tier in self.tree.findall("TIER"):		   
			tierid = tier.attrib['TIER_ID']

			for alignableAnnotation in tier.findall("ANNOTATION/ALIGNABLE_ANNOTATION"):			  
				anId = alignableAnnotation.attrib['ANNOTATION_ID']
				ts1 = alignableAnnotation.attrib['TIME_SLOT_REF1']
				ts2 = alignableAnnotation.attrib['TIME_SLOT_REF2']								
				value = alignableAnnotation[0].text			 
				self.dictionary.setdefault(anId,[]).append(tierid)			 
				self.dictionary[anId].append(ts1)
				self.dictionary[anId].append(ts2)				
				self.dictionary[anId].append(str(self.timeSlots[ts1]))				
				self.dictionary[anId].append(str(self.timeSlots[ts2]))				
				self.dictionary[anId].append(value)							  

		for tierElement in rootElement.getElements("TIER"):
			idTier = tierElement.getAttribute("TIER_ID")
			linguisticType = tierElement.getAttribute("LINGUISTIC_TYPE_REF")					
			timeAlignable = self.linguistictypesDict[linguisticType]
			participant = tierElement.getAttribute("PARTICIPANT")
			locale = tierElement.getAttribute("PARTICIPANT")
			parent = tierElement.getAttribute("PARENT_REF")
			
			self.tiersDict[idTier] = {
				'linguistic_type' : linguisticType,
				'time_alignable' : timeAlignable,
				'participant' : participant,
				'locale' : locale,
				'parent' : parent
			}
			
			for annotationElement in tierElement.getElements("ANNOTATION"):
				if timeAlignable:
					for alignableElement in annotationElement.getElements("ALIGNABLE_ANNOTATION"):
						idAnn = alignableElement.getAttribute("ANNOTATION_ID")
						ts1 = alignableElement.getAttribute("TIME_SLOT_REF1")
						ts2 = alignableElement.getAttribute("TIME_SLOT_REF2")
						value = alignableElement.getElements("ANNOTATION_VALUE")[0].getData()
						self.alignableAnnotationsDict[idAnn] = {
							'id' : idAnn,
							'tierId' : idTier,
							'ts1' : ts1,
							'ts2' : ts2,
							'value' : value
						}
				else:
					for refElement in annotationElement.getElements("REF_ANNOTATION"):
						idAnn = refElement.getAttribute("ANNOTATION_ID")
						annRef = refElement.getAttribute("ANNOTATION_REF")
						prevAnn = refElement.getAttribute("PREVIOUS_ANNOTATION")
						value = refElement.getElements("ANNOTATION_VALUE")[0].getData()
						self.refAnnotationsDict[idAnn] = {
							'id' : idAnn,
							'tierId' : idTier,
							'annRef' : annRef,
							'prevAnn' : prevAnn,
							'value' : value
						}
						idByTierAndAnnRef = "%s.%s" % (idTier, annRef)
						if idByTierAndAnnRef in self.refAnnotationsDictByTierAndAnnRef:
							self.refAnnotationsDictByTierAndAnnRef[idByTierAndAnnRef].append(idAnn)
						else:
							self.refAnnotationsDictByTierAndAnnRef[idByTierAndAnnRef] = [ idAnn ]

	def tiers(self):
		"""Returns a dictionary of tiers: name -> type"""
		return dict([j.attrib['TIER_ID'], j.attrib['LINGUISTIC_TYPE_REF']] for j in self.tree.findall('TIER'))
		
	def tostring(self):
		"""Returns the XML string representation of the object"""
		return ET.tostring(self.tree.getroot(), pretty_print=True, encoding="utf-8")
	
	def getLocaleForTier(self, idTier):
		"""Returns the locale for the tier given"""
		return self.tiersDict[idTier]["locale"]

	def getParticipantForTier(self, idTier):
		"""Returns the participant for the tier given"""
		return self.tiersDict[idTier]["participant"]

	def getTierIdsForLinguisticType(self, type, parent = None):
		"""Returns the ID for a certain linguistic type"""
		return [ id for id in self.tiersDict
				if self.tiersDict[id]["linguistic_type"] == type
				and (parent == None or self.tiersDict[id]["parent"] == parent)]
	
	def getLinguisticTypeForTier(self, idTier):
		"""Returns the linguistic type for a given tier, returns None if tier not exists"""
		if idTier in self.tierDict:
			return self.tierDict[idTier]['linguistic_type']
		return None
	
	def getAnnotationIdsForTier(self, idTier):
		"""Returns a list of annotation ids for the tier given"""
		return [key for key in self.dictionary.iterkeys() if self.dictionary[key][0]==idTier]

	def getRefAnnotationIdForAnnotationId(self, idTier, idAnnotation):
		"""Returns the ref annotations for the given tier and given annotation"""
		return self.refAnnotationsDict[idAnnotation]["annRef"]

	def getRefAnnotationIdsForTier(self, idTier, annRef = None,  prevAnn = None):
		"""Returns the ref annotations for the entire tier"""
		if annRef != None and prevAnn == None:
			idByTierIdAndAnnRef = "%s.%s" % (idTier, annRef)
			if idByTierIdAndAnnRef in self.refAnnotationsDictByTierAndAnnRef:
				return self.refAnnotationsDictByTierAndAnnRef[idByTierIdAndAnnRef]
			else:
				return []
		else:
			return [ id for id in self.refAnnotationsDict
					if self.refAnnotationsDict[id]["tierId"] == idTier
					and (annRef == None or self.refAnnotationsDict[id]["annRef"] == annRef)
					and (prevAnn == None or self.refAnnotationsDict[id]["prevAnn"] == prevAnn)]

	def getAlignableAnnotationIdsForTier(self, idTier, startTs = None,  endTs = None):
		"""Returns all the alignable annotations for a given tier"""
		return [ id for id in self.alignableAnnotationsDict
				if self.alignableAnnotationsDict[id]["tierId"] == idTier
				and (startTs == None or self.alignableAnnotationsDict[id]["ts1"] == startTs)
				and (endTs == None or self.alignableAnnotationsDict[id]["ts2"] == endTs)]

	def getStartTsForAnnotation(self, idTier, idAnn):
		"""Returns the start time for an annotation, None if the annotation doesn't exist"""
		if idAnn in self.alignableAnnotationsDict:
			return self.alignableAnnotationsDict[idAnn]["ts1"]
		return None
		
	def getEndTsForAnnotation(self, idTier, idAnn):
		"""Returns the end time for an annotation, None if the annotation doesn't exist"""
		if idAnn in self.alignableAnnotationsDict:
			return self.alignableAnnotationsDict[idAnn]["ts2"]
		return None
	
	def getStartTimeForAnnotation(self, idTier, idAnnotation):
		"""Returns the start time for an annotation, None if the annotation doesn't exist"""
		startTs = self.getStartTsForAnnotation(idTier, idAnnotation)
		if startTs is not None:
			return int(self.timeSlots[startTs])
		return None

	def getEndTimeForAnnotation(self, idTier, idAnnotation):
		"""Returns the end time for an annotation, None if the annotation doesn't exist"""
		endTs = self.getEndTsForAnnotation(idTier, idAnnotation)
		if endTs is not None:
			return int(self.timeSlots[endTs])
		return None
				
	def getAnnotationValueForAnnotation(self, idTier, idAnn):
		"""Returns the value for the annotation in the given tier"""
		if self.tiersDict[idTier]["time_alignable"] and idAnn in self.alignableAnnotationsDict:
			return self.alignableAnnotationsDict[idAnn]["value"]
		elif idAnn in self.refAnnotationsDict:
			return self.refAnnotationsDict[idAnn]["value"]
		else:
			return None

	def getLinguisticTypeForTier(self, idTier):
		"""Returns the linguistic type for a tier, None if the tier doesn't exist"""
		if idTier in self.tiersDict:
			return self.tiersDict[idTier]["linguistic_type"]
		return None

	def getSubAnnotationIdsForAnnotationInTier(self, idAnn, idTier, idSubTier):
		"""Returns the subannotations for an annotation in a given tier"""
		ret = []
		if self.tiersDict[idSubTier]["time_alignable"]:
			startTs = self.getStartTsForAnnotation(idTier, idAnn)
			endTs = self.getEndTsForAnnotation(idTier, idAnn)
			ret = self.getAlignableAnnotationIdsForTier(idSubTier, startTs, endTs)
		else:
			ret = self.getRefAnnotationIdsForTier(idSubTier, idAnn)
		return ret

	## extension functions are added from here
	
	def generateTsId(self):
		"""Generaties a new timeslot id"""
		try:
			last = self.tree.find("TIME_ORDER")[-1]
			last_tsId = last.attrib['TIME_SLOT_ID']
			newnumber = int(last_tsId[2:]) + 1
		except:
			newnumber = 1
		return 'ts%d' % newnumber

	def generateAnnotationId(self):
		"""Generates a new annotation id"""
		last = int(self.tree.find("HEADER/PROPERTY").text)
		return 'a%d' % last+1

	def updateAnnotationId(self):
		"""Updates an annotation with a newly generated id"""
		self.tree.find("HEADER/PROPERTY").text = self.generateAnnotationId()		   
	
	def insertAnnotation(self, idTier, start, end, value=''):
		"""Inserts a new annotation in the given tier"""
		#insert time slots with TIME_SLOT_IDs
		numberOfTimeSlots = len(self.tree.findall("TIME_ORDER/TIME_SLOT"))
		newId1 = self.generateTsId()
		newId2 = 'ts' + str(int(newId1[2:]) + 2)
		newEl1 = lxml.etree.Element("TIME_SLOT", TIME_SLOT_ID=newId1, TIME_VALUE=str(start))
		self.tree.find("TIME_ORDER").append(newEl1)
		newEl2 = lxml.etree.Element("TIME_SLOT", TIME_SLOT_ID=newId2, TIME_VALUE=str(end))
		self.tree.find("TIME_ORDER").append(newEl2)
		self.timeSlots[newId1] = start
		self.timeSlots[newId2] = end

		# insert annotation in tier
		newId = self.generateAnnotationId()
		newAnnotation = lxml.etree.Element("ANNOTATION")				
		newAnnotation.append(lxml.etree.Element("ALIGNABLE_ANNOTATION", ANNOTATION_ID=newId, TIME_SLOT_REF1=newId1, TIME_SLOT_REF2=newId2))
		newAnnotation[0].append(lxml.etree.Element("ANNOTATION_VALUE"))
		newAnnotation[0][0].text = value
		tier = self.tree.find("TIER[@TIER_ID='%s']" % idTier)	
		tier.append(newAnnotation)
		self.updateAnnotationId()

	def getAnnotationValueAtTime(self, targetTier, time):
		"""Returns the annotation value at a given time in the given tier"""
		self.getAnnotationValueForAnnotation(targetTier, getAnnotationIdAtTime(targetTier, time))
# 		findTime = lambda time,timeList:min(timeList,key=lambda x:abs(time-x))						  
# 		time = int(time)				 
# 		firstandSecondClosestTime=[]											 
# 		flag = 0
# 		
# 		#possibletimesList will have the list of "ts" used in the targetTier
# 		startEndtimeAnnotationIdList = sorted([[int(self.dictionary[key][3]),int(self.dictionary[key][4]),key] for key, value in self.dictionary.iteritems() if targetTier in value[0]])
# 
# 		if len(startEndtimeAnnotationIdList) > 0:
# 			closestTime = findTime(time,[d[0] for d in startEndtimeAnnotationIdList])			   
# 			firstandSecondClosestTime.append(closestTime)
# 			indexofColesestTime = [d[0] for d in startEndtimeAnnotationIdList].index(closestTime)						  
# 			
# 			if time < closestTime:											
# 					if indexofColesestTime > 0:
# 							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime-1]
# 							firstandSecondClosestTime.append(secondClosestTime)												   
# 			else:
# 					if indexofColesestTime < len(startEndtimeAnnotationIdList)-1:								
# 							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime+1]
# 							firstandSecondClosestTime.append(secondClosestTime)										   
# 							
# 			count = 0				
# 			while count<2:
# 					if count <= len(firstandSecondClosestTime):								
# 						indexOfClosestTime = [d[0] for d in startEndtimeAnnotationIdList].index(firstandSecondClosestTime[count])					
# 						if startEndtimeAnnotationIdList[indexOfClosestTime][0] <= time:
# 								if time <= startEndtimeAnnotationIdList[indexOfClosestTime][1]:									
# 										return self.dictionary[startEndtimeAnnotationIdList[indexOfClosestTime][2]][5]
# 						count = count + 1					
# 		else:
# 			return None
# 		
# 		if flag==0:
# 				return None

	def getAnnotationIdAtTime(self,targetTier,time):
		"""Returns the annotation ID at the given time in the given tier"""
		findTime = lambda time,timeList:min(timeList,key=lambda x:abs(time-x))						  
		time = int(time)				 
		firstandSecondClosestTime=[]											 
		flag = 0
		
		#possibletimesList will have the list of "ts" used in the targetTier
		startEndtimeAnnotationIdList = sorted([[int(self.dictionary[key][3]),int(self.dictionary[key][4]),key] for key, value in self.dictionary.iteritems() if targetTier == value[0]])
		
		if len(startEndtimeAnnotationIdList) > 0:
			closestTime = findTime(time,[d[0] for d in startEndtimeAnnotationIdList])		 
		   
			firstandSecondClosestTime.append(closestTime)
			indexofColesestTime = [d[0] for d in startEndtimeAnnotationIdList].index(closestTime)						  
		 
			if time < closestTime:											
					if indexofColesestTime > 0:
							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime-1]
							firstandSecondClosestTime.append(secondClosestTime)												   
			else:
					if indexofColesestTime < len(startEndtimeAnnotationIdList)-1:								
							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime+1]
							firstandSecondClosestTime.append(secondClosestTime)										   
							
			count = 0
			
			while count<2:
					if count < len(firstandSecondClosestTime):								
						indexOfClosestTime = [d[0] for d in startEndtimeAnnotationIdList].index(firstandSecondClosestTime[count])					
						if startEndtimeAnnotationIdList[indexOfClosestTime][0] <= time:
								if time <= startEndtimeAnnotationIdList[indexOfClosestTime][1]:									
										return startEndtimeAnnotationIdList[indexOfClosestTime][2]
					count = count + 1					
						
			if flag==0:
					return None
		else:
			return None

	def getAnnotationIdsInOverlap(self, targetTier, startOfInterval, endOfInterval):
		"""Returns the annotation IDs that are in overlap within the interval in the given tier"""
		basket = []	  
		findTime = lambda startOfInterval,timeList:min(timeList,key=lambda x:abs(startOfInterval-x))						  
		startOfInterval = int(startOfInterval)				 
		firstandSecondClosestTime=[]											 
		flag = 0		
		#possibletimesList will have the list of "ts" used in the targetTier
		startEndtimeAnnotationIdList = sorted([[int(self.dictionary[key][3]),int(self.dictionary[key][4]),key] for key, value in self.dictionary.iteritems() if targetTier == value[0]])
		startId=0
		endId=0
		if len(startEndtimeAnnotationIdList) != 0:
			closestTime = findTime(startOfInterval,[d[0] for d in startEndtimeAnnotationIdList])			
			firstandSecondClosestTime.append(closestTime)
			indexofColesestTime = [d[0] for d in startEndtimeAnnotationIdList].index(closestTime)		   
			if startOfInterval < closestTime:											
					if indexofColesestTime > 0:
							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime-1]
							firstandSecondClosestTime.append(secondClosestTime)												   
			else:
					if indexofColesestTime < len(startEndtimeAnnotationIdList)-1:								
							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime+1]
							firstandSecondClosestTime.append(secondClosestTime)															   
			count = 0
			firstandSecondClosestTime = sorted(firstandSecondClosestTime)			
			while count< len(firstandSecondClosestTime):
				indexOfClosestTime = [d[0] for d in startEndtimeAnnotationIdList].index(firstandSecondClosestTime[count])				
				if startEndtimeAnnotationIdList[indexOfClosestTime][0] >= startOfInterval:
					if startEndtimeAnnotationIdList[indexOfClosestTime][1] <= endOfInterval:
						startId= startEndtimeAnnotationIdList[indexOfClosestTime][2]
						flag= flag+1
						count =len(firstandSecondClosestTime)
				else:
					if startEndtimeAnnotationIdList[indexOfClosestTime][1] <= endOfInterval:
						if startEndtimeAnnotationIdList[indexOfClosestTime][1] >= startOfInterval:
							 startId= startEndtimeAnnotationIdList[indexOfClosestTime][2]
							 flag= flag+1
							 count =len(firstandSecondClosestTime)
				
				count =count+1		   

			##get the end ID
			findTime = lambda endOfInterval,timeList:min(timeList,key=lambda x:abs(endOfInterval-x))						  
			endOfInterval = int(endOfInterval)				 
			firstandSecondClosestTime=[]													 
			
			#possibletimesList will have the list of "ts" used in the targetTier
			startEndtimeAnnotationIdList = sorted([[int(self.dictionary[key][3]),int(self.dictionary[key][4]),key] for key, value in self.dictionary.iteritems() if targetTier == value[0]])
			closestTime = findTime(endOfInterval,[d[0] for d in startEndtimeAnnotationIdList])			   
			firstandSecondClosestTime.append(closestTime)
			indexofColesestTime = [d[0] for d in startEndtimeAnnotationIdList].index(closestTime)						  
		   
			if endOfInterval < closestTime:											
					if indexofColesestTime > 0:
							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime-1]
							firstandSecondClosestTime.append(secondClosestTime)												   
			else:
					if indexofColesestTime < len(startEndtimeAnnotationIdList)-1:								
							secondClosestTime = [d[0] for d in startEndtimeAnnotationIdList][indexofColesestTime+1]
							firstandSecondClosestTime.append(secondClosestTime)										   
							
			count = 0	 
			firstandSecondClosestTime=sorted(firstandSecondClosestTime)		   
			while count<2:
					if count < len(firstandSecondClosestTime):								
						indexOfClosestTime = [d[0] for d in startEndtimeAnnotationIdList].index(firstandSecondClosestTime[count])					   
						if startEndtimeAnnotationIdList[indexOfClosestTime][0] <= endOfInterval:
							if startEndtimeAnnotationIdList[indexOfClosestTime][0] >= startOfInterval:
##								if endOfInterval <= startEndtimeAnnotationIdList[indexOfClosestTime][1]:						
										flag=flag+1
										endId= startEndtimeAnnotationIdList[indexOfClosestTime][2]										
						if len(firstandSecondClosestTime) == 1:
							count = 1
						count = count + 1
			
		if startId != 0:
			if endId == 0:
				basket.append(startId)
				return basket
		elif startId == 0:
			if endId !=0:
				basket.append(endId)
				return basket
			if endId == 0:
				return None
   
		repeat =1
		start= int(startId.split('a')[1])
		end= int(endId.split('a')[1])

		while repeat:
			anId = 'a'+str(start)			
			if anId in self.dictionary.keys():
				if str(self.alignableAnnotationsDict[anId]['tierId'])==targetTier:
					basket.append(anId)				
			start=start+1
			if(start>end):
				repeat = 0
		
		return basket

	def removeTier(self, tierId):
		"""Removes the given tier"""
		linguisticTypeRef = self.getLinguisticTypeForTier(tierId)
		tiers = [] 
		if linguisticTypeRef != "default-lt":						
			tiers = self.tree.findall("TIER[@LINGUISTIC_TYPE_REF='%s']" %linguisticTypeRef)
			if len(tiers) == 1:
				self.removeLingusticType(linguisticTypeRef)	   
		a= self.tree.find("TIER[@TIER_ID='%s']"% tierId)
		self.tree.getroot().remove(a) 
		self.cleanTimeSlots()

	def cleanTimeSlots(self): 
		"""Cleans the timeslots"""
		a = self.tree.find("TIME_ORDER")
		timeSlotsInTiers = []		   
		for tier in self.tiers():
			for annotation in self.tree.find("TIER[@TIER_ID='%s']" % tier):
				try:							
					timeSlotsInTiers.append(annotation[0].attrib["TIME_SLOT_REF1"])
					timeSlotsInTiers.append(annotation[0].attrib["TIME_SLOT_REF2"])
				except:
					pass	
		for element in a.getchildren():
			if element.attrib['TIME_SLOT_ID'] not in timeSlotsInTiers:
				a.remove(element)
							
	def addControlledVocabularyToLinguisticType(self, linguisticType, cvId):
		"""Adds a controlled Vocabulary to a linguistic type"""
		a = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % linguisticType)
		a.set("CONTROLLED_VOCABULARY_REF", cvId)

	
	def createControlledVocabulary(self, cvEntries, cvId, description=''):
		"""Creates a controlled vocabulary"""
		newEl = lxml.etree.Element("CONTROLLED_VOCABULARY", CV_ID=cvId, DESCRIPTION=description)
		for item in cvEntries:
				newEl.append(lxml.etree.Element("CV_ENTRY", DESCRIPTION=''))
				newEl.getchildren()[-1].text = item
		self.tree.getroot().append(newEl)
				
	def removeControlledVocabulary(self, cv):
		"""Removes a controlled vocabulary"""
		a= self.tree.find("CONTROLLED_VOCABULARY[@CV_ID='%s']" % cv)
		if a is not None:
			a.getparent().remove(a)	

	def getVideotimeOrigin(self):
		"""Returns the video start time, None if there is none"""
		media = self.tree.find("HEADER")
		media_file = media.getchildren()
		flag= 0
		for i in range(len(media_file)):
			file_type = media_file[i].get("MIME_TYPE")
			if file_type is not None:
				if file_type.startswith('video'):
					flag =1
					time_origin= media_file[i].get("TIME_ORIGIN")
					return time_origin
		if flag==0:
			return None

	def getAudiotimeOrigin(self):
		"""Returns the audio start time, None if there is none"""
		media = self.tree.find("HEADER")
		media_file = media.getchildren()
		flag= 0
		for i in range(len(media_file)):
			file_type = media_file[i].get("MIME_TYPE")
			if file_type is not None:
				if file_type.startswith('audio'):
					flag =1
					time_origin= media_file[i].get("TIME_ORIGIN")
					return time_origin
		if flag==0:
			return None

						   
	def getAudio(self):
		"""Returns the audio file, None if there is none"""
		media = self.tree.find("HEADER")
		media_files = media.getchildren()		
		flag = 0		
		for i in range(len(media_files)):		   
			file_type = media_files[i].get("MIME_TYPE")
			if file_type is not None:
				if file_type.startswith('audio'):
					flag=1
					file_name = media_files[i].get("MEDIA_URL")
					file_name = file_name.split("file:///")[-1]			
					return str(file_name)
		if flag==0:
			return None

	def getVideo(self):
		"""Returns the video file, None if there is none"""
		media = self.tree.find("HEADER")
		media_files = media.getchildren()		
		flag = 0
		for i in range(len(media_files)):		   
			file_type = media_files[i].get("MIME_TYPE")
			if file_type is not None:
				if file_type.startswith('video'):
					flag=1
					file_name = media_files[i].get("MEDIA_URL")
					file_name = file_name.split("file:///")[-1]
					return str(file_name)
		if flag==0:
			return None
	
	def extract(self,from_time,to_time,file_name,margin=0):
		"""Extracts a frame out of the elan file and saves it to the filename given"""
		#file_name : extracted part of the ELAN is save as the file_name
		#from_time and to_time are the time range of extraction
		#margin is the amount of time should be added to from_time and to_time	
		file_audio = self.getAudio()
		file_video = self.getVideo()
		from_time = from_time+margin
		to_time = to_time+margin		
		 
		audio_origin = self.getAudiotimeOrigin()
		video_origin = self.getVideotimeOrigin()
		
		if audio_origin is not None:
			 from_time_audio = audio_origin+from_time
		else:
			from_time_audio = from_time		   

		file_name = file_name+'_'+str(from_time)+'_'+str(to_time)
		
		if video_origin is not None:
			from_time_video = int(video_origin)+int(from_time)
		else:
			from_time_video = from_time		
		
		error = self.createEaffile(file_audio,file_video,from_time_audio,from_time_video,file_name)
		file_name=file_name+'.eaf'
		
		if error is None:
			newFile_obj = EafPythonic(file_name)
			
			old_tiers = self.tree.findall('TIER')
			for tier in old_tiers:
				tierid= tier.attrib['TIER_ID']
				##gets the attribute information of the tier
				##More attributes can be added				
				try:
					tier_id=tier.attrib['TIER_ID']
				except:
					tier_id=''
					pass			
				try:
					tier_type=tier.attrib['LINGUISTIC_TYPE_REF']					 
				except:
					tier_type='default-lt'
					pass
				try:
					tier_participant=tier.attrib['PARTICIPANT']
				except:
					tier_participant=''
					pass
				try:
					tier_annotator=tier.attrib['ANNOTATOR']
				except:
					tier_annotator=''
					pass
				try:
					tier_parent=tier.attrib['PARENT']
				except:
					tier_parent=None
					pass
				try:
					tier_default_locale=tier.attrib['DEFAULT_LOCALE']
				except:
					tier_default_locale=None
					pass
				
				try:
					newFile_obj.addTier(tier_id,tier_type,tier_parent,tier_default_locale,tier_participant)
				except:
					pass				
				#get the annotations in the range from_time+margin to to_time+margin
				anids_inrange=self.getAnnotationIdsInOverlap(tierid,from_time,to_time)				
				##add the annotations to the 'tier_id'
				if anids_inrange is not None:
					startTimesForallIDs = []
					startTimesForallIDs.append(int(from_time))
					for sub_anid in anids_inrange:
						startTimesForallIDs.append(self.getStartTimeForAnnotation(tierid,sub_anid))
						
					minStarttime = min(startTimesForallIDs)
					for sub_anid in anids_inrange:
						startTime = self.getStartTimeForAnnotation(tierid,sub_anid)-int(minStarttime)
						endTime = self.getEndTimeForAnnotation(tierid,sub_anid)-self.getStartTimeForAnnotation(tierid,sub_anid) + startTime
						newFile_obj.insertAnnotation(tier_id,startTime,endTime,self.getAnnotationValueForAnnotation(tierid,sub_anid))				
				
				fi=file_name.split('.eaf')[0]+str(tier_id)+'.eaf'
			
			##add linguistic type and controlled vocabulary
			LINGUISTIC_text=''
			CONSTRAINT_text=''
			CONTROLLED_VOCABULARY_text = ''
			##adding the linguistic type and controlled vocabulary using minidom object
			for child in self.dom.childNodes:
				for subchild in child.childNodes:
					##if conditions can be added if there are more xml tags					
					if subchild.nodeName == 'LINGUISTIC_TYPE':
						if subchild.getAttribute('LINGUISTIC_TYPE_ID') != 'default-lt':
							LINGUISTIC_text = LINGUISTIC_text+subchild.toxml("utf-8")				   
					elif subchild.nodeName == 'CONTROLLED_VOCABULARY':
						CONTROLLED_VOCABULARY_text= CONTROLLED_VOCABULARY_text+subchild.toxml("utf-8")

			
			linguistic_xml= newFile_obj.tostring()		  
			##adding linguistic type by appending the dom text to the xml
			##linguistic type
			default_LINGUISTIC_text='<LINGUISTIC_TYPE GRAPHIC_REFERENCES="false" LINGUISTIC_TYPE_ID="default-lt" TIME_ALIGNABLE="true"/>'
			output_xml=linguistic_xml.split(default_LINGUISTIC_text)[0]
			output_xml=output_xml+default_LINGUISTIC_text+LINGUISTIC_text+linguistic_xml.split(default_LINGUISTIC_text)[1]			
			##adding controlled vocabulary by appending the dom text to the xml
			##controlled vocabulary			
			output_xml = output_xml.split('</ANNOTATION_DOCUMENT>')[0]
			output_xml=output_xml+CONTROLLED_VOCABULARY_text+'</ANNOTATION_DOCUMENT>'	  
			
			f=open(file_name,'w')
			f.write(output_xml)
			f.close()

	##gets the gaps and overlaps, speaker and duration
	def getGapsAndOverlapsduration(self,tier1,tier2):
		"""Returns a list of gaps and overlaps"""
		##timeA contains the start and end time of each annotation in tier1
		timeA=[[int(self.dictionary[key][3]),int(self.dictionary[key][4])] for key, value in self.dictionary.iteritems() if tier1==value[0]]
		##timeB contains the start and end time of each annotation in tier1
		timeB=[[int(self.dictionary[key][3]),int(self.dictionary[key][4])] for key, value in self.dictionary.iteritems() if tier2==value[0]]
		timeA=sorted(timeA)
		timeB=sorted(timeB)	  
		duration=self.__gapsandOverlaps(timeA,timeB)

		return duration
		

	## adds gaps and overlap between the two given tiers	 
	def createGapsAndOverlapsTier(self, tier1, tier2, tierName=None):
		"""Creates a tier containing the gaps and overlaps with an optional tierName"""
		##timeA contains the start and end time of each annotation in tier1
		timeA=[[int(self.dictionary[key][3]),int(self.dictionary[key][4])] for key, value in self.dictionary.iteritems() if tier1==value[0]]
		##timeB contains the start and end time of each annotation in tier1
		timeB=[[int(self.dictionary[key][3]),int(self.dictionary[key][4])] for key, value in self.dictionary.iteritems() if tier2==value[0]]
		timeA=sorted(timeA)
		timeB=sorted(timeB)	  
		duration=self.__gapsandOverlaps(timeA,timeB)
		
		if tierName is None:
			tierName = 'gapOverlap_'+tier1+'_'+tier2

		try:
			self.removeTier(tierName)
		except:
			pass
		
		self.addTier(tierName,'default-lt')
	   
		if len(timeA) != 0:
			if len(timeB) != 0:
				for i in range(len(duration)):
				  if float(duration[i][0] < 0):
						 start = float(duration[i][2])
						 end = (float(duration[i][2]) + (-1 * float(duration[i][0])))
						 start = str(start).split('.')[0]
						 end = str(end).split('.')[0]
						 text = "overlap_"+str(duration[i][1])
						 self.insertAnnotation(tierName,start,end,text)
				  elif float(duration[i][0] > 0):				
						 end = float(duration[i][2])
						 start = (float(duration[i][2]) - (float(duration[i][0])))
						 start = str(start).split('.')[0]
						 end = str(end).split('.')[0]
						 text = "gap_"+str(duration[i][1])
						 self.insertAnnotation(tierName,start,end,text)
			

	def __gapsandOverlaps(self,timeA, timeB):
		"""Internal function that searches for gaps and overlaps"""
		#check who is starting the conversation
		duration = []
	  
		if len(timeA) == 0:
			return duration
		elif len(timeB) == 0:
			return duration
			
		if timeA[len(timeA)-1][1] < timeB[len(timeB)-1][1]:
			count = len(timeA)
		else:
			count = len(timeB)
		
		countA = 0
		countB = 0
		i = 0
		 
		if timeA[countA][0]< timeB[countB][0]:
				speaker ="A"
		else:
				speaker ="B"
	 
		while(i < count-1):			
			overlap_tag=''	  
			overlap = 0
			gap = 0
			startTime = 0
			if speaker == "A":
				#A has continous speech with gaps
				#these gaps are not considered as gaps between
				#speakers
				if countA < len(timeA)-1:								
					if timeB[countB][0] >= timeA[countA+1][0]:
						countA +=1
					elif timeB[countB][0] == timeB[countB-1][1]:
						countB+=1
						speaker = "B" 
					#B is interepting A
					elif timeB[countB][0] < timeA[countA][1]:
						#how much time B is intereptig A
						if timeB[countB][1] < timeA[countA][1]:																	   
							overlap = timeB[countB][0] - timeB[countB][1]					   
							startTime = timeB[countB][0]
							countB +=1										
						else:					   
							overlap = timeB[countB][0] - timeA[countA][1]					   
							startTime = timeB[countB][0]
							countA +=1
							speaker = "B"										
					#B is followig A
					elif timeB[countB][0] > timeA[countA][1]:				   
						gap = timeB[countB][0] - timeA[countA][1]
						startTime = timeB[countB][0]
						countA +=1
						speaker = "B"							 
					else:
						speaker = "B"
						countA +=1
				else:
					#B is interepting A
					if timeB[countB][0] < timeA[countA][1]:
						#how much time B is intereptig A
						if timeB[countB][1] < timeA[countA][1]:					 
							overlap = timeB[countB][0] - timeB[countB][1]
							startTime = timeB[countB][0]
							countB +=1										  
						else:					   
							overlap = timeB[countB][0]-timeA[countA][1]					 
							startTime = timeB[countB][0]
							countA +=1
							speaker = "B"										
					#B is followig A
					elif timeB[countB][0] > timeA[countA][1]:				   
						gap = timeB[countB][0] - timeA[countA][1]
						startTime = timeB[countB][0]
						countA +=1
						speaker = "B"							 
					else:
						speaker = "B"
						countA +=1
					
			elif speaker == "B":
				#B has continous speech with gaps
				#these gaps ar not considered as gaps between
				#speakers
				if countB < len(timeB)-1:
					if timeA[countA][0] >= timeB[countB+1][0]:
						countB +=1
					elif timeA[countA][0] == timeA[countA-1][1]:
						countA+=1
						speaker = "A" 
					#A is interepting B
					elif timeA[countA][0] < timeB[countB][1]:
						#how much time A is intereptig B
						if timeA[countA][1] < timeB[countB][1]:					 
							overlap = timeA[countA][0] - timeA[countA][1]					   
							startTime = timeA[countA][0]
							countA +=1
						
						else:					   
							overlap = timeA[countA][0]-timeB[countB][1]					 
							startTime = timeA[countA][0]
							countB +=1
							speaker = "A"														   
					#A is followig B
					elif timeA[countA][0] > timeB[countB][1]:				   
						gap = timeA[countA][0] - timeB[countB][1]
						startTime = timeA[countA][0]
						countB +=1
						speaker = "A"
					else:
						speaker = "A"
						countB +=1
				else:
					#A is interepting B
					if timeA[countA][0] < timeB[countB][1]:
						#how much time A is intereptig B
						if timeA[countA][1] < timeB[countB][1]:							
							overlap = timeA[countA][0] - timeA[countA][1]					   
							startTime = timeA[countA][0]
							countA +=1
							speaker = 'A'
						else:
							overlap = timeA[countA][0]-timeB[countB][1]					 
							startTime = timeA[countA][0]
							countB +=1
							speaker = "A"														   
					#A is followig B
					elif timeA[countA][0] > timeB[countB][1]:				   
						gap = timeA[countA][0] - timeB[countB][1]			   
						startTime = timeA[countA][0]
						countB +=1
						speaker = "A"
					else:
						speaker = "A"
						countB +=1		
				
			
			if overlap != 0:
				if len(duration) > 0:
					if startTime >= duration[len(duration)-1][2]:
						duration.append([])
						duration[len(duration)-1].append(overlap)
						duration[len(duration)-1].append(speaker)
						duration[len(duration)-1].append(startTime)
				else:
					duration.append([])
					duration[len(duration)-1].append(overlap)
					duration[len(duration)-1].append(speaker)
					duration[len(duration)-1].append(startTime)
			if gap != 0:
				if len(duration) >0:
					if startTime >= duration[len(duration)-1][2]:
						duration.append([])
						duration[len(duration)-1].append(gap)
						duration[len(duration)-1].append(speaker)
						duration[len(duration)-1].append(startTime)
				else:
					duration.append([])
					duration[len(duration)-1].append(gap)
					duration[len(duration)-1].append(speaker)
					duration[len(duration)-1].append(startTime)
					

			if timeA[len(timeA)-1][1] < timeB[len(timeB)-1][1]:
				i = countA
			else:
				i = countB

		overlap =0
		gap =0
	
		if speaker == "A":			
			if timeA[countA][1] < timeB[countB][0]:
				gap = timeB[countB][0]-timeA[countA][1]
				startTime = timeB[countB][0]
			elif timeA[countA][1] >timeB[countB][0]:
				overlap = timeA[countA][1] - timeB[countB][1]
				startTime = timeA[countA][1]
			
		elif speaker == "B":				  
			if timeB[countB][1] < timeA[countA][0]:
				gap = timeA[countA][0]-timeB[countB][1]
				startTime = timeA[countA][0]
			elif timeB[countB][1] >timeA[countA][0]:
				overlap = timeB[countB][1] - timeA[countA][1]
				startTime = timeB[countB][1]
	  
		if overlap != 0:
			duration.append([])
			duration[len(duration)-1].append(overlap)
			duration[len(duration)-1].append(speaker)
			duration[len(duration)-1].append(startTime)
		if gap != 0:
			duration.append([])
			duration[len(duration)-1].append(gap)
			duration[len(duration)-1].append(speaker)
			duration[len(duration)-1].append(startTime)
	   
		return duration		 
			
	
	def createEaffile(self, file_audio, file_video=None,start_time_audio_ms=None,start_time_video_ms=None,file_name=None):
		"""Generates an eaf file from arguments"""
		if file_audio is not None:
			file_audio= file_audio.replace('\\','/')
		else:
			file_audio = None
		if file_video is not None:
			file_video= file_video.replace('\\','/')
						
		xmlText = '<ANNOTATION_DOCUMENT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" AUTHOR="" DATE="2012-07-17T18:18:15+01:00" FORMAT="2.7" VERSION="2.7" '
		xmlText +=  'xsi:noNamespaceSchemaLocation="http://www.mpi.nl/tools/elan/EAFv2.7.xsd">'+'\n'
		xmlText += '	   <HEADER MEDIA_FILE="" TIME_UNITS="milliseconds">'+'\n'
		
		if start_time_audio_ms is not None:
			xmlText += '			   <MEDIA_DESCRIPTOR MEDIA_URL="file:///'+file_audio+'" MIME_TYPE="audio/x-wav" RELATIVE_MEDIA_URL="file:'+file_audio+'" TIME_ORIGIN="'+str(start_time_audio_ms)+'"/>'+'\n'
		else:
			xmlText += '			   <MEDIA_DESCRIPTOR MEDIA_URL="file:///'+file_audio+'" MIME_TYPE="audio/x-wav" RELATIVE_MEDIA_URL="file:'+file_audio+'"/>'+'\n'
		
		if file_video is not None: 
			if start_time_video_ms is not None:
				xmlText += '			   <MEDIA_DESCRIPTOR MEDIA_URL="file:///'+file_video+'" MIME_TYPE="audio/x-wav" RELATIVE_MEDIA_URL="file:'+file_video+'" TIME_ORIGIN="'+str(start_time_video_ms)+'"/>'+'\n'
			else:
				xmlText += '			   <MEDIA_DESCRIPTOR MEDIA_URL="file:///'+file_video+'" MIME_TYPE="audio/x-wav" RELATIVE_MEDIA_URL="file:'+file_video+'"/>'+'\n'
		
		xmlText += '			   <PROPERTY NAME="lastUsedAnnotationId">0</PROPERTY>'+'\n'
		xmlText += '	   </HEADER>' + '\n'
		xmlText += '	   <TIME_ORDER/>' + '\n'
		xmlText += '	   <TIER LINGUISTIC_TYPE_REF="default-lt" TIER_ID="default"/>'+'\n'+'	   <LINGUISTIC_TYPE GRAPHIC_REFERENCES="false" LINGUISTIC_TYPE_ID="default-lt" TIME_ALIGNABLE="true"/>'+'\n'+'	   <CONSTRAINT DESCRIPTION="Time subdivision of parent annotation'+"'"+'s time interval, no time gaps allowed within this interval" STEREOTYPE="Time_Subdivision"/>'+'\n'+ '	   <CONSTRAINT DESCRIPTION="Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered" STEREOTYPE="Symbolic_Subdivision"/>'+'\n'+'	   <CONSTRAINT DESCRIPTION="1-1 association with a parent annotation" STEREOTYPE="Symbolic_Association"/>'+'\n'+'	   <CONSTRAINT DESCRIPTION="Time alignable annotations within the parent annotation'+"'"+'s time interval, gaps are allowed" STEREOTYPE="Included_In"/>'+'\n'+'</ANNOTATION_DOCUMENT>'
		
		if file_name is not None:
			outputFile= file_name+'.txt'
		else:
			outputFile = file_audio.split('.')[0]+'.txt'
			
		outputFile = outputFile.replace('\\','/')
		fo = open(outputFile,'w')
		fo.write(xmlText)		
		fo.close()
		
		try:
			base = os.path.splitext(outputFile)[0]
			os.rename(outputFile, base+".eaf")
		except:
			 print 'this file already exists:'
			 print file_name
			 print 'Please delete and try again'
			 return 'error'
	
	def addTier(self,  idTier,  tierType,  parent = None, defaultLocale = None,  participant = ''):
		"""Adds a tier"""
		newtier = Element("TIER")
		newtier.attrib['TIER_ID'] = idTier
		newtier.attrib['LINGUISTIC_TYPE_REF'] = tierType
		if parent != None:
			newtier.attrib['PARENT_REF'] = parent
		if defaultLocale != None:
			newtier.attrib['DEFAULT_LOCALE'] = defaultLocale
		newtier.attrib['PARTICIPANT'] = participant
		newIndex = self.getIndexOfLastTier()
		if parent != None:
			i = self.getIndexOfTier(parent)
			if i != None:
				newIndex = i
		self.tree.getroot().insert(newIndex, newtier) 
			 
## still working on this function
	def removeLinguisticType(self, linguisticType):
		"""NOT FINISHED: removes a linguistic type"""
		a = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % linguisticType)							  
		a.getparent().remove(a)
		self.removeControlledVocabulary(linguisticType)
			
		
class XmlElement(object):
	''' A parsed XML element '''
	
	def __init__(self, name, attributes):
		
		# Record tagname and attributes dictionary
		self.name = name
		self.attributes = attributes
		# Initialize the element's cdata and children to empty
		self.cdata = ''
		self.children = [  ]
		
	def addChild(self, element):
		self.children.append(element)
		
	def getAttribute(self, key):
		return self.attributes.get(key)
		
	def getData(self):
		return self.cdata
	
	def getElements(self, name=''):
		if name:
			return [c for c in self.children if c.name == name]
		else:
			return list(self.children)

class Xml2Obj(object):
	
	def __init__(self):
		self.root = None
		self.nodeStack = [  ]

	def startElement(self, name, attributes):
		'Expat start element event handler'
		# Instantiate an Element object
		element = XmlElement(name.encode( ), attributes)
		# Push element onto the stack and make it a child of parent
		if self.nodeStack:
			parent = self.nodeStack[-1]
			parent.addChild(element)
		else:
			self.root = element
		self.nodeStack.append(element)

	def endElement(self, name):
		'Expat end element event handler'
		self.nodeStack.pop( )

	def characterData(self, data):
		'Expat character data event handler'
		if data.strip( ):
			#data = data.decode("utf-8")
			#data = data.encode( )
			element = self.nodeStack[-1]
			element.cdata += data

	def parse(self, filename):
		# Create an Expat parser
		Parser = expat.ParserCreate("utf-8")
		# Set the Expat event handlers to our methods
		Parser.StartElementHandler = self.startElement
		Parser.EndElementHandler = self.endElement
		Parser.CharacterDataHandler = self.characterData
		# Parse the XML File
		ParserStatus = Parser.Parse(open(filename).read( ), 1)
		return self.root
