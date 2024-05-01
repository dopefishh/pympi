from xml.etree import cElementTree as etree
import re
import sys
import time
import pathlib
import warnings

VERSION = '1.70.2'


class Eaf:
    """Read and write Elan's Eaf files.

    .. note:: All times are in milliseconds and can't have decimals.

    :var dict adocument: Annotation document TAG entries.
    :var list licenses: Licences included in the file of the form:
        ``(name, url)``.
    :var dict header: XML header.
    :var list media_descriptors: Linked files, where every file is of the
        form: ``{attrib}``.
    :var list properties: Properties, where every property is of the form:
        ``(key, value)``.
    :var list linked_file_descriptors: Secondary linked files, where every
        linked file is of the form: ``{attrib}``.
    :var dict timeslots: Timeslot data of the form: ``{id -> time(ms)}``.
    :var dict tiers: Tiers, where every tier is of the form:
        ``{tier_name -> (aligned_annotations, reference_annotations,
        attributes, ordinal)}``,

        aligned_annotations of the form: ``[{id -> (begin_ts, end_ts, value,
        svg_ref)}]``,

        reference annotations of the form: ``[{id -> (reference, value,
        previous, svg_ref)}]``.
    :var list linguistic_types: Linguistic types, where every type is of the
        form: ``{id -> attrib}``.
    :var dict locales: Locales, of the form:
        ``{lancode -> (countrycode, variant)}``.
    :var dict languages: Languages, of the form:
        ``{langid -> (langdef, langlabel)}``.
    :var dict constraints: Constraints, every constraint is of the form:
        ``{stereotype -> description}``.
    :var dict controlled_vocabularies: Controlled vocabulary, where every
        controlled vocabulary is of the form: ``{id -> (descriptions, entries,
        ext_ref)}``,

        descriptions of the form: ``[(value, lang_ref, description)]``,

        entries of the form: ``{id -> (values, ext_ref)}``,

        values of the form:  ``[(lang_ref, description, text)]``.
    :var list external_refs: External references of the form:
        ``{id -> (type, value)}``.
    :var list lexicon_refs: Lexicon references, where every reference is of
        the form: ``{id -> {attribs}}``.

    :var dict annotations: Dictionary of annotations of the form:
        ``{id -> tier}``, this is only used internally.
    """
    ETYPES = {'iso12620', 'ecv', 'cve_id', 'lexen_id', 'resource_url'}
    CONSTRAINTS = {
        'Time_Subdivision': "Time subdivision of parent annotation's time inte"
        'rval, no time gaps allowed within this interval',
        'Symbolic_Subdivision': 'Symbolic subdivision of a parent annotation. '
        'Annotations refering to the same parent are ordered',
        'Symbolic_Association': '1-1 association with a parent annotation',
        'Included_In': 'Time alignable annotations within the parent annotatio'
        "n's time interval, gaps are allowed"}
    MIMES = {'wav': 'audio/x-wav', 'mpg': 'video/mpeg', 'mpeg': 'video/mpg',
             'mp4': 'video/mp4', 'xml': 'text/xml'}

    def __init__(self, file_path=None, author='pympi',
                 suppress_version_warning=False):
        """Construct either a new Eaf file or read on from a file/stream.

        :param str file_path: Path to read from, - for stdin. If ``None`` an
            empty Eaf file will be created.
        :param str author: Author of the file.
        :param bool supress_version_warning: Suppress the warning for
            unsupported EAF file versions
        """
        ctz = -time.altzone if time.localtime(time.time()).tm_isdst and\
            time.daylight else -time.timezone
        self.maxts = 1
        self.maxaid = 1
        self.adocument = {
            'AUTHOR': author,
            'DATE': time.strftime('%Y-%m-%dT%H:%M:%S{:0=+3d}:{:0=2d}').format(
                ctz // 3600, ctz % 3600),
            'VERSION': '2.8',
            'FORMAT': '2.8',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:noNamespaceSchemaLocation':
                'http://www.mpi.nl/tools/elan/EAFv2.8.xsd'}
        self.annotations = {}
        self.constraints = {}
        self.controlled_vocabularies = {}
        self.external_refs = {}
        self.header = {}
        self.languages = {}
        self.lexicon_refs = {}
        self.linguistic_types = {}
        self.locales = {}
        self.tiers = {}
        self.timeslots = {}
        self.licenses = []
        self.linked_file_descriptors = []
        self.media_descriptors = []
        self.properties = []

        if file_path is None:
            self.add_linguistic_type('default-lt')
            self.constraints = self.CONSTRAINTS.copy()
            self.properties.append(('lastUsedAnnotation', 0))
            self.add_tier('default')
        else:
            parse_eaf(file_path, self, suppress_version_warning)

    def add_annotation(self, id_tier, start, end, value='', svg_ref=None):
        """Add an annotation.

        :param str id_tier: Name of the tier.
        :param int start: Start time of the annotation.
        :param int end: End time of the annotation.
        :param str value: Value of the annotation.
        :param str svg_ref: Svg reference.
        :raises KeyError: If the tier is non existent.
        :raises ValueError: If one of the values is negative or start is bigger
                            then end or if the tiers already contains ref
                            annotations.
        """
        if self.tiers[id_tier][1]:
            raise ValueError('Tier already contains ref annotations...')
        if not isinstance(start, int) or not isinstance(end, int):
            raise ValueError('start and end must be an integer...')
        if start == end:
            raise ValueError('Annotation length is zero...')
        if start > end:
            raise ValueError('Annotation length is negative...')
        if start < 0:
            raise ValueError('Start is negative...')
        start_ts = self.generate_ts_id(start)
        end_ts = self.generate_ts_id(end)
        aid = self.generate_annotation_id()
        self.annotations[aid] = id_tier
        self.tiers[id_tier][0][aid] = (start_ts, end_ts, value, svg_ref)

    def add_controlled_vocabulary(self, cv_id, ext_ref=None):
        """Add a controlled vocabulary. This will initialize the controlled
        vocabulary without entries.

        :param str cv_id: Name of the controlled vocabulary.
        :param str ext_ref: External reference.
        """
        self.controlled_vocabularies[cv_id] = ([], {}, ext_ref)

    def add_cv_entry(self, cv_id, cve_id, values, ext_ref=None):
        """Add an entry to a controlled vocabulary.

        :param str cv_id: Name of the controlled vocabulary to add an entry.
        :param str cve_id: Name of the entry.
        :param list values: List of values of the form:
            ``(value, lang_ref, description)`` where description can be
            ``None``.
        :param str ext_ref: External reference.
        :throws KeyError: If there is no controlled vocabulary with that id.
        :throws ValueError: If a language in one of the entries doesn't exist.
        """
        for value, lang_ref, description in values:
            if lang_ref not in self.languages:
                raise ValueError('Language not present: {}'.format(lang_ref))
        self.controlled_vocabularies[cv_id][1][cve_id] = (values, ext_ref)

    def add_cv_description(self, cv_id, lang_ref, description=None):
        """Add a description to a controlled vocabulary.

        :param str cv_id: Name of the controlled vocabulary to add the
            description.
        :param str lang_ref: Language reference.
        :param str description: Description, this can be none.
        :throws KeyError: If there is no controlled vocabulary with that id.
        :throws ValueError: If the language provided doesn't exist.
        """
        if lang_ref not in self.languages:
            raise ValueError('Language not present: {}'.format(lang_ref))
        self.controlled_vocabularies[cv_id][0].append((lang_ref, description))

    def add_external_ref(self, eid, etype, value):
        """Add an external reference.

        :param str eid: Name of the external reference.
        :param str etype: Type of the external reference, has to be in
            ``['iso12620', 'ecv', 'cve_id', 'lexen_id', 'resource_url']``.
        :param str value: Value of the external reference.
        :throws KeyError: if etype is not in the list of possible types.
        """
        if etype not in self.ETYPES:
            raise KeyError('etype not in {}'.format(self.ETYPES))
        self.external_refs[eid] = (etype, value)

    def add_language(self, lang_id, lang_def=None, lang_label=None):
        """Add a language.

        :param str lang_id: ID of the language.
        :param str lang_def: Definition of the language(preferably ISO-639-3).
        :param str lang_label: Label of the language.
        """
        self.languages[lang_id] = (lang_def, lang_label)

    def add_lexicon_ref(self, lrid, name, lrtype, url, lexicon_id,
                        lexicon_name, datcat_id=None, datcat_name=None):
        """Add lexicon reference.

        :param str lrid: Lexicon reference internal ID.
        :param str name: Lexicon reference display name.
        :param str lrtype: Lexicon reference service type.
        :param str url: Lexicon reference service location
        :param str lexicon_id: Lexicon reference service id.
        :param str lexicon_name: Lexicon reference service name.
        :param str datacat_id: Lexicon reference identifier of data category.
        :param str datacat_name: Lexicon reference name of data category.
        """
        self.lexicon_refs[lrid] = {
            'LEX_REF_ID': lrid,
            'NAME': name,
            'TYPE': lrtype,
            'URL': url,
            'LEXICON_ID': lexicon_id,
            'LEXICON_NAME': lexicon_name,
            'DATCAT_ID': datcat_id,
            'DATCAT_NAME': datcat_name
            }

    def add_license(self, name, url):
        """Add a license

        :param str name: Name of the license.
        :param str url: URL of the license.
        """
        self.licenses.append((name, url))

    def add_linguistic_type(self, lingtype, constraints=None,
                            timealignable=True, graphicreferences=False,
                            extref=None, param_dict=None):
        """Add a linguistic type.

        :param str lingtype: Name of the linguistic type.
        :param str constraints: Constraint name.
        :param bool timealignable: Flag for time alignable.
        :param bool graphicreferences: Flag for graphic references.
        :param str extref: External reference.
        :param dict param_dict: TAG attributes, when this is not ``None`` it
                                 will ignore all other options. Please only use
                                 dictionaries coming from the
                                 :func:`get_parameters_for_linguistic_type`
        :raises KeyError: If a constraint is not defined
        """
        if param_dict:
            self.linguistic_types[lingtype] = param_dict
        else:
            if constraints:
                self.constraints[constraints]
            self.linguistic_types[lingtype] = {
                'LINGUISTIC_TYPE_ID': lingtype,
                'TIME_ALIGNABLE': str(timealignable).lower(),
                'GRAPHIC_REFERENCES': str(graphicreferences).lower(),
                'CONSTRAINTS': constraints}
            if extref is not None:
                self.linguistic_types[lingtype]['EXT_REF'] = extref

    def add_linked_file(self, file_path, relpath=None, mimetype=None,
                        time_origin=None, ex_from=None):
        """Add a linked file.

        :param str file_path: Path of the file.
        :param str relpath: Relative path of the file.
        :param str mimetype: Mimetype of the file, if ``None`` it tries to
            guess it according to the file extension which currently only works
            for wav, mpg, mpeg and xml.
        :param int time_origin: Time origin for the media file.
        :param str ex_from: Extracted from field.
        :raises KeyError: If mimetype had to be guessed and a non standard
                          extension or an unknown mimetype.
        """
        if mimetype is None:
            mimetype = self.MIMES[file_path.split('.')[-1].lower()]
        self.media_descriptors.append({
            'MEDIA_URL': file_path, 'RELATIVE_MEDIA_URL': relpath,
            'MIME_TYPE': mimetype, 'TIME_ORIGIN': time_origin,
            'EXTRACTED_FROM': ex_from})

    def add_locale(self, language_code, country_code=None, variant=None):
        """Add a locale.

        :param str language_code: The language code of the locale.
        :param str country_code: The country code of the locale.
        :param str variant: The variant of the locale.
        """
        self.locales[language_code] = (country_code, variant)

    def add_property(self, key, value):
        """Add a property

        :param str key: Key of the property.
        :param str value: Value of the property.
        """
        self.properties.append((key, value))

    def add_ref_annotation(self, id_tier, tier2, time, value='',
                           prev=None, svg=None):
        """Add a reference annotation.
        .. note:: When a timepoint matches two annotations the new reference
        annotation will reference to the first annotation. To circumvent this
        it's always safer to take the middle of the annotation you want to
        reference to.

        :param str id_tier: Name of the tier.
        :param str tier2: Tier of the referenced annotation.
        :param int time: Time of the referenced annotation.
        :param str value: Value of the annotation.
        :param str prev: Id of the previous annotation.
        :param str svg_ref: Svg reference.
        :raises KeyError: If the tier is non existent.
        :raises ValueError: If the tier already contains normal annotations or
            if there is no annotation in the tier on the time to reference to.
        """
        if self.tiers[id_tier][0]:
            raise ValueError('This tier already contains normal annotations.')
        ann = None
        # tier2 is an independent (aligned reference) tier
        if self.tiers[tier2][0]:
            for aid, (begin, end, _, _) in self.tiers[tier2][0].items():
                begin = self.timeslots[begin]
                end = self.timeslots[end]
                if begin <= time and end >= time:
                    ann = aid
                    break
        # tier2 is a reference tier, so we grab the top tier in the hierarchy
        else:
            for aid, (reference, _, _, _) in self.tiers[tier2][1].items():
                refann = self.get_parent_aligned_annotation(aid)
                begin = self.timeslots[refann[0]]
                end = self.timeslots[refann[1]]
                if begin <= time and end >= time:
                    ann = aid
                    break
        if not ann:
            raise ValueError('There is no annotation to reference to.')
        aid = self.generate_annotation_id()
        self.annotations[aid] = id_tier
        self.tiers[id_tier][1][aid] = (ann, value, prev, svg)

    def add_secondary_linked_file(self, file_path, relpath=None, mimetype=None,
                                  time_origin=None, assoc_with=None):
        """Add a secondary linked file.

        :param str file_path: Path of the file.
        :param str relpath: Relative path of the file.
        :param str mimetype: Mimetype of the file, if ``None`` it tries to
            guess it according to the file extension which currently only works
            for wav, mpg, mpeg and xml.
        :param int time_origin: Time origin for the media file.
        :param str assoc_with: Associated with field.
        :raises KeyError: If mimetype had to be guessed and a non standard
                          extension or an unknown mimetype.
        """
        if mimetype is None:
            mimetype = self.MIMES[file_path.split('.')[-1]]
        self.linked_file_descriptors.append({
            'LINK_URL': file_path, 'RELATIVE_LINK_URL': relpath,
            'MIME_TYPE': mimetype, 'TIME_ORIGIN': time_origin,
            'ASSOCIATED_WITH': assoc_with})

    def add_tier(self, tier_id, ling='default-lt', parent=None, locale=None,
                 part=None, ann=None, language=None, tier_dict=None):
        """Add a tier. When no linguistic type is given and the default
        linguistic type is unavailable then the assigned linguistic type will
        be the first in the list.

        :param str tier_id: Name of the tier.
        :param str ling: Linguistic type, if the type is not available it will
                         warn and pick the first available type.
        :param str parent: Parent tier name.
        :param str locale: Locale, if the locale is not present this option is
            ignored and the locale will not be set.
        :param str part: Participant.
        :param str ann: Annotator.
        :param str language: Language , if the language is not present this
            option is ignored and the language will not be set.
        :param dict tier_dict: TAG attributes, when this is not ``None`` it
                               will ignore all other options. Please only use
                               dictionaries coming from the
                               :func:`get_parameters_for_tier`
        :raises ValueError: If the tier_id is empty
        """
        if not tier_id:
            raise ValueError('Tier id is empty...')
        if ling not in self.linguistic_types:
            ling = sorted(self.linguistic_types.keys())[0]
        if locale and locale not in self.locales:
            locale = None
        if language and language not in self.languages:
            language = None
        if tier_dict is None:
            self.tiers[tier_id] = ({}, {}, {
                'TIER_ID': tier_id,
                'LINGUISTIC_TYPE_REF': ling,
                'PARENT_REF': parent,
                'PARTICIPANT': part,
                'DEFAULT_LOCALE': locale,
                'LANG_REF': language,
                'ANNOTATOR': ann}, len(self.tiers))
        else:
            self.tiers[tier_id] = ({}, {}, tier_dict, len(self.tiers))

    def child_tiers_for(self, id_tier):
        """.. deprecated: 1.5

        Use :func:`get_child_tiers_for`
        """
        return self.get_child_tiers_for(id_tier)

    def clean_time_slots(self):
        """Clean up all unused timeslots.

        .. warning:: This can and will take time for larger tiers.

        When you want to do a lot of operations on a lot of tiers please unset
        the flags for cleaning in the functions so that the cleaning is only
        performed afterwards.
        """
        ts = ((a[0], a[1]) for t in self.tiers.values() for a in t[0].values())
        for a in {a for b in ts for a in b} ^ set(self.timeslots):
            del(self.timeslots[a])

    def copy_tier(self, eaf_obj, tier_name):
        """Copies a tier to another :class:`pympi.Elan.Eaf` object.

        :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
        :param str tier_name: Name of the tier.
        :raises KeyError: If the tier doesn't exist.
        """
        if tier_name in eaf_obj.get_tier_names():
            eaf_obj.remove_tier(tier_name)
        eaf_obj.add_tier(tier_name,
                         tier_dict=self.get_parameters_for_tier(tier_name))
        for ann in self.get_annotation_data_for_tier(tier_name):
            eaf_obj.insert_annotation(tier_name, ann[0], ann[1], ann[2])

    def create_gaps_and_overlaps_tier(self, tier1, tier2, tier_name=None,
                                      maxlen=-1, fast=False):
        """Create a tier with the gaps and overlaps of the annotations.
        For types see :func:`get_gaps_and_overlaps`

        :param str tier1: Name of the first tier.
        :param str tier2: Name of the second tier.
        :param str tier_name: Name of the new tier, if ``None`` the name will
                              be generated.
        :param int maxlen: Maximum length of gaps (skip longer ones), if ``-1``
                           no maximum will be used.
        :param bool fast: Flag for using the fast method.
        :returns: List of gaps and overlaps of the form:
                  ``[(type, start, end)]``.
        :raises KeyError: If a tier is non existent.
        :raises IndexError: If no annotations are available in the tiers.
        """
        if tier_name is None:
            tier_name = '{}_{}_ftos'.format(tier1, tier2)
        self.add_tier(tier_name)
        ftos = []
        ftogen = self.get_gaps_and_overlaps2(tier1, tier2, maxlen) if fast\
            else self.get_gaps_and_overlaps(tier1, tier2, maxlen)
        for fto in ftogen:
            ftos.append(fto)
            if fto[1]-fto[0] >= 1:
                self.add_annotation(tier_name, fto[0], fto[1], fto[2])
        self.clean_time_slots()
        return ftos

    def extract(self, start, end):
        """Extracts the selected time frame as a new object.

        :param int start: Start time.
        :param int end: End time.
        :returns: class:`pympi.Elan.Eaf` object containing the extracted frame.
        """
        from copy import deepcopy
        eaf_out = deepcopy(self)

        align_tier_names = []
        ref_tier_names = []
        for t in eaf_out.get_tier_names():
            t_type = eaf_out.tiers[t][2]['LINGUISTIC_TYPE_REF']
            if eaf_out.linguistic_types[t_type]['TIME_ALIGNABLE'] == 'true':
                align_tier_names.append(t)
            else:
                ref_tier_names.append(t)

        # Make sure that annotations on reference tiers are removed first (so
        # that it's possible to look up their start and end times from their
        # time-aligned parent annotations when calling 'remove_annotation').
        for t in ref_tier_names + align_tier_names:
            for ab, ae, value, *_ in eaf_out.get_annotation_data_for_tier(t):
                if ab > end or ae < start:
                    eaf_out.remove_annotation(t, (ae + ab) // 2, False)
        eaf_out.clean_time_slots()
        return eaf_out

    def filter_annotations(self, tier, tier_name=None, filtin=None,
                           filtex=None, regex=False, safe=False):
        """Filter annotations in a tier using an exclusive and/or inclusive
        filter.

        :param str tier: Name of the tier.
        :param str tier_name: Name of the output tier, when ``None`` the name
            will be generated.
        :param list filtin: List of strings to be included, if None all
            annotations all is included.
        :param list filtex: List of strings to be excluded, if None no strings
            are excluded.
        :param bool regex: If this flag is set, the filters are seen as regex
            matches.
        :param bool safe: Ignore zero length annotations(when working with
            possible malformed data).
        :returns: Name of the created tier.
        :raises KeyError: If the tier is non existent.
        """
        if tier_name is None:
            tier_name = '{}_filter'.format(tier)
        self.add_tier(tier_name)
        func = (lambda x, y: re.match(x, y)) if regex else lambda x, y: x == y
        for begin, end, value in self.get_annotation_data_for_tier(tier):
            if (filtin and not any(func(f, value) for f in filtin)) or\
                    (filtex and any(func(f, value) for f in filtex)):
                continue
            if not safe or end > begin:
                self.add_annotation(tier_name, begin, end, value)
        self.clean_time_slots()
        return tier_name

    def generate_annotation_id(self):
        """Generate the next annotation id, this function is mainly used
        internally.
        """
        if not self.maxaid:
            valid_anns = [int(''.join(filter(str.isdigit, a)))
                          for a in self.timeslots]
            self.maxaid = max(valid_anns + [1])+1
        else:
            self.maxaid += 1
        return 'a{:d}'.format(self.maxaid)

    def generate_ts_id(self, time=None):
        """Generate the next timeslot id, this function is mainly used
        internally

        :param int time: Initial time to assign to the timeslot.
        :raises ValueError: If the time is negative.
        """
        if time and time < 0:
            raise ValueError('Time is negative...')

        if not self.maxts:
            valid_ts = [int(''.join(filter(str.isdigit, a)))
                        for a in self.timeslots]
            self.maxts = max(valid_ts + [1])+1
        else:
            self.maxts += 1
        ts = 'ts{:d}'.format(self.maxts)
        self.timeslots[ts] = time
        return ts

    def get_annotation_data_at_time(self, id_tier, time):
        """Give the annotations at the given time. When the tier contains
        reference annotations this will be returned, check
        :func:`get_ref_annotation_data_at_time` for the format.

        :param str id_tier: Name of the tier.
        :param int time: Time of the annotation.
        :returns: List of annotations at that time.
        :raises KeyError: If the tier is non existent.
        """
        if self.tiers[id_tier][1]:
            return self.get_ref_annotation_at_time(id_tier, time)
        anns = self.tiers[id_tier][0]
        return sorted([(self.timeslots[m[0]], self.timeslots[m[1]], m[2])
                       for m in anns.values() if
                       self.timeslots[m[0]] <= time and
                       self.timeslots[m[1]] >= time])

    def get_annotation_data_after_time(self, id_tier, time):
        """Give the annotation before a given time. When the tier contains
        reference annotations this will be returned, check
        :func:`get_ref_annotation_data_before_time` for the format. If an
        annotation overlaps with ``time`` that annotation will be returned.

        :param str id_tier: Name of the tier.
        :param int time: Time to get the annotation before.
        :raises KeyError: If the tier is non existent.
        """
        if self.tiers[id_tier][1]:
            return self.get_ref_annotation_after_time(id_tier, time)
        befores = self.get_annotation_data_between_times(
            id_tier, time, self.get_full_time_interval()[1])
        if befores:
            return [min(befores, key=lambda x: x[0])]
        else:
            return []

    def get_annotation_data_before_time(self, id_tier, time):
        """Give the annotation before a given time. When the tier contains
        reference annotations this will be returned, check
        :func:`get_ref_annotation_data_before_time` for the format. If an
        annotation overlaps with ``time`` that annotation will be returned.

        :param str id_tier: Name of the tier.
        :param int time: Time to get the annotation before.
        :raises KeyError: If the tier is non existent.
        """
        if self.tiers[id_tier][1]:
            return self.get_ref_annotation_before_time(id_tier, time)
        befores = self.get_annotation_data_between_times(id_tier, 0, time)
        if befores:
            return [max(befores, key=lambda x: x[0])]
        else:
            return []

    def get_annotation_data_between_times(self, id_tier, start, end):
        """Gives the annotations within the times.
        When the tier contains reference annotations this will be returned,
        check :func:`get_ref_annotation_data_between_times` for the format.

        :param str id_tier: Name of the tier.
        :param int start: Start time of the annotation.
        :param int end: End time of the annotation.
        :returns: List of annotations within that time.
        :raises KeyError: If the tier is non existent.
        """
        if self.tiers[id_tier][1]:
            return self.get_ref_annotation_data_between_times(
                id_tier, start, end)
        anns = ((self.timeslots[a[0]], self.timeslots[a[1]], a[2])
                for a in self.tiers[id_tier][0].values())
        return sorted(a for a in anns if a[1] >= start and a[0] <= end)

    def get_annotation_data_for_tier(self, id_tier):
        """Gives a list of annotations of the form: ``(begin, end, value)``
        When the tier contains reference annotations this will be returned,
        check :func:`get_ref_annotation_data_for_tier` for the format.

        :param str id_tier: Name of the tier.
        :raises KeyError: If the tier is non existent.
        """
        if self.tiers[id_tier][1]:
            return self.get_ref_annotation_data_for_tier(id_tier)
        a = self.tiers[id_tier][0]
        return [(self.timeslots[a[b][0]], self.timeslots[a[b][1]], a[b][2])
                for b in a]
    
    def get_annotation_data_for_symbsub_tier(self, id_tier):
        """"Give a list of all annotations of id_tier with their calculated start, end and value of the form:
        ``[(start, end, value, value)]``

        :param str id_tier: Name of the tier.
        :raises KeyError: If the tier is non existent.
        :returns: Reference annotations within that tier.
        """
        ref_ann = self.get_ref_annotation_data_for_tier(id_tier)
        bucket = []
        children = []
        begin,end,value,ref = ref_ann[0]
        prevEnd = end
        for i in range(0, len(ref_ann)-1):
            if ref_ann[i][1] == prevEnd:
                children.append([ref_ann[i][0],ref_ann[i][1],ref_ann[i][2]])
            else:
                nbChildren = len(children)
                duration = round((children[nbChildren-1][1] - children[0][0])/nbChildren)
                for j in range(0,nbChildren-1):
                    children[j][0] = begin
                    children[j][1] = children[j][0] + duration
                    begin = children[j][1]
                children[nbChildren-1][0] = begin
                children[nbChildren-1][1] = prevEnd
                for child in children:
                    bucket.append((child[0],child[1],child[2]))
                children = []
                prevEnd = ref_ann[i][1]
                begin = ref_ann[i][0]
                children.append([begin, end, ref_ann[i][2]])
        #print('bucket');print(bucket)
        return bucket
    
    def get_child_tiers_for(self, id_tier):
        """Give all child tiers for a tier.

        :param str id_tier: Name of the tier.
        :returns: List of all children
        :raises KeyError: If the tier is non existent.
        """
        self.tiers[id_tier]
        return [m for m in self.tiers if 'PARENT_REF' in self.tiers[m][2] and
                self.tiers[m][2]['PARENT_REF'] == id_tier]

    def get_full_time_interval(self):
        """Give the full time interval of the file. Note that the real interval
        can be longer because the sound file attached can be longer.

        :returns: Tuple of the form: ``(min_time, max_time)``.
        """
        return (0, 0) if not self.timeslots else\
            (min(v for v in self.timeslots.values() if v is not None),
             max(v for v in self.timeslots.values() if v is not None))

    def get_gaps_and_overlaps(self, tier1, tier2, maxlen=-1):
        """Give gaps and overlaps. The return types are shown in the table
        below. The string will be of the format: ``id_tiername_tiername``.

        .. note:: There is also a faster method: :func:`get_gaps_and_overlaps2`

        For example when a gap occurs between tier1 and tier2 and they are
        called ``speakerA`` and ``speakerB`` the annotation value of that gap
        will be ``G12_speakerA_speakerB``.

        | The gaps and overlaps are calculated using Heldner and Edlunds
          method found in:
        | *Heldner, M., & Edlund, J. (2010). Pauses, gaps and overlaps in
          conversations. Journal of Phonetics, 38(4), 555–568.
          doi:10.1016/j.wocn.2010.08.002*

        +-----+---------------------------------------------+
        | id  | Description                                 |
        +=====+=============================================+
        | O12 | Overlap from tier1 to tier2                 |
        +-----+---------------------------------------------+
        | O21 | Overlap from tier2 to tier1                 |
        +-----+---------------------------------------------+
        | G12 | Between speaker gap from tier1 to tier2     |
        +-----+---------------------------------------------+
        | G21 | Between speaker gap from tier2 to tier1     |
        +-----+---------------------------------------------+
        | W12 | Within speaker overlap from tier2 in tier1  |
        +-----+---------------------------------------------+
        | W21 | Within speaker overlap from tier1 in tier2  |
        +-----+---------------------------------------------+
        | P1  | Pause for tier1                             |
        +-----+---------------------------------------------+
        | P2  | Pause for tier2                             |
        +-----+---------------------------------------------+

        :param str tier1: Name of the first tier.
        :param str tier2: Name of the second tier.
        :param int maxlen: Maximum length of gaps (skip longer ones), if ``-1``
                           no maximum will be used.
        :yields: Tuples of the form ``[(start, end, type)]``.
        :raises KeyError: If a tier is non existent.
        :raises IndexError: If no annotations are available in the tiers.
        """
        spkr1anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]])
                           for a in self.tiers[tier1][0].values())
        spkr2anns = sorted((self.timeslots[a[0]], self.timeslots[a[1]])
                           for a in self.tiers[tier2][0].values())
        line1 = []

        def isin(x, lst):
            return False if\
                len([i for i in lst if i[0] <= x and i[1] >= x]) == 0 else True
        minmax = (min(spkr1anns[0][0], spkr2anns[0][0]),
                  max(spkr1anns[-1][1], spkr2anns[-1][1]))
        last = (1, minmax[0])
        for ts in range(*minmax):
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
        line1.append((last[0], last[1], minmax[1]))
        for i in range(len(line1)):
            if line1[i][0] == 'N':
                if i != 0 and i < len(line1) - 1 and\
                        line1[i-1][0] != line1[i+1][0]:
                    t = ('G12', tier1, tier2) if line1[i-1][0] == '1' else\
                        ('G21', tier2, tier1)
                    if maxlen == -1 or abs(line1[i][1]-line1[i][2]) < maxlen:
                        yield (line1[i][1], line1[i][2]-1, '_'.join(t))
                else:
                    t = ('P1', tier1) if line1[i-1][0] == '1' else\
                        ('P2', tier2)
                    if maxlen == -1 or abs(line1[i][1]-line1[i][2]) < maxlen:
                        yield (line1[i][1], line1[i][2]-1, '_'.join(t))
            elif line1[i][0] == 'B':
                if i != 0 and i < len(line1) - 1 and\
                        line1[i-1][0] != line1[i+1][0]:
                    t = ('O12', tier1, tier2) if line1[i-1][0] == '1' else\
                        ('O21', tier2, tier1)
                    yield (line1[i][1], line1[i][2]-1, '_'.join(t))
                else:
                    t = ('W12', tier1, tier2) if line1[i-1][0] == '1' else\
                        ('W21', tier2, tier1)
                    yield (line1[i][1], line1[i][2]-1, '_'.join(t))

    def get_gaps_and_overlaps2(self, tier1, tier2, maxlen=-1):
        """Faster variant of :func:`get_gaps_and_overlaps`. Faster in this case
        means almost 100 times faster...

        :param str tier1: Name of the first tier.
        :param str tier2: Name of the second tier.
        :param int maxlen: Maximum length of gaps (skip longer ones), if ``-1``
                           no maximum will be used.
        :yields: Tuples of the form ``[(start, end, type)]``.
        :raises KeyError: If a tier is non existent.
        """
        ad = sorted(((a, i+1) for i, t in enumerate([tier1, tier2]) for a in
                     self.get_annotation_data_for_tier(t)), reverse=True)
        if ad:
            last = (lambda x: (x[0][0], x[0][1], x[1]))(ad.pop())

            def thr(x, y):
                return maxlen == -1 or abs(x-y) < maxlen
            while ad:
                (begin, end, _), current = ad.pop()
                if last[2] == current and thr(begin, last[1]):
                    yield (last[1], begin, 'P{}'.format(current))
                elif last[0] < begin and last[1] > end:
                    yield (begin, end, 'W{}{}'.format(last[2], current))
                    continue
                elif last[1] > begin:
                    yield (begin, last[1], 'O{}{}'.format(last[2], current))
                elif last[1] < begin and thr(begin, last[1]):
                    yield (last[1], begin, 'G{}{}'.format(last[2], current))
                last = (begin, end, current)

    def get_controlled_vocabulary_names(self):
        """Gives all the controlled vocabulary names"""
        return self.controlled_vocabularies.keys()

    def get_cv_entries(self, cv_id):
        """Gives all the controlled vocabulary entries names.

        :param str cv_id: Name of the controlled vocabulary.
        :throws KeyError: If there is no controlled vocabulary with that id.
        """
        return self.controlled_vocabularies[cv_id][1]

    def get_cv_descriptions(self, cv_id):
        """Gives all the controlled vocabulary descriptions.

        :param str cv_id: Name of the controlled vocabulary.
        :throws KeyError: If there is no controlled vocabulary with that id.
        """
        return self.controlled_vocabularies[cv_id][0]

    def get_external_ref(self, eid):
        """Give the external reference matching the id.

        :param str eid: Name of the external reference.
        :throws KeyError: If there is no external reference with that id.
        """
        return self.external_refs[eid]

    def get_external_ref_names(self):
        """Gives all the external reference names."""
        return self.external_refs.keys()

    def get_lexicon_ref(self, reid):
        """Gives the lexicon reference.

        :param str reid: Lexicon reference id.
        :throws KeyError: If there is no lexicon reference matching the id.
        """
        return self.lexicon_refs[reid]

    def get_lexicon_ref_names(self):
        """Gives all the lexicon reference names."""
        return self.lexicon_refs.keys()

    def get_languages(self):
        """Gives all the languages in the format:
        ``{lang_id -> (lang_def, lang_label)}``
        """
        return self.languages

    def get_licenses(self):
        """Gives all the licenses in the format: ``[(name, url)]``"""
        return self.licenses

    def get_linguistic_type_names(self):
        """Give a list of available linguistic types.

        :returns: List of linguistic type names.
        """
        return self.linguistic_types.keys()

    def get_linked_files(self):
        """Give all linked files."""
        return self.media_descriptors

    def get_locales(self):
        """Gives all the locales in the format: ``{language_code ->
        (country_code, variant)}``
        """
        return self.locales

    def get_parameters_for_linguistic_type(self, lingtype):
        """Give the parameter dictionary, this is usable in
        :func:`add_linguistic_type`.

        :param str lingtype: Name of the linguistic type.
        :raises KeyError: If the linguistic type doesn't exist.
        """
        return self.linguistic_types[lingtype]

    def get_parameters_for_tier(self, id_tier):
        """Give the parameter dictionary, this is useable in :func:`add_tier`.

        :param str id_tier: Name of the tier.
        :returns: Dictionary of parameters.
        :raises KeyError: If the tier is non existent.
        """
        return self.tiers[id_tier][2]

    def get_properties(self):
        """Gives all the properties in the format: ``[(key, value)]``"""
        return self.properties

    def get_ref_annotation_at_time(self, tier, time):
        """Give the ref annotations at the given time of the form
        ``[(start, end, value, refvalue)]``

        :param str tier: Name of the tier.
        :param int time: Time of the annotation of the parent.
        :returns: List of annotations at that time.
        :raises KeyError: If the tier is non existent.
        """
        bucket = []
        for aid, (ref, value, _, _) in self.tiers[tier][1].items():
            begin, end, rvalue, _ = self.tiers[self.annotations[ref]][0][ref]
            begin = self.timeslots[begin]
            end = self.timeslots[end]
            if begin <= time and end >= time:
                bucket.append((begin, end, value, rvalue))
        return bucket

    def get_ref_annotation_data_after_time(self, id_tier, time):
        """Give the ref annotation after a time. If an annotation overlaps
        with `ktime`` that annotation will be returned.

        :param str id_tier: Name of the tier.
        :param int time: Time to get the annotation after.
        :returns: Annotation after that time in a list
        :raises KeyError: If the tier is non existent.
        """
        befores = self.get_ref_annotation_data_between_times(
            id_tier, time, self.get_full_time_interval())
        if befores:
            return [min(befores, key=lambda x: x[0])]
        else:
            return []

    def get_ref_annotation_data_before_time(self, id_tier, time):
        """Give the ref annotation before a time. If an annotation overlaps
        with ``time`` that annotation will be returned.

        :param str id_tier: Name of the tier.
        :param int time: Time to get the annotation before.
        :returns: Annotation before that time in a list
        :raises KeyError: If the tier is non existent.
        """
        befores = self.get_ref_annotation_data_between_times(id_tier, 0, time)
        if befores:
            return [max(befores, key=lambda x: x[0])]
        else:
            return []

    def get_ref_annotation_data_between_times(self, id_tier, start, end):
        """Give the ref annotations between times of the form
        ``[(start, end, value, refvalue)]``

        :param str tier: Name of the tier.
        :param int start: End time of the annotation of the parent.
        :param int end: Start time of the annotation of the parent.
        :returns: List of annotations at that time.
        :raises KeyError: If the tier is non existent.
        """
        bucket = []
        for aid, (ref, value, _, _) in self.tiers[id_tier][1].items():
            begin, end, rvalue, _ = self.tiers[self.annotations[ref]][0][ref]
            begin = self.timeslots[begin]
            end = self.timeslots[end]
            if begin <= end and end >= begin:
                bucket.append((begin, end, value, rvalue))
        return bucket

    def get_ref_annotation_data_for_tier(self, id_tier):
        """"Give a list of all reference annotations of the form:
        ``[(start, end, value, refvalue)]``

        :param str id_tier: Name of the tier.
        :raises KeyError: If the tier is non existent.
        :returns: Reference annotations within that tier.
        """
        bucket = []
        for aid, (ref, value, prev, _) in self.tiers[id_tier][1].items():
            refann = self.get_parent_aligned_annotation(ref)
            bucket.append((self.timeslots[refann[0]],
                           self.timeslots[refann[1]], value, refann[2]))
        return bucket

    def get_parent_aligned_annotation(self, ref_id):
        """" Give the aligment annotation that a reference annotation belongs to directly, or indirectly through other
        reference annotations.
        :param str ref_id: Id of a reference annotation.
        :raises KeyError: If no annotation exists with the id or if it belongs to an alignment annotation.
        :returns: The alignment annotation at the end of the reference chain.
        """
        parentTier = self.tiers[self.annotations[ref_id]]
        while 'PARENT_REF' in parentTier[2] and parentTier[2]['PARENT_REF'] and len(parentTier[2]) > 0:
            ref_id = parentTier[1][ref_id][0]
            parentTier = self.tiers[self.annotations[ref_id]]

        return parentTier[0][ref_id]

    def get_secondary_linked_files(self):
        """Give all linked files."""
        return self.linked_file_descriptors

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

    def get_tier_names(self):
        """List all the tier names.

        :returns: List of all tier names
        """
        return self.tiers.keys()

    def insert_annotation(self, id_tier, start, end, value='', svg_ref=None):
        """.. deprecated:: 1.2

        Use :func:`add_annotation` instead.
        """
        return self.add_annotation(id_tier, start, end, value, svg_ref)

    def insert_ref_annotation(self, id_tier, tier2, time, value='',
                              prev=None, svg=None):
        """.. deprecated:: 1.2

        Use :func:`add_ref_annotation` instead.
        """
        return self.add_ref_annotation(id_tier, tier2, time, value, prev, svg)

    def merge_tiers(self, tiers, tiernew=None, gapt=0, sep='_', safe=False):
        """Merge tiers into a new tier and when the gap is lower then the
        threshhold glue the annotations together.

        :param list tiers: List of tier names.
        :param str tiernew: Name for the new tier, if ``None`` the name will be
                            generated.
        :param int gapt: Threshhold for the gaps, if the this is set to 10 it
                         means that all gaps below 10 are ignored.
        :param str sep: Separator for the merged annotations.
        :param bool safe: Ignore zero length annotations(when working with
            possible malformed data).
        :returns: Name of the created tier.
        :raises KeyError: If a tier is non existent.
        """
        if tiernew is None:
            tiernew = u'{}_merged'.format('_'.join(tiers))
        self.add_tier(tiernew)
        aa = [(sys.maxsize, sys.maxsize, None)] + sorted((
            a for t in tiers for a in self.get_annotation_data_for_tier(t)),
            reverse=True)
        l = None
        while aa:
            begin, end, value = aa.pop()
            if l is None:
                l = [begin, end, [value]]
            elif begin - l[1] >= gapt:
                if not safe or l[1] > l[0]:
                    self.add_annotation(tiernew, l[0], l[1], sep.join(l[2]))
                l = [begin, end, [value]]
            else:
                if end > l[1]:
                    l[1] = end
                l[2].append(value)
        return tiernew

    def remove_all_annotations_from_tier(self, id_tier, clean=True):
        """remove all annotations from a tier

        :param str id_tier: Name of the tier.
        :raises KeyError: If the tier is non existent.
        """
        for aid in self.tiers[id_tier][0]:
            del(self.annotations[aid])
        for aid in self.tiers[id_tier][1]:
            del(self.annotations[aid])

        self.tiers[id_tier][0].clear()
        self.tiers[id_tier][1].clear()
        if clean:
            self.clean_time_slots()

    def remove_annotation(self, id_tier, time, clean=True):
        """Remove an annotation in a tier, if you need speed the best thing is
        to clean the timeslots after the last removal. When the tier contains
        reference annotations :func:`remove_ref_annotation` will be executed
        instead.

        :param str id_tier: Name of the tier.
        :param int time: Timepoint within the annotation.
        :param bool clean: Flag to clean the timeslots afterwards.
        :raises KeyError: If the tier is non existent.
        :returns: Number of removed annotations.
        """
        if self.tiers[id_tier][1]:
            return self.remove_ref_annotation(id_tier, time)
        removed = 0
        for b in sorted([a for a in self.tiers[id_tier][0].items() if
                  self.timeslots[a[1][0]] <= time and
                  self.timeslots[a[1][1]] >= time], reverse=True):
            del(self.tiers[id_tier][0][b[0]])
            del(self.annotations[b[0]])
            removed += 1
        if clean:
            self.clean_time_slots()
        return removed

    def remove_controlled_vocabulary(self, cv_id):
        """Remove a controlled vocabulary.

        :param str cv_id: Name of the controlled vocabulary.
        :throws KeyError: If there is no controlled vocabulary with that name.
        """
        del(self.controlled_vocabularies[cv_id])

    def remove_cv_entry(self, cv_id, cve_id):
        """Remove a controlled vocabulary entry.

        :param str cv_id: Name of the controlled vocabulary.
        :paarm str cve_id: Name of the entry.
        :throws KeyError: If there is no entry or controlled vocabulary with
            that name.
        """
        del(self.controlled_vocabularies[cv_id][1][cve_id])

    def remove_cv_description(self, cv_id, lang_ref):
        """Remove a controlled vocabulary description.

        :param str cv_id: Name of the controlled vocabulary.
        :paarm str cve_id: Name of the entry.
        :throws KeyError: If there is no controlled vocabulary with that name.
        """
        for i, (l, d) in reversed(enumerate(
                self.controlled_vocabularies[cv_id][1])):
            if l == lang_ref:
                del(self.controlled_vocabularies[cv_id][1][i])

    def remove_external_ref(self, eid):
        """Remove an external reference.

        :param str eid: Name of the external reference.
        :throws KeyError: If there is no external reference with that id.
        """
        del(self.external_refs[eid])

    def remove_language(self, lang_id):
        """Remove the language mathing the id.

        :param str lang_id: Language id of the language.
        :throws KeyError: If there is no language matching the language id.
        """
        del(self.languages[lang_id])

    def remove_lexicon_ref(self, reid):
        """Remove a lexicon reference matching the id.

        :param str reid: Lexicon reference id.
        :throws KeyError: If there is no lexicon reference matching the id.
        """
        del(self.lexicon_refs[reid])

    def remove_license(self, name=None, url=None):
        """Remove all licenses matching both key and value.

        :param str name: Name of the license.
        :param str url: URL of the license.
        """
        for k, v in self.licenses[:]:
            if (name is None or name == k) and (url is None or url == v):
                del(self.licenses[self.licenses.index((k, v))])

    def remove_linguistic_type(self, ling_type):
        """Remove a linguistic type.

        :param str ling_type: Name of the linguistic type.
        :raises KeyError: When the linguistic type doesn't exist.
        """
        del(self.linguistic_types[ling_type])

    def remove_linked_files(self, file_path=None, relpath=None, mimetype=None,
                            time_origin=None, ex_from=None):
        """Remove all linked files that match all the criteria, criterias that
        are ``None`` are ignored.

        :param str file_path: Path of the file.
        :param str relpath: Relative filepath.
        :param str mimetype: Mimetype of the file.
        :param int time_origin: Time origin.
        :param str ex_from: Extracted from.
        """
        for attrib in self.media_descriptors[:]:
            if file_path is not None and attrib['MEDIA_URL'] != file_path:
                continue
            if relpath is not None and attrib['RELATIVE_MEDIA_URL'] != relpath:
                continue
            if mimetype is not None and attrib['MIME_TYPE'] != mimetype:
                continue
            if time_origin is not None and\
                    attrib['TIME_ORIGIN'] != time_origin:
                continue
            if ex_from is not None and attrib['EXTRACTED_FROM'] != ex_from:
                continue
            del(self.media_descriptors[self.media_descriptors.index(attrib)])

    def remove_locale(self, language_code):
        """Remove the locale matching the language code.

        :param str language_code: Language code of the locale.
        :throws KeyError: If there is no locale matching the language code.
        """
        del(self.locales[language_code])

    def remove_property(self, key=None, value=None):
        """Remove all properties matching both key and value.

        :param str key: Key of the property.
        :param str value: Value of the property.
        """
        for k, v in self.properties[:]:
            if (key is None or key == k) and (value is None or value == v):
                del(self.properties[self.properties.index((k, v))])

    def remove_ref_annotation(self, id_tier, time):
        """Remove a reference annotation.

        :param str id_tier: Name of tier.
        :param int time: Time of the referenced annotation
        :raises KeyError: If the tier is non existent.
        :returns: Number of removed annotations.
        """
        removed = 0
        bucket = []
        for aid, (ref, value, _, _) in self.tiers[id_tier][1].items():
            begin, end, rvalue, _ = self.tiers[self.annotations[ref]][0][ref]
            begin = self.timeslots[begin]
            end = self.timeslots[end]
            if begin <= time and end >= time:
                removed += 1
                bucket.append(aid)
        for aid in bucket:
            del(self.tiers[id_tier][1][aid])
        return removed

    def remove_secondary_linked_files(self, file_path=None, relpath=None,
                                      mimetype=None, time_origin=None,
                                      assoc_with=None):
        """Remove all secondary linked files that match all the criteria,
        criterias that are ``None`` are ignored.

        :param str file_path: Path of the file.
        :param str relpath: Relative filepath.
        :param str mimetype: Mimetype of the file.
        :param int time_origin: Time origin.
        :param str ex_from: Extracted from.
        """
        for attrib in self.linked_file_descriptors[:]:
            if file_path is not None and attrib['LINK_URL'] != file_path:
                continue
            if relpath is not None and attrib['RELATIVE_LINK_URL'] != relpath:
                continue
            if mimetype is not None and attrib['MIME_TYPE'] != mimetype:
                continue
            if time_origin is not None and\
                    attrib['TIME_ORIGIN'] != time_origin:
                continue
            if assoc_with is not None and\
                    attrib['ASSOCIATED_WITH'] != assoc_with:
                continue
            del(self.linked_file_descriptors[
                self.linked_file_descriptors.index(attrib)])

    def remove_tier(self, id_tier, clean=True):
        """Remove a tier.

        :param str id_tier: Name of the tier.
        :param bool clean: Flag to also clean the timeslots.
        :raises KeyError: If tier is non existent.
        """
        del(self.tiers[id_tier])
        if clean:
            self.clean_time_slots()

    def remove_tiers(self, tiers):
        """Remove multiple tiers, note that this is a lot faster then removing
        them individually because of the delayed cleaning of timeslots.

        :param list tiers: Names of the tier to remove.
        :raises KeyError: If a tier is non existent.
        """
        for a in tiers:
            self.remove_tier(a, clean=False)
        self.clean_time_slots()

    def rename_tier(self, id_from, id_to):
        """Rename a tier. Note that this renames also the child tiers that have
        the tier as a parent.

        :param str id_from: Original name of the tier.
        :param str id_to: Target name of the tier.
        :throws KeyError: If the tier doesnt' exist.
        """
        childs = self.get_child_tiers_for(id_from)
        self.tiers[id_to] = self.tiers.pop(id_from)
        self.tiers[id_to][2]['TIER_ID'] = id_to
        for child in childs:
            self.tiers[child][2]['PARENT_REF'] = id_to

    def shift_annotations(self, time):
        """Shift all annotations in time. Annotations that are in the beginning
        and a left shift is applied can be squashed or discarded.

        :param int time: Time shift width, negative numbers make a left shift.
        :returns: Tuple of a list of squashed annotations and a list of removed
                  annotations in the format: ``(tiername, start, end, value)``.
        """
        total_re = []
        total_sq = []
        for name, tier in self.tiers.items():
            squashed = []
            for aid, (begin, end, value, _) in tier[0].items():
                if self.timeslots[end]+time <= 0:
                    squashed.append((name, aid))
                elif self.timeslots[begin]+time < 0:
                    total_sq.append((name, self.timeslots[begin],
                                     self.timeslots[end], value))
                    self.timeslots[begin] = 0
                else:
                    self.timeslots[begin] += time
                    self.timeslots[end] += time
            for name, aid in squashed:
                start, end, value, _ = self.tiers[name][0][aid]
                del(self.tiers[name][0][aid])
                del(self.annotations[aid])
                total_re.append(
                    (name, self.timeslots[start], self.timeslots[end], value))
        return total_sq, total_re

    def to_file(self, file_path, pretty=True):
        """Write the object to a file, if the file already exists a backup will
        be created with the ``.bak`` suffix.

        :param str file_path: Filepath to write to.
        :param bool pretty: Flag for pretty XML printing (Only unset this if
            you are afraid of wasting bytes because it won't print unneccesary
            whitespace).
        """
        to_eaf(file_path, self, pretty)

    def to_textgrid(self, filtin=[], filtex=[], regex=False):
        """Convert the object to a :class:`pympi.Praat.TextGrid` object.

        :param list filtin: Include only tiers in this list, if empty
            all tiers are included.
        :param list filtex: Exclude all tiers in this list.
        :param bool regex: If this flag is set the filters are seen as regexes.
        :returns: :class:`pympi.Praat.TextGrid` representation.
        :raises ImportError: If the pympi.Praat module can't be loaded.
        """
        from pympi.Praat import TextGrid
        _, end = self.get_full_time_interval()
        tgout = TextGrid(xmax=end/1000.0)
        func = (lambda x, y: re.match(x, y)) if regex else lambda x, y: x == y
        for tier in self.tiers:
            if (filtin and not any(func(f, tier) for f in filtin)) or\
                    (filtex and any(func(f, tier) for f in filtex)):
                continue
            ctier = tgout.add_tier(tier)
            for intv in self.get_annotation_data_for_tier(tier):
                try:
                    ctier.add_interval(intv[0]/1000.0, intv[1]/1000.0, intv[2])
                except:
                    pass
        return tgout


