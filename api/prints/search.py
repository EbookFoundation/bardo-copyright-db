from flask import Blueprint, request, jsonify, make_response
from sqlalchemy.orm.exc import NoResultFound

from api.db import db, QueryManager
from api.elastic import elastic
from api.response import MultiResponse

search = Blueprint('search', __name__, url_prefix='/search')


@search.route('/fulltext', methods=['GET'])
def fullTextQuery():
    queryText = request.args.get('query', '')
    sourceReturn = request.args.get('source', False)
    page, perPage = MultiResponse.parsePaging(request.args)
    matchingDocs = elastic.query_fulltext(
        queryText,
        page=page,
        perPage=perPage
    )
    textResponse = MultiResponse(
        'text',
        matchingDocs.hits.total,
        request.base_url,
        queryText,
        page,
        perPage
    )
    qManager = QueryManager(db.session)
    for entry in matchingDocs:
        if entry.meta.index == 'cce':
            dbEntry = qManager.registrationQuery(entry.uuid)
            textResponse.addResult(MultiResponse.parseEntry(
                dbEntry,
                xml=sourceReturn
            ))
        else:
            try:
                dbRenewal = qManager.renewalQuery(entry.uuid)
                textResponse.addResult(MultiResponse.parseRenewal(
                    dbRenewal,
                    source=sourceReturn
                ))
            except NoResultFound:
                dbRenewal = qManager.orphanRenewalQuery(entry.uuid)
                textResponse.addResult(MultiResponse.parseRenewal(
                    dbRenewal,
                    source=sourceReturn
                ))

    textResponse.createDataBlock()
    return make_response(jsonify(textResponse.createResponse(200)), 200)


@search.route('/registration/<regnum>', methods=['GET'])
def regQuery(regnum):
    page, perPage = MultiResponse.parsePaging(request.args)
    sourceReturn = request.args.get('source', False)
    matchingDocs = elastic.query_regnum(regnum, page=page, perPage=perPage)
    regResponse = MultiResponse(
        'number',
        matchingDocs.hits.total,
        request.base_url,
        regnum,
        page,
        perPage
    )
    qManager = QueryManager(db.session)
    for entry in matchingDocs:
        dbEntry = qManager.registrationQuery(entry.uuid)
        regResponse.addResult(MultiResponse.parseEntry(
            dbEntry,
            xml=sourceReturn
        ))

    regResponse.createDataBlock()
    return make_response(jsonify(regResponse.createResponse(200)), 200)


@search.route('/renewal/<rennum>', methods=['GET'])
def renQuery(rennum):
    page, perPage = MultiResponse.parsePaging(request.args)
    sourceReturn = request.args.get('source', False)
    matchingDocs = elastic.query_rennum(rennum, page=page, perPage=perPage)
    renResponse = MultiResponse(
        'number',
        matchingDocs.hits.total,
        request.base_url,
        rennum,
        page,
        perPage
    )
    qManager = QueryManager(db.session)
    for entry in matchingDocs:
        dbRenewal = qManager.renewalQuery(entry.uuid)
        renResponse.extendResults(parseRetRenewal(
            dbRenewal,
            source=sourceReturn
        ))

    renResponse.createDataBlock()
    return make_response(jsonify(renResponse.createResponse(200)), 200)


def parseRetRenewal(dbRenewal):
    if len(dbRenewal.registrations) == 0:
        return [MultiResponse.parseRenewal(dbRenewal)]

    registrations = []
    for reg in dbRenewal.registrations:
        registrations.append(MultiResponse.parseEntry(reg.cce))
    return registrations
