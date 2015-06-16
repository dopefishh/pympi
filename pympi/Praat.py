#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import re
import struct

VERSION = '1.30'


class TextGrid:
    """Read write and edit Praat's TextGrid files.

    .. note:: All times are in seconds and can have decimals

    :var float xmin: Minimum x value.
    :var float xmax: Maximum x value.
    :var int tier_num: Number of tiers.
    :var list tiers: Internal (unsorted) list of tiers.
    :var str codec: Codec of the input file.
    """
    def __init__(self, file_path=None, xmin=0, xmax=None, codec='utf-8'):
        """Construct either a new TextGrid object or read one from a
        file/stream. When you create an empty TextGrid you must at least
        specify the xmax. When you want to load a TextGrid from file you need
        to specify at least the file_path and optionally the codec. Binary,
        short and normal TextGrids are supported.

        :param str file_path: Path to read from, - for stdin. If ``None`` an
                              empty TextGrid will be created.
        :param int xmin: Xmin value, only needed when not loading from file.
        :param int xmax: Xmax value, needed when not loading from file.
        :param str codec: Text encoding for the input. Note that this will be
            ignored for binary TextGrids.
        :raises Exception: If filepath is not specified but no xmax
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
            with open(file_path, 'rb') as f:
                self.from_file(f, codec)

    def from_file(self, ifile, codec='ascii'):
        """Read textgrid from stream.

        :param file ifile: Stream to read from.
        :param str codec: Text encoding for the input. Note that this will be
            ignored for binary TextGrids.
        """
        if ifile.read(12) == b'ooBinaryFile':
            def bin2str(ifile):
                textlen = struct.unpack('>h', ifile.read(2))[0]
                # Single byte characters
                if textlen >= 0:
                    return ifile.read(textlen).decode('ascii')
                # Multi byte characters have initial len -1 and then \xff bytes
                elif textlen == -1:
                    textlen = struct.unpack('>h', ifile.read(2))[0]
                    data = ifile.read(textlen*2)
                    # Hack to go from number to unicode in python3 and python2
                    fun = unichr if 'unichr' in __builtins__ else chr
                    charlist = (data[i:i+2] for i in range(0, len(data), 2))
                    return u''.join(
                        fun(struct.unpack('>h', i)[0]) for i in charlist)

            ifile.read(ord(ifile.read(1)))  # skip oo type
            self.xmin = struct.unpack('>d', ifile.read(8))[0]
            self.xmax = struct.unpack('>d', ifile.read(8))[0]
            ifile.read(1)  # skip <exists>
            self.tier_num = struct.unpack('>i', ifile.read(4))[0]
            for i in range(self.tier_num):
                tier_type = ifile.read(ord(ifile.read(1))).decode('ascii')
                name = bin2str(ifile)
                tier = Tier(0, 0, name=name, tier_type=tier_type)
                self.tiers.append(tier)
                tier.xmin = struct.unpack('>d', ifile.read(8))[0]
                tier.xmax = struct.unpack('>d', ifile.read(8))[0]
                nint = struct.unpack('>i', ifile.read(4))[0]
                for i in range(nint):
                    x1 = struct.unpack('>d', ifile.read(8))[0]
                    if tier.tier_type == 'IntervalTier':
                        x2 = struct.unpack('>d', ifile.read(8))[0]
                    text = bin2str(ifile)
                    if tier.tier_type == 'IntervalTier':
                        tier.intervals.append((x1, x2, text))
                    elif tier.tier_type == 'TextTier':
                        tier.intervals.append((x1, text))
                    else:
                        raise Exception('Tiertype does not exist.')
        else:
            def nn(ifile, pat):
                line = next(ifile).decode(codec)
                return pat.search(line).group(1)

            regfloat = re.compile('([\d.]+)\s*$', flags=re.UNICODE)
            regint = re.compile('([\d]+)\s*$', flags=re.UNICODE)
            regstr = re.compile('"(.*)"\s*$', flags=re.UNICODE)
            # Skip the Headers and empty line
            next(ifile), next(ifile), next(ifile)
            self.xmin = float(nn(ifile, regfloat))
            self.xmax = float(nn(ifile, regfloat))
            # Skip <exists>
            line = next(ifile)
            short = line.strip() == b'<exists>'
            self.tier_num = int(nn(ifile, regint))
            not short and next(ifile)
            for i in range(self.tier_num):
                not short and next(ifile)  # skip item[]: and item[\d]:
                tier_type = nn(ifile, regstr)
                name = nn(ifile, regstr)
                tier = Tier(0, 0, name=name, tier_type=tier_type)
                self.tiers.append(tier)
                tier.xmin = float(nn(ifile, regfloat))
                tier.xmax = float(nn(ifile, regfloat))
                for i in range(int(nn(ifile, regint))):
                    not short and next(ifile)  # skip intervals [\d]
                    x1 = float(nn(ifile, regfloat))
                    if tier.tier_type == 'IntervalTier':
                        x2 = float(nn(ifile, regfloat))
                        t = nn(ifile, regstr)
                        tier.intervals.append((x1, x2, t))
                    elif tier.tier_type == 'TextTier':
                        t = nn(ifile, regstr)
                        tier.intervals.append((x1, t))

    def sort_tiers(self, key=lambda x: x.name):
        """Sort the tiers given the key. Example key functions:

        Sort according to the tiername in a list:

        ``lambda x: ['name1', 'name2' ... 'namen'].index(x.name)``.

        Sort according to the number of annotations:

        ``lambda x: len(list(x.get_intervals()))``

        :param func key: A key function. Default sorts alphabetically.
        """
        self.tiers.sort(key=key)

    def add_tier(self, name, tier_type='IntervalTier', number=None):
        """Add an IntervalTier or a TextTier on the specified location.

        :param str name: Name of the tier, duplicate names is allowed.
        :param str tier_type: Type of the tier.
        :param int number: Place to insert the tier, when ``None`` the number
            is generated and the tier will be placed on the bottom.
        :returns: The created tier.
        :raises ValueError: If the number is out of bounds.
        """
        if number is None:
            number = 1 if not self.tiers else len(self.tiers)+1
        elif number < 1 or number > len(self.tiers):
            raise ValueError('Number not in [1..{}]'.format(len(self.tiers)))
        elif tier_type not in Tier.P_TIERS:
            raise ValueError('tier_type has to be in {}'.format(self.P_TIERS))
        self.tiers.insert(number-1,
                          Tier(self.xmin, self.xmax, name, tier_type))
        return self.tiers[number-1]

    def remove_tier(self, name_num):
        """Remove a tier, when multiple tiers exist with that name only the
        first is removed.

        :param name_num: Name or number of the tier to remove.
        :type name_num: int or str
        :raises IndexError: If there is no tier with that number.
        """
        if isinstance(name_num, int):
            del(self.tiers[name_num-1])
        else:
            self.tiers = [i for i in self.tiers if i.name != name_num]

    def get_tier(self, name_num):
        """Gives a tier, when multiple tiers exist with that name only the
        first is returned.

        :param name_num: Name or number of the tier to return.
        :type name_num: int or str
        :returns: The tier.
        :raises IndexError: If the tier doesn't exist.
        """
        return self.tiers[name_num - 1] if isinstance(name_num, int) else\
            [i for i in self.tiers if i.name == name_num][0]

    def change_tier_name(self, name_num, name2):
        """Changes the name of the tier, when multiple tiers exist with that
        name only the first is renamed.

        :param name_num: Name or number of the tier to rename.
        :type name_num: int or str
        :param str name2: New name of the tier.
        :raises IndexError: If the tier doesn't exist.
        """
        self.get_tier(name_num).name = name2

    def get_tiers(self):
        """Give all tiers.

        :yields: All tiers
        """
        for tier in self.tiers:
            yield tier

    def get_tier_name_num(self):
        """Give all tiers with their numbers.

        :yield: Enumerate of the form ``[(num1, tier1),  ... (numn, tiern)]``
        """
        return enumerate((s.name for s in self.tiers), 1)

    def to_file(self, filepath, codec='utf-8', mode='normal'):
        """Write the object to a file.

        :param str filepath: Path of the fil.
        :param str codec: Text encoding.
        :param string mode: Flag to for write mode, possible modes:
            'n'/'normal', 's'/'short' and 'b'/'binary'
        """
        self.tier_num = len(self.tiers)
        if mode in ['binary', 'b']:
            with open(filepath, 'wb') as f:
                def writebstr(s):
                    try:
                        bstr = s.encode('ascii')
                    except UnicodeError:
                        f.write(b'\xff\xff')
                        bstr = b''.join(struct.pack('>h', ord(c)) for c in s)
                    f.write(struct.pack('>h', len(s)))
                    f.write(bstr)

                f.write(b'ooBinaryFile\x08TextGrid')
                f.write(struct.pack('>d', self.xmin))
                f.write(struct.pack('>d', self.xmax))
                f.write(b'\x01')
                f.write(struct.pack('>i', self.tier_num))
                for tier in self.tiers:
                    f.write(chr(len(tier.tier_type)).encode('ascii'))
                    f.write(tier.tier_type.encode('ascii'))
                    writebstr(tier.name)
                    f.write(struct.pack('>d', tier.xmin))
                    f.write(struct.pack('>d', tier.xmax))
                    ints = tier.get_all_intervals()
                    f.write(struct.pack('>i', len(ints)))
                    itier = tier.tier_type == 'IntervalTier'
                    for c in ints:
                        f.write(struct.pack('>d', c[0]))
                        itier and f.write(struct.pack('>d', c[1]))
                        writebstr(c[2 if itier else 1])
        elif mode in ['normal', 'n', 'short', 's']:
            with codecs.open(filepath, 'w', codec) as f:
                short = mode[0] == 's'

                def wrt(indent, prefix, value, ff=''):
                    indent = 0 if short else indent
                    prefix = '' if short else prefix
                    if value is not None or not short:
                        s = u'{{}}{{}}{}\n'.format(ff)
                        f.write(s.format(' '*indent, prefix, value))

                f.write(u'File type = "ooTextFile"\n'
                        u'Object class = "TextGrid"\n\n')
                wrt(0, u'xmin = ', self.xmin, '{:f}')
                wrt(0, u'xmax = ', self.xmax, '{:f}')
                wrt(0, u'tiers? ', u'<exists>', '{}')
                wrt(0, u'size = ', self.tier_num, '{:d}')
                wrt(0, u'item []:', None)
                for tnum, tier in enumerate(self.tiers, 1):
                    wrt(4, u'item [{:d}]:'.format(tnum), None)
                    wrt(8, u'class = ', tier.tier_type, '"{}"')
                    wrt(8, u'name = ', tier.name, '"{}"')
                    wrt(8, u'xmin = ', tier.xmin, '{:f}')
                    wrt(8, u'xmax = ', tier.xmax, '{:f}')
                    if tier.tier_type == 'IntervalTier':
                        ints = tier.get_all_intervals()
                        wrt(8, u'intervals: size = ', len(ints), '{:d}')
                        for i, c in enumerate(ints):
                            wrt(8, 'intervals [{:d}]:'.format(i+1), None)
                            wrt(12, 'xmin = ', c[0], '{:f}')
                            wrt(12, 'xmax = ', c[1], '{:f}')
                            wrt(12, 'text = ', c[2].replace('"', '""'), '"{}"')
                    elif tier.tier_type == 'TextTier':
                        wrt(8, u'points: size = ', len(tier.intervals), '{:d}')
                        for i, c in enumerate(tier.get_intervals()):
                            wrt(8, 'points [{:d}]:'.format(i+1), None)
                            wrt(12, 'number = ', c[0], '{:f}')
                            wrt(12, 'mark = ', c[1].replace('"', '""'), '"{}"')
        else:
            raise Exception('Unknown mode')

    def to_eaf(self, skipempty=True, pointlength=0.1):
        """Convert the object to an pympi.Elan.Eaf object

        :param int pointlength: Length of respective interval from points in
                                seconds
        :param bool skipempty: Skip the empty annotations
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
                if ann[2].strip() or not skipempty:
                    eaf_out.add_annotation(tier.name, int(round(ann[0]*1000)),
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
    P_TIERS = {'IntervalTier', 'TextTier'}

    def __init__(self, xmin, xmax, name=None, tier_type=None):
        """Creates a tier, if lines is ``None`` a new tier is created.

        :param str name: Name of the tier.
        :param str tier_type: Type of the tier('IntervalTier' or 'TextTier').
        :raises TierTypeException: If the tier type is unknown.
        """
        self.intervals = []
        self.name = name
        self.tier_type = tier_type
        self.xmin, self.xmax = xmin, xmax
        if tier_type not in self.P_TIERS:
            raise Exception('Tiertype does not exist.')

    def add_point(self, point, value, check=True):
        """Add a point to the TextTier

        :param int point: Time of the point.
        :param str value: Text of the point.
        :param bool check: Flag to check for overlap.
        :raises Exception: If overlap or wrong tiertype.
        """
        if self.tier_type != 'TextTier':
            raise Exception('Tiertype must be TextTier.')
        if check and any(i for i in self.intervals if i[0] == point):
                raise Exception('No overlap is allowed')
        self.intervals.append((point, value))

    def add_interval(self, begin, end, value, check=True):
        """Add an interval to the IntervalTier.

        :param float begin: Start time of the interval.
        :param float end: End time of the interval.
        :param str value: Text of the interval.
        :param bool check: Flag to check for overlap.
        :raises Exception: If overlap, begin > end or wrong tiertype.
        """
        if self.tier_type != 'IntervalTier':
            raise Exception('Tiertype must be IntervalTier')
        if check:
            if any(i for i in self.intervals if begin < i[1] and end > i[0]):
                raise Exception('No overlap is allowed')
            if begin > end:
                raise Exception('Begin must be smaller then end')
        self.intervals.append((begin, end, value))

    def remove_interval(self, time):
        """Remove an interval, if no interval is found nothing happens.

        :param int time: Time of the interval.
        :raises TierTypeException: If the tier is not a IntervalTier.
        """
        if self.tier_type != 'IntervalTier':
            raise Exception('Tiertype must be IntervalTier.')
        self.intervals = [i for i in self.intervals
                          if not(i[0] <= time and i[1] >= time)]

    def remove_point(self, time):
        """Remove a point, if no point is found nothing happens.

        :param int time: Time of the point.
        :raises TierTypeException: If the tier is not a TextTier.
        """
        if self.tier_type != 'TextTier':
            raise Exception('Tiertype must be TextTier.')
        self.intervals = [i for i in self.intervals if i[0] != time]

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

    def get_all_intervals(self):
        """Returns the true list of intervals including the empty intervals."""
        ints = sorted(self.get_intervals(True))
        if self.tier_type == 'IntervalTier':
            if not ints:
                ints.append((self.xmin, self.xmax, ''))
            else:
                if ints[0][0] > self.xmin:
                    ints.insert(0, (self.xmin, ints[0][0], ''))
                if ints[-1][1] < self.xmax:
                    ints.append((ints[-1][1], self.xmax, ''))
                p = ints[-1]
                for index, i in reversed(list(enumerate(ints[:-1], 1))):
                    if p[0] - i[1] != 0:
                        ints.insert(index, (i[1], p[0], ''))
                    p = i
        return ints
