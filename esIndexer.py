import os
from datetime import datetime
from elasticsearch.helpers import bulk, BulkIndexError, streaming_bulk
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError,
    TransportError,
    ConflictError
)
from elasticsearch_dsl import connections
from elasticsearch_dsl.wrappers import Range

from sqlalchemy import or_
from sqlalchemy.orm import configure_mappers, raiseload
from sqlalchemy.dialects import postgresql

from model.cce import CCE as dbCCE
from model.renewal import Renewal as dbRenewal
from model.registration import Registration as dbRegistration
from model.elastic import (
    CCE,
    Registration,
    Renewal,
    Claimant
)


class ESIndexer():
    def __init__(self, manager, loadFromTime):
        self.cce_index = os.environ['ES_CCE_INDEX']
        self.ccr_index = os.environ['ES_CCR_INDEX']
        self.client = None
        self.session = manager.session
        self.loadFromTime = loadFromTime if loadFromTime else datetime.strptime('1970-01-01', '%Y-%m-%d')

        self.createElasticConnection()
        self.createIndex()

        configure_mappers()

    def createElasticConnection(self):
        host = os.environ['ES_HOST']
        port = os.environ['ES_PORT']
        timeout = int(os.environ['ES_TIMEOUT'])
        try:
            self.client = Elasticsearch(
                hosts=[{'host': host, 'port': port}],
                timeout=timeout
            )
        except ConnectionError as err:
            print('Failed to connect to ElasticSearch instance')
            raise err
        connections.connections._conns['default'] = self.client

    def createIndex(self):
        if self.client.indices.exists(index=self.cce_index) is False:
            CCE.init()
        if self.client.indices.exists(index=self.ccr_index) is False:
            Renewal.init()
    
    def indexRecords(self, recType='cce'):
        """Process the current batch of updating records. This utilizes the
        elasticsearch-py bulk helper to import records in chunks of the
        provided size. If a record in the batch errors that is reported and
        logged but it does not prevent the other records in the batch from
        being imported.
        """
        success, failure = 0, 0
        errors = []
        try:
            for status, work in streaming_bulk(self.client, self.process(recType)):
                print(status, work)
                if not status:
                    errors.append(work)
                    failure += 1
                else:
                    success += 1
            
            print('Success {} | Failure: {}'.format(success, failure))
        except BulkIndexError as err:
            print('One or more records in the chunk failed to import')
            raise err

    def process(self, recType):
        if recType == 'cce':
            for cce in self.retrieveEntries():
                esEntry = ESDoc(cce)
                esEntry.indexEntry()
                yield esEntry.entry.to_dict(True)
        elif recType == 'ccr':
            for ccr in self.retrieveRenewals():
                esRen = ESRen(ccr)
                esRen.indexRen()
                if esRen.renewal.rennum == '': continue
                yield esRen.renewal.to_dict(True)

    def retrieveEntries(self):
        retQuery = self.session.query(dbCCE)\
            .filter(dbCCE.date_modified > self.loadFromTime)
        for cce in retQuery.all():
            yield cce
    
    def retrieveRenewals(self):
        renQuery = self.session.query(dbRenewal)\
            .filter(dbRenewal.date_modified > self.loadFromTime)
        for ccr in renQuery.all():
            yield ccr


class ESDoc():
    def __init__(self, cce):
        self.dbRec = cce
        self.entry = None 
        
        self.initEntry()
    
    def initEntry(self):
        print('Creating ES record for {}'.format(self.dbRec))

        self.entry = CCE(meta={'id': self.dbRec.uuid})

    def indexEntry(self):
        self.entry.uuid = self.dbRec.uuid
        self.entry.title = self.dbRec.title
        self.entry.authors = [ a.name for a in self.dbRec.authors ]
        self.entry.publishers = [ p.name for p in self.dbRec.publishers ]
        self.entry.lccns = [ l.lccn for l in self.dbRec.lccns ]
        self.entry.registrations = [
            Registration(regnum=r.regnum, regdate=r.reg_date)
            for r in self.dbRec.registrations
        ]


class ESRen():
    def __init__(self, ccr):
        self.dbRen = ccr
        self.renewal = None 
        
        self.initRenewal()
    
    def initRenewal(self):
        print('Creating ES record for {}'.format(self.dbRen))

        self.renewal = Renewal(meta={'id': self.dbRen.renewal_num})

    def indexRen(self):
        self.renewal.uuid = self.dbRen.uuid
        self.renewal.rennum = self.dbRen.renewal_num
        self.renewal.rendate = self.dbRen.renewal_date
        self.renewal.title = self.dbRen.title
        self.renewal.authors = self.dbRen.author
        self.renewal.claimants = [
            Claimant(name=c.name, claim_type=c.claimant_type)
            for c in self.dbRen.claimants
        ]
