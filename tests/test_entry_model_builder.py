from datetime import datetime

from builder import CCEFile


class TestEntryBuilder(object):
    def test_dateReader(self):
        outDate = CCEFile.dateReader(('2019-01-01', 'Jan. 1, 2019'))
        assert outDate == datetime(2019, 1, 1)

    def test_dateReader_text(self):
        outDate = CCEFile.dateReader(('2019-01-01', 'Jan. 1, 2019'), text=True)
        assert outDate == 'Jan. 1, 2019'

    def test_dateReader_error(self, mocker):
        mockParser = mocker.patch('builder.parser.parse')
        mockParser.side_effect = ValueError

        outDate = CCEFile.dateReader('2020')
        assert outDate is None

    def test_fetchDateValue(self):
        outDate = CCEFile.fetchDateValue([])
        assert outDate is None

    def test_fetchDateValue_single(self, mocker):
        mockReader = mocker.patch('builder.CCEFile.dateReader')
        mockReader.return_value = True

        mockDate = ('2019-01-01', 'Jan. 1')
        outDate = CCEFile.fetchDateValue([mockDate])

        mockReader.assert_called_once_with(mockDate, False)
        assert outDate

    def test_fetchDateValue_multiple(self, mocker):
        mockReader = mocker.patch('builder.CCEFile.dateReader')
        mockReader.return_value = True

        firstDate = ('2019', '2019')
        secondDate = ('2019-01', 'January')
        thirdDate = ('2019-01-01', 'Jan. 1')
        outDate = CCEFile.fetchDateValue([firstDate, secondDate, thirdDate])

        mockReader.assert_called_once_with(thirdDate, False)
        assert outDate
