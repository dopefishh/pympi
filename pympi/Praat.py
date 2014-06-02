#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import re
import sys
import warnings

rexmin = re.compile(r'xmin = ([0-9.]*)')
rexmax = re.compile(r'xmax = ([0-9.]*)')
retext = re.compile(r'text = "(.*)"')
remark = re.compile(r'mark = "(.*)"')
resize = re.compile(r'size = ([0-9]*)')
renumb = re.compile(r'number = ([0-9.]*)')
reitem = re.compile(r'item \[([0-9]*)\]')
retype = re.compile(r'class = "(.*)"')
rename = re.compile(r'name = "(.*)"')


class TextGrid:
    """Class to read and write in TextGrid files,
<br />
    note all the times are in seconds<br />
    xmin    - maximum x value<br />
    xmax    - maximum y value<br />
    tierNum - number of tiers currently present<br />
    tiers   - dict of tiers<br />
    """
    def __init__(self, filePath=None, codec='ascii'):
        """Constructor,
<br />
        filePath -- Filepath to read from - for stdin<br />
        codec    -- File encoding"""
        self.tiers = dict()
        if filePath is None:
            self.xmin = 0
            self.xmax = 0
            self.tierNum = 0
        else:
            if filePath == "-":
                f = sys.stdin
            else:
                f = codecs.open(filePath, 'r', codec)
            lines = [line for line in f.readlines() if line]
            self.xmin = float(rexmin.search(lines[3]).group(1))
            self.xmax = float(rexmax.search(lines[4]).group(1))
            self.tierNum = int(resize.search(lines[6]).group(1))
            lines = lines[8:]
            for currentTier in range(self.tierNum):
                number = int(reitem.search(lines[0]).group(1))
                tierType = retype.search(lines[1]).group(1)
                name = rename.search(lines[2]).group(1)
                numinterval = int(resize.search(lines[5]).group(1))
                lpitem = 3 if tierType == 'TextTier' else 4
                self.tiers[name] = Tier(name, number, tierType,
                                        lines[:6 + lpitem * numinterval])
                lines = lines[6+lpitem*numinterval:]
            f.close()

    def __update(self):
        """Update the internal values"""
        self.xmin = 0 if len(self.tiers) == 0 else\
            min(tier.xmin for tier in self.tiers.itervalues())
        self.xmax = 0 if len(self.tiers) == 0 else\
            max(tier.xmax for tier in self.tiers.itervalues())
        self.tierNum = len(self.tiers)

    def addTier(self, name, tierType='IntervalTier', number=None):
        """
        Add a tier<br />
<br />
        name     -- Name of the tier<br />
        tierType -- Type of the tier<br />
        number   -- Position of the tier"""
        if number is None:
            number = 1 if len(self.tiers) is 0 else\
                int(max(j.number for j in self.tiers.itervalues()))+1
        self.tiers[name] = Tier(name, number, tierType)
        self.__update()
        return self.tiers[name]

    def removeTier(self, name):
        """
        Remove a tier<br />
<br />
        name -- Name of the tier"""
        if name in self.tiers:
            del(self.tiers[name])
            return 0
        else:
            warning.warn('removeTier: tier non existent')
            return 1

    def getTier(self, name):
        """
        Give a tier<br />
<br />
        name -- Name of the tier"""
        try:
            return self.tiers[name]
        except KeyError:
            warnings.warn('getTier: tier non existent')
            return None

    def getTiers(self):
        """Give a dictionary with the tiers"""
        return self.tiers

