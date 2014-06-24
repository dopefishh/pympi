# -*- coding: utf-8 -*-

from xml.etree import ElementTree
import sys


def parseEaf(filePath, eafObj):
    """
    Parse an elan file

    filePath -- Filepath to parse from - for stdin
    eafObj   -- Object to put the data in"""
    if filePath == "-":
        filePath = sys.stdin
    treeRoot = ElementTree.parse(filePath).getroot()
    eafObj.annotationDocument.update(treeRoot.attrib)
    del(eafObj.annotationDocument[
        '{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation'
        ])
    tierNumber = 0
    for elem in treeRoot:
        if elem.tag == 'HEADER':
            eafObj.header.update(elem.attrib)
            for elem1 in elem:
                if elem1.tag == 'MEDIA_DESCRIPTOR':
                    eafObj.media_descriptors.append(elem1.attrib)
                elif elem1.tag == 'LINKED_FILE_DESCRIPTOR':
                    eafObj.linked_file_descriptors.append(elem1.attrib)
                elif elem1.tag == 'PROPERTY':
                    eafObj.properties.append((elem1.text, elem1.attrib))
        elif elem.tag == 'TIME_ORDER':
            for elem1 in elem:
                if int(elem1.attrib['TIME_SLOT_ID'][2:]) > eafObj.new_time:
                    eafObj.new_time = int(elem1.attrib['TIME_SLOT_ID'][2:])
                eafObj.timeslots[elem1.attrib['TIME_SLOT_ID']] =\
                    int(elem1.attrib['TIME_VALUE'])
        elif elem.tag == 'TIER':
            tierId = elem.attrib['TIER_ID']
            align = {}
            ref = {}
            for elem1 in elem:
                if elem1.tag == 'ANNOTATION':
                    for elem2 in elem1:
                        if elem2.tag == 'ALIGNABLE_ANNOTATION':
                            annotID = elem2.attrib['ANNOTATION_ID']
                            if int(annotID[1:]) > eafObj.new_ann:
                                eafObj.new_ann = int(annotID[1:])
                            annotStart = elem2.attrib['TIME_SLOT_REF1']
                            annotEnd = elem2.attrib['TIME_SLOT_REF2']
                            svg_ref = None if 'SVG_REF' not in elem2.attrib\
                                else elem2.attrib['SVG_REF']
                            align[annotID] = (
                                annotStart, annotEnd, ''
                                if list(elem2)[0].text is None
                                else list(elem2)[0].text, svg_ref)
                        elif elem2.tag == 'REF_ANNOTATION':
                            annotRef = elem2.attrib['ANNOTATION_REF']
                            previous = None\
                                if 'PREVIOUS_ANNOTATION' not in elem2.attrib\
                                else elem2.attrib['PREVIOUS_ANNOTATION']
                            annotId = elem2.attrib['ANNOTATION_ID']
                            if int(annotID[1:]) > eafObj.new_ann:
                                eafObj.new_ann = int(annotID[1:])
                            svg_ref = None\
                                if 'SVG_REF' not in elem2.attrib\
                                else elem2.attrib['SVG_REF']
                            ref[annotId] = (
                                annotRef,
                                '' if list(elem2)[0].text is None else
                                list(elem2)[0].text,
                                previous, svg_ref)
            eafObj.tiers[tierId] = (align, ref, elem.attrib, tierNumber)
            tierNumber += 1
        elif elem.tag == 'LINGUISTIC_TYPE':
            eafObj.linguistic_types[elem.attrib['LINGUISTIC_TYPE_ID']] =\
                elem.attrib
        elif elem.tag == 'LOCALE':
            eafObj.locales.append(elem.attrib)
        elif elem.tag == 'CONSTRAINT':
            eafObj.constraints[elem.attrib['STEREOTYPE']] =\
                elem.attrib['DESCRIPTION']
        elif elem.tag == 'CONTROLLED_VOCABULARY':
            vcId = elem.attrib['CV_ID']
            descr = elem.attrib['DESCRIPTION']
            ext_ref = None if 'EXT_REF' not in elem.attrib else\
                elem.attrib['EXT_REF']
            entries = {}
            for elem1 in elem:
                if elem1.tag == 'CV_ENTRY':
                    entries[elem1.attrib['DESCRIPTION']] =\
                        (elem1.attrib, elem1.text)
            eafObj.controlled_vocabularies[vcId] = (descr, entries, ext_ref)
        elif elem.tag == 'LEXICON_REF':
            eafObj.lexicon_refs.append(elem.attrib)
        elif elem.tag == 'EXTERNAL_REF':
            eafObj.external_refs.append((elem.attrib['EXT_REF_ID'],
                                         elem.attrib['TYPE'],
                                         elem.attrib['VALUE']))


