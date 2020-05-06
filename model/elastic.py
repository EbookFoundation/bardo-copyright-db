import os
import yaml
import pprint
from elasticsearch_dsl import (
    Index,
    Document,
    Keyword,
    Text,
    Date,
    InnerDoc,
    Nested
)


class BaseDoc(Document):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        return super(BaseDoc, self).save(** kwargs)

class BaseInner(InnerDoc):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        return super(BaseInner, self).save(** kwargs)


class Registration(BaseInner):
    regnum = Keyword()
    regdate = Date()


class Claimant(BaseInner):
    name = Text(fields={'keyword': Keyword()})
    claim_type = Keyword()


class Renewal(BaseDoc):
    uuid = Keyword(store=True)
    rennum = Keyword()
    rendate = Date()
    title = Text(fields={'keyword': Keyword()})
    authors = Text()

    claimants = Nested(Claimant)
    # pprint.pprint(dict(os.environ), width = 1) 
    class Index:
        name = os.environ['ES_CCR_INDEX']


class CCE(BaseDoc):
    uuid = Keyword(store=True)
    title = Text(fields={'keyword': Keyword()})
    authors = Text(multi=True)
    publishers = Text(multi=True)
    lccns = Keyword(multi=True)
    registrations = Nested(Registration)

    class Index:
        name = os.environ['ES_CCE_INDEX']
