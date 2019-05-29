import base64
from datetime import datetime
from github import Github
import lccnorm
from lxml import etree
import os
import re
import traceback

from model.cce import CCE
from model.errorCCE import ErrorCCE
from model.volume import Volume

from helpers.errors import DataError

class CCEReader():
    def __init__(self, manager=None):
        self.git = Github(os.environ['ACCESS_TOKEN'])
        self.repo = self.git.get_repo(os.environ['CCE_REPO'])
        self.dbManager = manager
        self.cceYears = {}

    def loadYears(self, selectedYear):
        for year in self.repo.get_contents('/xml'):
            if not re.match(r'^19[0-9]{2}$', year.name): continue
            if selectedYear is not None and year.name != selectedYear: continue
            yearInfo = {'path': year.path, 'yearFiles': []}
            self.cceYears[year.name] = yearInfo
    
    def loadYearFiles(self, year, loadFromTime):
        yearInfo = self.cceYears[year]
        for yearFile in self.repo.get_contents(yearInfo['path']):
            if 'alto' in yearFile.name or 'TOC' in yearFile.name: continue
            fileCommit = self.repo.get_commits(path=yearFile.path)[0]
            commitDate = fileCommit.commit.committer.date
            if loadFromTime is not None and commitDate < loadFromTime: continue
            self.cceYears[year]['yearFiles'].append({
                'filename': yearFile.name,
                'path': yearFile.path,
                'sha': yearFile.sha
            })
    
    def getYearFiles(self, loadFromTime):
        for year in self.cceYears.keys():
            print('Loading files for {}'.format(year))
            self.loadYearFiles(year, loadFromTime)
    
    def importYearData(self):
        for year in self.cceYears.keys(): self.importYear(year)
    
    def importYear(self, year):
        yearFiles = self.cceYears[year]['yearFiles']
        for yearFile in yearFiles: self.importFile(yearFile)
    
    def importFile(self, yearFile):
        print('Importing data from {}'.format(yearFile['filename']))
        cceFile = CCEFile(self.repo, yearFile, self.dbManager.session)
        cceFile.loadFileXML()
        cceFile.readXML()
        self.dbManager.commitChanges()


