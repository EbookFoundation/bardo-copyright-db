from datetime import datetime
from unittest.mock import MagicMock, call
import pytest
from elasticsearch.helpers import BulkIndexError
from elasticsearch.exceptions import ConnectionError

from esIndexer import ESIndexer, ESDoc, ESRen


class TestIndexer(object):
    @pytest.fixture
    def setEnvVars(self, mocker):
        mocker.patch.dict('os.environ', {
            'ES_CCE_INDEX': 'test_cce',
            'ES_CCR_INDEX': 'test_ccr',
            'ES_HOST': 'test',
            'ES_PORT': '9999',
            'ES_TIMEOUT': '0'
        })

    @pytest.fixture
    def testIndexer(self, mocker, setEnvVars):
        mocker.patch('esIndexer.configure_mappers')
        mocker.patch('esIndexer.ESIndexer.createElasticConnection')
        mocker.patch('esIndexer.ESIndexer.createIndex')
        mockManager = MagicMock()
        mockManager.session = 'session'

        return ESIndexer(mockManager, 10)

    def test_indexerInit(self, mocker, testIndexer):
        assert testIndexer.cce_index == 'test_cce'
        assert testIndexer.ccr_index == 'test_ccr'
        assert testIndexer.session == 'session'

    def test_indexerInit_no_time(self, mocker, setEnvVars):
        mockConfig = mocker.patch('esIndexer.configure_mappers')
        mockConn = mocker.patch('esIndexer.ESIndexer.createElasticConnection')
        mockCreate = mocker.patch('esIndexer.ESIndexer.createIndex')
        mockManager = MagicMock()
        mockManager.session = 'session'

        testIndexer = ESIndexer(mockManager, None)

        assert testIndexer.cce_index == 'test_cce'
        assert testIndexer.ccr_index == 'test_ccr'
        assert testIndexer.session == 'session'
        assert testIndexer.loadFromTime == datetime(1970, 1, 1)
        assert mockConn.called
        assert mockCreate.called
        assert mockConfig.called

    def test_elastic_connection(self, mocker, setEnvVars):
        mockConfig = mocker.patch('esIndexer.configure_mappers')
        mockCreate = mocker.patch('esIndexer.ESIndexer.createIndex')
        mockManager = MagicMock()
        mockManager.session = 'session'

        mockElastic = mocker.patch('esIndexer.Elasticsearch')
        mockElastic.return_value = 'test_client'
        mocker.patch('esIndexer.connections')

        testIndexer = ESIndexer(mockManager, 10)

        assert testIndexer.cce_index == 'test_cce'
        assert testIndexer.ccr_index == 'test_ccr'
        assert testIndexer.session == 'session'
        assert testIndexer.client == 'test_client'
        assert mockCreate.called
        assert mockConfig.called
        assert mockElastic.called_once_with(
            hosts=[{'host': 'test', 'port': '9999'}],
            timeout='0'
        )

    def test_elastic_conn_err(self, mocker, setEnvVars):
        mocker.patch('esIndexer.configure_mappers')
        mocker.patch('esIndexer.ESIndexer.createIndex')
        mockManager = MagicMock()
        mockManager.session = 'session'

        mockElastic = mocker.patch('esIndexer.Elasticsearch')
        mockElastic.side_effect = ConnectionError
        mocker.patch('esIndexer.connections')
        with pytest.raises(ConnectionError):
            ESIndexer(mockManager, 10)

    def test_index_create(self, mocker, setEnvVars):
        mockConfig = mocker.patch('esIndexer.configure_mappers')
        mockClient = MagicMock()
        mockClient.indices.exists.side_effect = [False, False]
        mockConn = mocker.patch('esIndexer.ESIndexer.createElasticConnection')
        mockConn.return_value = mockClient
        mockCCE = mocker.patch('esIndexer.CCE')
        mockCCR = mocker.patch('esIndexer.Renewal')
        mockManager = MagicMock()
        mockManager.session = 'session'

        testIndexer = ESIndexer(mockManager, 10)

        assert testIndexer.cce_index == 'test_cce'
        assert testIndexer.ccr_index == 'test_ccr'
        assert testIndexer.session == 'session'
        assert mockConn.called
        assert mockConfig.called
        assert mockCCE.init.called
        assert mockCCR.init.called

    def test_bulk_index_success(self, mocker, testIndexer):
        mockProcess = mocker.patch('esIndexer.ESIndexer.process')
        mockProcess.return_value = ['test1', 'test2', 'test3']
        mockStreaming = mocker.patch('esIndexer.streaming_bulk')
        mockStreaming.return_value = [
            (True, 'test1'),
            (False, 'test2'),
            (True, 'test3')
        ]

        testIndexer.indexRecords()

        assert mockProcess.called
        assert mockStreaming.called

    def test_bulk_index_failure(self, mocker, testIndexer):
        mockProcess = mocker.patch('esIndexer.ESIndexer.process')
        mockProcess.return_value = ['test1', 'test2', 'test3']
        mockStreaming = mocker.patch('esIndexer.streaming_bulk')
        mockStreaming.side_effect = BulkIndexError

        with pytest.raises(BulkIndexError):
            testIndexer.indexRecords()

    def test_process_cce(self, mocker, testIndexer):
        mockRetrieve = mocker.patch('esIndexer.ESIndexer.retrieveEntries')
        mockRetrieve.return_value = ['test1', 'test2', 'test3']
        mockDoc = mocker.patch('esIndexer.ESDoc')
        mockDoc().entry.to_dict.side_effect = ['test1', 'test2', 'test3']

        processed = [p for p in testIndexer.process('cce')]
        assert processed[0] == 'test1'

    def test_process_ccr(self, mocker, testIndexer):
        mockRens = []
        for i in range(1, 4):
            tmpRen = MagicMock()
            tmpRen.renewal.rennum = '' if i == 1 else i
            tmpRen.renewal.to_dict.return_value = 'test{}'.format(str(i))
            mockRens.append(tmpRen)

        mockRetrieve = mocker.patch('esIndexer.ESIndexer.retrieveRenewals')
        mockRetrieve.return_value = ['test1', 'test2', 'test3']
        mockDoc = mocker.patch('esIndexer.ESRen')
        mockDoc.side_effect = mockRens

        processed = [p for p in testIndexer.process('ccr')]
        assert processed[0] == 'test2'

    def test_retrieveEntries(self, mocker, testIndexer):
        mockSession = MagicMock()
        mockAll = MagicMock()
        mockAll.all.return_value = ['cce1', 'cce2', 'cce3']
        mockSession.query().filter.return_value = mockAll
        testIndexer.session = mockSession

        entries = [e for e in testIndexer.retrieveEntries()]

        assert entries[1] == 'cce2'

    def test_retrieveRenewals(self, mocker, testIndexer):
        mockSession = MagicMock()
        mockAll = MagicMock()
        mockAll.all.return_value = ['ccr1', 'ccr2', 'ccr3']
        mockSession.query().filter.return_value = mockAll
        testIndexer.session = mockSession

        renewals = [r for r in testIndexer.retrieveRenewals()]

        assert renewals[2] == 'ccr3'