def indent(el, level=0):
    """
    Pretty prints the xml

    level -- Level of indenting, only used internally"""
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


def toEaf(filePath, eafObj, pretty=True):
    """
    Write an elan object to a file

    filePath -- Filpath to write to - for stdout
    eafObj   -- The elan object
    pretty   -- Use pretty indentation in xml"""
    rmNone = lambda x:\
        dict((k, unicode(v)) for k, v in x.iteritems() if v is not None)
    ANNOTATION_DOCUMENT = ElementTree.Element('ANNOTATION_DOCUMENT',
                                              eafObj.annotationDocument)

    HEADER = ElementTree.SubElement(ANNOTATION_DOCUMENT, 'HEADER',
                                    eafObj.header)
    for m in eafObj.media_descriptors:
        ElementTree.SubElement(HEADER, 'MEDIA_DESCRIPTOR', rmNone(m))
    for m in eafObj.linked_file_descriptors:
        ElementTree.SubElement(HEADER, 'LINKED_FILE_DESCRIPTOR', rmNone(m))
    for m in eafObj.properties:
        ElementTree.SubElement(HEADER, 'PROPERTY', rmNone(m[1])).text =\
            unicode(m[0])

    TIME_ORDER = ElementTree.SubElement(ANNOTATION_DOCUMENT, 'TIME_ORDER')
    for t in sorted(eafObj.timeslots.iteritems(), key=lambda x: int(x[0][2:])):
        ElementTree.SubElement(
            TIME_ORDER, 'TIME_SLOT',
            rmNone({'TIME_SLOT_ID': t[0], 'TIME_VALUE': t[1]}))

    for t in eafObj.tiers.iteritems():
        tier = ElementTree.SubElement(ANNOTATION_DOCUMENT, 'TIER',
                                      rmNone(t[1][2]))
        for a in t[1][0].iteritems():
            ann = ElementTree.SubElement(tier, 'ANNOTATION')
            alan = ElementTree.SubElement(ann,
                                          'ALIGNABLE_ANNOTATION',
                                          rmNone({'ANNOTATION_ID': a[0],
                                                  'TIME_SLOT_REF1': a[1][0],
                                                  'TIME_SLOT_REF2': a[1][1],
                                                  'SVG_REF': a[1][3]}))
            ElementTree.SubElement(alan, 'ANNOTATION_VALUE').text =\
                unicode(a[1][2])
        for a in t[1][1].iteritems():
            ann = ElementTree.SubElement(tier, 'ANNOTATION')
            rean = ElementTree.SubElement(ann,
                                          'REF_ANNOTATION',
                                          rmNone({
                                              'ANNOTATION_ID': a[0],
                                              'ANNOTATION_REF': a[1][0],
                                              'PREVIOUS_ANNOTATION': a[1][2],
                                              'SVG_REF': a[1][3]}))
            ElementTree.SubElement(rean, 'ANNOTATION_VALUE').text =\
                unicode(a[1][1])

    for l in eafObj.linguistic_types.itervalues():
        ElementTree.SubElement(ANNOTATION_DOCUMENT, 'LINGUISTIC_TYPE',
                               rmNone(l))

    for l in eafObj.locales:
        ElementTree.SubElement(ANNOTATION_DOCUMENT, 'LOCALE', l)

    for l in eafObj.constraints.iteritems():
        ElementTree.SubElement(ANNOTATION_DOCUMENT, 'CONSTRAINT',
                               rmNone({'STEREOTYPE': l[0],
                                       'DESCRIPTION': l[1]}))

    for l in eafObj.controlled_vocabularies.iteritems():
        cv = ElementTree.SubElement(ANNOTATION_DOCUMENT,
                                    'CONTROLLED_VOCABULARY',
                                    rmNone({'CV_ID': l[0],
                                            'DESCRIPTION': l[1][0],
                                            'EXT_REF': l[1][2]}))
        for c in l[1][1].itervalues():
            ElementTree.SubElement(cv, 'CV_ENTRY', rmNone(c[0])).text =\
                unicode(c[1])

    for r in eafObj.external_refs:
        ElementTree.SubElement(ANNOTATION_DOCUMENT, 'EXTERNAL_REF',
                               rmNone({'EXT_REF_ID': r[0],
                                       'TYPE': r[1],
                                       'VALUE': r[2]}))

    for l in eafObj.lexicon_refs:
        ElementTree.SubElement(ANNOTATION_DOCUMENT, 'LEXICON_REF', l)

    if pretty:
        indent(ANNOTATION_DOCUMENT)
    if filePath == "-":
        filePath = sys.stdout
    ElementTree.ElementTree(ANNOTATION_DOCUMENT).write(filePath,
                                                       xml_declaration=True,
                                                       encoding='UTF-8')
