# -*- coding: utf-8 -*-

import time
import EafIO
import warnings


class Eaf:
    """class that represents ELAN's eaf files

    Internal variables:
    annotation_document     -- dict of all annotationdocument TAG entries.
    licences                -- dictionary of licences
    header                  -- dict of the header TAG entries.
    media_descriptors       -- list of all linked files: [{attrib}]
    properties              -- list of all properties: [(value, {attrib})]
    linked_file_descriptors -- list of all secondary linked files: [{attrib}].
    timeslots               -- timeslot data: {TimslotID -> time(ms)}
    tiers                   -- tier data:
        {tier_name -> (aligned_annotations, reference_annotations,
                       attributes, ordinal)} where

                              aligned_annotations:
        [{annotation_id -> (begin_ts, end_ts, value, svg_ref)}]

                              reference_annotations:
        [{annotation_id -> (reference, value, previous, svg_ref)}]
    linguistic_types        -- linguistic type data: [{id -> attrib}]
    locales                 -- list of locale data: [{attrib}]
    constraints             -- constraint data: {stereotype -> description}
    controlled_vocabularies -- controlled vocabulary data:
        {id -> (descriptions, entries, ext_ref)} where
                              descriptions:
            [(lang_ref, text)]
                              entries:
            {id -> (values, ext_ref)}
                              values:
            [(lang_ref, description, text)]
    external refs           -- external refs [extref] where
                              extref: [id, type, value]
    lexicon_refs            -- lexicon refs [{attribs}]
    """

    def __init__(self, file_path=None, author='Elan.py'):
        """constructor, builds an elan object from file or if the path is None
        it creates an empty object

        Keyword arguments:
        file_path -- path to load the file from (default None)
        author    -- author used in the xml tag (default Elan.py)
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
            self.constraints = {'Time_Subdivision': """Time subdivision of par\
