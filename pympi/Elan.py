# -*- coding: utf-8 -*-

import time
import EafIO
import warnings


class Eaf:
    """
    Class to work with elan files
    <br />
    annotationDocument      - Dict of all annotationdocument TAG entries.<br />
    header                  - Dict of the header TAG entries.<br />
    media_descriptors       - List of all linked files: [{attrib}]<br />
    properties              - List of all properties: [(value, {attrib})]<br />
    linked_file_descriptors - List of all secondary linked files: [{attrib}].<br />
    timeslots               - Timeslot data: {TimslotID -> time(ms)}<br />
    tiers                   - Tier data: {TierName -><br />
            (alignedAnnotations, referenceAnnotations, attributes, ordinal)},<br />
                              alignedAnnotations: [{annotationId -><br />
            (beginTs, endTs, value, svg_ref)}]<br />
                              referenceAnnotations: [{annotationId -><br />
            (reference, value, previous, svg_ref)}]<br />
    linguistic_types        - Linguistic type data [{id -> attrib}]<br />
    locales                 - List of locale data: [{attrib}]<br />
    constraints             - Constraint data: {stereotype -> description}<br />
    controlled_vocabularies - Controlled vocabulary data: {id -><br />
            (description, entries, ext_ref)}<br />
                                entry: {description -> (attrib, value)}<br />
    external refs           - External refs [extref]<br />
                                extref: [id, type, value]<br />
    lexicon_refs            - Lexicon refs [{attribs}]<br />
    """

    def __init__(self, filePath=None, author='Elan.py'):
        """
        Constructor, builds an elan object from file or an empty one<br />
<br />
        filepath -- The path to load the file from<br />
        author   -- The author used in the xml tag<br />
        """
        self.naiveGenAnn, self.naiveGenTS = False, False
        now = time.localtime()
        self.annotationDocument = {
            'AUTHOR': author,
            'DATE': time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            'VERSION': '2.7',
            'FORMAT': '2.7',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:noNamespaceSchemaLocation':
                'http://www.mpi.nl/tools/elan/EAFv2.7.xsd'}
        self.controlled_vocabularies = {}
        self.constraints = {}
        self.tiers = {}
        self.linguistic_types = {}
        self.header = {}
        self.timeslots = {}
        self.external_refs = []
        self.lexicon_refs = []
        self.locales = []
        self.media_descriptors = []
        self.properties = []
        self.linked_file_descriptors = []
        self.new_time, self.new_ann = 0, 0

        if filePath is None:
            self.addLinguisticType('default-lt', None)
            self.constraints = {
                'Time_Subdivision':
                    'Time subdivision of parent annotation\'s time interval' +
                    ', no time gaps allowed within this interval',
                'Symbolic_Subdivision':
                    'Symbolic subdivision of a parent annotation. Annotation' +
                    's refering to the same parent are ordered',
                'Symbolic_Association':
                    '1-1 association with a parent annotation',
                'Included_In':
                    'Time alignable annotations within the parent annotation' +
                    '\'s time interval, gaps are allowed'}
            self.properties.append(('0', {'NAME': 'lastUsedAnnotation'}))
            self.addTier('default')
        else:
            EafIO.parseEaf(filePath, self)

    def tofile(self, filePath, pretty=True):
        """
        Exports the eaf object to a file with or without pretty printing<br />
<br />
        filePath -- The output file path - for stdout<br />
        pretty   -- Flag for pretty indented output"""
        EafIO.toEaf(filePath, self)

    def toTextGrid(self, filePath, excludedTiers=[], includedTiers=[]):
        """
        Convert the elan file to praat's TextGrid, returns 0 if succesfull<br />
<br />
        filePath      -- The output file path - for stdout<br />
        excludedTiers -- Tiers to exclude<br />
        includedTiers -- Tiers to include if empty all tiers are included"""
        try:
            from pympi.Praat import TextGrid
        except ImportError:
            warnings.warn(
                'Please install the pympi.Praat module from the py' +
                'mpi module found at https://github.com/dopefishh/pympi')
            return 1
        tgout = TextGrid()
        for tier in [a for a in self.tiers if a not in excludedTiers and
                     (not includedTiers or a in includedTiers)]:
            currentTier = tgout.addTier(tier)
            for interval in self.getAnnotationDataForTier(tier):
                if interval[0] == interval[1]:
                    continue
                currentTier.addInterval(
                    interval[0]/1000.0,
                    interval[1]/1000.0,
                    interval[2])
        tgout.tofile(filePath)
        return 0

    def extract(self, start, end):
        """
        Extracts a timeframe from the eaf file and returns it<br />
<br />
        start -- Starting time<br />
        end   -- Ending time"""
        from copy import deepcopy
        eafOut = deepcopy(self)
        for tier in eafOut.tiers.itervalues():
            rems = []
            for ann in tier[0]:
                if eafOut.timeslots[tier[0][ann][1]] > end or\
                        eafOut.timeslots[tier[0][ann][0]] < start:
                    rems.append(ann)
            for r in rems:
                del tier[0][r]
        return eafOut

    def getLinkedFiles(self):
        """Gives a list of all media files"""
        return self.media_descriptors

    def addLinkedFile(self, filePath, relpath=None, mimetype=None,
                      time_origin=None, exfrom=None):
        """Adds the linked file to the object
<br />
        filePath    -- Path of the file to link<br />
        relpath     -- Relative filepath<br />
        mimetype    -- MIME-type, if none it tries to guess it<br />
        time_origin -- Time origin for media files<br />
        exfrom      -- Extracted from"""
        if mimetype is None:
            mimes = {'wav': 'audio/x-wav', 'mpg': 'video/mpeg',
                     'mpeg': 'video/mpg', 'xml': 'text/xml'}
            mimetype = mimes[filePath.split('.')[-1]]
        self.media_descriptors.append({
            'MEDIA_URL': filepath, 'RELATIVE_MEDIA_URL': relpath,
            'MIME_TYPE': mimetype, 'TIME_ORIGIN': time_origin,
            'EXTRACTED_FROM': exfrom})

    def copyTier(self, eafObj, tierName):
        """
        Copies the tier to this object<br />
<br />
        eafObj   -- Elan object<br />
        tierName -- Tier name"""
        eafObj.removeTier(tierName)
        try:
            t = self.tiers[tierName][3]
            eafObj.addTier(tierName, tierDict=self.tiers[tierName][3])
            for ann in self.getAnnotationDataForTier(tierName):
                eafObj.insertAnnotation(tierName, ann[0], ann[1], ann[2])
            return 0
        except KeyError:
            warnings.warn('copyTier: Tier non existent!')
            return 1

    def addTier(self, tierId, ling='default-lt', parent=None, locale=None,
                part=None, ann=None, tierDict=None):
        """
        Add a tier to the object<br />
<br />
        tierId   -- Name of the tier<br />
        ling     -- Linguistic type<br />
        parent   -- ID of parent tier<br />
        locale   -- Locale used<br />
        part     -- Participant<br />
        ann      -- Annotator<br />
        tierDict -- Tier dict to use the quick function, when this is not None<br />
                    it will ignore all other options"""
        if ling not in self.linguistic_types:
            warnings.warn(
                'addTier: Linguistic type non existent, choosing the first')
            ling = self.linguistic_types.keys()[0]
        if tierDict is None:
            self.tiers[tierId] = ({}, {}, {
                'TIER_ID': tierId,
                'LINGUISTIC_TYPE_REF': ling,
                'PARENT_REF': parent,
                'PARTICIPANT': part,
                'DEFAULT_LOCALE': locale,
                'ANNOTATOR': ann}, len(self.tiers))
        else:
            self.tiers[tierId] = ({}, {}, tierDict, len(self.tiers))

    def removeTiers(self, tiers):
        """
        Remove tiers<br />
<br />
        tiers -- List of names of tiers to remove"""
        for a in tiers:
            self.removeTier(a, check=False, clean=False)
        self.cleanTimeSlots()

    def removeTier(self, idTier, clean=True):
        """
        Remove tier<br />
<br />
        idTier -- Name of the tier<br />
        clean  -- Flag to also clean up the timeslot id's(takes time)"""
        try:
            del(self.tiers[idTier])
            if clean:
                self.cleanTimeSlots()
            return 0
        except KeyError:
            warnings.warn(
                'removeTier: Tier non existent!\nlooking for: %s' % idTier)
            return 1

    def getTierNames(self):
        """Give a list of tiernames"""
        return self.tiers.keys()

    def getParametersForTier(self, idTier):
        """
        Gives the tierdict that is usable in the addTier function<br />
<br />
        idTier -- Name of the tier"""
        try:
            return self.tiers[idTier][2]
        except KeyError:
            warnings.warn('getParameterDictForTier: Tier non existent!')
            return None

    def childTiersFor(self, idTier):
        """
        Gives all children tiers<br />
<br />
        idTier -- Parent tier"""
        try:
            return [m for m in self.tiers
                    if 'PARENT_REF' in self.tiers[m][2] and
                    self.tiers[m][2]['PARENT_REF'] == idTier]
        except KeyError:
            warnings.warn('childTierFor: Tier non existent!')
            return None

    def getAnnotationDataForTier(self, idTier):
        """
        Gives a list of annotations in the format (start, end, value)<br />
<br />
        idTier -- Name of the tier"""
        try:
            a = self.tiers[idTier][0]
            return [(self.timeslots[a[b][0]], self.timeslots[a[b][1]], a[b][2])
                    for b in a]
        except KeyError:
            warnings.warn('getAnnotationDataForTier: Tier non existent!')
            return None

    def getAnnotationDataAtTime(self, idTier, time):
        """
        Gives the annotation at time<br />
<br />
        idTier -- Name of the tier<br />
        time   -- Time"""
        try:
            anns = self.tiers[idTier][0]
            return sorted(
                [(self.timeslots[m[0]], self.timeslots[m[1]], m[2])
                    for m in anns.itervalues() if
                    self.timeslots[m[0]] <= time and
                    self.timeslots[m[1]] >= time])
        except KeyError:
            warnings.warn('getAnnotationDataAtTime: Tier non existent!')
            return None

    def getAnnotationDatasBetweenTimes(self, idTier, start, end):
        """
        Gives a list of annotations that occur between times<br />
<br />
        idTier -- Name of the tier<br />
        start  -- Start time<br />
        end    -- End time"""
        try:
            anns = self.tiers[idTier][0]
            return sorted([
                (self.timeslots[m[0]], self.timeslots[m[1]], m[2])
                for m in anns.itervalues() if self.timeslots[m[1]] >= start and
                self.timeslots[m[0]] <= end])
        except KeyError:
            warnings.warn('getAnnotationDatasBetweenTimes: Tier non existent!')
            return None

    def removeAllAnnotationsFromTier(self, idTier):
        """
        Remove all annotations from a tier<br />
<br />
        idTier -- Name of the tier"""
        try:
            self.tiers[idTier][0], self.tiers[idTier][1] = {}, {}
            self.cleanTimeSlots()
            return 0
        except KeyError:
            warnings.warn('removeAllAnnotationsFromTier: Tier non existent!')
            return 1

    def insertAnnotation(self, idTier, start, end, value='', svg_ref=None):
        """
        Insert an annotation in a tier<br />
<br />
        idTier  -- Name of the tier<br />
        start   -- Start time of the annotation<br />
        end     -- End time of the annotation<br />
        value   -- Value of the annotation<br />
        svg_ref -- SVG reference"""
        try:
            startTs = self.generateTsId(start)
            endTs = self.generateTsId(end)
            self.tiers[idTier][0][self.generateAnnotationId()] =\
                (startTs, endTs, value, svg_ref)
            return 0
        except KeyError:
            warnings.warn('insertAnnotation: Tier non existent')
            return 1

    def removeAnnotation(self, idTier, time, clean=True):
        """
        Remove an annotation at time<br />
<br />
        idTier -- Name of the tier<br />
        time   -- Time<br />
        clean  -- Flag to clean timeslots(this takes time)"""
        try:
            for b in [a for a in self.tiers[tier][0].iteritems() if
                      a[1][0] >= time and a[1][1] <= time]:
                del(self.tiers[tier][0][b[0]])
            if clean:
                self.cleanTimeSlots()
            return 0
        except KeyError:
            warnings.warn('removeAnnotation: Tier non existent')
        return 1

    def insertRefAnnotation(self, idTier, ref, value, prev, svg_ref=None):
        """
        Insert a ref annotation in a tier<br />
<br />
        idTier  -- Name of the tier<br />
        ref     -- Reference<br />
        value   -- Value of the annotation<br />
        prev    -- Previous annotation<br />
        svg_ref -- SVG reference"""
        try:
            self.tiers[idTier][1][self.generateAnnotationId()] =\
                (ref, value, prev, svg_ref)
            return 0
        except KeyError:
            warnings.warn('insertRefAnnotation: Tier non existent')
            return 1

    def getRefAnnotationDataForTier(self, idTier):
        """"
        Give a list of all reference annotations<br />
<br />
        idTier -- Name of the tier"""
        try:
            return self.tiers[idTier][1]
        except KeyError:
            warnings.warn('getRefAnnotationDataForTier: Tier non existent!')
            return None

    def removeControlledVocabulary(self, cv):
        """
        Remove a controlled vocabulary<br />
<br />
        cv -- Controlled vocabulary ID"""
        try:
            del(self.controlled_vocabularies[cv])
            return 0
        except KeyError:
            warnings.warn('removeControlledVocabulary: Controlled vocabulary' +
                          ' non existent!')
            return 1

    def generateAnnotationId(self):
        """Generate the next annotation ID"""
        if self.naiveGenAnn:
            new = self.lastAnn+1
            self.lastAnn = new
        else:
            new = 1
            anns = {int(ann[1:]) for tier in self.tiers.itervalues()
                    for ann in tier[0]}
            if len(anns) > 0:
                newann = set(xrange(1, max(anns))).difference(anns)
                if len(newann) == 0:
                    new = max(anns)+1
                    self.naiveGenAnn = True
                    self.lastAnn = new
                else:
                    new = sorted(newann)[0]
        return 'a%d' % new

    def generateTsId(self, time=None):
        """Generate the next timeslot ID"""
        if self.naiveGenTS:
            new = self.lastTS+1
            self.lastTS = new
        else:
            new = 1
            tss = {int(x[2:]) for x in self.timeslots}
            if len(tss) > 0:
                newts = set(xrange(1, max(tss))).difference(tss)
                if len(newts) == 0:
                    new = max(tss)+1
                    self.naiveGenTS = True
                    self.lastTS = new
                else:
                    new = sorted(newts)[0]
        ts = 'ts%d' % new
        self.timeslots[ts] = time
        return ts

    def cleanTimeSlots(self):
        """Clean up all unused timeslots(warning this can take time)"""
        tsInTier = set(sum([a[0:2] for tier in self.tiers.itervalues()
                            for a in tier[0].itervalues()], ()))
        tsAvail = set(self.timeslots)
        for a in tsInTier.symmetric_difference(tsAvail):
            del(self.timeslots[a])
        self.naiveGenTS = False
        self.naiveGenAnn = False

    def generateAnnotationConcat(self, tiers, start, end):
        """
        Generate an concatenated annotation from annotations within a timeframe<br />
<br />
        tiers -- List of tiers<br />
        start -- Start time<br />
        end   -- End time"""
        return '_'.join(set(d[2] for t in tiers if t in self.tiers for d in
                        self.getAnnotationDatasBetweenTimes(t, start, end)))

    def mergeTiers(self, tiers, tiernew=None, gaptresh=1):
        """
        Merge tiers<br />
<br />
        tiers    -- List of tiers to merge<br />
        tiernew  -- Name of the new tier, if None it will be generated<br />
        gaptresh -- Treshhold to glue annotations in ms"""
        if len([t for t in tiers if t not in self.tiers]) > 0:
            warnings.warn('mergeTiers: One or more tiers non existent!')
            return 1
        if tiernew is None:
            tiernew = '%s_Merged' % '_'.join(tiers)
        self.removeTier(tiernew)
        self.addTier(tiernew)
        try:
            timepts = sorted(set.union(
                *[set(j for j in xrange(d[0], d[1])) for d in
                    [ann for tier in tiers for ann in
                     self.getAnnotationDataForTier(tier)]]))
        except TypeError:
            warnings.warn('mergeTiers: No annotations found!')
            return 1
        if len(timepts) > 1:
            start = timepts[0]
            for i in xrange(1, len(timepts)):
                if timepts[i]-timepts[i-1] > gaptresh:
                    self.insertAnnotation(
                        tiernew,
                        start,
                        timepts[i-1],
                        self.generateAnnotationConcat(
                            tiers, start, timepts[i-1]))
                    start = timepts[i]
            self.insertAnnotation(
                tiernew,
                start,
                timepts[i-1],
                self.generateAnnotationConcat(tiers, start, timepts[i-1]))
        return 0

    def shiftAnnotations(self, time):
        """
        Shift all annotations to the left or right, this creates a new object<br />
<br />
        time -- Shift width in ms negative for right shift"""
        e = self.extract(
            -1*time, self.getFullTimeInterval()[1]) if time < 0 else\
            self.extract(0, self.getFullTimeInterval()[1]-time)
        for tier in e.tiers.itervalues():
            for ann in tier[0].itervalues():
                e.timeslots[ann[0]] = e.timeslots[ann[0]]+offset
                e.timeslots[ann[1]] = e.timeslots[ann[1]]+offset
        e.cleanTimeSlots()
        return e

    def filterAnnotations(self, tier, tierName=None, filtin=None, filtex=None):
        """
        Filter annotations in tier<br />
<br />
        tier     -- Tier to filter<br />
        tierName -- Tier to put the filtered annotations in<br />
        filtin   -- Include everything in this list<br />
        filtex   -- Exclude everything in this list"""
        if tier not in self.tiers:
            warnings.warn('filterAnnotations: Tier non existent!' + tier)
            return 1
        if tierName is None:
            tierName = '%s_filter' % tier1
        self.removeTier(tierName)
        self.addTier(tierName)
        for a in [b for b in self.getAnnotationDataForTier(tier)
                  if (filtex is None or b[2] not in filtex) and
                  (filtin is None or b[2] in filtin)]:
            self.insertAnnotation(tierName, a[0], a[1], a[2])
        return 0

    def glueAnnotationsInTier(self, tier, tierName=None, treshhold=85,
                              filtin=None, filtex=None):
        """
        Glue annotatotions together<br />
<br />
        tier      -- Tier to glue<br />
        tierName  -- Name for the output tier<br />
        treshhold -- Maximal gap to glue<br />
        filtin    -- Include only this annotations<br />
        filtex    -- Exclude all this annotations"""
        if tier not in self.tiers:
            warnings.warn('glueAnnotationsInTier: Tier non existent!')
            return 1
        if tierName is None:
            tierName = '%s_glued' % tier
        self.removeTier(tierName)
        self.addTier(tierName)
        tierData = sorted(self.getAnnotationDataForTier(tier))
        tierData = [t for t in tierData if
                    (filtin is None or t[2] in filtin) and
                    (filtex is None or t[2] not in filtex)]
        currentAnn = None
        for i in xrange(0, len(tierData)):
            if currentAnn is None:
                currentAnn = (tierData[i][0], tierData[i][1], tierData[i][2])
            elif tierData[i][0] - currentAnn[1] < treshhold:
                currentAnn = (currentAnn[0], tierData[i][1],
                              '%s_%s' % (currentAnn[2], tierData[i][2]))
            else:
                self.insertAnnotation(tierName, currentAnn[0], currentAnn[1],
                                      currentAnn[2])
                currentAnn = tierData[i]
        if currentAnn is not None:
            self.insertAnnotation(tierName, currentAnn[0],
                                  tierData[len(tierData)-1][1], currentAnn[2])
        return 0

    def getFullTimeInterval(self):
        """Give a tuple with the start and end of the entire file"""
        return (min(self.timeslots.itervalues()),
                max(self.timeslots.itervalues()))

    def createGapsAndOverlapsTier(self, tier1, tier2, tierNam=None, maxlen=-1):
        """
        Create a tier with the gaps and overlaps<br />
<br />
        tier1   -- Name of the first tier<br />
        tier2   -- Name of the second tier<br />
        tierNam -- Name of the output tier<br />
        maxlen  -- Maximum length of the ftos"""
        if tier1 not in self.tiers or tier2 not in self.tiers:
            warnings.warn(
                'createGapsAndOverlapsTier: One or more tiers non existent!')
            return None
        if tierName is None:
            tierName = '%s_%s_ftos' % (tier1, tier2)
        self.removeTier(tierName)
        self.addTier(tierName)
        ftos = self.getGapsAndOverlapsDuration(tier1, tier2, maxlen)
        for fto in ftos:
            self.insertAnnotation(tierName, fto[1], fto[2], fto[0])
        return ftos

    def getGapsAndOverlapsDuration(self, tier1, tier2, maxlen=-1,
                                   progressbar=False):
        """
        Give gaps and overlaps in the format (type, start, end)<br />
<br />
        tier1       -- Name of the first tier<br />
        tier2       -- Name of the second tier<br />
        maxlen      -- Maximum length of the ftos<br />
        progressbar -- Flag to display the progress"""
        if tier1 not in self.tiers or tier2 not in self.tiers:
            warnings.warn(
                'getGapsAndOverlapsDuration: One or more tiers non existent!')
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
                'getGapsAndOverlapsDuration: No annotations found...')
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

    def createControlledVocabulary(self, cvEntries, cvId, description=''):
        """
        Add a controlled vocabulary<br />
<br />
        cvEntries   -- Entries in the controlled vocabulary<br />
        cvId        -- Name of the controlled vocabulary<br />
        description -- Description"""
        self.controlledvocabularies[cvId] = (description, cvEntries)

    def getTierIdsForLinguisticType(self, lingType, parent=None):
        """
        Give a list of all tiers matching a linguistic type<br />
<br />
        lingType -- The linguistic type<br />
        parent   -- Only match tiers from this parent"""
        return [t for t in self.tiers if
                self.tiers[t][2]['LINGUISTIC_TYPE_REF'] == lingType and
                (parent is None or self.tiers[t][2]['PARENT_REF'] == parent)]

    def removeLinguisticType(self, lingType):
        """
        Remove a linguistic type<br />
<br />
        lingType -- Name of the linguistic type"""
        try:
            del(self.linguistic_types[lingType])
            return 0
        except KeyError:
            warnings.warn(
                'removeLinguisticType: Linguistic type non existent!')
            return 1

    def addLinguisticType(self, lingtype, constraints, timealignable=True,
                          graphicreferences=False, extref=None):
        """
        Add a linguistic type<br />
<br />
        lingtype          -- Name of the linguistic type<br />
        constraints       -- Constraint names<br />
        timealignable     -- Flag for time alignable<br />
        graphicreferences -- Graphic references<br />
        extref            -- External references"""
        self.linguistic_types[lingtype] = {
            'LINGUISTIC_TYPE_ID': lingtype,
            'TIME_ALIGNABLE': str(timealignable).lower(),
            'GRAPHIC_REFERENCES': str(graphicreferences).lower(),
            'CONSTRAINTS': constraints}
        if extref is not None:
            self.linguistic_types[lingtype]['EXT_REF'] = extref

    def getLinguisticTypes(self):
        """Give a list of available linguistic types"""
        return self.linguistic_types.keys()
