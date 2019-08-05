from sqlalchemy.types import PickleType
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import relationship, backref
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    PrimaryKeyConstraint,
    Table
)

from model.core import Base, Core


@compiles(String, 'postgresql')
def compile_xml(type_, compiler, **kw):
    return 'XML'


ENTRY_XML = Table(
    'entry_xml',
    Base.metadata,
    Column('cce_id', Integer, ForeignKey('cce.id'), index=True),
    Column('xml_id', Integer, ForeignKey('xml.id'), index=True)
)

ERROR_XML = Table(
    'error_entry_xml',
    Base.metadata,
    Column('error_cce_id', Integer, ForeignKey('error_cce.id'), index=True),
    Column('xml_id', Integer, ForeignKey('xml.id'), index=True)
)


class XML(Core, Base):
    __tablename__ = 'xml'
    id = Column(Integer, primary_key=True)
    xml_source = Column(String)

    entry = relationship(
        'CCE',
        secondary=ENTRY_XML,
        backref='xml_sources',
        single_parent=True,
        cascade='all, delete-orphan'
    )

    error_entry = relationship(
        'ErrorCCE',
        secondary=ERROR_XML,
        backref='xml_sources',
        single_parent=True,
        cascade='all, delete-orphan'
    )
