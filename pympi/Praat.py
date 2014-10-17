#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import itertools
import re
import sys

VERSION = 1.1

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
    def __init__(self, file_path=None, xmin=0, xmax=None, codec='ascii',
                 stream=False):
        """Construct either a new TextGrid object or read one from a
        file/stream. When you create an empty TextGrid you must at least
        specify the xmax.


        :param str file_path: Path to read from, - for stdin. If ``None`` an
                              empty TextGrid will be created.
        :param int xmin: Xmin value, only needed when not loading from file.
        :param int xmax: Xmax value, needed when not loading from file.
        :param str codec: Text encoding for the input.
        :param bool stream: Flag for loading from a stream(not used, only for
                            debugging purposes)
        :raises Exception: If filepath is specified but no xmax
        """
        self.tiers = []
        self.codec = codec
        if not file_path:
            if xmax is None:
                raise Exception('No xmax specified')
            self.tier_num = 0
            self.xmin = xmin
            self.xmax = xmax
        elif stream:
            self.from_stream(file_path, codec)
        else:
            ifile = sys.stdin if file_path == '-' else\
                codecs.open(file_path, 'r', codec)
            self.from_stream(ifile, codec)
            if file_path != '-':
                ifile.close()

    def from_stream(self, ifile, codec='ascii'):
        """Read textgrid from stream.

        :param file ifile: Stream to read from.
        :param str codec: Text encoding.
        """
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

    def update(self):
        """Update the xmin, xmax and number of tiers value"""
        self.tier_num = len(self.tiers)

    def add_tier(self, name, tier_type='IntervalTier', number=None):
        """Add an IntervalTier or a TextTier on the specified location.

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
                'Number has to be in [1..{}]'.format(len(self.tiers)))
        elif tier_type not in ['IntervalTier', 'TextTier']:
            raise ValueError(
                'tier_type has to be either IntervalTier or TextTier')
        else:
            for tier in self.tiers:
                if tier.number >= number:
                    tier.number += 1
        self.tiers.append(Tier(name, tier_type, number))
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

    def to_file(self, filepath, codec='utf-8'):
        """Write the object to a file.

        :param str filepath: Path of the file, '-' for stdout.
        :param str codec: Text encoding.
        """
        try:
            stream = sys.stdout if filepath == '-' else\
                codecs.open(filepath, 'w', codec)
            self.to_stream(stream, codec)
        finally:
            if stream != sys.stdout:
                stream.close()

    def to_stream(self, f, codec='utf-8'):
        """Write the object to a stream.

        :param file f: Open stream to write to.
        :param str codec: Text encoding.
        """
        for t in self.tiers:
            t.update()
        self.update()
        f.write(u"""\
File Type = "ooTextFile
Object class = "TextGrid"

xmin = {:f}
xmax = {:f}
tiers? <exists>
size = {:d}
item []:
""".format(float(self.xmin), float(self.xmax), self.tier_num))
        for tier in sorted(self.tiers, key=lambda x: x.number):
            f.write(u'{:>4}item [{:d}]:\n'.format(' ', tier.number))
            f.write(u'{:>8}class = "{}"\n'.format(' ', tier.tier_type))
            f.write(u'{:>8}name = "{}"\n'.format(' ', tier.name))
            f.write(u'{:>8}xmin = {:f}\n'.format(' ', tier.xmin))
            f.write(u'{:>8}xmax = {:f}\n'.format(' ', tier.xmax))
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
                if ints and ints[-1][1] < self.xmax:
                    ints.append((ints[-1][1], self.xmax, ''))
                f.write(
                    u'{:>8}intervals: size = {:d}\n'.format(' ', len(ints)))
                for i, c in enumerate(ints):
                    f.write(u'{:>8}intervals [{:d}]:\n'.format(' ', i+1))
                    f.write(u'{:>12}xmin = {:f}\n'.format(' ', c[0]))
                    f.write(u'{:>12}xmax = {:f}\n'.format(' ', c[1]))
                    f.write(u'{:>12}text = "{}"\n'.format(
                        ' ', c[2].replace('"', '""').decode(codec)))
            elif tier.tier_type == 'TextTier':
                f.write(u'{:>8}points: size = {:d}\n'.format(' ', len(srtint)))
                for i, c in enumerate(srtint):
                    f.write(u'{:>8}points [{:d}]:\n'.format(' ', i + 1))
                    f.write(u'{:>12}number = {:f}\n'.format(' ', c[0]))
                    f.write(u'{:>12}mark = "{}"\n'.format(
                        ' ', c[1].replace('"', '""').decode(codec)))

    def to_eaf(self, pointlength=0.1):
        """Convert the object to an pympi.Elan.Eaf object

        :param int pointlength: Length of respective interval from points in
                                seconds
        :returns: :class:`pympi.Elan.Eaf` object
        :raises ImportError: If the Eaf module can't be loaded.
        :raises ValueError: If the pointlength is not strictly positive.
        """
        from pympi.Elan import Eaf
        eaf_out = Eaf()
        if pointlength <= 0:
            raise ValueError('Pointlength should be strictly positive')
        for tier in self.get_tiers():
            eaf_out.add_tier(tier.name)
            for ann in tier.get_intervals(True):
                if tier.tier_type == 'TextTier':
                    ann = (ann[0], ann[0]+pointlength, ann[1])
                eaf_out.insert_annotation(tier.name, int(round(ann[0]*1000)),
                                          int(round(ann[1]*1000)), ann[2])
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
        self.intervals = []
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
                        replace('""', '"').encode(codec)
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

    def add_interval(self, begin, end, value, check=True):
        """Add an interval to the IntervalTier.

        :param float begin: Start time of the interval.
        :param float end: End time of the interval.
        :param str value: Text of the interval.
        :param bool check: Flag to check for overlap.
        :raises TierTypeException: If the tier is not a IntervalTier.
        :raises Exception: If there is already an interval in that time.
        """
        if self.tier_type != 'IntervalTier':
            raise TierTypeException()
        if check is False or\
                not [i for i in self.intervals if begin < i[1] and end > i[0]]\
                and begin < end:
            self.intervals.append((begin, end, value))
        else:
            raise Exception(
                'No overlap is allowed!, and begin should be smaller then end')

    def remove_interval(self, time):
        """Remove an interval, if no interval is found nothing happens.

        :param int time: Time of the interval.
        :raises TierTypeException: If the tier is not a IntervalTier.
        """
        if self.tier_type != 'IntervalTier':
            raise TierTypeException()
        for r in [i for i in self.intervals if i[0] <= time and i[1] >= time]:
            self.intervals.remove(r)

    def remove_point(self, time):
        """Remove a point, if no point is found nothing happens.

        :param int time: Time of the point.
        :raises TierTypeException: If the tier is not a TextTier.
        """
        if self.tier_type != 'TextTier':
            raise TierTypeException()
        for r in [i for i in self.intervals if i[0] == time]:
            self.intervals.remove(r)

    def get_intervals(self, sort=False):
        """Give all the intervals or points.

        :param bool sort: Flag for yielding the intervals or points sorted.
        :yields: All the intervals
        """
        for i in sorted(self.intervals) if sort else self.intervals:
            yield i

    def clear_intervals(self):
        """Removes all the intervals in the tier"""
        self.intervals = []
