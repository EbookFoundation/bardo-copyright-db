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


class RenClaimant(Core, Base):
    __tablename__ = 'renewal_claimant'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False, index=True)
    claimant_type = Column(Unicode, index=True)

    renewal_id = Column(Integer, ForeignKey('renewal.id'))

    renewal = relationship('Renewal', backref='claimants')
    
    def __repr__(self):
        return '<Claimant(name={}, type={})>'.format(self.name, self.claimant_type)