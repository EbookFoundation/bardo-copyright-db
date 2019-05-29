
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Core(object):
    """A mixin for other SQLAlchemy ORM classes. Includes a date_craeted and
    date_updated field for all database tables."""
    date_created = Column(
        DateTime,
        default=datetime.now()
    )

    date_modified = Column(
        DateTime,
        default=datetime.now(),
        onupdate=datetime.now()
    )