def eaf_from_chat(file_path, codec=None, extension='wav'):
    """Reads a .cha file and converts it to an elan object. The functions tries
    to mimic the CHAT2ELAN program that comes with the CLAN package as close as
    possible. This function however converts to the latest ELAN file format
    since the library is designed for it. All CHAT headers will be added as
    Properties in the object and the headers that have a similar field in an
    Eaf file will be added there too. The file description of chat files can be
    found `here <https://talkbank.org/manuals/CHAT.pdf>`_.

    :param str file_path: The file path of the .cha file.
    :param str codec: The codec, if the @UTF8 header is present it will choose
        utf-8, default is ascii. Older CHAT files don't have their encoding
        embedded in a header so you will probably need to choose some obscure
        ISO charset then.
    :param str extension: The extension of the media file.
    :throws StopIteration: If the file doesn't contain a @End header, thus
        inferring the file is broken.
    """
    eafob = Eaf()
    eafob.add_linguistic_type('parent')
    eafob.add_linguistic_type(
        'child', constraints='Symbolic_Association', timealignable=False)
    participantsdb = {}
    last_annotation = None
    # attempt to resolve the file codec
    if codec is None:
        codec = 'latin-1'
        with open(file_path, 'r', encoding=codec) as chatin:
            if '@UTF8' == chatin.readline().strip():
                codec = 'utf8'
    # Read the whole file into memory. Sometimes lines are continued into the
    # next line which begins with whitespace. In that case, we attempt to concat
    # the continued line with the previous.
    lines = []
    line_prefixes = ('@', '%', '*')
    with open(file_path, 'r', encoding=codec) as chatin:
        for line in chatin:
            line = line.strip()
            if line.startswith(line_prefixes):
                lines.append(line)
            elif lines:
                lines[-1] = " ".join((lines[-1], line.strip()))
            else:
                lines.append(line)
    end_flag = False
    for line in lines:
        if line == '@UTF8':  # Codec marker
            continue
        elif line == '@Begin':
            continue
        elif line == '@New Episode':
            continue
        elif line == '@End':  # End of file marker
            end_flag = True
            continue
        elif line.startswith('@'):  # Header marker
            key, value = line.split(':\t')
            eafob.add_property('{}:\t'.format(key), value)
            if key == '@Languages':
                for language in value.split(','):
                    eafob.add_language(language)
            elif key == '@Participants':
                for participant in value.split(','):
                    splits = participant.strip().split(' ')
                    splits = [part.replace('_', ' ') for part in splits]
                    if len(splits) == 2:
                        participantsdb[splits[0]] = (None, splits[1])
                    elif len(splits) == 3:
                        participantsdb[splits[0]] = (splits[1], splits[2])
            elif key == '@ID':
                ids = [part.replace('_', '') for part in value.split('|')]
                eafob.add_tier(ids[2], part=participantsdb[ids[2]][0],
                               language=ids[0])
            elif key == '@Media':
                media = value.split(',')
                eafob.add_linked_file(
                    'file://{}.{}'.format(media[0], extension))
            elif key == '@Transcriber:':
                for tier in eafob.get_tier_names():
                    eafob.tiers[tier][2]['ANNOTATOR'] = value
        elif line.startswith('*'):  # Main tier marker
            for participant in participantsdb.keys():
                if line.startswith('*{}:'.format(participant)):
                    splits = ''.join(line.split(':')[1:]).strip()
                    # Check if the main tier contains timestamps. If it does not
                    # fallback to the previous annotation or insert a dummy time
                    if len(splits.split('\x15')) == 3:
                        utt, time, _ = splits.split('\x15')
                        time = [int(part) for part in time.split('_')]
                    else:
                        utt = splits
                        if last_annotation is not None:
                            time = last_annotation[1], last_annotation[2]
                        else:
                            time = [0, 1] # fallback annotation
                    last_annotation = (participant, time[0], time[1], utt)
                    eafob.add_annotation(*last_annotation)
        elif line.startswith('%'):  # Dependant tier marker
            splits = line.split(':')
            name = '{}_{}'.format(last_annotation[0], splits[0][1:])
            if name not in eafob.get_tier_names():
                eafob.add_tier(name, 'child', last_annotation[0])
            eafob.add_ref_annotation(
                name, last_annotation[0], sum(last_annotation[1:3])/2,
                ''.join(splits[1:]).strip())
        else:
            warnings.warn('Unable to parse line of chat file: {}'.format(line))
    if not end_flag:
        raise StopIteration # backward compatibility
    return eafob


