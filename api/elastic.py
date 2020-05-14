from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

class Elastic():
    def __init__(self):
        self.client = Elasticsearch()
    
    def init_app(self, app):
        try:
            self.client = Elasticsearch(hosts=app.config['ELASTICSEARCH_INDEX_URI'])
        except ConnectionError as err:
            print('Failed to connect to ElasticSearch instance')
            raise err
    
    def create_search(self, index):
        s = Search(using=self.client, index=index)
        return s

    def query_regnum(self, regnum, page=0, perPage=10):
        startPos, endPos = Elastic.getFromSize(page, perPage)
        search = self.create_search('cce')
        nestedQ = Q('term', registrations__regnum=regnum)
        nestedSearch = search.query('nested', path='registrations', query=nestedQ)[startPos:endPos]
        return nestedSearch.execute()
    
    def query_rennum(self, rennum, page=0, perPage=10):
        startPos, endPos = Elastic.getFromSize(page, perPage)
        search = self.create_search('ccr')
        renewalSearch = search.query('term', rennum=rennum)[startPos:endPos]
        return renewalSearch.execute()
    
    def query_fulltext(self, queryText, page=0, perPage=10):
        startPos, endPos = Elastic.getFromSize(page, perPage)
        search = self.create_search('cce,ccr')
        renewalSearch = search.query('query_string', query=queryText)[startPos:endPos]
        return renewalSearch.execute()

    #New Query Types
    def query_title(self, queryText,page=0, perPage=10):
        startPos, endPos = Elastic.getFromSize(page, perPage)
        search = self.create_search('cce,ccr')
        titleSearch = search.query('match', title=queryText)[startPos:endPos]
        return titleSearch.execute()

    def query_author(self, queryText,page=0, perPage=10):
        startPos, endPos = Elastic.getFromSize(page, perPage)
        search = self.create_search('cce,ccr')
        titleSearch = search.query('match', authors=queryText)[startPos:endPos]
        return titleSearch.execute()


    # If query is given for publisher field, don't check renewals?
    def query_multifields(self, params, page=0, perPage=10):
        startPos, endPos = Elastic.getFromSize(page, perPage)
        if "publishers" in params:
            search = self.create_search('cce')
            search = search.query('match', publishers=params["publishers"])
        else:
            search = self.create_search('cce,ccr')
        if "title" in params:
            search = search.query('match', title=params['title'])
        if "authors" in params:
            search = search.query('match', authors=params['authors'])
        titleSearch = search[startPos:endPos]
        return titleSearch.execute()

    
    @staticmethod
    def getFromSize(page, perPage):
        startPos = page * perPage
        endPos = startPos + perPage
        return startPos, endPos

elastic = Elastic()
