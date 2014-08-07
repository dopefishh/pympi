#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import itertools
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


class TierNotFoundException(Exception):
    """Exception that is raised when a tier is adressed that doesn't exist"""
    def __init__(self, tier):
        """Construct a TierNotFoundException.

        :param tier: Name or number of the tier.
        :type tier: int or str
        """
        if isinstance(tier, int):
            string = 'Tier with number {} not found...'
        else:
            string = 'Tier with name "{}" not found...'
        Exception.__init__(self, string.format(tier))


class TierTypeException(Exception):
    """Exception that is raised when a tiertype is unknown or wrong for the
    function in which it is raised"""
    def __init__(self):
        """Construct a TierTypeException."""
        Exception.__init__(self, 'Wrong or unknown TierType')


class TextGrid:
    """Read write and edit Praat's TextGrid files.

    .. note:: All times are in seconds and can have decimals

    :var float xmin: Minimum x value.
    :var float xmax: Maximum x value.
    :var int tier_num: Number of tiers.
    :var list tiers: Internal (unsorted) list of tiers.
    :var str codec: Codec of the input file.
    """
    def __init__(self, file_path=None, codec='ascii'):
        """Construct either a new TextGrid object or read one from a
        file/stream.

        :param str file_path: Path to read from, - for stdin. If ``None`` an
                              empty TextGrid will be created.
        :param str codec: Text encoding for the input.
        """
        self.tiers = []
        self.codec = codec
        if not file_path:
            self.xmin, self.xmax, self.tier_num = [0]*3
        else:
            ifile = sys.stdin if file_path == '-' else\
                codecs.open(file_path, 'r', codec)
            lines = itertools.ifilter(lambda x: x.strip(), ifile)
            # skipping: 'File Type...' and 'Object class...'
            lines.next(), lines.next()
            self.xmin = float(rexmin.search(lines.next()).group(1))
            self.xmax = float(rexmax.search(lines.next()).group(1))
            # skipping: 'tiers? <exists>'
            lines.next()
            self.tier_num = int(resize.search(lines.next()).group(1))
            # skipping: 'item []:'
            lines.next()
            for current_tier in xrange(self.tier_num):
                number = int(reitem.search(lines.next()).group(1))
                tier_type = retype.search(lines.next()).group(1)
                name = rename.search(lines.next()).group(1)
                self.tiers.append(Tier(name, tier_type, number, lines, codec))
            if file_path == '-':
                ifile.close()

    def __update(self):
        """Update the xmin, xmax and number of tiers value"""
        self.xmin = 0 if not self.tiers else\
            min(tier.xmin for tier in self.tiers)
        self.xmax = 0 if not self.tiers else\
            max(tier.xmax for tier in self.tiers)
        self.tier_num = len(self.tiers)

    def add_tier(self, name, tier_type='IntervalTier', number=None):
        """Add an Interval or a PointTier on the specified location.

        :param str name: Name of the tier, duplicate names is allowed.
        :param str tier_type: Type of the tier. ('IntervalTier', 'TextTier')
        :param int number: Place to insert the tier, when ``None`` the number
                           is generated and the tier will be placed on the
                           bottom.
        :returns: The created tier.
        :raises ValueError: If the number is out of bounds.
        """
        if number is None:
            number = 1 if not self.tiers else\
                max(i.number for i in self.tiers) + 1
        elif number < 1 or number > len(self.tiers):
            raise ValueError(
                'Number has to be in [1..{}'.format(len(self.tiers)))
        else:
            for tier in self.tiers:
                if tier.number >= number:
                    tier.number += 1
        self.tiers.append(Tier(name, tier_type, number))
        self.__update()
        return self.tiers[-1]

    def remove_tier(self, name_num):
        """Remove a tier, when multiple tiers exist with that name only the
        first is removed.

        :param name_num: Name or number of the tier to remove.
        :type name_num: int or str
        :raises TierNotFoundException: If the tier doesn't exist.
        """
        num = isinstance(name_num, int)
        for tier in self.tiers:
            if (num and tier.number == name_num) or\
                    not num and tier.name == name_num:
                num = tier.number
                self.tiers.remove(tier)
                for tier in self.tiers:
                    if tier.number > num:
                        tier.number -= 1
                break
        else:
            raise TierNotFoundException(name_num)

    def get_tier(self, name_num):
        """Gives a tier, when multiple tiers exist with that name only the
        first is returned.

        :param name_num: Name or number of the tier to return.
        :type name_num: int or str
        :returns: The tier.
        :raises TierNotFoundException: If the tier doesn't exist.
        """
        num = isinstance(name_num, int)
        for tier in self.tiers:
            if (num and tier.number == name_num) or\
                    not num and tier.name == name_num:
                return tier
        raise TierNotFoundException(name_num)

    def change_tier_name(self, name_num, name2):
        """Changes the name of the tier, when multiple tiers exist with that
        name only the first is renamed.

        :param name_num: Name or number of the tier to rename.
        :type name_num: int or str
        :param str name2: New name of the tier.
        :raises TierNotFoundException: If the tier doesn't exist.
        """
        self.get_tier(name_num).name = name2

    def get_tiers(self):
        """Give all tiers.

        :yields: Available tiers
        """
        for tier in self.tiers:
            yield tier

    def get_tier_name_num(self):
        """Give all tiers with their numbers.

        :returns: List consisting of the form
                  ``[(num1, tier1), (num2, tier2) ... (numn, tiern)]``
        """
        return sorted((s.number, s.name) for s in self.tiers)

    def to_file(self, filepath, codec='utf-16'):
        """Write the object to a TextGrid file.

        :param str file_path: Path to write to, - for stdout.
        :param str codec: Text encoding for the output.
        """
        f = sys.stdout if filepath == '-' else\
            codecs.open(filepath, 'w', codec)

        for t in self.tiers:
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
        for tier in sorted(self.tiers, key=lambda x: x.number):
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

    def to_eaf(self):
        """Convert the object to an pympi.Elan.Eaf object

        :returns: :class:`pympi.Elan.Eaf` object
        :raises ImportError: If the Eaf module can't be loaded.
        """
        from pympi.Elan import Eaf
        eaf_out = Eaf()
        for tier in self.tiers:
            eaf_out.add_tier(tier.name)
            for annotation in tier.intervals:
                eaf_out.insert_annotation(tier.name, int(annotation[0]*1000),
                                          int(annotation[1]*1000),
                                          annotation[2])
        return eaf_out


