import base64
import csv
from datetime import datetime
from github import Github
from io import StringIO
import os
import re

from sqlalchemy.orm.exc import MultipleResultsFound

from model.renewal import Renewal
from model.registration import Registration

class CCRReader():
    def __init__(self, manager):
        self.git = Github(os.environ['ACCESS_TOKEN'])
        self.repo = self.git.get_repo(os.environ['CCR_REPO'])
        self.ccrYears = {}
        self.dbManager = manager

    def loadYears(self, selectedYear, loadFromTime):
        for year in self.repo.get_contents('/data'):
            yearMatch = re.match(r'^([0-9]{4}).*\.tsv$', year.name)
            if not yearMatch: continue
            fileYear = yearMatch.group(1)
            if selectedYear is not None and selectedYear != fileYear: continue
            fileCommit = self.repo.get_commits(path=year.path)[0]
            commitDate = fileCommit.commit.committer.date
            if loadFromTime is not None and commitDate < loadFromTime: continue
            yearInfo = {
                'path': year.path,
                'filename': year.name,
                'sha': year.sha
            }
            self.ccrYears[fileYear] = yearInfo
    
    def importYears(self):
        for year in self.ccrYears.keys(): self.importYear(year)
    
    def importYear(self, year):
        yearInfo = self.ccrYears[year]
        print('Loading Year {}'.format(year))
        cceFile = CCRFile(self.repo, yearInfo, self.dbManager.session)
        cceFile.loadFileTSV()
        cceFile.readRows()
        self.dbManager.commitChanges()


class CCRFile():
    def __init__(self, repo, ccrFile, session):
        self.repo = repo
        self.ccrFile = ccrFile
        self.session = session

        self.rows = []

    def loadFileTSV(self):
        yearBlob = self.repo.get_git_blob(self.ccrFile['sha'])
        tsvString = base64.b64decode(yearBlob.content).decode('utf-8')
        tsvFile = StringIO(tsvString)
        self.rows = csv.DictReader(tsvFile, delimiter='\t', quotechar='"')
    
    def readRows(self):        
        for row in self.rows: self.parseRow(row)

    def parseRow(self, row):

        rec = self.matchRenewal(row['entry_id'])
        if rec: self.updateRenewal(rec, row)
        else: self.createRenewal(row)

    def createRenewal(self, row):
        title = CCRFile.cascadeFieldNameLoad('title', 'titl', row=row)
        renewalDateText = CCRFile.cascadeFieldNameLoad('rdat', 'dreg', row=row)
        source = CCRFile.cascadeFieldNameLoad('source', 'full_text', row=row)
        author = CCRFile.cascadeFieldNameLoad('author', 'auth', row=row)
        notes = CCRFile.cascadeFieldNameLoad('notes', 'note', row=row)

        try:
            renDate = datetime.strptime(renewalDateText, '%Y-%m-%d')
        except ValueError:
            renDate = None

        renRec = Renewal(
            uuid=row['entry_id'],
            author=author,
            title=title,
            reg_data='{}|{}'.format(row['oreg'], row['odat']),
            renewal_num=row['id'],
            renewal_date=renDate,
            renewal_date_text=renewalDateText,
            new_matter=row['new_matter'],
            see_also_regs=row['see_also_reg'],
            see_also_rens=row['see_also_ren'],
            notes=notes,
            source=source
        )

        for numField in ['volume', 'part', 'number', 'page']:
            setattr(
                renRec,
                numField, 
                row[numField] if row[numField] != '' else None
            )

        self.matchRegistrations(renRec, row['oreg'], row['odat'])
        renRec.addClaimants(row['claimants'])

        self.session.add(renRec)
        print('INSERT', renRec)

    def updateRenewal(self, rec, row):
        rec.uuid = row['entry_id']
        rec.title = CCRFile.cascadeFieldNameLoad('title', 'titl', row=row)
        rec.source = CCRFile.cascadeFieldNameLoad('source', 'full_text', row=row)
        rec.author = CCRFile.cascadeFieldNameLoad('author', 'auth', row=row)
        rec.notes = CCRFile.cascadeFieldNameLoad('notes', 'note', row=row)
        rec.reg_data = '{}|{}'.format(row['oreg'], row['odat'])
        rec.renewal_num = row['id']
        rec.new_matter = row['new_matter']
        if row['see_also_reg']:
            rec.see_also_regs = row['see_also_reg']
        if row['see_also_ren']:
            rec.see_also_rens = row['see_also_ren']

        rec.renewal_date_text = CCRFile.cascadeFieldNameLoad('rdat', 'dreg', row=row)
        try:
            rec.renewal_date = datetime.strptime(rec.renewal_date_text, '%Y-%m-%d')
        except ValueError:
            rec.renewal_date = None

        for numField in ['volume', 'part', 'number', 'page']:
            setattr(
                rec,
                numField, 
                row[numField] if row[numField] != '' else None
            )

        self.matchRegistrations(rec, row['oreg'], row['odat'])
        rec.updateClaimants(row['claimants'])

        print('UPDATE', rec)

    def matchRenewal(self, uuid):
        return self.session.query(Renewal).filter(Renewal.uuid == uuid).one_or_none()

    def matchRegistrations(self, renRec, regnum, origDate):
        if regnum is None or regnum.strip() == '': return
        try:
            checkDate = datetime.strptime(origDate, '%Y-%m-%d')
        except ValueError:
            checkDate = None
        regnumQuery = self.session.query(Registration)\
                .filter(Registration.regnum == regnum)\
                .filter(Registration.reg_date == checkDate)
        try:
            origReg = regnumQuery.one_or_none()
        except MultipleResultsFound:
            origRegs = regnumQuery.all()

            if len(origRegs) < 1:
                origReg = None
                seeAlsoRegs = regnumQuery.all()
                renRec.see_also_regs = '{}|{}'.format(
                    renRec.see_also_regs,
                    '|'.join([ r.regnum for r in seeAlsoRegs ])
                )
            else:
                origReg = origRegs[0]
                if len(origRegs) > 1:
                    renRec.see_also_regs = '{}|{}'.format(
                        renRec.see_also_regs,
                        '|'.join([ r.regnum for r in origRegs[1:] ])
                    )

        if origReg:
            renRec.registrations.append(origReg)
            renRec.orphan = False
        else:
            print('Matching Registration not found!')
            if len(renRec.registrations) < 1:
                renRec.orphan = True

    @staticmethod
    def cascadeFieldNameLoad(*fields, row=None):
        for field in fields:
            try:
                return row[field]
            except KeyError:
                pass
        print('No matching field found!')
        raise KeyError