ent annotation\'s time interval, no time gaps allowed within this interval""",
                                'Symbolic_Subdivision': """Symbolic subdivision\
of a parent annotation. Annotations refering to the same parent are ordered""",
                                'Symbolic_Association': """1-1 association wit\
h a parent annotation""",
                                'Included_In': """Time alignable annotations w\
ithin the parent annotation's time interval, gaps are allowed"""}
            self.properties.append(('0', {'NAME': 'lastUsedAnnotation'}))
            self.add_tier('default')
        else:
            EafIO.parse_eaf(file_path, self)

    def to_file(self, file_path, pretty=True):
        """exports the eaf object to a file, if the file already exists it will
        create a backup with the .bak suffix

        Required arguments:
        file_path -- file path - for stdout

        Keyword arguments:
        pretty    -- flag for pretty indented output (default True)
        """
        EafIO.to_eaf(file_path, self)

    def to_textgrid(self, file_path, excluded_tiers=[], included_tiers=[],
                    encoding='utf-16'):
        """convert the elan file to praat's TextGrid

        Required arguments:
        file_path      -- file path, - for stdout
        excluded_tiers -- tiers to specifically exclude
        included_tiers -- tiers to specifically include, if empty all tiers are
                          included

        Keyword arguments:
        encoding       -- character encoding (default utf-16)
        """
        try:
            from pympi.Praat import TextGrid
        except ImportError:
            warnings.warn(
                'Please install the pympi.Praat module from the py' +
                'mpi module found at https://github.com/dopefishh/pympi')
            return 1
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
        tgout.to_file(file_path, codec=encoding)
        return 0

    def extract(self, start, end):
        """extract a timeframe

        Required arguments:
        start -- starting time
        end   -- ending time
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
        """give a list of all media files"""
        return self.media_descriptors

    def add_linked_file(self, file_path, relpath=None, mimetype=None,
                        time_origin=None, ex_from=None):
        """add a linked file

        Required arguments:
        file_path   -- path of the file

        Keyword arguments:
        relpath     -- relative filepath (default None)
        mimetype    -- MIME-type, if none it tries to guess it (default None)
        time_origin -- time origin for media files (default None)
        ex_from      -- extracted from (default None)
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
        """copies the tier to another eaf object

        eaf_obj   -- eaf object
        tier_name -- tier name
        """
        eaf_obj.remove_tier(tier_name)
        try:
            eaf_obj.add_tier(tier_name, tier_dict=self.tiers[tier_name][3])
            for ann in self.get_annotation_data_for_tier(tier_name):
                eaf_obj.insert_annotation(tier_name, ann[0], ann[1], ann[2])
            return 0
        except KeyError:
            warnings.warn('copy_tier: Tier non existent!')
            return 1

    def add_tier(self, tier_id, ling='default-lt', parent=None, locale=None,
                 part=None, ann=None, tier_dict=None):
        """add a tier

        Required arguments:
        tier_id   -- name of the tier

        Keyword arguments:
        ling      -- linguistic type (default None)
        parent    -- id of parent tier (default None)
        locale    -- locale of the tier (default None)
        part      -- participant (default None)
        ann       -- annotator (default None)
        tier_dict -- tier dict to use the quick function, when this is not None
                     it will ignore all other options (default None)
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
        """remove tiers

        Required arguments:
        tiers -- list of names of tiers to remove
        """
        for a in tiers:
            self.remove_tier(a, check=False, clean=False)
        self.clean_time_slots()

    def remove_tier(self, id_tier, clean=True):
        """remove tier

        Required arguments:
        id_tier -- name of the tier

        Keyword arguments:
        clean   -- flag to also clean up the timeslot id's (default True)
        """
        try:
            del(self.tiers[id_tier])
            if clean:
                self.clean_time_slots()
            return 0
        except KeyError:
            warnings.warn(
                'remove_tier: Tier non existent!\nlooking for: %s' % id_tier)
            return 1

    def get_tier_names(self):
        """give a list of tiernames"""
        return self.tiers.keys()

    def get_parameters_for_tier(self, id_tier):
        """gives the tierdict that is usable in the add_tier function

        Required arguments:
        id_tier -- name of the tier
        """
        try:
            return self.tiers[id_tier][2]
        except KeyError:
            warnings.warn('get_parameters_for_tier: Tier non existent!')
            return None

    def child_tiers_for(self, id_tier):
        """gives all child tiers

        Required arguments:
        id_tier -- tier name
        """
        try:
            return [m for m in self.tiers
                    if 'PARENT_REF' in self.tiers[m][2] and
                    self.tiers[m][2]['PARENT_REF'] == id_tier]
        except KeyError:
            warnings.warn('child_tier_for: Tier non existent!')
            return None

    def get_annotation_data_for_tier(self, id_tier):
        """gives a list of annotations in the format (start, end, value)

        Required arguments:
        id_tier -- name of the tier
        """
        try:
            a = self.tiers[id_tier][0]
            return [(self.timeslots[a[b][0]], self.timeslots[a[b][1]], a[b][2])
                    for b in a]
        except KeyError:
            warnings.warn('get_annotation_data_for_tier: Tier non existent!')
            return None

    def get_annotation_data_at_time(self, id_tier, time):
        """give the annotation at the given time

        Required arguments:
        id_tier -- name of the tier
        time    -- time
        """
        try:
            anns = self.tiers[id_tier][0]
            return sorted(
                [(self.timeslots[m[0]], self.timeslots[m[1]], m[2])
                    for m in anns.itervalues() if
                    self.timeslots[m[0]] <= time and
                    self.timeslots[m[1]] >= time])
        except KeyError:
            warnings.warn('get_annotation_data_at_time: Tier non existent!')
            return None

    def get_annotation_datas_between_times(self, id_tier, start, end):
        """
        Gives a list of annotations that occur between times

        Required arguments:
        id_tier -- name of the tier
        start   -- start time
        end     -- end time
        """
        try:
            anns = self.tiers[id_tier][0]
            return sorted([
                (self.timeslots[m[0]], self.timeslots[m[1]], m[2])
                for m in anns.itervalues() if self.timeslots[m[1]] >= start and
                self.timeslots[m[0]] <= end])
        except KeyError:
            warnings.warn('annotation_datas_between_times: Tier non existent!')
            return None

    def remove_all_annotations_from_tier(self, id_tier):
        """remove all annotations from a tier

        Required arguments:
        id_tier -- name of the tier
        """
        try:
            self.tiers[id_tier][0], self.tiers[id_tier][1] = {}, {}
            self.clean_time_slots()
            return 0
        except KeyError:
            warnings.warn('removeallannotations_from_tier: Tier non existent!')
            return 1

    def insert_annotation(self, id_tier, start, end, value='', svg_ref=None):
        """insert an annotation in a tier

        Required arguments:
        id_tier -- name of the tier
        start   -- start time of the annotation
        end     -- end time of the annotation

        Keyword arguments:
        value   -- value of the annotation (default )
        svg_ref -- svg reference (default None)
        """
        try:
            start_ts = self.generate_ts_id(start)
            end_ts = self.generate_ts_id(end)
            self.tiers[id_tier][0][self.generate_annotation_id()] =\
                (start_ts, end_ts, value, svg_ref)
            return 0
        except KeyError:
            warnings.warn('insert_annotation: Tier non existent')
            return 1

    def remove_annotation(self, id_tier, time, clean=True):
        """remove an annotation at time

        Required arguments:
        id_tier -- name of the tier
        time    -- time

        Keyword arguments:
        clean   -- flag to clean timeslots (default True)
        """
        try:
            for b in [a for a in self.tiers[id_tier][0].iteritems() if
                      a[1][0] >= time and a[1][1] <= time]:
                del(self.tiers[id_tier][0][b[0]])
            if clean:
                self.clean_time_slots()
            return 0
        except KeyError:
            warnings.warn('remove_annotation: Tier non existent')
        return 1

    def insert_ref_annotation(self, id_tier, ref, value, prev, svg_ref=None):
        """insert a ref annotation

        Required arguments:
        id_tier -- name of the tier
        ref     -- reference
        value   -- value of the annotation
        prev    -- previous annotation

        Keyword arguments:
        svg_ref -- svg reference (default None)
        """
        try:
            self.tiers[id_tier][1][self.generate_annotation_id()] =\
                (ref, value, prev, svg_ref)
            return 0
        except KeyError:
            warnings.warn('insert_ref_annotation: Tier non existent')
            return 1

    def get_ref_annotation_data_for_tier(self, id_tier):
        """"give a list of all reference annotations

        Required arguments:
        id_tier -- Name of the tier
        """
        try:
            return self.tiers[id_tier][1]
        except KeyError:
            warnings.warn("""get_ref_annotation_data_for_tier: Tier non existe\
