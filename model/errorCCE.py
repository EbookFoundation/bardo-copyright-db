from lxml import etree
import uuid
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    Boolean
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.exc import NoResultFound

from model.core import Base, Core

from model.author import Author
from model.publisher import Publisher
from model.lccn import LCCN


class ErrorCCE(Core, Base):
    __tablename__ = 'error_cce'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=False, nullable=False, index=True)
    regnum = Column(Unicode, unique=False, nullable=True)
    page = Column(Integer)
    page_position = Column(Integer)
    reason = Column(Unicode)

    volume_id = Column(Integer, ForeignKey('volume.id'))

    def __repr__(self):
        return '<ErrorCCE(regnum={}, uuid={})>'.format(self.regnum, self.uuid)

    def addXML(self, xml):
        xmlString = etree.tostring(xml, encoding='utf-8').decode()
        self.xml_sources.append(XML(xml_source=xmlString))