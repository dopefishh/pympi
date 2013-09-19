#!/usr/bin/env python
# -*- coding: utf-8 -*-

class TextGrid:
	"""Class to read and write in TextGrid files, note all the times are in seconds"""

	def __init__(self, filePath=None):
		"""Constructor, if the filepath is not given an empty grid is created"""
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
		self.xmin = 0 if len(self.tiers) is 0 else min(t.xmin for t in self.tiers.itervalues())
		self.xmax = 0 if len(self.tiers) is 0 else max(t.xmax for t in self.tiers.itervalues())
		self.tierNum = len(self.tiers)

	def addTier(self, name, tierType='IntervalTier', number=None):
		"""Add a tier to the grid the number it gets is optional and when not given it will be generated, the added tier is returned"""
		if number is None:
			number = 1 if len(self.tiers) is 0 else int(max(j.number for j in self.tiers.itervalues()))+1
		self.tiers[name] = Tier(name, number, tierType)
		self.__update()
		return self.tiers[name]

	def removeTier(self, name):
		"""Removes a tier, returns None if failed else 1"""
		if name in self.tiers:
			del(self.tiers[name])
			return 1
		return None
	
	def getTier(self, name):
		"""Returns the tier if it exists else it returns None"""
		return None if not self.tiers.has_key(name) else self.tiers[name]

	def getTiers(self):
		"""Returns the dictionary with tiers"""
		return self.tiers

	def tofile(self, filepath):
		"""Writes the object to a file given by the filepath"""
		self.__update()
		with open(filepath, 'w') as f:
			f.write('File Type = "ooTextFile"\n')
			f.write('Object class = "TextGrid"\n')
			f.write('\n')
			f.write('xmin = %f\n' % self.xmin)
			f.write('xmax = %f\n' % self.xmax)
			f.write('tiers? <exists>\n')
			f.write('size = %d\n' % self.tierNum)
			f.write('item []:\n')
			
			for tierName in sorted(self.tiers.keys(), key=lambda k: self.tiers[k].number):
				tier = self.getTier(tierName)
				f.write('%sitem [%d]:\n' % (' '*4, tier.number))
				f.write('%sclass = "%s"\n' % (' '*8, tier.tierType))
				f.write('%sname = "%s"\n' % (' '*8, tier.name))
				f.write('%sxmin = %f\n' % (' '*8, tier.xmin))
				f.write('%sxmax = %f\n' % (' '*8, tier.xmax))
				f.write('%sintervals: size = %d\n' % (' '*8, len(tier.getIntervals())))
				ints = tier.getIntervals()
				for it in range(len(tier.getIntervals())):
					if tier.tierType is 'TextTier':
						f.write('%spoints [%d]:\n' % (' '*8, it+1))
						f.write('%snumber = %f\n' % (' '*12, ints[it][0]))
						f.write('%smark = "%s"\n' % (' '*12, ints[it][1]))
					elif tier.tierType is 'IntervalTier':
						f.write('%sintervals [%d]:\n' % (' '*8, it+1))
						f.write('%sxmin = %f\n' % (' '*12, ints[it][0]))
						f.write('%sxmax = %f\n' % (' '*12, ints[it][1]))
						f.write('%stext = "%s"\n' % (' '*12, ints[it][2]))

	def toEaf(self, filepath):
		"""Converts the object to elan's eaf format, pointtiers not converted"""
		try:
			from Elan import Eaf
		except ImportError:
			print 'Please install the Eaf module from the Elan.py file found at https://github.com/dopefishh/pympi'
			exit()
		eafOut = Eaf()
		for tier in self.tiers:
			eafOut.addTier(tier)
			for annotation in self.tiers[tier].intervals:
				eafOut.insertAnnotation(tier, int(annotation[0]*1000), int(annotation[1]*1000), annotation[2])
		eafOut.tofile(filepath)

class Tier:
	"""Class to represent a TextGrid tier: IntervalTier or TextTier"""

	def __init__(self, name, number, tierType, lines=None):
		"""Constructor, if no lines are given a empty tier is created"""
		self.name = name
		self.intervals = list()
		self.number = number
		self.tierType = tierType
		if lines is None:
			self.xmin = 0
			self.xmax = 0
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
				raise Exception('Unknown tiertype')
	
	def __update(self):
		"""Update the internal values"""
		self.intervals.sort()
		if self.tierType is 'TextTier':
			self.xmin = min(i[0] for i in self.intervals)
			self.xmax = max(i[0] for i in self.intervals)
		elif self.tierType is 'IntervalTier':
			self.xmin = min(i[0] for i in self.intervals)
			self.xmax = max(i[1] for i in self.intervals)
	
	def addPoint(self, point, value, check=True):
		"""Adds a point to the tier"""
		if self.tierType is not 'TextTier':
			raise Exception('Wrong tier type...')
		elif check is False or point not in [i[0] for i in self.intervals]:
			self.intervals.append((point, value))
		else:
			raise Exception('No overlap is allowed!')
		self.__update()

	def addInterval(self, begin, end, value, check=True, threshhold=5):
		"""Add an interval to the tier, with overlap checking(default: true)"""
		listt = [i for i in self.intervals if begin<i[1]-threshhold and end>i[0]+threshhold]
		if check is False or len(listt) == 0:
			self.intervals.append((begin, end, value))
		else:
			raise Exception('No overlap is allowed!')
		self.__update()
	
	def removeInterval(self, time):
		"""Removes the interval at the given time, returns the number of removals"""
		remove = []
		for interval in self.intervals:
			if interval[0]<=time and interval[1]>=time:
				remove.append(interval)
		for r in remove:
			self.intervals.remove(r)
		return len(remove)

	def getIntervals(self):
		"""Returns all the intervals in (begin, end, text) format"""
		return self.intervals

	def clearIntervals(self):
		"""Removes all the intervals in the tier"""
		self.intervals = []