#    def getGapsAndOverlapsDuration(self, tier1, tier2):
#        """
#        Give a list of gaps and overlaps between tiers (type, begin, end)<br />
#<br />
#        tier1 -- Name of tier 1<br />
#        tie<br />
#        """Gives the gaps and the overlaps between tiers in (type, begin, end)
#        None if one of the tiers doesn't exist"""
#        if tier1 not in self.tiers or tier2 not in self.tiers:
#            return None
#        spkr1anns = sorted(self.tiers[tier1].getIntervals())
#        spkr2anns = sorted(self.tiers[tier2].getIntervals())
#        line1 = []
#        isin = lambda x, lst: False if\
#            len([i for i in lst if i[0] <= x and i[1] >= x]) == 0 else True
#        minmax = (min(spkr1anns[0][0], spkr2anns[0][0]),
#                  max(spkr1anns[-1][1], spkr2anns[-1][1]))
#        last = (1, minmax[0])
#        for ts in xrange(*minmax):
#            in1, in2 = isin(ts, spkr1anns), isin(ts, spkr2anns)
#            if in1 and in2:
#                if last[0] == 'B':
#                    continue
#                ty = 'B'
#            elif in1:
#                if last[0] == '1':
#                    continue
#                ty = '1'
#            elif in2:
#                if last[0] == '2':
#                    continue
#                ty = '2'
#            else:
#                if last[0] == 'N':
#                    continue
#                ty = 'N'
#            line1.append((last[0], last[1], ts))
#            last = (ty, ts)
#        line1.append((last[0], last[1], minmax[1]))
#        ftos = []
#        for i in xrange(len(line1)):
#            if line1[i][0] == 'N':
#                if i != 0 and i < len(line1) - 1 and\
#                        line1[i - 1][0] != line1[i + 1][0]:
#                    ftos.append(('G12_%s_%s' % (tier1, tier2)
#                                 if line1[i-1][0] == '1' else
#                                 'G21_%s_%s' % (tier2, tier1), line1[i][1],
#                                 line1[i][2]))
#                else:
#                    ftos.append(('P_%s' % tier1
#                                 if line1[i-1][0] == '1' else
#                                 tier2, line1[i][1], line1[i][2]))
#            elif line1[i][0] == 'B':
#                if i != 0 and i < len(line1) - 1 and\
#                        line1[i - 1][0] != line1[i + 1][0]:
#                    ftos.append(('O12_%s_%s' % (tier1, tier2)
#                                 if line1[i-1][0] else
#                                 'O21_%s_%s' % (tier2, tier1), line1[i][1],
#                                 line1[i][2]))
#                else:
#                    ftos.append(('B_%s' % tier1 if line1[i - 1][0] == '1' else
#                                 tier2, line1[i][1], line1[i][2]))
#        return ftos
#
#    def createGapsAndOverlapsTier(self, tier1, tier2, tierName=None):
#        """Creates a gaps and overlap tier and returns the gaps and
#        overlaps as triplets(type, start, end)"""
#        if tierName is None:
#            tierName = '%s_%s_go' % (tier1, tier2)
#        self.removeTier(tierName)
#        goTier = self.addTier(tierName)
#        ftos = self.getGapsAndOverlapsDuration(tier1, tier2)
#        for fto in ftos:
#            goTier.addInterval(fto[1], fto[2], fto[0])
#        return ftos

    def tofile(self, filepath, codec='utf-16'):
        """
        Write the object to a file<br />
<br />
        filepath -- Path to write to - for stdout<br />
        codec    -- Encoding to write to"""
        if filepath == "-":
            f = sys.stdout
        else:
            f = codecs.open(filepath, 'w', codec)
        for t in self.tiers.itervalues():
            t.update()
        self.__update()
        f.write(('File Type = "ooTextFile\n' +
                 'Object class = "TextGrid"\n\n' +
                 'xmin = %f\n' +
                 'xmax = %f\n' +
                 'tiers? <exists>\n' +
                 'size = %d\n' +
                 'item []:\n') % (self.xmin, self.xmax, self.tierNum))
        for tierName in sorted(self.tiers.keys(),
                               key=lambda k: self.tiers[k].number):
            tier = self.getTier(tierName)
            f.write('%sitem [%d]:\n' % (' '*4, tier.number))
            f.write('%sclass = "%s"\n' % (' '*8, tier.tierType))
            f.write('%sname = "%s"\n' % (' '*8, tier.name))
            f.write('%sxmin = %f\n' % (' '*8, tier.xmin))
            f.write('%sxmax = %f\n' % (' '*8, tier.xmax))
            srtint = sorted(tier.getIntervals())
            ints = []
            if srtint and srtint[0][0] > 0.0:
                ints.append((0.0, srtint[0][0], ""))
            for i in srtint:
                if i[1] - i[0] == 0:
                    continue
                if ints and ints[-1][1] < i[0]:
                    ints.append((ints[-1][1], i[0], ""))
                ints.append(i)
            f.write('%sintervals: size = %d\n' % (' '*8, len(ints)))
            for i, c in enumerate(ints):
                if tier.tierType == 'TextTier':
                    f.write('%spoints [%d]:\n' % (' '*8, i + 1))
                    f.write('%snumber = %f\n' % (' '*12, c[0]))
                    f.write('%smark = "%s"\n' % (' '*12,
                                                 c[1].replace('"', '""')))
                elif tier.tierType == 'IntervalTier':
                    f.write('%sintervals [%d]:\n' % (' '*8, i + 1))
                    f.write('%sxmin = %f\n' % (' '*12, c[0]))
                    f.write('%sxmax = %f\n' % (' '*12, c[1]))
                    f.write('%stext = "%s"\n' % (' '*12,
                                                 c[2].replace('"', '""')))
        if filepath != "-":
            f.close()

    def toEaf(self, filepath):
        """
        Write to eaf<br />
<br />
        filepath -- Filepath to write to - for stdout"""
        try:
            from pympi.Elan import Eaf
        except ImportError:
            warnings.warn('toEaf: Please install the pympi.Elan.Eaf module f' +
                          'from the pympi package found at https://github.co' +
                          'm/dopefishh/pympi')
            return 1
        eafOut = Eaf()
        for tier in self.tiers:
            eafOut.addTier(tier)
            for annotation in self.tiers[tier].intervals:
                eafOut.insertAnnotation(tier, int(annotation[0]*1000),
                                        int(annotation[1]*1000), annotation[2])
        eafOut.tofile(filepath)
        return 0


