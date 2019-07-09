from datetime import datetime
from unittest.mock import MagicMock, call
import pytest
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

    def test_indexerInit(self, mocker, setEnvVars):
        mockConfig = mocker.patch('esIndexer.configure_mappers')
        mockConn = mocker.patch('esIndexer.ESIndexer.createElasticConnection')
        mockCreate = mocker.patch('esIndexer.ESIndexer.createIndex')
        mockManager = MagicMock()
        mockManager.session = 'session'

        testIndexer = ESIndexer(mockManager, 10)

        assert testIndexer.cce_index == 'test_cce'
        assert testIndexer.ccr_index == 'test_ccr'
        assert testIndexer.session == 'session'
        assert mockConn.called
        assert mockCreate.called
        assert mockConfig.called

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

    #def test_index_create(self, mocker, monkeypatch, setEnvVars):
    #    mockConfig = mocker.patch('esIndexer.configure_mappers')
    #    mockConn = mocker.patch('esIndexer.ESIndexer.createElasticConnection')
    #    mockCCE = mocker.patch('esIndexer.CCE')
    #    mockCCR = mocker.patch('esIndexer.Renewal')
    #    mockManager = MagicMock()
    #    mockManager.session = 'session'

    #    mockClient = MagicMock()
    #    mockClient.indices.exists.side_effect = [False, False]

    #    testIndexer = ESIndexer(mockManager, 10)

    #    assert testIndexer.cce_index == 'test_cce'
    #    assert testIndexer.ccr_index == 'test_ccr'
    #    assert testIndexer.session == 'session'
    #    assert mockConn.called
    #    assert mockConfig.called
    #    assert mockCCE.init.called
    #    assert mockCCR.init.called
