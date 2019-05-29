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


class LCCN(Core, Base):
    __tablename__ = 'lccn'
    id = Column(Integer, primary_key=True)
    lccn = Column(Unicode, nullable=False, index=True)

    cce_id = Column(Integer, ForeignKey('cce.id'), index=True)
    