class Tier:
    """Class representing a TextGrid tier, either an Interval or TextTier

    :var str name: Name of the tier.
    :var list intervals: List of intervals where each interval is
                         (start, [end,] value).
    :var int number: Number of the tier.
    :var str tier_type: Type of the tier('IntervalTier' or 'TextTier').
    :var int xmin: Minimum x value.
    :var int xmax: Maximum x value.
    """

    def __init__(self, name, tier_type, number, lines=None, codec='ascii'):
        """Creates a tier, if lines is ``None`` a new tier is created and codec
        is ignored.

        :param str name: Name of the tier.
        :param str tier_type: Type of the tier('IntervalTier' or 'TextTier').
        :param int number: Number of the tier.
        :param iter lines: Iterator of the input lines.
        :param str codec: Text encoding of the input.
        :raises TierTypeException: If the tier type is unknown.
        """
        self.name = name
        self.intervals = list()
        self.number = number
        self.tier_type = tier_type
        if lines is None:
            self.xmin, self.xmax = 0, 0
        else:
            self.xmin = float(rexmin.search(lines.next()).group(1))
            self.xmax = float(rexmax.search(lines.next()).group(1))
            num_int = int(resize.search(lines.next()).group(1))
            if self.tier_type == 'IntervalTier':
                for i in xrange(num_int):
                    # intervals [1]:
                    lines.next()
                    xmin = float(rexmin.search(lines.next()).group(1))
                    xmax = float(rexmax.search(lines.next()).group(1))
                    xtxt = retext.search(lines.next()).group(1).\
                        replace('""', '"')
                    self.intervals.append((xmin, xmax, xtxt))
            elif self.tier_type == 'TextTier':
                for i in range(num_int):
                    # points [1]:
                    lines.next()
                    number = float(renumb.search(lines.next()).group(1))
                    mark = remark.search(lines.next()).group(1).\
                        replace('""', '"')
                    mark = mark.encode(codec)
                    self.intervals.append((number, mark))
            else:
                raise TierTypeException()

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
        """Add a point to the TextTier

        :param int point: Time of the point.
        :param str value: Text of the point.
        :param bool check: Flag to check for overlap.
        :raises TierTypeException: If the tier is not a TextTier.
        :raises Exception: If there is already a point at that time.
        """
        if self.tier_type is not 'TextTier':
            raise TierTypeException()
        if check is False or point not in [i[0] for i in self.intervals]:
            self.intervals.append((point, value))
        else:
            raise Exception('No overlap is allowed')
        self.__update()

    def add_interval(self, begin, end, value, check=True):
        """Add an interval to the IntervalTier.

        :param float begin: Start time of the interval.
        :param float end: End time of the interval.
        :param str value: Text of the interval.
        :param bool check: Flag to check for overlap.
        :raises TierTypeException: If the tier is not an IntervalTier.
        :raises Exception: If there is already an interval in that time.
        """
        if self.tier_type != 'IntervalTier':
            raise TierTypeException()
        if check is False or len([i for i in self.intervals
                                  if begin < i[1] and end > i[0]]) == 0:
            self.intervals.append((begin, end, value))
        else:
            raise Exception('No overlap is allowed!')
        self.update()

    def remove_interval(self, time):
        """Remove a point or an interval, if no point or interval is found
        nothing happens.

        :param int time: Time of the point or time in the interval.
        """
        for r in [i for i in self.intervals if i[0] <= time and i[1] >= time]:
            self.intervals.remove(r)

    def get_intervals(self, sort=False):
        """Give all the intervals or points.

        :param bool sort: Flag for yielding the intervals or points sorted.
        :yields: All the intervals
        """
        if sort:
            self.intervals = sorted(self.intervals)
        for i in self.intervals:
            yield i

    def clearIntervals(self):
        """Removes all the intervals in the tier"""
        self.intervals = []
