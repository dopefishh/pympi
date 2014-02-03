#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings

class TextGrid:
	"""Class to read and write in TextGrid files, note all the times are in seconds
	xmin    - maximum x value
	xmax    - maximum y value
	tierNum - number of tiers currently present
	tiers   - dict of tiers
	"""
	def __init__(self, filePath=None):
		"""Constructor, if the filepath is not given an empty TextGrid is created"""
		self.tiers = dict()
		if filePath is None:
			self.xmin = 0
			self.xmax = 0
			self.tierNum = 0
		else:
			with open(filePath, 'r') as f:
				lines = f.readlines()
				self.xmin = float(lines[3][7:-1])
				self.xmax = float(lines[4][7:-1])
				self.tierNum = int(lines[6][7:-1])
				lines = lines[8:]
				for currentTier in range(self.tierNum):
					number = int(lines[0].strip()[6:-2])
					tierType = lines[1].strip()[9:-1]
					name = lines[2].strip()[8:-1]
					numinterval = int(lines[5].strip()[18:])
					self.tiers[name] = Tier(name, number, tierType, lines[:6+4*numinterval])
					lines = lines[6+4*numinterval:]

	def __update(self):
		"""Update the internal values"""
		self.xmin = 0 if len(self.tiers) == 0 else min(tier.xmin for tier in self.tiers.itervalues())
		self.xmax = 0 if len(self.tiers) == 0 else max(tier.xmax for tier in self.tiers.itervalues())
		self.tierNum = len(self.tiers)

	def addTier(self, name, tierType='IntervalTier', number=None):
		"""Add a tier to the grid the number it gets is optional and when not given it will be generated, the added tier is returned"""
		if number is None:
			number = 1 if len(self.tiers) is 0 else int(max(j.number for j in self.tiers.itervalues()))+1
		self.tiers[name] = Tier(name, number, tierType)
		self.__update()
		return self.tiers[name]

	def removeTier(self, name):
		"""Removes a tier, when the tier doesn't exist nothing happens"""
		if name in self.tiers:
			del(self.tiers[name])
			return 0
		else:
			warning.warn('removeTier: tier non existent')
			return 1

	def getTier(self, name):
		"""Returns the tier if it exists else it returns None"""
		try:
			return self.tiers[name]
		except KeyError:
			warnings.warn('getTier: tier non existent')
			return None

	def getTiers(self):
		"""Returns the dictionary with tiers"""
		return self.tiers

	def getGapsAndOverlapsDuration(self, tier1, tier2):
		"""Gives the gaps and the overlaps between tiers in (type, begin, end), None if one of the tiers doesn't exist"""
		if tier1 not in self.tiers or tier2 not in self.tiers: return None
		spkr1anns = sorted(self.tiers[tier1].getIntervals())
		spkr2anns = sorted(self.tiers[tier2].getIntervals())
		line1 = []
		isin = lambda x, lst: False if len([i for i in lst if i[0]<=x and i[1]>=x])==0 else True
		minmax = (min(spkr1anns[0][0], spkr2anns[0][0]), max(spkr1anns[-1][1], spkr2anns[-1][1]))
		last = (1, minmax[0])
		for ts in xrange(*minmax):
			in1, in2 = isin(ts, spkr1anns), isin(ts, spkr2anns)
			if in1 and in2:
				if last[0] == 'B': continue
				ty = 'B'
			elif in1:
				if last[0] == '1': continue
				ty = '1'
			elif in2:
				if last[0] == '2': continue
				ty = '2'
			else:
				if last[0] == 'N': continue
				ty = 'N'
			line1.append( (last[0], last[1], ts) )
			last = (ty, ts)
		line1.append( (last[0], last[1], minmax[1]) )
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

	def createGapsAndOverlapsTier(self, tier1, tier2, tierName=None):
		"""Creates a gaps and overlap tier and returns the gaps and overlaps as triplets(type, start, end)"""
		if tierName is None: tierName = '%s_%s_go' % (tier1, tier2)
		self.removeTier(tierName)
		goTier = self.addTier(tierName)
		ftos = self.getGapsAndOverlapsDuration(tier1, tier2)
		for fto in ftos:
			goTier.addInterval(fto[1], fto[2], fto[0])
		return ftos

	def tofile(self, filepath):
		"""Writes the object to a file given by the filepath"""
		with open(filepath, 'w') as f:
			for t in self.tiers.itervalues():
				t.update()
			self.__update()
			f.write(('File Type = "ooTextFile\n'+
					'Object class = "TextGrid"\n\n'+
					'xmin = %f\n'+
					'xmax = %f\n'+
					'tiers? <exists>\n'+
					'size = %d\n'+
					'item []:\n') % (self.xmin, self.xmax, self.tierNum))
			for tierName in sorted(self.tiers.keys(), key=lambda k: self.tiers[k].number):
				tier = self.getTier(tierName)
				f.write('%sitem [%d]:\n' % (' '*4, tier.number))
				f.write('%sclass = "%s"\n' % (' '*8, tier.tierType))
				f.write('%sname = "%s"\n' % (' '*8, tier.name))
				f.write('%sxmin = %f\n' % (' '*8, tier.xmin))
				f.write('%sxmax = %f\n' % (' '*8, tier.xmax))
				sorted(tier.getIntervals())
				ints = []
				for i in sorted(tier.getIntervals()):
					if ints and ints[-1][1] != i[0]:
						ints.append( (ints[-1][1], i[0], "") )
					ints.append(i)
				f.write('%sintervals: size = %d\n' % (' '*8, len(ints)))
				for i, c in enumerate(ints):
					if tier.tierType is 'TextTier':
						f.write('%spoints [%d]:\n' % (' '*8, i+1))
						f.write('%snumber = %f\n' % (' '*12, c[0]))
						f.write('%smark = "%s"\n' % (' '*12, c[1]))
					elif tier.tierType is 'IntervalTier':
						f.write('%sintervals [%d]:\n' % (' '*8, i+1))
						f.write('%sxmin = %f\n' % (' '*12, c[0]))
						f.write('%sxmax = %f\n' % (' '*12, c[1]))
						f.write('%stext = "%s"\n' % (' '*12, c[2].encode('utf-8').replace('"', '')))

	def toEaf(self, filepath):
		"""Converts the object to elan's eaf format, pointtiers not converted, returns 0 if succesfull"""
		try:
			from Elan import Eaf
		except ImportError:
			warnings.warn('toEaf: Please install the Eaf module from the Elan.py file found at https://github.com/dopefishh/pympi')
			return 1
		eafOut = Eaf()
		for tier in self.tiers:
			eafOut.addTier(tier)
			for annotation in self.tiers[tier].intervals:
				eafOut.insertAnnotation(tier, int(annotation[0]*1000), int(annotation[1]*1000), annotation[2])
		eafOut.tofile(filepath)
		return 0

