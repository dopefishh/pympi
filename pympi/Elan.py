# -*- coding: utf-8 -*-

import time
import EafIO
import warnings


class Eaf:
    """Read and write Elan's Eaf files.

    .. note:: All times are in milliseconds and can't have decimals.

    :var dict annotation_document: Annotation document TAG entries.
    :var dict licences: Licences included in the file.
    :var dict header: XML header.
    :var list media_descriptors: Linked files, where every file is of the
                                 form: ``{attrib}``.
    :var list properties: Properties, where every property is of the form:
                          ``(value, {attrib})``.
    :var list linked_file_descriptors: Secondary linked files, where every
                                       linked file is of the form:
                                       ``{attrib}``.
    :var dict timeslots: Timeslot data of the form:
                         ``{TimslotID -> time(ms)}``.
    :var dict tiers: Tier data of the form:
                     ``{tier_name -> (aligned_annotations,
                     reference_annotations, attributes, ordinal)}``,

                     aligned_annotations of the form:
                     ``[{annotation_id ->
                     (begin_ts, end_ts, value, svg_ref)}]``,

                     reference annotations of the form:
                     ``[{annotation_id ->
                     (reference, value, previous, svg_ref)}]``.
    :var list linguistic_types: Linguistic types, where every type is of the
                                form: ``{id -> attrib}``.
    :var list locales: Locales, where every locale is of the form:
                       ``{attrib}``.
    :var dict constraints: Constraint data of the form:
                           ``{stereotype -> description}``.
    :var dict controlled_vocabularies: Controlled vocabulary data of the
                                       form: ``{id ->
                                       (descriptions, entries, ext_ref)}``,

                                       descriptions of the form:
                                       ``[(lang_ref, text)]``,

                                       entries of the form:
                                       ``{id -> (values, ext_ref)}``,

                                       values of the form:
                                       ``[(lang_ref, description, text)]``.
    :var list external_refs: External references, where every reference is of
                             the form ``[id, type, value]``.
    :var list lexicon_refs: Lexicon references, where every reference is of
                            the form: ``[{attribs}]``.
    """

    def __init__(self, file_path=None, author='pympi'):
        """Construct either a new Eaf file or read on from a file/stream.

        :param str file_path: Path to read from, - for stdin. If ``None`` an
                              empty Eaf file will be created.
        :param str author: Author of the file.
        """
        self.naive_gen_ann, self.naive_gen_ts = False, False
        self.annotation_document = {
            'AUTHOR': author,
            'DATE': time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            'VERSION': '2.8',
            'FORMAT': '2.8',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:noNamespaceSchemaLocation':
                'http://www.mpi.nl/tools/elan/EAFv2.8.xsd'}
        self.constraints = {}
        self.controlled_vocabularies = {}
        self.header = {}
        self.licences = {}
        self.linguistic_types = {}
        self.tiers = {}
        self.timeslots = {}
        self.external_refs = []
        self.lexicon_refs = []
        self.linked_file_descriptors = []
        self.locales = []
        self.media_descriptors = []
        self.properties = []
        self.new_time, self.new_ann = 0, 0

        if file_path is None:
            self.add_linguistic_type('default-lt', None)
            self.constraints = {'Time_Subdivision': 'Time subdivision of paren'
                                't annotation\'s time interval, no time gaps a'
                                'llowed within this interval',
                                'Symbolic_Subdivision': 'Symbolic subdivision '
                                'of a parent annotation. Annotations refering '
                                'to the same parent are ordered',
                                'Symbolic_Association': '1-1 association with '
                                'a parent annotation',
                                'Included_In': 'Time alignable annotations wit'
                                'hin the parent annotation\'s time interval, g'
                                'aps are allowed'}
            self.properties.append(('0', {'NAME': 'lastUsedAnnotation'}))
            self.add_tier('default')
        else:
            EafIO.parse_eaf(file_path, self)

    def to_file(self, file_path, pretty=True):
        """Write the object to a file, if the file already exists a backup will
        be created with the ``.bak`` suffix.

        :param str file_path: Path to write to, - for stdout.
        :param bool pretty: Flag for pretty XML printing.
        """
        EafIO.to_eaf(file_path, self, pretty)

    def to_textgrid(self, excluded_tiers=[], included_tiers=[]):
        """Convert the object to a :class:`pympi.Praat.TextGrid` object.

        :param list excluded_tiers: Specifically exclude these tiers.
        :param list included_tiers: Only include this tiers, when empty all are
                                    included.
        :returns: :class:`pympi.Praat.TextGrid` object
        :raises ImportError: If the pympi.Praat module can't be loaded.
        """
        from pympi.Praat import TextGrid
        tgout = TextGrid()
        tiers = [a for a in self.tiers if a not in excluded_tiers]
        if included_tiers:
            tiers = [a for a in tiers if a in included_tiers]
        for tier in tiers:
            currentTier = tgout.add_tier(tier)
            for interval in self.get_annotation_data_for_tier(tier):
                if interval[0] == interval[1]:
                    continue
                currentTier.add_interval(interval[0]/1000.0,
                                         interval[1]/1000.0, interval[2])
        return tgout

    def extract(self, start, end):
        """Extracts the selected time frame as a new object.

        :param int start: Start time.
        :param int end: End time.
        :returns: The extracted frame in a new object.
        """
        from copy import deepcopy
        eaf_out = deepcopy(self)
        for tier in eaf_out.tiers.itervalues():
            rems = []
            for ann in tier[0]:
                if eaf_out.timeslots[tier[0][ann][1]] > end or\
                        eaf_out.timeslots[tier[0][ann][0]] < start:
                    rems.append(ann)
            for r in rems:
                del tier[0][r]
        return eaf_out

    def get_linked_files(self):
        """Give all linked files."""
        return self.media_descriptors

    def add_linked_file(self, file_path, relpath=None, mimetype=None,
                        time_origin=None, ex_from=None):
        """Add a linked file.

        :param str file_path: Path of the file.
        :param str relpath: Relative path of the file.
        :param str mimetype: Mimetype of the file, if ``None`` it tries to
                             guess it according to the file extension which
                             currently only works for wav, mpg, mpeg and xml.
        :param int time_origin: Time origin for the media file.
        :param str ex_from: Extracted from field.
        :raises KeyError: If mimetype had to be guessed and a non standard
                          extension or an unknown mimetype.
        """
        if mimetype is None:
            mimes = {'wav': 'audio/x-wav', 'mpg': 'video/mpeg',
                     'mpeg': 'video/mpg', 'xml': 'text/xml'}
            mimetype = mimes[file_path.split('.')[-1]]
        self.media_descriptors.append({
            'MEDIA_URL': file_path, 'RELATIVE_MEDIA_URL': relpath,
            'MIME_TYPE': mimetype, 'TIME_ORIGIN': time_origin,
            'EXTRACTED_FROM': ex_from})

    def copy_tier(self, eaf_obj, tier_name):
        """Copies a tier to another :class:`pympi.Elan.Eaf` object.

        :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
        :param str tier_name: Name of the tier.
        :raises KeyError: If the tier doesn't exist.
        """
        eaf_obj.remove_tier(tier_name)
        eaf_obj.add_tier(tier_name, tier_dict=self.tiers[tier_name][3])
        for ann in self.get_annotation_data_for_tier(tier_name):
            eaf_obj.insert_annotation(tier_name, ann[0], ann[1], ann[2])

    def add_tier(self, tier_id, ling='default-lt', parent=None, locale=None,
                 part=None, ann=None, tier_dict=None):
        """Add a tier.

        :param str tier_id: Name of the tier.
        :param str ling: Linguistic type, if the type is not available it will
                         warn and pick the first available type.
        :param str parent: Parent tier name.
        :param str locale: Locale.
        :param str part: Participant.
        :param str ann: Annotator.
        :param dict tier_dict: TAG attributes, when this is not ``None`` it
                               will ignore all other options.
        """
        if ling not in self.linguistic_types:
            warnings.warn(
                'add_tier: Linguistic type non existent, choosing the first')
            ling = self.linguistic_types.keys()[0]
        if tier_dict is None:
            self.tiers[tier_id] = ({}, {}, {
                'TIER_ID': tier_id,
                'LINGUISTIC_TYPE_REF': ling,
                'PARENT_REF': parent,
                'PARTICIPANT': part,
                'DEFAULT_LOCALE': locale,
                'ANNOTATOR': ann}, len(self.tiers))
        else:
            self.tiers[tier_id] = ({}, {}, tier_dict, len(self.tiers))

    def remove_tiers(self, tiers):
        """Remove multiple tiers, note that this is a lot faster then removing
        them individually because of the delayed cleaning of timeslots.

        :param list tiers: Names of the tier to remove.
        :raises KeyError: If a tier is non existent.
        """
        for a in tiers:
            self.remove_tier(a, check=False, clean=False)
        self.clean_time_slots()

    def remove_tier(self, id_tier, clean=True):
        """Remove tier.

        :param str id_tier: Name of the tier.
        :param bool clean: Flag to also clean the timeslots.
        :raises KeyError: If tier is non existent.
        """
        del(self.tiers[id_tier])
        if clean:
            self.clean_time_slots()

    def get_tier_names(self):
        """List all the tier names.

        :returns: List of all tier names
        """
        return self.tiers.keys()

    def get_parameters_for_tier(self, id_tier):
        """Give the parameter dictionary, this is usaable in :func:`add_tier`.

        :param str id_tier: Name of the tier.
        :returns: Dictionary of parameters.
        :raises KeyError: If the tier is non existent.
        """
        return self.tiers[id_tier][2]

    def child_tiers_for(self, id_tier):
        """Give all child tiers for a tier.

        :param str id_tier: Name of the tier.
        :returns: List of all children
        :raises KeyError: If the tier is non existent.
        """
        return [m for m in self.tiers if 'PARENT_REF' in self.tiers[m][2] and
                self.tiers[m][2]['PARENT_REF'] == id_tier]

    def get_annotation_data_for_tier(self, id_tier):
        """Gives a list of annotations of the form: ``(begin, end, value)``

        :param str id_tier: Name of the tier.
        :raises KeyError: If the tier is non existent.
        """
        a = self.tiers[id_tier][0]
        return [(self.timeslots[a[b][0]], self.timeslots[a[b][1]], a[b][2])
                for b in a]

    def get_annotation_data_at_time(self, id_tier, time):
        """Give the annotations at the given time.

        :param str id_tier: Name of the tier.
        :param int time: Time of the annotation.
        :returns: List of annotations at that time.
        :raises KeyError: If the tier is non existent.
        """
        anns = self.tiers[id_tier][0]
        return sorted(
            [(self.timeslots[m[0]], self.timeslots[m[1]], m[2])
                for m in anns.itervalues() if
                self.timeslots[m[0]] <= time and
                self.timeslots[m[1]] >= time])

    def get_annotation_datas_between_times(self, id_tier, start, end):
        """Gives the annotations within the times.

        :param str id_tier: Name of the tier.
        :param int start: Start time of the annotation.
        :param int end: End time of the annotation.
        :returns: List of annotations within that time.
        :raises KeyError: If the tier is non existent.
        """
        anns = self.tiers[id_tier][0]
        return sorted([
            (self.timeslots[m[0]], self.timeslots[m[1]], m[2])
            for m in anns.itervalues() if self.timeslots[m[1]] >= start and
            self.timeslots[m[0]] <= end])

    def remove_all_annotations_from_tier(self, id_tier):
        """remove all annotations from a tier

        :param str id_tier: Name of the tier.
        :raises KeyError: If the tier is non existent.
        """
        self.tiers[id_tier][0], self.tiers[id_tier][1] = {}, {}
        self.clean_time_slots()

    def insert_annotation(self, id_tier, start, end, value='', svg_ref=None):
        """Insert an annotation.

        :param str id_tier: Name of the tier.
        :param int start: Start time of the annotation.
        :param int end: End time of the annotation.
        :param str value: Value of the annotation.
        :param str svg_ref: Svg reference.
        :raises KeyError: If the tier is non existent.
        """
        start_ts = self.generate_ts_id(start)
        end_ts = self.generate_ts_id(end)
        self.tiers[id_tier][0][self.generate_annotation_id()] =\
            (start_ts, end_ts, value, svg_ref)

    def remove_annotation(self, id_tier, time, clean=True):
        """Remove an annotation in a tier, if you need speed the best thing is
        to clean the timeslots after the last removal.

        :param str id_tier: Name of the tier.
        :param int time: Timepoint within the annotation.
        :param bool clean: Flag to clean the timeslots afterwards.
        :raises KeyError: If the tier is non existent.
        """
        for b in [a for a in self.tiers[id_tier][0].iteritems() if
                  a[1][0] >= time and a[1][1] <= time]:
            del(self.tiers[id_tier][0][b[0]])
        if clean:
            self.clean_time_slots()

    def insert_ref_annotation(self, id_tier, ref, value, prev, svg_ref=None):
        """Insert a reference annotation.

        :param str id_tier: Name of the tier.
        :param str ref: Id of the referenced annotation.
        :param str value: Value of the annotation.
        :param str prev: Id of the previous annotation.
        :param str svg_ref: Svg reference.
        :raises KeyError: If the tier is non existent.
        """
        self.tiers[id_tier][1][self.generate_annotation_id()] =\
            (ref, value, prev, svg_ref)

    def get_ref_annotation_data_for_tier(self, id_tier):
        """"Give a list of all reference annotations of the form:
        ``[{id -> (ref, value, previous, svg_ref}]``

        :param str id_tier: Name of the tier.
        :raises KeyError: If the tier is non existent.
        """
        return self.tiers[id_tier][1]

    def remove_controlled_vocabulary(self, cv):
        """Remove a controlled vocabulary.

        :param str cv: Controlled vocabulary id.
        :raises KeyError: If the controlled vocabulary is non existent.
        """
        del(self.controlled_vocabularies[cv])

    def generate_annotation_id(self):
        """Generate the next annotation id, this function is mainly used
        internally.
        """
        if self.naive_gen_ann:
            new = self.last_ann+1
            self.last_ann = new
        else:
            new = 1
            anns = {int(ann[1:]) for tier in self.tiers.itervalues()
                    for ann in tier[0]}
            if len(anns) > 0:
                newann = set(xrange(1, max(anns))).difference(anns)
                if len(newann) == 0:
                    new = max(anns)+1
                    self.naive_gen_ann = True
                    self.last_ann = new
                else:
                    new = sorted(newann)[0]
        return 'a%d' % new

    def generate_ts_id(self, time=None):
        """Generate the next timeslot id, this function is mainly used
        internally

        :param int time: Initial time to assign to the timeslot
        """
        if self.naive_gen_ts:
            new = self.last_ts+1
            self.last_ts = new
        else:
            new = 1
            tss = {int(x[2:]) for x in self.timeslots}
            if len(tss) > 0:
                newts = set(xrange(1, max(tss))).difference(tss)
                if len(newts) == 0:
                    new = max(tss)+1
                    self.naive_gen_ts = True
                    self.last_ts = new
                else:
                    new = sorted(newts)[0]
        ts = 'ts%d' % new
        self.timeslots[ts] = time
        return ts

    def clean_time_slots(self):
        """Clean up all unused timeslots.
        .. warning:: This can and will take time for larger tiers. When you
                     want to do a lot of operations on a lot of tiers please
                     unset the flags for cleaning in the functions so that the
                     cleaning is only performed afterwards.
        """
        ts_in_tier = set(sum([a[0:2] for tier in self.tiers.itervalues()
                              for a in tier[0].itervalues()], ()))
        ts_avail = set(self.timeslots)
        for a in ts_in_tier.symmetric_difference(ts_avail):
            del(self.timeslots[a])
        self.naive_gen_ts = False
        self.naive_gen_ann = False

    def generate_annotation_concat(self, tiers, start, end, sep='-'):
        """Give a string of concatenated annotation values for annotations
        within a timeframe.

        :param list tiers: List of tier names.
        :param int start: Start time.
        :param int end: End time.
        :param str sep: Separator string to use.
        :returns: String containing a concatenation of annotation values.
        :raises KeyError: If a tier is non existent.
        """
        return sep.join(
            set(d[2] for t in tiers if t in self.tiers for d in
                self.get_annotation_datas_between_times(t, start, end)))

    def merge_tiers(self, tiers, tiernew=None, gaptresh=1):
        """Merge tiers into a new tier and when the gap is lower then the
        threshhold glue the annotations together.

        :param list tiers: List of tier names.
        :param str tiernew: Name for the new tier, if ``None`` the name will be
                            generated.
        :param int gapthresh: Threshhold for the gaps.
        :raises KeyError: If a tier is non existent.
        :raises TypeError: If there are no annotations within the tiers.
        """
        if tiernew is None:
            tiernew = '%s_Merged' % '_'.join(tiers)
        self.remove_tier(tiernew)
        self.add_tier(tiernew)
        timepts = sorted(set.union(
            *[set(j for j in xrange(d[0], d[1])) for d in
                [ann for tier in tiers for ann in
                 self.get_annotation_data_for_tier(tier)]]))
        if len(timepts) > 1:
            start = timepts[0]
            for i in xrange(1, len(timepts)):
                if timepts[i]-timepts[i-1] > gaptresh:
                    self.insert_annotation(
                        tiernew, start, timepts[i-1],
                        self.generate_annotation_concat(tiers, start,
                                                        timepts[i-1]))
                    start = timepts[i]
            self.insert_annotation(
                tiernew, start, timepts[i-1],
                self.generate_annotation_concat(tiers, start, timepts[i-1]))

    def shift_annotations(self, time):
        """Shift all annotations in time, this creates a new object.

        :param int time: Time shift width, negative numbers make a right shift.
        :returns: Shifted :class:`pympi.Elan.Eaf' object.
        """
        e = self.extract(
            -1*time, self.get_full_time_interval()[1]) if time < 0 else\
            self.extract(0, self.get_full_time_interval()[1]-time)
        for tier in e.tiers.itervalues():
            for ann in tier[0].itervalues():
                e.timeslots[ann[0]] = e.timeslots[ann[0]]+time
                e.timeslots[ann[1]] = e.timeslots[ann[1]]+time
        e.clean_time_slots()
        return e

    def filterAnnotations(self, tier, tier_name=None, filtin=None,
                          filtex=None):
        """Filter annotations in a tier

        :param str tier: Name of the tier:
        :param str tier_name: Name of the new tier, when ``None`` the name will
                              be generated.
        :param list filtin: List of strings to be included, if None all
                            annotations all is included.
        :param list filtex: List of strings to be excluded, if None no strings
                            are excluded.
        :raises KeyError: If the tier is non existent.
        """
        if tier_name is None:
            tier_name = '%s_filter' % tier
        self.remove_tier(tier_name)
        self.add_tier(tier_name)
        for a in [b for b in self.get_annotation_data_for_tier(tier)
                  if (filtex is None or b[2] not in filtex) and
                  (filtin is None or b[2] in filtin)]:
            self.insert_annotation(tier_name, a[0], a[1], a[2])

    def glue_annotations_in_tier(self, tier, tier_name=None, treshhold=85,
                                 filtin=None, filtex=None):
        """Glue annotatotions together in a tier.

        :param str tier: Name of the tier.
        :param str tier_name: Name of the new tier, if ``None`` the name will
                              be generated.
        :param int threshhold: Threshhold for the maximum gap to still glue.
        :param list filtin: List of strings to be included, if None all
                            annotations all is included.
        :param list filtex: List of strings to be excluded, if None no strings
                            are excluded.
        :raises KeyError: If the tier is non existent.
        """
        if tier_name is None:
            tier_name = '%s_glued' % tier
        self.remove_tier(tier_name)
        self.add_tier(tier_name)
        tier_data = sorted(self.get_annotation_data_for_tier(tier))
        tier_data = [t for t in tier_data if
                     (filtin is None or t[2] in filtin) and
                     (filtex is None or t[2] not in filtex)]
        currentAnn = None
        for i in xrange(0, len(tier_data)):
            if currentAnn is None:
                currentAnn = (tier_data[i][0], tier_data[i][1],
                              tier_data[i][2])
            elif tier_data[i][0] - currentAnn[1] < treshhold:
                currentAnn = (currentAnn[0], tier_data[i][1],
                              '%s_%s' % (currentAnn[2], tier_data[i][2]))
            else:
                self.insert_annotation(tier_name, currentAnn[0], currentAnn[1],
                                       currentAnn[2])
                currentAnn = tier_data[i]
        if currentAnn is not None:
            self.insert_annotation(tier_name, currentAnn[0],
                                   tier_data[len(tier_data)-1][1],
                                   currentAnn[2])

    def get_full_time_interval(self):
        """Give the full time interval of the file.

        :returns: Tuple of the form: ``(min_time, max_time``.
        """
        return (min(self.timeslots.itervalues()),
                max(self.timeslots.itervalues()))

    def create_gaps_and_overlaps_tier(self, tier1, tier2, tier_name=None,
                                      maxlen=-1):
        """Create a tier with the gaps and overlaps of the annotations.
        For types see :func:`get_gaps_and_overlaps_duration`

        :param str tier1: Name of the first tier.
        :param str tier2: Name of the second tier.
        :param str tier_name: Name of the new tier, if ``None`` the name will
                              be generated.
        :param int maxlen: Maximum length of gaps (skip longer ones), if ``-1``
                           no maximum will be used.
        :returns: List of gaps and overlaps of the form:
                  ``[(type, start, end)]``.
        :raises KeyError: If a tier is non existent.
        :raises IndexError: If no annotations are available in the tiers.
        """
        if tier_name is None:
            tier_name = '%s_%s_ftos' % (tier1, tier2)
        self.remove_tier(tier_name)
        self.add_tier(tier_name)
        ftos = self.get_gaps_and_overlaps_duration(tier1, tier2, maxlen)
        for fto in ftos:
            self.insert_annotation(tier_name, fto[1], fto[2], fto[0])
        return ftos

    def get_gaps_and_overlaps_duration(self, tier1, tier2, maxlen=-1,
                                       progressbar=False):
        """Give gaps and overlaps. The return types are shown in the table
        below. The string will be of the format: ``id_tiername_tiername``.

        For example when a gap occurs between tier1 and tier2 and they are
        called ``speakerA`` and ``speakerB`` the annotation value of that gap
        will be ``G12_speakerA_speakerB``.

        | The gaps and overlaps are calculated using Heldner and Edlunds
          method found in:
        | *Heldner, M., & Edlund, J. (2010). Pauses, gaps and overlaps in
         conversations. Journal of Phonetics, 38(4), 555–568.
         doi:10.1016/j.wocn.2010.08.002*

        +-----+--------------------------------------------+
        | id  | Description                                |
        +=====+============================================+
        | O12 | Overlap from tier1 to tier2                |
        +-----+--------------------------------------------+
        | O21 | Overlap from tier2 to tier1                |
        +-----+--------------------------------------------+
        | G12 | Gap from tier1 to tier2                    |
        +-----+--------------------------------------------+
        | G21 | Gap from tier2 to tier1                    |
        +-----+--------------------------------------------+
        | P1  | Pause for tier1                            |
        +-----+--------------------------------------------+
        | P2  | Pause for tier2                            |
        +-----+--------------------------------------------+
        | B12 | Within speaker overlap from tier1 to tier2 |
        +-----+--------------------------------------------+
        | B21 | Within speaker overlap from tier2 to tier1 |
        +-----+--------------------------------------------+

        :param str tier1: Name of the first tier.
        :param str tier2: Name of the second tier.
        :param int maxlen: Maximum length of gaps (skip longer ones), if ``-1``
                           no maximum will be used.
        :param bool progressbar: Flag for debugging purposes that shows the
                                 progress during the process.
        :returns: List of gaps and overlaps of the form:
                  ``[(type, start, end)]``.
        :raises KeyError: If a tier is non existent.
        :raises IndexError: If no annotations are available in the tiers.
        """
        spkr1anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]])
                           for a in self.tiers[tier1][0].values())
        spkr2anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]])
                           for a in self.tiers[tier2][0].values())
        line1 = []
        isin = lambda x, lst: False if\
            len([i for i in lst if i[0] <= x and i[1] >= x]) == 0 else True
        minmax = (min(spkr1anns[0][0], spkr2anns[0][0]),
                  max(spkr1anns[-1][1], spkr2anns[-1][1]))
        last = (1, minmax[0])
        lastP = 0
        for ts in xrange(*minmax):
            in1, in2 = isin(ts, spkr1anns), isin(ts, spkr2anns)
            if in1 and in2:      # Both speaking
                if last[0] == 'B':
                    continue
                ty = 'B'
            elif in1:            # Only 1 speaking
                if last[0] == '1':
                    continue
                ty = '1'
            elif in2:            # Only 2 speaking
                if last[0] == '2':
                    continue
                ty = '2'
            else:                # None speaking
                if last[0] == 'N':
                    continue
                ty = 'N'
            line1.append((last[0], last[1], ts))
            last = (ty, ts)
            if progressbar and int((ts*1.0/minmax[1])*100) > lastP:
                lastP = int((ts*1.0/minmax[1])*100)
                print '%d%%' % lastP
        line1.append((last[0], last[1], minmax[1]))
        ftos = []
        for i in xrange(len(line1)):
            if line1[i][0] == 'N':
                if i != 0 and i < len(line1) - 1 and\
                        line1[i-1][0] != line1[i+1][0]:
                    ftos.append(('G12_%s_%s' % (tier1, tier2)
                                if line1[i-1][0] == '1' else 'G21_%s_%s' %
                                (tier2, tier1), line1[i][1], line1[i][2]))
                else:
                    ftos.append(('P_%s' %
                                (tier1 if line1[i-1][0] == '1' else tier2),
                                line1[i][1], line1[i][2]))
            elif line1[i][0] == 'B':
                if i != 0 and i < len(line1) - 1 and\
                        line1[i-1][0] != line1[i+1][0]:
                    ftos.append(('O12_%s_%s' % ((tier1, tier2)
                                if line1[i-1][0] else 'O21_%s_%s' %
                                (tier2, tier1)), line1[i][1], line1[i][2]))
                else:
                    ftos.append(('B_%s_%s' % ((tier1, tier2)
                                if line1[i-1][0] == '1' else
                                (tier2, tier1)), line1[i][1], line1[i][2]))
        return [f for f in ftos if maxlen == -1 or abs(f[2] - f[1]) < maxlen]

    def create_controlled_vocabulary(self, cv_id, descriptions, entries,
                                     ext_ref=None):
        """Create a controlled vocabulary.
        .. warning:: This is a very raw implementation and you should check the
                     Eaf file format specification for the entries.

        :param str cv_id: Name of the controlled vocabulary.
        :param list descriptions: List of descriptions.
        :param dict entries: Entries dictionary.
        :param str ext_ref: External reference.
        """
        self.controlledvocabularies[cv_id] = (descriptions, entries, ext_ref)

    def get_tier_ids_for_linguistic_type(self, ling_type, parent=None):
        """Give a list of all tiers matching a linguistic type.

        :param str ling_type: Name of the linguistic type.
        :param str parent: Only match tiers from this parent, when ``None``
                           this option will be ignored.
        :returns: List of tiernames.
        :raises KeyError: If a tier or linguistic type is non existent.
        """
        return [t for t in self.tiers if
                self.tiers[t][2]['LINGUISTIC_TYPE_REF'] == ling_type and
                (parent is None or self.tiers[t][2]['PARENT_REF'] == parent)]

    def remove_linguistic_type(self, ling_type):
        """Remove a linguistic type.

        :param str ling_type: Name of the linguistic type.
        """
        del(self.linguistic_types[ling_type])

    def add_linguistic_type(self, lingtype, constraints=None,
                            timealignable=True, graphicreferences=False,
                            extref=None):
        """Add a linguistic type.

        :param str lingtype: Name of the linguistic type.
        :param list constraints: Constraint names.
        :param bool timealignable: Flag for time alignable.
        :param bool graphicreferences: Flag for graphic references.
        :param str extref: External reference.
        """
        self.linguistic_types[lingtype] = {
            'LINGUISTIC_TYPE_ID': lingtype,
            'TIME_ALIGNABLE': str(timealignable).lower(),
            'GRAPHIC_REFERENCES': str(graphicreferences).lower(),
            'CONSTRAINTS': constraints}
        if extref is not None:
            self.linguistic_types[lingtype]['EXT_REF'] = extref

    def get_linguistic_types(self):
        """Give a list of available linguistic types.

        :returns: List of linguistic type names.
        """
        return self.linguistic_types.keys()