nt!""")
            return None

    def remove_controlled_vocabulary(self, cv):
        """remove a controlled vocabulary

        Required arguments:
        cv -- Controlled vocabulary ID
        """
        try:
            del(self.controlled_vocabularies[cv])
            return 0
        except KeyError:
            warnings.warn("""remove_controlled_vocabulary: Controlled vocabula\
ry non existent!""")
            return 1

    def generate_annotation_id(self):
        """generate the next annotation ID"""
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
        """generate the next timeslot ID

        Keyword arguments:
        time -- initial time to set
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
        """clean up all unused timeslots
        !!! this can and will take time for larger tiers, this is only
        necessary after a lot of deleting
        """
        ts_in_tier = set(sum([a[0:2] for tier in self.tiers.itervalues()
                              for a in tier[0].itervalues()], ()))
        ts_avail = set(self.timeslots)
        for a in ts_in_tier.symmetric_difference(ts_avail):
            del(self.timeslots[a])
        self.naive_gen_ts = False
        self.naive_gen_ann = False

    def generate_annotation_concat(self, tiers, start, end, sep='-'):
        """concatenate annotations within a timeframe

        Required arguments:
        tiers -- list of tiers
        start -- start time
        end   -- end time

        Keyword arguments:
        sep   -- separator character
        """
        return sep.join(set(d[2] for t in tiers if t in self.tiers for d in
                        self.get_annotation_datas_between_times(t, start,
                                                                end)))

    def merge_tiers(self, tiers, tiernew=None, gaptresh=1):
        """merge tiers into a new tier

        Required arguments:
        tiers    -- list of tiers

        Keyword arguments:
        tiernew  -- nome of the new tier, if None the name will be generated
        gaptresh -- treshhold to glue annotations
        """
        if len([t for t in tiers if t not in self.tiers]) > 0:
            warnings.warn('merge_tiers: One or more tiers non existent!')
            return 1
        if tiernew is None:
            tiernew = '%s_Merged' % '_'.join(tiers)
        self.remove_tier(tiernew)
        self.add_tier(tiernew)
        try:
            timepts = sorted(set.union(
                *[set(j for j in xrange(d[0], d[1])) for d in
                    [ann for tier in tiers for ann in
                     self.get_annotation_data_for_tier(tier)]]))
        except TypeError:
            warnings.warn('merge_tiers: No annotations found!')
            return 1
        if len(timepts) > 1:
            start = timepts[0]
            for i in xrange(1, len(timepts)):
                if timepts[i]-timepts[i-1] > gaptresh:
                    self.insert_annotation(
                        tiernew,
                        start,
                        timepts[i-1],
                        self.generate_annotation_concat(
                            tiers, start, timepts[i-1]))
                    start = timepts[i]
            self.insert_annotation(
                tiernew,
                start,
                timepts[i-1],
                self.generate_annotation_concat(tiers, start, timepts[i-1]))
        return 0

    def shift_annotations(self, time):
        """shift all annotations in time, this creates a new object

        Required arguments:
        time -- time shift width negative for right shift
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

    def filterAnnotations(self, tier,
                          tier_name=None, filtin=None, filtex=None):
        """filter annotations in a tier

        Required arguments:
        tier      -- tier name

        Keyword arguments:
        tier_name -- output tier name, if none it will be generated
        filtin    -- inclusion list, if None all is included
        filtex    -- exclusion list, if Nonen nothing is excluded
        """
        if tier not in self.tiers:
            warnings.warn('filterAnnotations: Tier non existent!' + tier)
            return 1
        if tier_name is None:
            tier_name = '%s_filter' % tier
        self.remove_tier(tier_name)
        self.add_tier(tier_name)
        for a in [b for b in self.get_annotation_data_for_tier(tier)
                  if (filtex is None or b[2] not in filtex) and
                  (filtin is None or b[2] in filtin)]:
            self.insert_annotation(tier_name, a[0], a[1], a[2])
        return 0

    def glue_annotations_in_tier(self, tier, tier_name=None, treshhold=85,
                                 filtin=None, filtex=None):
        """glue annotatotions together in a tier

        Required arguments:
        tier      -- tier name

        Keyword arguments:
        tier_name  -- output tier name, if None it will be generated
        treshhold  -- gap threshhold
        filtin     -- include only this annotations, if None all is included
        filtex     -- exclude all this annotations
        """
        if tier not in self.tiers:
            warnings.warn('glue_annotations_in_tier: Tier non existent!')
            return 1
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
        return 0

    def get_full_time_interval(self):
        """give a tuple with the start and end time of the entire file"""
        return (min(self.timeslots.itervalues()),
                max(self.timeslots.itervalues()))

    def create_gaps_and_overlaps_tier(self, tier1, tier2, tier_name=None,
                                      maxlen=-1):
        """create a tier with the gaps and overlaps

        Required arguments:
        tier1   -- name of the first tier
        tier2   -- name of the second tier

        Keyword arguments:
        tierNam -- name of the output tier
        maxlen  -- maximum length of the gaps
        """
        if tier1 not in self.tiers or tier2 not in self.tiers:
            warnings.warn("""create_gaps_and_overlaps_tier: One or more tiers \
