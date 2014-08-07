# -*- coding: utf-8 -*-

from xml.etree import ElementTree as etree
import sys
import os


def parse_eaf(file_path, eaf_obj):
    """Parse an EAF file

    :param str file_path: Path to read from, - for stdin.
    :param pympi.Elan.Eaf eaf_obj: Existing EAF object to put the data in.
    :returns: EAF object.
    """
    if file_path == "-":
        file_path = sys.stdin
    # Annotation document
    tree_root = etree.parse(file_path).getroot()
    eaf_obj.annotation_document.update(tree_root.attrib)
    del(eaf_obj.annotation_document[
        '{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation'
        ])
    tier_number = 0
    for elem in tree_root:
        # Licence
        if elem.tag == 'LICENCE':
            eaf_obj.licences[elem.text] = elem.attrib
        # Header
        if elem.tag == 'HEADER':
            eaf_obj.header.update(elem.attrib)
            for elem1 in elem:
                if elem1.tag == 'MEDIA_DESCRIPTOR':
                    eaf_obj.media_descriptors.append(elem1.attrib)
                elif elem1.tag == 'LINKED_FILE_DESCRIPTOR':
                    eaf_obj.linked_file_descriptors.append(elem1.attrib)
                elif elem1.tag == 'PROPERTY':
                    eaf_obj.properties.append((elem1.text, elem1.attrib))
        # Time order
        elif elem.tag == 'TIME_ORDER':
            for elem1 in elem:
                if int(elem1.attrib['TIME_SLOT_ID'][2:]) > eaf_obj.new_time:
                    eaf_obj.new_time = int(elem1.attrib['TIME_SLOT_ID'][2:])
                eaf_obj.timeslots[elem1.attrib['TIME_SLOT_ID']] =\
                    int(elem1.attrib['TIME_VALUE'])
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
                            if int(annot_id[1:]) > eaf_obj.new_ann:
                                eaf_obj.new_ann = int(annot_id[1:])
                            annot_start = elem2.attrib['TIME_SLOT_REF1']
                            annot_end = elem2.attrib['TIME_SLOT_REF2']
                            svg_ref = elem2.attrib.get('SVG_REF', None)
                            align[annot_id] = (annot_start, annot_end,
                                               '' if not list(elem2)[0].text
                                               else list(elem2)[0].text,
                                               svg_ref)
                        elif elem2.tag == 'REF_ANNOTATION':
                            annotRef = elem2.attrib['ANNOTATION_REF']
                            previous = elem2.attrib.get('PREVIOUS_ANNOTATION',
                                                        None)
                            annotId = elem2.attrib['ANNOTATION_ID']
                            if int(annot_id[1:]) > eaf_obj.new_ann:
                                eaf_obj.new_ann = int(annot_id[1:])
                            svg_ref = elem2.attrib.get('SVG_REF', None)
                            ref[annotId] = (annotRef,
                                            '' if not list(elem2)[0].text else
                                            list(elem2)[0].text,
                                            previous, svg_ref)
            eaf_obj.tiers[tier_id] = (align, ref, elem.attrib, tier_number)
            tier_number += 1
        # Linguistic type
        elif elem.tag == 'LINGUISTIC_TYPE':
            eaf_obj.linguistic_types[elem.attrib['LINGUISTIC_TYPE_ID']] =\
                elem.attrib
        # Locale
        elif elem.tag == 'LOCALE':
            eaf_obj.locales.append(elem.attrib)
        # Constraint
        elif elem.tag == 'CONSTRAINT':
            eaf_obj.constraints[elem.attrib['STEREOTYPE']] =\
                elem.attrib['DESCRIPTION']
        # Controlled vocabulary
        elif elem.tag == 'CONTROLLED_VOCABULARY':
            cv_id = elem.attrib['CV_ID']
            ext_ref = elem.attrib.get('EXT_REF', None)
            descriptions = []
            entries = {}
            for elem1 in elem:
                if elem1.tag == 'DESCRIPTION':
                    descriptions.append((elem1.attrib['LANG_REF'], elem1.text))
                elif elem1.tag == 'CV_ENTRY_ML':
                    cem_ext_ref = elem1.attrib.get('EXT_REF', None)
                    cve_id = elem1.attrib['CVE_ID']
                    cve_values = []
                    for elem2 in elem1:
                        if elem2.tag == 'CVE_VALUE':
                            cve_values.append((elem2.attrib['LANG_REF'],
                                               elem2.get('DESCRIPTION', None),
                                               elem2.text))
                    entries[cve_id] = (cve_values, cem_ext_ref)
            eaf_obj.controlled_vocabularies[cv_id] =\
                (descriptions, entries, ext_ref)
        # Lexicon ref
        elif elem.tag == 'LEXICON_REF':
            eaf_obj.lexicon_refs.append(elem.attrib)
        # External ref
        elif elem.tag == 'EXTERNAL_REF':
            eaf_obj.external_refs.append((elem.attrib['EXT_REF_ID'],
                                          elem.attrib['TYPE'],
                                          elem.attrib['VALUE']))


def indent(el, level=0):
    """Function to pretty print the xml, meaning adding tabs and newlines.

    :param ElementTree.Element el: Current element.
    :param int level: Current level.
    """
    i = '\n' + level*'\t'
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


