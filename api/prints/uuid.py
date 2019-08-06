from flask import Blueprint, request, jsonify, make_response
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound

from api.db import db
from api.response import SingleResponse
from model.cce import CCE
from model.registration import Registration
from model.renewal import Renewal, RENEWAL_REG
from helpers.errors import LookupError

uuid = Blueprint('uuid', __name__, url_prefix='/')


@uuid.route('/registration/<uuid>', methods=['GET'])
def regQuery(uuid):
    err = None
    regRecord = SingleResponse('uuid', request.base_url)
    try:
        dbEntry = db.session.query(CCE)\
            .outerjoin(Registration, RENEWAL_REG, Renewal)\
            .filter(CCE.uuid == uuid).one()

        regRecord.result = SingleResponse.parseEntry(dbEntry, xml=True)
        regRecord.createDataBlock()
        status = 200
    except NoResultFound:
        status = 404
        err = LookupError('Unable to locate UUID {} in database'.format(uuid))
    except DataError:
        status = 500
        err = LookupError('Malformed UUID {} received'.format(uuid))
    return make_response(
        jsonify(regRecord.createResponse(status, err=err)),
        status
    )


@uuid.route('/renewal/<uuid>', methods=['GET'])
def renQuery(uuid):
    err = None
    renRecord = SingleResponse('uuid', request.base_url)
    try:
        dbRenewal = db.session.query(Renewal)\
            .outerjoin(RENEWAL_REG, Registration, CCE)\
            .filter(Renewal.uuid == uuid).one()

        renRecord.result = parseRetRenewal(dbRenewal)
        renRecord.createDataBlock()
        status = 200
    except NoResultFound:
        status = 404
        err = LookupError('Unable to locate UUID {} in database'.format(uuid))
    except DataError:
        status = 500
        err = LookupError('Malformed UUID {} received'.format(uuid))
    return make_response(
        jsonify(renRecord.createResponse(status, err=err)),
        status
    )


def parseRetRenewal(dbRenewal):
    if len(dbRenewal.registrations) == 0:
        return [SingleResponse.parseRenewal(dbRenewal, source=True)]

    registrations = []
    for reg in dbRenewal.registrations:
        registrations.append(SingleResponse.parseEntry(reg.cce, xml=True))
    return registrations
