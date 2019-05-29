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


class Publisher(Core, Base):
    __tablename__ = 'publisher'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False, index=True)
    claimant = Column(Boolean, index=True)

    cce_id = Column(Integer, ForeignKey('cce.id'), index=True)
    
    def __repr__(self):
        return '<Publisher(name={}, claimant={})>'.format(self.name, self.claimant)