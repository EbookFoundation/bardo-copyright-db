import os
import yaml
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
        return super(BaseDoc, self).save(**kwargs)

class BaseInner(InnerDoc):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        return super(BaseInner, self).save(**kwargs)


class Registration(BaseInner):
    regnum = Keyword()
    regdate = Date()


class Renewal(BaseDoc):
    rennum = Keyword()
    rendate = Date()
    title = Text(fields={'keyword': Keyword()})
    claimants = Text(multi=True)

    class Index:
        with open('config.yaml', 'r') as yamlFile:
            config = yaml.safe_load(yamlFile)
            name = config['ELASTICSEARCH']['ES_CCR_INDEX']


class CCE(BaseDoc):
    uuid = Keyword(store=True)
    title = Text(fields={'keyword': Keyword()})
    authors = Text(multi=True)
    publishers = Text(multi=True)
    lccns = Keyword(multi=True)

    registrations = Nested(Registration)

    class Index:
        with open('config.yaml', 'r') as yamlFile:
            config = yaml.safe_load(yamlFile)
            name = config['ELASTICSEARCH']['ES_CCE_INDEX']
