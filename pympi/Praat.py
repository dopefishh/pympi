#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import re
import struct
import sys

VERSION = '1.29'

regfloat = re.compile('([\d.]+)\s*$')
lamfloat = lambda x: struct.unpack('>d', x.read(8))[0]
regint = re.compile('([\d]+)\s*$')
lamint = lambda x: struct.unpack('>i', x.read(4))[0]
lamsht = lambda x: struct.unpack('>h', x.read(2))[0]
regstr = re.compile('"(.*)"\s*$')


def lamstr(ifile):
    textlen = lamsht(ifile)
    if textlen == 0:
        return u''
    elif textlen > 0:
        return ifile.read(textlen)
    elif textlen == -1:
        textlen = lamsht(ifile)
        return ''.join(unichr(struct.unpack('>h', i)[0]) for i in
                       re.findall('.{2}', ifile.read(textlen*2)))


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
                 stream=False, binary=False):
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
        else:
            if stream:
                self.from_stream(file_path, codec)
            else:
                ifile = sys.stdin if file_path == '-' else open(file_path, 'r')
                self.from_stream(ifile, codec)
                if file_path != '-':
                    ifile.close()

    def from_stream(self, ifile, codec='ascii'):
        """Read textgrid from stream.

        :param file ifile: Stream to read from.
        :param str codec: Text encoding.
        """
        if ifile.read(12) == 'ooBinaryFile':
            ifile.read(ord(ifile.read(1)))  # skip oo type
            self.xmin = lamfloat(ifile)
            self.xmax = lamfloat(ifile)
            ifile.read(1)  # skip <exists>
            self.tier_num = lamint(ifile)
            for i in range(self.tier_num):
                self.tiers.append(Tier(ifile=ifile, codec=codec, binary=True))
        else:
            # Skip the Headers and empty line
            next(ifile), next(ifile), next(ifile)
            self.xmin = float(regfloat.search(next(ifile)).group(1))
            self.xmax = float(regfloat.search(next(ifile)).group(1))
            # Skip <exists>
            line = next(ifile)
            short = line.strip() == '<exists>'
            self.tier_num = int(regint.search(next(ifile)).group(1))
            if not short:
                next(ifile)
            for i in range(self.tier_num):
                if not short:
                    next(ifile)  # skip item[]: and item[\d]:
                self.tiers.append(Tier(ifile=ifile, codec=codec))

    def update(self):
        """Update the xmin, xmax and number of tiers value"""
        self.tier_num = len(self.tiers)

    def sort_tiers(self, key=None):
        """Sort the tiers given the key. Example key functions:

        Sort according to the tiername in a list:

        ``lambda x: ['name1', 'name2' ... 'namen'].index(x.name)``.

        Sort according to the number of annotations:

        ``lambda x: len(x.get_intervals())``

        Sort by name in reverse:

        ``lambda x: list(reversed(['name1', 'name2' ...
        'namen'])).index(x.name)``.

        :param func key: A key function. Default sorts on name.
        """
        if not key:
            key = lambda x: x.name
        self.tiers.sort(key=key)

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
            number = 1 if not self.tiers else len(self.tiers)+1
        elif number < 1 or number > len(self.tiers):
            raise ValueError(
                'Number has to be in [1..{}]'.format(len(self.tiers)))
        elif tier_type not in ['IntervalTier', 'TextTier']:
            raise ValueError(
                'tier_type has to be either IntervalTier or TextTier')
        self.tiers.insert(number-1, Tier(name, tier_type))
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
            if (num and self.tiers.index(tier)+1 == name_num) or\
                    not num and tier.name == name_num:
                self.tiers.remove(tier)
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
            if (num and self.tiers.index(tier)+1 == name_num) or\
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
        return list(enumerate((s.name for s in self.tiers), 1))

    def to_file(self, filepath, codec='utf-8', short=False):
        """Write the object to a file.

        :param str filepath: Path of the file, '-' for stdout.
        :param str codec: Text encoding.
        """
        try:
            stream = sys.stdout if filepath == '-' else\
                codecs.open(filepath, 'w', codec)
            self.to_stream(stream, codec, short)
        finally:
            if stream != sys.stdout:
                stream.close()

    def to_stream(self, f, codec='utf-8', short=False):
        """Write the object to a stream.

        :param file f: Open stream to write to.
        :param str codec: Text encoding.
        :param bool short: Flag to use the short notation(saves space)
        """
        for t in self.tiers:
            t.update()
        self.update()
        f.write(u'File type = "ooTextFile"\nObject class = "TextGrid"\n\n')
        f.write(u'{}{:f}\n'.format('' if short else 'xmin = ', self.xmin))
        f.write(u'{}{:f}\n'.format('' if short else 'xmax = ', self.xmax))
        f.write(u'{}\n'.format('<exists>' if short else 'tiers? <exists>'))
        f.write(u'{}{:d}\n'.format('' if short else 'size = ', self.tier_num))
        if not short:
            f.write(u'item []:\n')
        for tnum, tier in enumerate(self.tiers, 1):
            if not short:
                f.write(u'{}item [{:d}]:\n'.format(' '*4, tnum))
            f.write(u'{}"{}"\n'.format(
                '' if short else ' '*8+'class = ', tier.tier_type))
            f.write(u'{}"{}"\n'.format(
                '' if short else ' '*8+'name = ', tier.name))
            f.write(u'{}{:f}\n'.format(
                '' if short else ' '*8+'xmin = ', tier.xmin))
            f.write(u'{}{:f}\n'.format(
                '' if short else ' '*8+'xmax = ', tier.xmax))
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
                f.write(u'{}{:d}\n'.format(
                    '' if short else ' '*8+'intervals: size = ', len(ints)))
                for i, c in enumerate(ints):
                    if not short:
                        f.write(u'{}intervals [{:d}]:\n'.format(' '*8, i+1))
                    f.write(u'{}{:f}\n'.format(
                        '' if short else ' '*12+'xmin = ', c[0]))
                    f.write(u'{}{:f}\n'.format(
                        '' if short else ' '*12+'xmax = ', c[1]))
                    line = u'{}"{}"\n'.format(
                        '' if short else ' '*12+'text = ',
                        c[2].replace('"', '""'))
                    f.write(line)
            elif tier.tier_type == 'TextTier':
                f.write(u'{}{:d}\n'.format(
                    '' if short else ' '*8+'points: size = ', len(srtint)))
                for i, c in enumerate(srtint):
                    if not short:
                        f.write(u'{}points [{:d}]:\n'.format(' '*8, i + 1))
                    f.write(u'{}{:f}\n'.format(
                        '' if short else ' '*12+'number = ', c[0]))
                    line = u'{}"{}"\n'.format(
                        '' if short else ' '*12+'mark = ',
                        c[1].replace('"', '""'))
                    f.write(line)

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
    :var str tier_type: Type of the tier('IntervalTier' or 'TextTier').
    :var int xmin: Minimum x value.
    :var int xmax: Maximum x value.
    """

    def __init__(self, name=None, tier_type=None, ifile=None, codec='ascii',
                 binary=False):
        """Creates a tier, if lines is ``None`` a new tier is created and codec
        is ignored.

        :param str name: Name of the tier.
        :param str tier_type: Type of the tier('IntervalTier' or 'TextTier').
        :param iter lines: Iterator of the input lines.
        :param str codec: Text encoding of the input.
        :param bool binary: Flag to read the files in binary.
        :raises TierTypeException: If the tier type is unknown.
        """
        self.intervals = []
        if ifile is None:
            self.name = name
            self.tier_type = tier_type
            self.xmin, self.xmax = 0, 0
        else:
            if binary:
                self.tier_type = ifile.read(ord(ifile.read(1)))
                self.name = lamstr(ifile)
                self.xmin = lamfloat(ifile)
                self.xmax = lamfloat(ifile)
                nint = lamint(ifile)
                for i in range(nint):
                    x1 = lamfloat(ifile)
                    if self.tier_type == 'IntervalTier':
                        x2 = lamfloat(ifile)
                    text = lamstr(ifile)
                    if self.tier_type == 'IntervalTier':
                        self.intervals.append((x1, x2, text))
                    elif self.tier_type == 'TextTier':
                        self.intervals.append((x1, text))
                    else:
                        raise TierTypeException()
            else:
                self.tier_type = regstr.search(next(ifile)).group(1)
                self.name = regstr.search(next(ifile)).group(1)
                self.xmin = float(regfloat.search(next(ifile)).group(1))
                self.xmax = float(regfloat.search(next(ifile)).group(1))
                line = next(ifile)
                short = not (line.strip().startswith('intervals:') or
                             line.strip().startswith('points:'))
                for i in range(int(regint.search(line).group(1))):
                    if not short:
                        next(ifile)  # skip intervals [\d]
                    x1 = float(regfloat.search(next(ifile)).group(1))
                    if self.tier_type == 'IntervalTier':
                        x2 = float(regfloat.search(next(ifile)).group(1))
                        t = regstr.search(next(ifile)).group(1)
                        self.intervals.append((x1, x2, t))
                    elif self.tier_type == 'TextTier':
                        t = regstr.search(next(ifile)).group(1)
                        self.intervals.append((x1, t))
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
