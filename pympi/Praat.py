#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import re
import sys

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
    """class to read and write in TextGrid files
    note that all times are in seconds

    Internal variables:
    xmin     -- maximum x value
    xmax     -- maximum y value
    tier_num -- number of tiers currently present
    tiers    -- dict of tiers
    codec    -- codec of the input files
    """
    def __init__(self, file_path=None, codec='ascii'):
        """constructor

        Keyword arguments:
        file_path -- path to read from - for stdin, if None an empty TextGrid
                     object will be created (default None)
        codec     -- source file encoding, only used when filepath is also
                     specified and not stdin
        """
        self.tiers = dict()
        self.codec = codec
        if file_path is None:
            self.xmin = 0
            self.xmax = 0
            self.tier_num = 0
        else:
            if file_path == "-":
                f = sys.stdin
            else:
                f = codecs.open(file_path, 'r', codec)
            lines = [line for line in f if line]
            self.xmin = float(rexmin.search(lines[3]).group(1))
            self.xmax = float(rexmax.search(lines[4]).group(1))
            self.tier_num = int(resize.search(lines[6]).group(1))
            lines = lines[8:]
            for current_tier in range(self.tier_num):
                number = int(reitem.search(lines[0]).group(1))
                tier_type = retype.search(lines[1]).group(1)
                name = rename.search(lines[2]).group(1)
                numinterval = int(resize.search(lines[5]).group(1))
                lpitem = 3 if tier_type == 'TextTier' else 4
                self.tiers[name] = Tier(name, number, tier_type,
                                        lines[:6 + lpitem * numinterval],
                                        codec)
                lines = lines[6+lpitem*numinterval:]
            f.close()

    def __update(self):
        """update the internal values"""
        self.xmin = 0 if not self.tiers else\
            min(tier.xmin for tier in self.tiers.itervalues())
        self.xmax = 0 if not self.tiers else\
            max(tier.xmax for tier in self.tiers.itervalues())
        self.tier_num = len(self.tiers)

    def add_tier(self, name, tier_type='IntervalTier', number=None):
        """add a tier to the object

        Required arguments:
        name      -- name of the tier

        Keyword arguments:
        tier_type -- type of the tier, currently only 'IntervalTier' and
                     'TextTier' are options (default 'IntervalTier')
        number    -- position of the tier, if None the position will be the
                     next available position (default None)
        """
        if number is None:
            number = 1 if not self.tiers else\
                max(i.number for i in self.tiers.itervalues()) + 1
        else:
            for tiername, tier in self.tiers.iteritems():
                if tier.number >= number:
                    tier.number += 1
        self.tiers[name] = Tier(name, number, tier_type)
        self.__update()
        return self.tiers[name]

    def remove_tier(self, name):
        """remove a tier, if the tier doesn't exist the function will return 1

        Required arguments:
        name -- name of the tier to remove
        """
        if name in self.tiers:
            num = self.tiers[name].number
            del(self.tiers[name])
            for tiername, tier in self.tiers.iteritems():
                if tier.number > num:
                    tier.number -= 1

    def get_tier(self, name):
        """get a tier, returns None if the tier doesn't exist

        Required arguments:
        name -- name of the tier
        """
        return self.tiers.get(name)

    def change_tier_name(self, name, name2):
        """change a tier's name

        Required arguments:
        name  -- source name
        name2 -- target name
        """
        if name in self.tiers:
            self.tiers[name2] = self.tiers.pop(name)
            self.tiers[name2].name = name2

    def get_tiers(self):
        """get the internal tier dictionary"""
        return self.tiers

    def to_file(self, filepath, codec='utf-16'):
        """write the object to a file

        Required arguments:
        filepath -- path to write to - for stdout

        Keyword arguments:
        codec    -- character encoding to use (default 'utf-16')
        """
        f = sys.stdout if filepath == '-' else\
            codecs.open(filepath, 'w', codec)

        for t in self.tiers.itervalues():
            t.update()
        self.__update()
        f.write("""\
File Type = "ooTextFile
Object class = "TextGrid"

xmin = {}
xmax = {}
tiers? <exists>
size = {}
item []:
""".format(self.xmin, self.xmax, self.tier_num))
        for tierName in sorted(self.tiers.keys(),
                               key=lambda k: self.tiers[k].number):
            tier = self.get_tier(tierName)
            f.write('{:>4}sitem [{}]:\n'.format(' ', tier.number))
            f.write('{:>8}class = "{}"\n'.format(' ', tier.tier_type))
            f.write('{:>8}name = "{}"\n'.format(' ', tier.name))
            f.write('{:>8}xmin = {}\n'.format(' ', tier.xmin))
            f.write('{:>8}xmax = {}\n'.format(' ', tier.xmax))
            srtint = sorted(list(tier.get_intervals()))
            if tier.tier_type == 'IntervalTier':
                ints = []
                if srtint and srtint[0][0] > 0.0:
                    ints.append((0.0, srtint[0][0], ''))
                for i in srtint:
                    if i[1] - i[0] == 0:
                        continue
                    if ints and ints[-1][1] < i[0]:
                        ints.append((ints[-1][1], i[0], ''))
                    ints.append(i)
                f.write('{:>8}intervals: size = {}\n'.format(' ', len(ints)))
                for i, c in enumerate(ints):
                    f.write('{:>8}intervals [{}]:\n'.format(' ', i+1))
                    f.write('{:>12}xmin = {}\n'.format(' ', c[0]))
                    f.write('{:>12}xmax = {}\n'.format(' ', c[1]))
                    f.write(u'{:>12}text = "{}"\n'.format(
                        ' ', c[2].replace('"', '""').decode(codec)))
            elif tier.tier_type == 'TextTier':
                f.write('{:>8}points: size = {}\n'.format(' ', len(srtint)))
                for i, c in enumerate(srtint):
                    f.write('{:>8}points [{}]:\n'.format(' ', i + 1))
                    f.write('{:>12}number = {}\n'.format(' ', c[0]))
                    f.write('{:>12}mark = "{}"\n'.format(
                        ' ', c[1].replace('"', '""').decode(codec)))
        if filepath != '-':
            f.close()

    def to_eaf(self, filepath):
        """write to eaf

        Required arguments:
        filepath -- path to write to
        """
        try:
            from pympi.Elan import Eaf
        except ImportError:
            raise Exception("""pympi.Elan.Eaf module not found, please install\
it from https://github.com/dopefishh/pympi""")
        eaf_out = Eaf()
        for tier in self.tiers:
            eaf_out.add_tier(tier)
            for annotation in self.tiers[tier].intervals:
                eaf_out.insert_annotation(
                    tier, int(annotation[0]*1000), int(annotation[1]*1000),
                    annotation[2])
        eaf_out.tofile(filepath)


