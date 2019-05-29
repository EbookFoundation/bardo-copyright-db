import uuid
import json
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    PrimaryKeyConstraint
)

from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.exc import NoResultFound

from model.core import Base, Core

class Volume(Core, Base):
    __tablename__ = 'volume'
    id = Column(Integer, primary_key=True)
    source = Column(Unicode)
    status = Column(Unicode)
    series = Column(Unicode)
    volume = Column(Integer)
    year = Column(Integer)
    part = Column(Unicode)
    group = Column(Integer)
    material = Column(Unicode)
    start_number = Column(Integer)
    end_number = Column(Integer)

    entries = relationship('CCE', backref='volume')
    error_entries = relationship('ErrorCCE', backref='volume')

    def __repr__(self):
        return '<Volume(series={}, volume={}, year={})>'.format(self.series, self.volume, self.year)