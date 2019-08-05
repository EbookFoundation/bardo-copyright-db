import sys
from unittest.mock import MagicMock, call
from main import main, loadCCE, loadCCR, indexUpdates, parseArgs


class TestHandler(object):
    def test_main_plain(self, mocker):
        mockSession = mocker.patch('main.SessionManager')
        mockLoadCCE = mocker.patch('main.loadCCE')
        mockLoadCCR = mocker.patch('main.loadCCR')
        mockIndex = mocker.patch('main.indexUpdates')

        main()

        assert mockSession.called
        assert mockLoadCCE.called
        assert mockLoadCCR.called
        assert mockIndex.called

    def test_main_args(self, mocker):
        mockSession = mocker.patch('main.SessionManager')
        mockLoadCCE = mocker.patch('main.loadCCE')
        mockLoadCCR = mocker.patch('main.loadCCR')
        mockIndex = mocker.patch('main.indexUpdates')

        main(
            secondsAgo=10,
            year=1900,
            exclude='ccr',
            reinit=True
        )

        assert mockSession.called
        assert mockLoadCCE.called
        assert mockLoadCCR.not_called
        assert mockIndex.called

    def test_cce_load(self, mocker):
        mockReader = mocker.patch('main.CCEReader')
        mockCCE = MagicMock()
        mockReader.return_value = mockCCE

        loadCCE('manager', 10, None)

        assert mockReader.called_once_with('manager')
        assert mockCCE.loadYears.called_once_with(None)
        assert mockCCE.getYearFiles.called_once_with(10)
        assert mockCCE.importYearData.called

    def test_ccr_load(self, mocker):
        mockReader = mocker.patch('main.CCRReader')
        mockCCR = MagicMock()
        mockReader.return_value = mockCCR

        loadCCR('manager', 10, None)

        assert mockReader.called_once_with('manager')
        assert mockCCR.loadYears.called_once_with(None, 10)
        assert mockCCR.importYears.called

    def test_indexer(self, mocker):
        mockIndexer = mocker.patch('main.ESIndexer')
        mockInd = MagicMock()
        mockIndexer.return_value = mockInd

        indexUpdates('manager', 10)

        assert mockIndexer.called_once_with('manager', 10)
        assert mockInd.indexRecords.mock_calls == \
            [call(recType='cce'), call(recType='ccr')]

    def test_parseArgs_success(self, mocker):
        args = ['main', '--time', '10', '--year', '1900', '--exclude', 'ccr']
        mocker.patch.object(sys, 'argv', args)

        args = parseArgs()

        assert int(args.time) == 10
        assert int(args.year) == 1900
        assert args.exclude == 'ccr'
        assert args.REINITIALIZE is False