class Tier:
    """Class to represent a TextGrid tier: IntervalTier or TextTier
<br />
    name      - tier name<br />
    intervals - list of intervals (start, [end,] value)<br />
    number    - number of the tier<br />
    tierType  - TextTier or IntervalTier<br />
    xmin      - minimum x value<br />
    xmax      - maximum x value<br />
    """

    def __init__(self, name, number, tierType, lines=None):
        """Constructor
<br />
        name     -- Name of the tier<br />
        number   -- Number of the tier<br />
        tierType -- Type of the tier<br />
        lines    -- Lines to parse the tier information from"""
        self.name = name
        self.intervals = list()
        self.number = number
        self.tierType = tierType
        if lines is None:
            self.xmin, self.xmax = 0, 0
        else:
            self.xmin = float(rexmin.search(lines[3]).group(1))
            self.xmax = float(rexmax.search(lines[4]).group(1))
            numInt = int(resize.search(lines[5]).group(1))
            lines = lines[6:]
            if self.tierType == 'IntervalTier':
                for i in range(numInt):
                    data = lines[4*i+1:4*i+1+3]
                    xmin = float(rexmin.search(data[0]).group(1))
                    xmax = float(rexmax.search(data[1]).group(1))
                    xtxt = retext.search(data[2]).group(1).replace('""', '"')
                    self.intervals.append((xmin, xmax, xtxt))
            elif self.tierType == 'TextTier':
                for i in range(numInt):
                    data = lines[3*i+1:4*i+3]
                    number = float(renumb.search(data[0]).group(1))
                    mark = remark.search(data[1]).group(1).replace('""', '"')
                    self.intervals.append((number, mark))
            else:
                raise Exception('Unknown tiertype: %s' % self.tierType)

    def update(self):
        """Update the internal values"""
        self.intervals.sort()
        if self.tierType is 'TextTier' and self.intervals:
            self.xmin = min(self.intervals)[0]
            self.xmax = max(self.intervals)[0]
        elif self.tierType is 'IntervalTier' and self.intervals:
            self.xmin = min(self.intervals)[0]
            self.xmax = max(self.intervals)[1]

    def addPoint(self, point, value, check=True):
        """
        Add a point to the tier<br />
<br />
        point -- Time point<br />
        value -- Value<br />
        check -- Flag for overlap checking"""
        if self.tierType is not 'TextTier':
            warnings.warn(
                'addPoint: Wrong tier type... Tier should be a TextTier')
            return 1
        elif check is False or point not in [i[0] for i in self.intervals]:
            self.intervals.append((point, value))
        else:
            warnings.warn('addPoint: No overlap is allowed!')
            return 1
        return 1
        self.__update()

    def addInterval(self, begin, end, value, check=True, threshhold=5):
        """
        Add an interval to the tier<br />
<br />
        begin      -- Start time<br />
        end        -- End time<br />
        value      -- Value<br />
        check      -- Flag for overlap checking<br />
        threshhold -- Threshhold for checking overlap"""
        if self.tierType != 'IntervalTier':
            warnings.warn('addInterval: Wrong tier type... Tier should be a ' +
                          'IntervalTier the tier is a')
            return 1
        if check is False or len(
                [i for i in self.intervals
                 if begin < i[1] - threshhold and
                 end > i[0] + threshhold]) == 0:
            self.intervals.append((begin, end, value))
        else:
            warnings.warn('addInterval: No overlap is allowed!')
            return 1
        return 0
        self.__update()

    def removeInterval(self, time):
        """
        Remove an interval at time<br />
<br />
        time -- Time"""
        for r in [i for i in self.intervals if i[0] <= time and i[1] >= time]:
            self.intervals.remove(r)

    def getIntervals(self):
        """Give a list of intervals in (begin, end, text) format"""
        return self.intervals

    def clearIntervals(self):
        """Removes all the intervals in the tier"""
        self.intervals = []