class Tier:
    """class that represents a TextGrid tier: IntervalTier or TextTier

    name      -- tier name
    intervals -- list of intervals (start, [end,] value)
    number    -- number of the tier
    tier_type -- TextTier or IntervalTier
    xmin      -- minimum x value
    xmax      -- maximum x value
    """

    def __init__(self, name, number, tier_type, lines=None, codec='ascii'):
        """constructor

        Required arguments:
        name      -- name of the tier
        number    -- number of the tier
        tier_type -- type of the tier

        Keyword arguments:
        lines     -- lines to parse the tier information from
        """
        self.name = name
        self.intervals = list()
        self.number = number
        self.tier_type = tier_type
        if lines is None:
            self.xmin, self.xmax = 0, 0
        else:
            self.xmin = float(rexmin.search(lines[3]).group(1))
            self.xmax = float(rexmax.search(lines[4]).group(1))
            num_int = int(resize.search(lines[5]).group(1))
            lines = lines[6:]
            if self.tier_type == 'IntervalTier':
                for i in range(num_int):
                    data = lines[4*i+1:4*i+1+3]
                    xmin = float(rexmin.search(data[0]).group(1))
                    xmax = float(rexmax.search(data[1]).group(1))
                    xtxt = retext.search(data[2]).group(1).replace('""', '"')
                    xtxt = xtxt.encode(codec)
                    self.intervals.append((xmin, xmax, xtxt))
            elif self.tier_type == 'TextTier':
                for i in range(num_int):
                    data = lines[3*i+1:4*i+3]
                    number = float(renumb.search(data[0]).group(1))
                    mark = remark.search(data[1]).group(1).replace('""', '"')
                    mark = mark.encode(codec)
                    self.intervals.append((number, mark))
            else:
                raise Exception('Unknown tiertype: {}'.format(self.tier_type))

    def update(self):
        """Update the internal values"""
        self.intervals.sort()
        if self.tier_type is 'TextTier' and self.intervals:
            self.xmin = min(self.intervals)[0]
            self.xmax = max(self.intervals)[0]
        elif self.tier_type is 'IntervalTier' and self.intervals:
            self.xmin = min(self.intervals)[0]
            self.xmax = max(self.intervals)[1]

    def add_point(self, point, value, check=True):
        """add a point to a TextTier

        Required arguments:
        point -- time of the annotation
        value -- text of the annotation

        Keyword arguments:
        check -- flag for overlap checkin (default True)
        """
        if self.tier_type is not 'TextTier':
            raise Exception("""addPoint: Wrong tier type... Tier should be a T\
extTier""")
        elif check is False or point not in [i[0] for i in self.intervals]:
            self.intervals.append((point, value))
        else:
            raise Exception('No overlap is allowed')
        self.__update()

    def add_interval(self, begin, end, value, check=True):
        """add an interval to a IntervalTier

        Required arguments:
        begin      -- start time
        end        -- end time
        value      -- text of the annotation

        Keyword arguments:
        check      -- flag for overlap checking (default=True)
        """
        if self.tier_type != 'IntervalTier':
            raise Exception('Wrong tier type... Tier should be a IntervalTier')
        if check is False or len([i for i in self.intervals
                                  if begin < i[1] and end > i[0]]) == 0:
            self.intervals.append((begin, end, value))
        else:
            raise Exception('No overlap is allowed!')
        self.update()

    def remove_interval(self, time):
        """remove an interval or point

        Required arguments:
        time -- time of the interval or point
        """
        for r in [i for i in self.intervals if i[0] <= time and i[1] >= time]:
            self.intervals.remove(r)

    def get_intervals(self, sort=False):
        """yield the intervals in [(begin, [end, ]text)] format

        Keyword arguments:
        sort -- sort the intervals first
        """
        if sort:
            self.intervals = sorted(self.intervals)
        for i in self.intervals:
            yield i

    def clearIntervals(self):
        """Removes all the intervals in the tier"""
        self.intervals = []