class TestESDoc(object):
    def test_ESDocInit(self, mocker):
        mockInit = mocker.patch('esIndexer.ESDoc.initEntry')
        mockInit.return_value = 'testCCE'

        testDoc = ESDoc('testRec')

        assert testDoc.dbRec == 'testRec'
        assert testDoc.entry == 'testCCE'

    def test_ESDocCreateEntry(self):
        mockRec = MagicMock()
        mockRec.uuid = 'testUUID'

        testDoc = ESDoc(mockRec)

        assert testDoc.entry.meta.id == 'testUUID'
    
    def test_esDoc_index(self, mocker):
        mockEntry = MagicMock()
        mockInit = mocker.patch('esIndexer.ESDoc.initEntry')
        mockInit.return_value = mockEntry

        mockDB = MagicMock()
        mockDB.uuid = 'testUUID'
        mockDB.title = 'Test Title'

        mockReg = MagicMock()
        mockReg.regnum = 'T0000'
        mockReg.reg_date = '1999-12-31'
        mockDB.registrations = [mockReg]

        testDoc = ESDoc(mockDB)
        testDoc.indexEntry()

        assert testDoc.entry.uuid == 'testUUID'
        assert testDoc.entry.registrations[0].regnum == 'T0000'


class TestESDen(object):
    def test_ESRenInit(self, mocker):
        mockInit = mocker.patch('esIndexer.ESRen.initRenewal')
        mockInit.return_value = 'testCCR'

        testDoc = ESRen('testRen')

        assert testDoc.dbRen == 'testRen'
        assert testDoc.renewal == 'testCCR'

    def test_ESRenCreateRenewal(self):
        mockRec = MagicMock()
        mockRec.renewal_num = 'testRennum'

        testRen = ESRen(mockRec)

        assert testRen.renewal.meta.id == 'testRennum'
    
    def test_esRen_index(self, mocker):
        mockRenewal = MagicMock()
        mockInit = mocker.patch('esIndexer.ESRen.initRenewal')
        mockInit.return_value = mockRenewal

        mockDB = MagicMock()
        mockDB.uuid = 'testUUID'
        mockDB.renewal_num = 'R0000'

        mockCla = MagicMock()
        mockCla.name = 'Test Claimant'
        mockCla.claimant_type = 'T'
        mockDB.claimants = [mockCla]

        testRen = ESRen(mockDB)
        testRen.indexRen()

        assert testRen.renewal.uuid == 'testUUID'
        assert testRen.renewal.claimants[0].claim_type == 'T'