class CCEFile():
    tagOptions = {
        'header': 'skipElement',
        'page': 'parsePage',
        'copyrightEntry': 'parseEntry',
        'entryGroup': 'parseGroup',
        'crossRef': 'skipElement'
    }

    dateTypes = ['regDate', 'copyDate', 'pubDate', 'affDate']

    def __init__(self, repo, cceFile, session):
        self.repo = repo
        self.cceFile = cceFile
        self.session = session

        self.xmlString = None
        self.root = None
        self.fileHeader = None
        self.currentPage = 0
        self.pagePos = 0

    def loadFileXML(self):
        yearBlob = self.repo.get_git_blob(self.cceFile['sha'])
        self.xmlString = base64.b64decode(yearBlob.content)
        self.root = etree.fromstring(self.xmlString)
    
    def readXML(self):
        self.loadHeader()

        for child in self.root:
            childOp = getattr(self, CCEFile.tagOptions[child.tag])
            self.pagePos += 1
            try:
                childOp(child)
            except DataError as err:
                print('Caught error')
                self.createErrorEntry(
                    getattr(err, 'uuid', child.get('id')),
                    getattr(err, 'regnum', None),
                    getattr(err, 'entry', child),
                    getattr(err, 'message', None)
                )
            except Exception as err:
                print('ERROR', err)
                print(traceback.print_exc())
                raise err

    def skipElement(self, el):
        print('Skipping element {}'.format(el.tag))

    def parsePage(self, page):
        self.currentPage = page.get('pgnum')
        self.pagePos = 0

    def parseEntry(self, entry, shared=[]):
        uuid = entry.get('id')
        
        if 'regnum' not in entry.attrib:
            print('Entry Missing REGNUM')
            raise DataError(
                'missing_regnum',
                uuid=uuid,
                entry=entry
            )
        
        regnums = self.loadRegnums(entry)
        
        entryDates = self.loadDates(entry)
        regDates = entryDates['regDate']
        if(len(regnums) != len(regDates)):
            if len(regDates) == 1 and len(regnums) > 0:
                regDates = [regDates[0]] * len(regnums)
            else:
                raise DataError(
                    'regnum_date_mismatch',
                    uuid=uuid,
                    regnum='; '.join(regnums),
                    entry=entry
                )
        
        regs = self.createRegistrations(regnums, regDates)
        existingRec = self.matchUUID(uuid)
        if existingRec:
            self.updateEntry(existingRec, entryDates, entry, shared, regs)
        else:
            self.createEntry(uuid, entryDates, entry, shared, regs)

    def matchUUID(self, uuid):
        return self.session.query(CCE).filter(CCE.uuid == uuid).one_or_none()

    def createEntry(self, uuid, dates, entry, shared, registrations):
        titles = self.createTitleList(entry, shared)
        authors = self.createAuthorList(entry, shared)
        copies = CCEFile.fetchText(entry, 'copies')
        description = CCEFile.fetchText(entry, 'desc')
        newMatter = len(entry.findall('newMatterClaimed')) > 0

        publishers = [
            (c.text, c.get('claimant', None)) 
            for c in entry.findall('.//pubName')
        ]

        lccn = [ lccnorm.normalize(l.text) for l in entry.findall('lccn') ]

        cceRec = CCE(
            uuid=uuid,
            page=self.currentPage,
            page_position=self.pagePos,
            title=titles,
            copies=copies,
            description=description,
            new_matter=newMatter,
            pub_date=CCEFile.fetchDateValue(dates['pubDate'], text=False),
            pub_date_text=CCEFile.fetchDateValue(dates['pubDate'], text=True),
            aff_date=CCEFile.fetchDateValue(dates['affDate'], text=False),
            aff_date_text=CCEFile.fetchDateValue(dates['affDate'], text=True),
            copy_date=CCEFile.fetchDateValue(dates['copyDate'], text=False),
            copy_date_text=CCEFile.fetchDateValue(dates['copyDate'], text=True)
        )
        cceRec.addRelationships(
            self.fileHeader,
            entry,
            authors=authors,
            publishers=publishers,
            lccn=lccn,
            registrations=registrations
        )
        self.session.add(cceRec)
        print('INSERT', cceRec)

    def updateEntry(self, rec, dates, entry, shared, registrations):
        rec.title = self.createTitleList(entry, shared)
        rec.copies = CCEFile.fetchText(entry, 'copies')
        rec.description = CCEFile.fetchText(entry, 'desc')
        rec.new_matter = len(entry.findall('newMatterClaimed')) > 0
        rec.page = self.currentPage
        rec.page_position = self.pagePos

        rec.pub_date = CCEFile.fetchDateValue(dates['pubDate'], text=False)
        rec.pub_date_text = CCEFile.fetchDateValue(dates['pubDate'], text=True)
        rec.aff_date = CCEFile.fetchDateValue(dates['affDate'], text=False)
        rec.aff_date_text = CCEFile.fetchDateValue(dates['affDate'], text=True)
        rec.copy_date = CCEFile.fetchDateValue(dates['copyDate'], text=False)
        rec.copy_date_text = CCEFile.fetchDateValue(dates['copyDate'], text=True)

        authors = self.createAuthorList(entry, shared)
        publishers = [
            (c.text, c.get('claimant', None)) 
            for c in entry.findall('.//pubName')
        ]
        lccn = [ lccnorm.normalize(l.text) for l in entry.findall('lccn') ]

        rec.updateRelationships(
            entry,
            authors=authors,
            publishers=publishers,
            lccn=lccn,
            registrations=registrations
        )
        print('UPDATE', rec)

    def createRegistrations(self, regnums, regdates):
        registrations = []
        for x in range(len(regnums)):
            try:
                regCat = re.match(r'([A-Z]+)', regnums[x][0]).group(1)
            except AttributeError:
                regCat ='Unknown'
            registrations.append({
                'regnum': regnums[x], 
                'category': regCat,
                'regDate': regdates[x][0],
                'regDateText': regdates[x][1]
            })
        return registrations

    def loadRegnums(self, entry):
        rawRegnums = entry.get('regnum').strip()
        regnums = rawRegnums.split(' ')
        regnums.extend(self.loadAddtlEntries(entry))
        outNums = []
        for num in regnums:
            parsedNum = self.parseRegNum(num)
            if type(parsedNum) is str: outNums.append(parsedNum)
            else: outNums.extend(parsedNum)
        return outNums
    
    def loadAddtlEntries(self, entry):
        moreRegnums = []
        for addtl in entry.findall('.//additionalEntry'):
            try:
                addtlRegnum = addtl.get('regnum').strip()
                moreRegnums.extend(addtlRegnum.split(' '))
            except AttributeError:
                continue
        return moreRegnums
    
    def parseRegNum(self, num):
        try:
            if (
                re.search(r'[0-9]+\-[A-Z0-9]+', num)
                and num[2] != '0'
                and num[:2] != 'B5'
            ):
                regnumRange = num.split('-')
                regRangePrefix = re.match(r'([A-Z]+)', regnumRange[0]).group(1)
                regRangeStart = int(regnumRange[0].replace(regRangePrefix, ''))
                regRangeEnd = int(regnumRange[1].replace(regRangePrefix, ''))
                if regRangeEnd - regRangeStart < 1000:
                    return [ 
                        '{}{}'.format(regRangePrefix, str(i))
                        for i in range(regRangeStart, regRangeEnd)
                    ]
        except (ValueError, AttributeError) as err:
            print('RANGE ERROR', self.currentPage, self.pagePos)
            raise DataError('regnum_range_parsing_error')
        
        return num

    def loadDates(self, entry):
        dates = {}
        for dType in CCEFile.dateTypes:
            dates[dType] = [
                (CCEFile.parseDate(d.get('date', None), '%Y-%m-%d'), d.text)
                for d in entry.findall('.//{}'.format(dType))
                if not ('ignore' in d.attrib and d.get('ignore') == 'yes')
            ]
        if len(dates['regDate']) < 1:
            if len(dates['copyDate']) > 0:
                dates['regDate'].append(dates['copyDate'][0])
            elif len(dates['pubDate']) > 0:
                dates['regDate'].append(dates['pubDate'][0])
        
        return dates

    @staticmethod
    def parseDate(date, dateFormat):
        if date is None or dateFormat == '': return None

        try:
            outDate = datetime.strptime(date, dateFormat)
            return outDate.strftime('%Y-%m-%d')
        except ValueError:
            return CCEFile.parseDate(date, dateFormat[:-3])

    def createTitleList(self, entry, shared):
        return '; '.join([
            t.text 
            for t in entry.findall('.//title') + [
                t for t in shared if t.tag == 'title'
            ]
            if t.text is not None
        ])

    def createErrorEntry(self, uuid, regnum, entry, reason):
        errorCCE = ErrorCCE(
            uuid=uuid,
            regnum=regnum,
            page=self.currentPage,
            page_position=self.pagePos,
            reason=reason
        )
        errorCCE.volume = self.fileHeader
        errorCCE.addXML(entry)
        self.session.add(errorCCE)

    def parseGroup(self, group):
        entries = []
        shared = []
        for field in group:
            if field.tag == 'page': self.parsePage(field)
            elif field.tag == 'copyrightEntry': entries.append(field)
            else: shared.append(field)
        
        for entry in entries: 
            try:
                self.parseEntry(entry, shared)
            except DataError as err:
                err.uuid = entry.get('id')
                raise err
        
    def createAuthorList(self, rec, shared=[]):
        authors = [
            (a.text, False) for a in rec.findall('.//authorName')
            if len(list(a.itersiblings(tag='role', preceding=True))) > 0
        ]
        if len(authors) < 1:
            try:
                authors.append((rec.findall('.//authorName')[0].text, False))
            except IndexError:
                pass
        
        authors.extend([
            (a.text, False) for a in shared if a.tag == 'authorName'
        ])

        try:
            authors[0] = (authors[0][0], True)
        except IndexError:
            pass
        
        return authors
    
    def loadHeader(self):
        header = self.root.find('.//header')

        startNum = endNum = None
        if header.find('cite/division/numbers') is not None:
            startNum = header.find('cite/division/numbers').get('start', None)
            endNum = header.find('cite/division/numbers').get('end', None)
        elif header.find('cite/division/number') is not None:
            volNum = CCEFile.fetchText(header, 'cite/division/number')
            startNum = volNum
            endNum= volNum

        headerDict = {
            'source': header.find('source').get('url', None),
            'status': CCEFile.fetchText(header, 'status'),
            'series': header.find('cite/series').get('label', None),
            'volume': CCEFile.fetchText(header, 'cite/volume'),
            'year': CCEFile.fetchText(header, 'cite/year'),
            'part': CCEFile.fetchText(header, 'cite/division/part'),
            'group': CCEFile.fetchText(header, 'cite/division/group'),
            'material': CCEFile.fetchText(header, 'cite/division/material'),
            'numbers': {
                'start': startNum,
                'end': endNum
            }  
        }
        
        self.fileHeader = Volume(
            source=headerDict['source'],
            status=headerDict['status'],
            series=headerDict['series'],
            volume=headerDict['volume'],
            year=headerDict['year'],
            part=headerDict['part'],
            group=headerDict['group'],
            material=headerDict['material'],
            start_number=headerDict['numbers']['start'],
            end_number=headerDict['numbers']['end']
        )
        self.session.add(self.fileHeader)

    @staticmethod
    def fetchText(parent, tag):
        element = parent.find(tag)
        return element.text if element is not None else None
    
    @staticmethod
    def fetchDateValue(date, text=False):
        x = 1 if text else 0
        return date[0][x] if len(date) > 0 else None