def parse_eaf(file_path, eaf_obj, suppress_version_warning=False):
    """Parse an EAF file

    :param str file_path: Path to read from, - for stdin.
    :param pympi.Elan.Eaf eaf_obj: Existing EAF object to put the data in.
    :returns: EAF object.
    """
    if file_path == '-':
        file_path = sys.stdin
    # Annotation document
    try:
        # py3.5 compat: etree.parse does not support pathlib.Path objects in py3.5.
        tree_root = etree.parse(str(file_path)).getroot()
    except etree.ParseError:
        raise Exception('Unable to parse eaf, can you open it in ELAN?')

    if not suppress_version_warning and \
            tree_root.attrib['VERSION'] not in ['3.0', '2.8', '2.7']:
        warnings.warn('Parsing unknown version of ELAN spec... '
                      'This could result in errors...')
    eaf_obj.adocument.update(tree_root.attrib)
    del(eaf_obj.adocument['{http://www.w3.org/2001/XMLSchema-instance}noNamesp'
                          'aceSchemaLocation'])
    tier_number = 0
    for elem in tree_root:
        # Licence
        if elem.tag == 'LICENSE':
            eaf_obj.licenses.append((elem.text, elem.attrib['LICENSE_URL']))
        # Header
        if elem.tag == 'HEADER':
            eaf_obj.header.update(elem.attrib)
            for elem1 in elem:
                if elem1.tag == 'MEDIA_DESCRIPTOR':
                    eaf_obj.media_descriptors.append(elem1.attrib)
                elif elem1.tag == 'LINKED_FILE_DESCRIPTOR':
                    eaf_obj.linked_file_descriptors.append(elem1.attrib)
                elif elem1.tag == 'PROPERTY':
                    eaf_obj.properties.append(
                        (elem1.attrib['NAME'], elem1.text))
        # Time order
        elif elem.tag == 'TIME_ORDER':
            for elem1 in elem:
                tsid = elem1.attrib['TIME_SLOT_ID']
                tsnum = int(''.join(filter(str.isdigit, tsid)))
                if tsnum and tsnum > eaf_obj.maxts:
                    eaf_obj.maxts = tsnum
                ts = elem1.attrib.get('TIME_VALUE', None)
                eaf_obj.timeslots[tsid] = ts if ts is None else int(ts)
        # Tier
        elif elem.tag == 'TIER':
            tier_id = elem.attrib['TIER_ID']
            align = {}
            ref = {}
            for elem1 in elem:
                if elem1.tag == 'ANNOTATION':
                    for elem2 in elem1:
                        if elem2.tag == 'ALIGNABLE_ANNOTATION':
                            annot_id = elem2.attrib['ANNOTATION_ID']
                            annot_num = int(''.join(
                                filter(str.isdigit, annot_id)))
                            if annot_num and annot_num > eaf_obj.maxaid:
                                eaf_obj.maxaid = annot_num
                            annot_start = elem2.attrib['TIME_SLOT_REF1']
                            annot_end = elem2.attrib['TIME_SLOT_REF2']
                            svg_ref = elem2.attrib.get('SVG_REF', None)
                            align[annot_id] = (annot_start, annot_end,
                                               '' if not list(elem2)[0].text
                                               else list(elem2)[0].text,
                                               svg_ref)
                            eaf_obj.annotations[annot_id] = tier_id
                        elif elem2.tag == 'REF_ANNOTATION':
                            annot_ref = elem2.attrib['ANNOTATION_REF']
                            previous = elem2.attrib.get('PREVIOUS_ANNOTATION',
                                                        None)
                            annot_id = elem2.attrib['ANNOTATION_ID']
                            annot_num = int(''.join(
                                filter(str.isdigit, annot_id)))
                            if annot_num and annot_num > eaf_obj.maxaid:
                                eaf_obj.maxaid = annot_num
                            svg_ref = elem2.attrib.get('SVG_REF', None)
                            ref[annot_id] = (annot_ref,
                                             '' if not list(elem2)[0].text else
                                             list(elem2)[0].text,
                                             previous, svg_ref)
                            eaf_obj.annotations[annot_id] = tier_id
            eaf_obj.tiers[tier_id] = (align, ref, elem.attrib, tier_number)
            tier_number += 1
        # Linguistic type
        elif elem.tag == 'LINGUISTIC_TYPE':
            eaf_obj.linguistic_types[elem.attrib['LINGUISTIC_TYPE_ID']] =\
                elem.attrib
        # Locale
        elif elem.tag == 'LOCALE':
            eaf_obj.locales[elem.attrib['LANGUAGE_CODE']] =\
                (elem.attrib.get('COUNTRY_CODE', None),
                 elem.attrib.get('VARIANT', None))
        # Language
        elif elem.tag == 'LANGUAGE':
            eaf_obj.languages[elem.attrib['LANG_ID']] =\
                (elem.attrib.get('LANG_DEF', None),
                 elem.attrib.get('LANG_LABEL', None))
        # Constraint
        elif elem.tag == 'CONSTRAINT':
            eaf_obj.constraints[elem.attrib['STEREOTYPE']] =\
                elem.attrib['DESCRIPTION']
        # Controlled vocabulary
        elif elem.tag == 'CONTROLLED_VOCABULARY':
            cv_id = elem.attrib['CV_ID']
            ext_ref = elem.attrib.get('EXT_REF', None)
            descriptions = []

            if 'DESCRIPTION' in elem.attrib:
                eaf_obj.languages['und'] = (
                    'http://cdb.iso.org/lg/CDB-00130975-001',
                    'undetermined (und)')
                descriptions.append(('und', elem.attrib['DESCRIPTION']))
            entries = {}
            for elem1 in elem:
                if elem1.tag == 'DESCRIPTION':
                    descriptions.append((elem1.attrib['LANG_REF'], elem1.text))
                elif elem1.tag == 'CV_ENTRY':
                    cve_value = (elem1.text, 'und',
                                 elem1.get('DESCRIPTION', None))
                    entries['cveid{}'.format(len(entries))] = \
                        ([cve_value], elem1.attrib.get('EXT_REF', None))
                elif elem1.tag == 'CV_ENTRY_ML':
                    cem_ext_ref = elem1.attrib.get('EXT_REF', None)
                    cve_id = elem1.attrib['CVE_ID']
                    cve_values = []
                    for elem2 in elem1:
                        if elem2.tag == 'CVE_VALUE':
                            cve_values.append((elem2.text,
                                               elem2.attrib['LANG_REF'],
                                               elem2.get('DESCRIPTION', None)))
                    entries[cve_id] = (cve_values, cem_ext_ref)
            eaf_obj.controlled_vocabularies[cv_id] =\
                (descriptions, entries, ext_ref)
        # Lexicon ref
        elif elem.tag == 'LEXICON_REF':
            eaf_obj.lexicon_refs[elem.attrib['LEX_REF_ID']] = elem.attrib
        # External ref
        elif elem.tag == 'EXTERNAL_REF':
            eaf_obj.external_refs[elem.attrib['EXT_REF_ID']] = (
                elem.attrib['TYPE'], elem.attrib['VALUE'])