def to_eaf(file_path, eaf_obj, pretty=True):
    """Write an Eaf object to file.

    :param str file_path: Filepath to write to, - for stdout.
    :param pympi.Elan.Eaf eaf_obj: Object to write.
    :param bool pretty: Flag to set pretty printing.
    """
    rm_none = lambda x:\
        dict((k, unicode(v)) for k, v in x.iteritems() if v is not None)
    # Annotation Document
    ANNOTATION_DOCUMENT = etree.Element('ANNOTATION_DOCUMENT',
                                        eaf_obj.annotation_document)

    # Licence
    for m in eaf_obj.licences.iteritems():
        n = etree.SubElement(ANNOTATION_DOCUMENT, 'LICENCE', m[1])
        n.text = m[0]
    # Header
    HEADER = etree.SubElement(ANNOTATION_DOCUMENT, 'HEADER', eaf_obj.header)

    # Media descriptiors
    for m in eaf_obj.media_descriptors:
        etree.SubElement(HEADER, 'MEDIA_DESCRIPTOR', rm_none(m))
    # Linked file descriptors
    for m in eaf_obj.linked_file_descriptors:
        etree.SubElement(HEADER, 'LINKED_FILE_DESCRIPTOR', rm_none(m))
    # Properties
    for m in eaf_obj.properties:
        etree.SubElement(HEADER, 'PROPERTY', rm_none(m[1])).text = \
            unicode(m[0])

    # Time order
    TIME_ORDER = etree.SubElement(ANNOTATION_DOCUMENT, 'TIME_ORDER')
    for t in sorted(eaf_obj.timeslots.iteritems(),
                    key=lambda x: int(x[0][2:])):
        etree.SubElement(TIME_ORDER, 'TIME_SLOT', rm_none(
            {'TIME_SLOT_ID': t[0], 'TIME_VALUE': t[1]}))

    # Tiers
    for t in eaf_obj.tiers.iteritems():
        tier = etree.SubElement(ANNOTATION_DOCUMENT, 'TIER', rm_none(t[1][2]))
        for a in t[1][0].iteritems():
            ann = etree.SubElement(tier, 'ANNOTATION')
            alan = etree.SubElement(ann, 'ALIGNABLE_ANNOTATION', rm_none(
                {'ANNOTATION_ID': a[0], 'TIME_SLOT_REF1': a[1][0],
                 'TIME_SLOT_REF2': a[1][1], 'SVG_REF': a[1][3]}))
            etree.SubElement(alan, 'ANNOTATION_VALUE').text =\
                unicode(a[1][2])
        for a in t[1][1].iteritems():
            ann = etree.SubElement(tier, 'ANNOTATION')
            rean = etree.SubElement(ann, 'REF_ANNOTATION', rm_none(
                {'ANNOTATION_ID': a[0], 'ANNOTATION_REF': a[1][0],
                 'PREVIOUS_ANNOTATION': a[1][2], 'SVG_REF': a[1][3]}))
            etree.SubElement(rean, 'ANNOTATION_VALUE').text =\
                unicode(a[1][1])

    # Linguistic types
    for l in eaf_obj.linguistic_types.itervalues():
        etree.SubElement(ANNOTATION_DOCUMENT, 'LINGUISTIC_TYPE', rm_none(l))

    # Locales
    for l in eaf_obj.locales:
        etree.SubElement(ANNOTATION_DOCUMENT, 'LOCALE', l)

    # Constraints
    for l in eaf_obj.constraints.iteritems():
        etree.SubElement(ANNOTATION_DOCUMENT, 'CONSTRAINT', rm_none(
            {'STEREOTYPE': l[0], 'DESCRIPTION': l[1]}))

    # Controlled vocabularies
    for cvid, (descriptions, cv_entries, ext_ref) in\
            eaf_obj.controlled_vocabularies.iteritems():
        cv = etree.SubElement(ANNOTATION_DOCUMENT, 'CONTROLLED_VOCABULARY',
                              rm_none({'CV_ID': cvid, 'EXT_REF': ext_ref}))
        for lang_ref, textvalue in descriptions:
            des = etree.SubElement(cv, 'DESCRIPTION', {'LANG_REF': lang_ref})
            des.text = textvalue
        for cveid, (values, ext_ref) in cv_entries.iteritems():
            cem = etree.SubElement(cv, 'CV_ENTRY_ML', rm_none({
                                   'CVE_ID': cveid, 'EXT_REF': ext_ref}))
            for lang_ref, description, textvalue in values:
                val = etree.SubElement(cem, 'CVE_VALUE', rm_none({
                                       'LANG_REF': lang_ref,
                                       'DESCRIPTION': description}))
                val.text = textvalue

    # Lexicon refs
    for l in eaf_obj.lexicon_refs:
        etree.SubElement(ANNOTATION_DOCUMENT, 'LEXICON_REF', l)

    # Exteral refs
    for r in eaf_obj.external_refs:
        etree.SubElement(ANNOTATION_DOCUMENT, 'EXTERNAL_REF', rm_none(
            {'EXT_REF_ID': r[0], 'TYPE': r[1], 'VALUE': r[2]}))

    if pretty:
        indent(ANNOTATION_DOCUMENT)
    if file_path == "-":
        file_path = sys.stdout
    elif os.access(file_path, os.F_OK):
        os.rename(file_path, '{}.bak'.format(file_path))
    etree.ElementTree(ANNOTATION_DOCUMENT).write(
        file_path, xml_declaration=True, encoding='UTF-8')
