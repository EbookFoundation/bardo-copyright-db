import os
from unittest.mock import mock_open, patch
from helpers.config import loadConfig


class TestConfigHelpers(object):
    def test_config_loader(self):
        testYAMLText = """
        TESTING:
          FIRST: STRING1
          SECOND: '10'

        EXTRA:
          VALUE: SOMETHING"""
        mockOpen = mock_open(read_data=testYAMLText)
        with patch('helpers.config.open', mockOpen):
            loadConfig()
            assert os.environ['FIRST'] == 'STRING1'
            assert os.environ['SECOND'] == '10'
            assert os.environ['VALUE'] == 'SOMETHING'
