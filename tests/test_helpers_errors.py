from helpers.errors import DataError


class TestErrorHelpers(object):
    def test_create_DataError(self):
        newDataErr = DataError('testing', source='pytest')
        assert newDataErr.message == 'testing'
        assert newDataErr.source == 'pytest'