non existent!""")
            return None
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
        """give gaps and overlaps in the format (type, start, end)

        Required arguments:
        tier1       -- name of the first tier
        tier2       -- name of the second tier

        Keyword arguments:
        maxlen      -- maximum length of the gaps, -1 is infinite
        progressbar -- flag to display the progress(debug purpose)
        """
        if tier1 not in self.tiers or tier2 not in self.tiers:
            warnings.warn("""get_gaps_and_overlaps_duration: One or more tiers\
non existent!""")
            return None
        spkr1anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]])
                           for a in self.tiers[tier1][0].values())
        spkr2anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]])
                           for a in self.tiers[tier2][0].values())
        line1 = []
        isin = lambda x, lst: False if\
            len([i for i in lst if i[0] <= x and i[1] >= x]) == 0 else True
        try:
            minmax = (min(spkr1anns[0][0], spkr2anns[0][0]),
                      max(spkr1anns[-1][1], spkr2anns[-1][1]))
        except IndexError:
            warnings.warn(
                'get_gaps_and_overlaps_duration: No annotations found...')
            return []
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
        """create a controlled vocabulary, warning check the class header for
        the required formats

        Required arguments:
        cv_id        -- name of the controlled vocabulary
        descriptions -- list of descriptions
        entries      -- dictionary of entries

        Keyword arguments:
        ext_ref      -- external ref
        """
        self.controlledvocabularies[cv_id] = (descriptions, entries, ext_ref)

    def get_tier_ids_for_linguistic_type(self, ling_type, parent=None):
        """give a list of all tiers matching a linguistic type

        Required arguments:
        ling_type -- linguistic type name

        Keyword arguments:
        parent    -- only match tiers from this parent
        """
        return [t for t in self.tiers if
                self.tiers[t][2]['LINGUISTIC_TYPE_REF'] == ling_type and
                (parent is None or self.tiers[t][2]['PARENT_REF'] == parent)]

    def remove_linguistic_type(self, ling_type):
        """remove a linguistic type

        Required arguments:
        ling_type -- name of the linguistic type
        """
        try:
            del(self.linguistic_types[ling_type])
            return 0
        except KeyError:
            warnings.warn("""remove_linguistic_type: Linguistic type non exist\
ent!""")
            return 1

    def create_linguistic_type(self, lingtype, constraints, timealignable=True,
                               graphicreferences=False, extref=None):
        """create a linguistic type

        Required arguments:
        lingtype          -- name of the linguistic type
        constraints       -- constraint names

        Keyword arguments:
        timealignable     -- flag for time alignable
        graphicreferences -- graphic references
        extref            -- external references
        """
        self.linguistic_types[lingtype] = {
            'LINGUISTIC_TYPE_ID': lingtype,
            'TIME_ALIGNABLE': str(timealignable).lower(),
            'GRAPHIC_REFERENCES': str(graphicreferences).lower(),
            'CONSTRAINTS': constraints}
        if extref is not None:
            self.linguistic_types[lingtype]['EXT_REF'] = extref

    def get_linguistic_types(self):
        """give a list of available linguistic types"""
        return self.linguistic_types.keys()
