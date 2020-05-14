import math

class Response():
    def __init__(self, queryType, endpoint):
        self.type = queryType
        self.endpoint = endpoint
        self.data = None

    def createResponse(self, status, err=None):
        if status != 200:
            return {
                'status': status,
                'message': err.message
            }
        else:
            return {
                'status': status,
                'data': self.data
            }

    @classmethod
    def parseEntry(cls, dbEntry, xml=False):
        response = {
            'uuid': dbEntry.uuid,
            'title': dbEntry.title,
            'copies': dbEntry.copies,
            'description': dbEntry.description,
            'pub_date': dbEntry.pub_date_text,
            'copy_date': dbEntry.copy_date_text,
            'registrations': [
                {'number': r.regnum, 'date': r.reg_date_text}
                for r in dbEntry.registrations
            ],
            'authors': [ a.name for a in dbEntry.authors ],
            'publishers': [ p.name for p in dbEntry.publishers ],
            'source': {
                'url': dbEntry.volume.source,
                'series': dbEntry.volume.series,
                'year': dbEntry.volume.year,
                'part': dbEntry.volume.part,
                'page': dbEntry.page,
                'page_position': dbEntry.page_position
            }
        }
        response['renewals'] = [
            cls.parseRenewal(ren, source=xml)
            for reg in dbEntry.registrations
            for ren in reg.renewals
        ]

        if xml: response['xml'] = dbEntry.xml_sources[0].xml_source

        return response

    @classmethod
    def parseRenewal(cls, dbRenewal, source=False):
        renewal = {
            'type': 'renewal',
            'uuid': dbRenewal.uuid,
            'title': dbRenewal.title,
            'author': dbRenewal.author,
            'claimants': [ 
                {'name': c.name, 'type': c.claimant_type} 
                for c in dbRenewal.claimants 
            ],
            'new_matter': dbRenewal.new_matter,
            'renewal_num': dbRenewal.renewal_num,
            'renewal_date': dbRenewal.renewal_date_text,
            'notes': dbRenewal.notes,
            'volume': dbRenewal.volume,
            'part': dbRenewal.part,
            'number': dbRenewal.number,
            'page': dbRenewal.page
        }

        if source: renewal['source'] = dbRenewal.source

        return renewal


class SingleResponse(Response):
    def __init__(self, queryType, endpoint):
        super().__init__(queryType, endpoint)
        self.result = None
    
    def createDataBlock(self):
        self.data = self.result


class MultiResponse(Response):
    def __init__(self, queryType, total, endpoint, query, page, perPage):
        super().__init__(queryType, endpoint)
        self.total = total
        self.query = query
        self.page = page
        self.perPage = perPage
        self.results = []
    
    def addResult(self, result):
        self.results.append(result)
    
    def extendResults(self, results):
        self.results.extend(results)

    def createDataBlock(self):
        self.data = {
            'total': self.total,
            'query': self.createQuery(),
            'paging': self.createPaging(),
            'results': self.results
        }
    
    def createQuery(self):
        return {
            'endpoint': self.endpoint,
            'term': self.query
        }
    
    def createPaging(self):
        paging = {}
        if self.type == 'text':
            urlRoot = '{}?query={}'.format(self.endpoint, self.query)
        else:
            urlRoot = self.endpoint

        if self.page > 0:
            paging['first'] = '{}&page={}&per_page={}'.format(
                urlRoot,
                0,
                self.perPage
            )
        else:
            paging['first'] = None
        
        prevPage = self.page - 1
        if prevPage >= 0:
            paging['previous'] = '{}&page={}&per_page={}'.format(
                urlRoot,
                prevPage,
                self.perPage
            )
        else:
            paging['previous'] = None
        
        nextPage = self.page + 1
        if (nextPage * self.perPage) < self.total:
            paging['next'] = '{}&page={}&per_page={}'.format(
                urlRoot,
                nextPage,
                self.perPage
            )
        else:
            paging['next'] = None
        
        lastPage = math.ceil(((self.total - self.perPage) / self.perPage))
        if (
            self.page * self.perPage < self.total and 
            self.total > self.perPage
        ):
            paging['last'] = '{}&page={}&per_page={}'.format(
                urlRoot,
                lastPage,
                self.perPage
            )
        else:
            paging['last'] = None
        
        return paging
    
    @staticmethod
    def parsePaging(reqArgs):
        perPage = int(reqArgs.get('per_page', 10))
        page = int(reqArgs.get('page', 0))
        return page, perPage