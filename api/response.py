from datetime import datetime


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
            'pub_date': Response.formatDate(dbEntry.pub_date),
            'copy_date': Response.formatDate(dbEntry.copy_date),
            'registrations': [
                {
                    'number': r.regnum,
                    'date': Response.formatDate(r.reg_date)
                }
                for r in dbEntry.registrations
            ],
            'authors': [a.name for a in dbEntry.authors],
            'publishers': [p.name for p in dbEntry.publishers],
            'source': {
                'page': dbEntry.page,
                'page_position': dbEntry.page_position,
                'part': dbEntry.volume.part,
                'group': dbEntry.volume.group,
                'series': dbEntry.volume.series,
                'volume': dbEntry.volume.volume,
                'matter': dbEntry.volume.material,
                'url': dbEntry.volume.source,
                'year': dbEntry.volume.year
            },
            'lccns': [l.lccn for l in dbEntry.lccns]
        }

        if '3' in response['source']['series']:
            startNum = dbEntry.volume.start_number
            endNum = dbEntry.volume.end_number
            if startNum == endNum:
                outNum = startNum
            else:
                outNum = '{}-{}'.format(startNum, endNum)
            response['source']['number'] = outNum

        response['renewals'] = [
            cls.parseRenewal(ren, source=xml)
            for reg in dbEntry.registrations
            for ren in reg.renewals
        ]

        if xml:
            response['xml'] = dbEntry.xml_sources[0].xml_source

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
            'renewal_date': Response.formatDate(dbRenewal.renewal_date),
            'notes': dbRenewal.notes,
            'volume': dbRenewal.volume,
            'part': dbRenewal.part,
            'number': dbRenewal.number,
            'page': dbRenewal.page
        }

        if source:
            renewal['source'] = dbRenewal.source

        return renewal

    @staticmethod
    def formatDate(date):
        if date:
            return datetime.strftime(date, '%Y-%m-%d')

        return None


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

        lastPage = int((self.total - self.perPage) / self.perPage)
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
