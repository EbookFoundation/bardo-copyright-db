from unittest.mock import MagicMock, DEFAULT
import pytest

from model.cce import CCE


class TestModelCCE(object):
    @pytest.fixture
    def mockCCE(self):
        return CCE()

    def test_cceCreate(self, mockCCE):
        mockCCE.uuid = 'testUUID'
        mockCCE.title = 'Testing'
        mockReg = MagicMock()
        mockCCE.registrations = [mockReg]

        assert str(mockCCE) == '<CCE(regnums=[{}], uuid={}, title={})>'.format(
            str(mockReg), 'testUUID', 'Testing'
        )

    def test_addRelationships(self, mocker, mockCCE):
        addMocks = mocker.patch.multiple('model.cce.CCE', addLCCN=DEFAULT,
                                         addAuthor=DEFAULT,
                                         addPublisher=DEFAULT,
                                         addRegistration=DEFAULT,
                                         addXML=DEFAULT)

        mockCCE = CCE()
        mockVol = MagicMock()
        mockVol.name = 'testVol'
        mockCCE.addRelationships(
            mockVol,
            '<xml>',
            lccn=[1, 2, 3],
            authors=['author1'],
            publishers=['pub1'],
            registrations=['reg1']
        )

        assert mockCCE.volume.name == 'testVol'
        assert addMocks['addAuthor'].called_once_with(['author1'])
        assert addMocks['addPublisher'].called_once_with(['pub1'])
        assert addMocks['addRegistration'].called_once_with(['reg1'])
        assert addMocks['addLCCN'].called_once_with([1, 2, 3])

    def test_addLCCN(self, mocker, mockCCE):
        mockLCCN = mocker.patch('model.cce.LCCN')
        mockLCs = []
        for i in range(1, 3):
            lcMock = MagicMock()
            lcMock.name = 'lccn{}'.format(i)
            mockLCs.append(lcMock)
        mockLCCN.side_effect = mockLCs

        mockCCE.addLCCN([1, 2])

        assert mockCCE.lccns[1].name == 'lccn2'

    def test_updatePublishers(self, mockCCE):
        mockPub = MagicMock()
        mockPub.name = 'Removed, Name'
        mockPub.claimant = True
        mockCCE.publishers.append(mockPub)
        newPublishers = [
            (None, 'yes'),
            ('Test, Testing', 'yes'),
            ('Removed, Name', 'yes')
        ]

        mockCCE.updatePublishers(newPublishers)
        assert len(list(mockCCE.publishers)) == 2
        assert list(mockCCE.publishers)[1].name == 'Test, Testing'
