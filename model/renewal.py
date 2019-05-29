import uuid
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    Boolean,
    Table
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.exc import NoResultFound

from model.core import Base, Core
from model.renClaimant import RenClaimant


RENEWAL_REG = Table(
    'renewal_registration',
    Base.metadata,
    Column('renewal_id', Integer, ForeignKey('renewal.id'), index=True),
    Column('registration_id', Integer, ForeignKey('registration.id'), index=True)
)


class Renewal(Core, Base):
    __tablename__ = 'renewal'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=False, nullable=False, index=True)
    volume = Column(Integer)
    part = Column(Unicode)
    number = Column(Integer)
    page = Column(Integer)
    author = Column(Unicode)
    title = Column(Unicode, index=True)
    reg_data = Column(Unicode)
    renewal_num = Column(Unicode)
    renewal_date = Column(Date)
    renewal_date_text = Column(Unicode)
    new_matter = Column(Unicode)
    see_also_regs = Column(Unicode)
    see_also_rens = Column(Unicode)
    notes = Column(Unicode)
    source = Column(Unicode)
    orphan = Column(Boolean, default=False)

    registrations = relationship(
        'Registration',
        secondary=RENEWAL_REG,
        backref='renewals'
    )

    def __repr__(self):
        return '<CCR(regs={}, uuid={}, title={})>'.format(self.registrations, self.uuid, self.title)
    
    def addClaimants(self, claimants):
        if claimants: 
            for claim in claimants.split('||'):
                cParts = claim.split('|')
                self.claimants.append(
                    RenClaimant(name=cParts[0], claimant_type=cParts[1])
                )
    
    def updateClaimants(self, claimants):
        addClaims = [
            claim.split('|') for claim in claimants.split('||')
        ]
        existingClaims = [ 
            c for c in self.claimants
            if c.name in [ a[0] for a in addClaims ]
        ]
        newClaims = [ 
            c for c in addClaims
            if c[0] not in [ e.name for e in existingClaims ]
            and c[0] != ''
        ]
        
        self.claimants = existingClaims + [
            RenClaimant(
                name=claim[0],
                claimant_type=claim[1]
            )
            for claim in newClaims
        ]
