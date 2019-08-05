from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
    Boolean
)

from model.core import Base, Core


class Author(Core, Base):
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False, index=True)
    primary = Column(Boolean, index=True)

    cce_id = Column(Integer, ForeignKey('cce.id'), index=True)

    def __repr__(self):
        return '<Author(name={}, primary={})>'.format(self.name, self.primary)