def indent(el, level=0):
    """Function to pretty print the xml, meaning adding tabs and newlines.

    :param ElementTree.Element el: Current element.
    :param int level: Current level.
    """
    i = '\n' + level * '\t'
    if len(el):
        if not el.text or not el.text.strip():
            el.text = i+'\t'
        if not el.tail or not el.tail.strip():
            el.tail = i
        for elem in el:
            indent(elem, level+1)
        if not el.tail or not el.tail.strip():
            el.tail = i
    else:
        if level and (not el.tail or not el.tail.strip()):
            el.tail = i


def to_adocument(eaf_obj, pretty=True):
    """Create an etree Element from an Eaf object

    :param pympi.Elan.Eaf eaf_obj: Object to write.
    :param bool pretty: Flag to set pretty printing.
    :return: etree.Element: the etree Element containing the Annotation Document
    """
    def rm_none(x):
        return {k: v if isinstance(v, str) else str(v) for k, v in x.items()
                if v is not None}
    # Annotation Document
    ADOCUMENT = etree.Element('ANNOTATION_DOCUMENT', eaf_obj.adocument)
    # Licence
    for m in eaf_obj.licenses:
        n = etree.SubElement(ADOCUMENT, 'LICENSE', {'LICENSE_URL': m[1]})
        n.text = m[0]
    # Header
    HEADER = etree.SubElement(ADOCUMENT, 'HEADER', eaf_obj.header)
    # Media descriptiors
    for m in eaf_obj.media_descriptors:
        etree.SubElement(HEADER, 'MEDIA_DESCRIPTOR', rm_none(m))
    # Linked file descriptors
    for m in eaf_obj.linked_file_descriptors:
        etree.SubElement(HEADER, 'LINKED_FILE_DESCRIPTOR', rm_none(m))
    # Properties
    for k, v in eaf_obj.properties:
        etree.SubElement(HEADER, 'PROPERTY', {'NAME': k}).text = str(v)
    # Time order
    TIME_ORDER = etree.SubElement(ADOCUMENT, 'TIME_ORDER')
    for t in sorted(
        eaf_obj.timeslots.items(),
        key=lambda x: (int(re.findall(r"ts(\d+)", x[0])[0]), x[0]),
    ):
        etree.SubElement(TIME_ORDER, 'TIME_SLOT', rm_none(
            {'TIME_SLOT_ID': t[0], 'TIME_VALUE': t[1]}))
    # Tiers
    for t in sorted(eaf_obj.tiers.items(), key=lambda x: x[1][3]):
        tier = etree.SubElement(ADOCUMENT, 'TIER', rm_none(t[1][2]))
        for a in t[1][0].items():
            ann = etree.SubElement(tier, 'ANNOTATION')
            alan = etree.SubElement(ann, 'ALIGNABLE_ANNOTATION', rm_none(
                {'ANNOTATION_ID': a[0], 'TIME_SLOT_REF1': a[1][0],
                 'TIME_SLOT_REF2': a[1][1], 'SVG_REF': a[1][3]}))
            etree.SubElement(alan, 'ANNOTATION_VALUE').text = a[1][2]
        for a in t[1][1].items():
            ann = etree.SubElement(tier, 'ANNOTATION')
            rean = etree.SubElement(ann, 'REF_ANNOTATION', rm_none(
                {'ANNOTATION_ID': a[0], 'ANNOTATION_REF': a[1][0],
                 'PREVIOUS_ANNOTATION': a[1][2], 'SVG_REF': a[1][3]}))
            etree.SubElement(rean, 'ANNOTATION_VALUE').text = a[1][1]
    # Linguistic types
    for l in eaf_obj.linguistic_types.values():
        etree.SubElement(ADOCUMENT, 'LINGUISTIC_TYPE', rm_none(l))
    # Locales
    for lc, (cc, vr) in eaf_obj.locales.items():
        etree.SubElement(ADOCUMENT, 'LOCALE', rm_none(
            {'LANGUAGE_CODE': lc, 'COUNTRY_CODE': cc, 'VARIANT': vr}))
    # Languages
    for lid, (ldef, label) in eaf_obj.languages.items():
        etree.SubElement(ADOCUMENT, 'LANGUAGE', rm_none(
            {'LANG_ID': lid, 'LANG_DEF': ldef, 'LANG_LABEL': label}))
    # Constraints
    for l in eaf_obj.constraints.items():
        etree.SubElement(ADOCUMENT, 'CONSTRAINT', rm_none(
            {'STEREOTYPE': l[0], 'DESCRIPTION': l[1]}))
    # Controlled vocabularies
    for cvid, (descriptions, cv_entries, ext_ref) in\
            eaf_obj.controlled_vocabularies.items():
        cv = etree.SubElement(ADOCUMENT, 'CONTROLLED_VOCABULARY',
                              rm_none({'CV_ID': cvid, 'EXT_REF': ext_ref}))
        for lang_ref, description in descriptions:
            des = etree.SubElement(cv, 'DESCRIPTION', {'LANG_REF': lang_ref})
            if description:
                des.text = description
        for cveid, (values, ext_ref) in cv_entries.items():
            cem = etree.SubElement(cv, 'CV_ENTRY_ML', rm_none({
                'CVE_ID': cveid, 'EXT_REF': ext_ref}))
            for value, lang_ref, description in values:
                val = etree.SubElement(cem, 'CVE_VALUE', rm_none({
                    'LANG_REF': lang_ref, 'DESCRIPTION': description}))
                val.text = value
    # Lexicon refs
    for l in eaf_obj.lexicon_refs.values():
        etree.SubElement(ADOCUMENT, 'LEXICON_REF', rm_none(l))
    # Exteral refs
    for eid, (etype, value) in eaf_obj.external_refs.items():
        etree.SubElement(ADOCUMENT, 'EXTERNAL_REF', rm_none(
            {'EXT_REF_ID': eid, 'TYPE': etype, 'VALUE': value}))

    if pretty:
        indent(ADOCUMENT)

    return ADOCUMENT

