#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import re
import struct
import sys

VERSION = '1.30'


def _intervallist(tier):
    srtint = list(tier.get_intervals(sort=True))
    ints = []
    if tier.tier_type == 'IntervalTier':
        # Add empty intervals for undefined spaces
        if srtint and srtint[0][0] > 0.0:
            ints.append((0.0, srtint[0][0], ''))
        for i in srtint:
            if i[1] - i[0] == 0:
                continue
            if ints and ints[-1][1] < i[0]:
                ints.append((ints[-1][1], i[0], ''))
            ints.append(i)
        if ints and ints[-1][1] < tier.xmax:
            ints.append((ints[-1][1], tier.xmax, ''))
    return ints or srtint


def _wrtval(fi, indent, prefix, value, short, f=''):
    indent = 0 if short else indent
    prefix = '' if short else prefix
    if value is not None or not short:
        fi.write(u'{{}}{{}}{}\n'.
                 format(f).format(' '*indent, prefix, value))


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
        specify the xmax. When you want to load a TextGrid from file you need
        to specify at least the file_path and optionally the codec. Binary,
        short and normal TextGrids are supported.

        :param str file_path: Path to read from, - for stdin. If ``None`` an
                              empty TextGrid will be created.
        :param int xmin: Xmin value, only needed when not loading from file.
        :param int xmax: Xmax value, needed when not loading from file.
        :param str codec: Text encoding for the input. Note that this will be
            ignored for binary TextGrids.
        :param bool stream: Flag for loading from a stream (Only use this if
            you know what you are doing...)
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
                ifile = sys.stdin if file_path == '-' else\
                    open(file_path, 'rb')
                self.from_stream(ifile, codec)
                if file_path != '-':
                    ifile.close()

    def from_stream(self, ifile, codec='ascii'):
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
                tier = Tier(name=name, tier_type=tier_type)
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
            regfloat = re.compile('([\d.]+)\s*$')
            regint = re.compile('([\d]+)\s*$')
            regstr = re.compile('"(.*)"\s*$')
            # Skip the Headers and empty line
            next(ifile), next(ifile), next(ifile)
            self.xmin = float(regfloat.search(next(ifile)).group(1))
            self.xmax = float(regfloat.search(next(ifile)).group(1))
            # Skip <exists>
            line = next(ifile)
            short = line.strip() == '<exists>'
            self.tier_num = int(regint.search(next(ifile)).group(1))
            not short and next(ifile)
            for i in range(self.tier_num):
                not short and next(ifile)  # skip item[]: and item[\d]:
                tier_type = regstr.search(next(ifile)).group(1)
                name = regstr.search(next(ifile)).group(1)
                tier = Tier(name=name, tier_type=tier_type)
                self.tiers.append(tier)
                tier.xmin = float(regfloat.search(next(ifile)).group(1))
                tier.xmax = float(regfloat.search(next(ifile)).group(1))
                for i in range(int(regint.search(next(ifile)).group(1))):
                    not short and next(ifile)  # skip intervals [\d]
                    x1 = float(regfloat.search(next(ifile)).group(1))
                    if tier.tier_type == 'IntervalTier':
                        x2 = float(regfloat.search(next(ifile)).group(1))
                        t = regstr.search(next(ifile)).group(1)
                        tier.intervals.append((x1, x2, t))
                    elif tier.tier_type == 'TextTier':
                        t = regstr.search(next(ifile)).group(1)
                        tier.intervals.append((x1, t))

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
            raise Exception('Tier not found.')

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
        raise Exception('Tier not found.')

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

    def to_file(self, filepath, codec='utf-8', mode='normal'):
        """Write the object to a file.

        :param str filepath: Path of the file, '-' for stdout.
        :param str codec: Text encoding.
        :param string mode: Flag to for write mode, possible modes:
            'n'/'normal', 's'/'short' and 'b'/'binary'
        """
        try:
            stream = sys.stdout if filepath == '-' else open(filepath, 'wb')\
                if mode in ['binary', 'b'] else\
                codecs.open(filepath, 'w', codec)
            self.to_stream(stream, codec, mode)
        finally:
            if stream != sys.stdout:
                stream.close()

    def to_stream(self, f, codec='utf-8', mode='normal'):
        """Write the object to a stream.

        :param file f: Open stream to write to.
        :param str codec: Text encoding.
        :param string mode: Flag to for write mode, possible modes:
            'n'/'normal', 's'/'short' and 'b'/'binary'
        """
        for t in self.tiers:
            t.update()
        self.update()

        if mode in ['short', 'normal', 's', 'n']:
            s = mode[0] == 's'
            f.write(u'File type = "ooTextFile"\nObject class = "TextGrid"\n\n')
            _wrtval(f, 0, u'xmin = ', self.xmin, s, '{:f}')
            _wrtval(f, 0, u'xmax = ', self.xmax, s, '{:f}')
            _wrtval(f, 0, u'tiers? ', u'<exists>', s, '{}')
            _wrtval(f, 0, u'size = ', self.tier_num, s, '{:d}')
            _wrtval(f, 0, u'item []:', None, s)
            for tnum, tier in enumerate(self.tiers, 1):
                _wrtval(f, 4, u'item [{:d}]:'.format(tnum), None, s)
                _wrtval(f, 8, u'class = ', tier.tier_type, s, '"{}"')
                _wrtval(f, 8, u'name = ', tier.name, s, '"{}"')
                _wrtval(f, 8, u'xmin = ', tier.xmin, s, '{:f}')
                _wrtval(f, 8, u'xmax = ', tier.xmax, s, '{:f}')

                ints = _intervallist(tier)
                if tier.tier_type == 'IntervalTier':
                    _wrtval(f, 8, u'intervals: size = ', len(ints), s, '{:d}')
                    for i, c in enumerate(ints):
                        _wrtval(f, 8, 'intervals [{:d}]:'.format(i+1), None, s)
                        _wrtval(f, 12, 'xmin = ', c[0], s, '{:f}')
                        _wrtval(f, 12, 'xmax = ', c[1], s, '{:f}')
                        _wrtval(f, 12, 'text = ',
                                c[2].replace('"', '""'), s, '"{}"')
                elif tier.tier_type == 'TextTier':
                    _wrtval(f, 8, u'points: size = ', len(ints), s, '{:d}')
                    for i, c in enumerate(ints):
                        _wrtval(f, 8, 'points [{:d}]:'.format(i+1), None, s)
                        _wrtval(f, 12, 'number = ', c[0], s, '{:f}')
                        _wrtval(f, 12, 'mark = ',
                                c[1].replace('"', '""'), s, '"{}"')
        elif mode in ['binary', 'b']:
            def writebstr(s, ofile):
                try:
                    bytestring = s.encode('ascii')
                except UnicodeError:
                    f.write(b'\xff\xff')
                    bytestring = b''.join(struct.pack('>h', ord(c)) for c in s)
                f.write(struct.pack('>h', len(s)))
                f.write(bytestring)

            f.write(b'ooBinaryFile\x08TextGrid')
            f.write(struct.pack('>d', self.xmin))
            f.write(struct.pack('>d', self.xmax))
            f.write(b'\x01')
            f.write(struct.pack('>i', self.tier_num))
            for tier in self.tiers:
                f.write(chr(len(tier.tier_type)).encode('ascii'))
                f.write(tier.tier_type.encode('ascii'))
                writebstr(tier.name, f)
                f.write(struct.pack('>d', tier.xmin))
                f.write(struct.pack('>d', tier.xmax))
                ints = _intervallist(tier)
                f.write(struct.pack('>i', len(ints)))
                itier = tier.tier_type == 'IntervalTier'
                for c in ints:
                    f.write(struct.pack('>d', c[0]))
                    itier and f.write(struct.pack('>d', c[1]))
                    writebstr(c[2 if itier else 1], f)
        else:
            raise Exception('Writing mode unknown or unsupported')

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

    def __init__(self, name=None, tier_type=None):
        """Creates a tier, if lines is ``None`` a new tier is created and codec
        is ignored.

        :param str name: Name of the tier.
        :param str tier_type: Type of the tier('IntervalTier' or 'TextTier').
        :raises TierTypeException: If the tier type is unknown.
        """
        self.intervals = []
        self.name = name
        self.tier_type = tier_type
        self.xmin, self.xmax = 0, 0
        if tier_type not in ['IntervalTier', 'TextTier']:
            raise Exception('Tiertype does not exist.')

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
            raise Exception('Tiertype must be TextTier.')
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
            raise Exception('Tiertype must be IntervalTier.')
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
            raise Exception('Tiertype must be IntervalTier.')
        for r in [i for i in self.intervals if i[0] <= time and i[1] >= time]:
            self.intervals.remove(r)

    def remove_point(self, time):
        """Remove a point, if no point is found nothing happens.

        :param int time: Time of the point.
        :raises TierTypeException: If the tier is not a TextTier.
        """
        if self.tier_type != 'TextTier':
            raise Exception('Tiertype must be TextTier.')
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
