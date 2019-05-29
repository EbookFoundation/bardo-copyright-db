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


class Registration(Core, Base):
    __tablename__ = 'registration'
    id = Column(Integer, primary_key=True)
    regnum = Column(Unicode, unique=False, nullable=False, index=True)
    category = Column(Unicode)
    reg_date = Column(Date)
    reg_date_text = Column(Unicode)

    cce_id = Column(Integer, ForeignKey('cce.id'), index=True)

    def __repr__(self):
        return '<Registration(regnum={}, date={})>'.format(self.regnum, self.reg_date_text)

    def update(self, newReg):
        for key, value in newReg.items():
            setattr(self, key, value)