def to_eaf(file_path, eaf_obj, pretty=True):
    """Write an Eaf object to file.

    :param str file_path: Filepath to write to, - for stdout.
    :param pympi.Elan.Eaf eaf_obj: Object to write.
    :param bool pretty: Flag to set pretty printing.
    """
    ADOCUMENT = to_adocument(eaf_obj, pretty)
    if file_path == '-':
        try:
            sys.stdout.write(etree.tostring(ADOCUMENT, encoding='unicode'))
        except LookupError:
            sys.stdout.write(etree.tostring(ADOCUMENT, encoding='UTF-8'))
    else:
        file_path = pathlib.Path(file_path)
        if file_path.exists():
            file_path.rename(file_path.with_suffix('.bak'))
        etree.ElementTree(ADOCUMENT).write(
            str(file_path), xml_declaration=True, encoding='UTF-8')


def to_string(eaf_obj, pretty=True, encoding='unicode'):
    """Serialize a Eaf object to a string

    :param pympi.Elan.Eaf eaf_obj: Object to write.
    :param bool pretty: Flag to set pretty printing.
    :param str encoding: the character encoding of the string
    :return: str: the serialized Annotation Document
    """
    ADOCUMENT = to_adocument(eaf_obj, pretty)
    return etree.tostring(ADOCUMENT, encoding=encoding)