class Tier:
	"""Class to represent a TextGrid tier: IntervalTier or TextTier"""

	"""
	name      - tier name
	intervals - list of intervals (start, [end,] value)
	number    - number of the tier
	tierType  - TextTier or IntervalTier
	xmin      - minimum x value
	xmax      - maximum x value
	"""

	def __init__(self, name, number, tierType, lines=None):
		"""Constructor, if no lines are given a empty tier is created"""
		self.name = name
		self.intervals = list()
		self.number = number
		self.tierType = tierType
		if lines is None:
			self.xmin, self.xmax = 0, 0
		else:
			self.xmin = float(lines[3].strip()[7:])
			self.xmax = float(lines[4].strip()[7:])
			numInt = int(lines[5].strip().split('=')[1].strip())
			lines = lines[6:]
			if self.tierType == 'IntervalTier':
				for i in range(numInt):
					data = lines[4*i+1:4*i+1+3]
					xmin = float(data[0].strip()[7:])
					xmax = float(data[1].strip()[7:])
					xtxt = data[2].strip()[8:-1]
					self.intervals.append((xmin, xmax, xtxt))
			elif self.tierType == 'TextTier':
				for i in range(numInt):
					data = lines[3*i+1:4*i+3]
					number = float(data[0].strip()[7:])
					mark = data[1].strip()[8:-1]
					self.intervals.append((number, mark))
			else:
				raise Exception('Unknown tiertype: %s' % self.tierType)

	def update(self):
		"""Update the internal values"""
		self.intervals.sort()
		if self.tierType is 'TextTier':
			self.xmin = min(self.intervals)[0]
			self.xmax = max(self.intervals)[0]
		elif self.tierType is 'IntervalTier':
			self.xmin = min(self.intervals)[0]
			self.xmax = max(self.intervals)[1]

	def addPoint(self, point, value, check=True):
		"""Adds a point to the tier"""
		if self.tierType is not 'TextTier': 
			warnings.warn('addPoint: Wrong tier type... Tier should be a TextTier')
			return 1
		elif check is False or point not in [i[0] for i in self.intervals]:
			self.intervals.append((point, value))
		else:
			warnings.warn('addPoint: No overlap is allowed!')
			return 1
		return 1
		self.__update()

	def addInterval(self, begin, end, value, check=True, threshhold=5):
		"""Add an interval to the tier, with overlap checking(default: true)"""
		if self.tierType is not 'IntervalTier': 
			warnings.warn('addInterval: Wrong tier type... Tier should be a IntervalTier')
			return 1
		if check is False or len([i for i in self.intervals if begin<i[1]-threshhold and end>i[0]+threshhold]) == 0:
			self.intervals.append((begin, end, value))
		else:
			warnings.warn('addInterval: No overlap is allowed!')
			return 1
		return 0
		self.__update()

	def removeInterval(self, time):
		"""Removes the interval at the given time, returns the number of removals"""
 		for r in [i for i in self.intervals if i[0]<=time and i[1]>=time]:
			self.intervals.remove(r)
		return len(remove)

	def getIntervals(self):
		"""Returns all the intervals in (begin, end, text) format"""
		return self.intervals

	def clearIntervals(self):
		"""Removes all the intervals in the tier"""
		self.intervals = []
