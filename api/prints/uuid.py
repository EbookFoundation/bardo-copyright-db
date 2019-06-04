from flask import (
    Blueprint, request, session, url_for, redirect, current_app, jsonify
)

from api.db import db
from api.elastic import elastic
from api.response import SingleResponse
from model.cce import CCE
from model.registration import Registration
from model.renewal import Renewal, RENEWAL_REG
from model.volume import Volume

uuid = Blueprint('uuid', __name__, url_prefix='/')


@uuid.route('/registration/<uuid>', methods=['GET'])
def regQuery(uuid):
    dbEntry = db.session.query(CCE)\
        .outerjoin(Registration, RENEWAL_REG, Renewal)\
        .filter(CCE.uuid == uuid).one()

    regRecord = SingleResponse('uuid', request.base_url)
    regRecord.result = SingleResponse.parseEntry(dbEntry, xml=True)
    regRecord.createDataBlock()
    return jsonify(regRecord.createResponse(200))


@uuid.route('/renewal/<uuid>', methods=['GET'])
def renQuery(uuid):
    dbRenewal = db.session.query(Renewal)\
        .outerjoin(RENEWAL_REG, Registration, CCE)\
        .filter(Renewal.uuid == uuid).one()

    renRecord = SingleResponse('uuid', request.base_url)
    renRecord.result = parseRetRenewal(dbRenewal)
    renRecord.createDataBlock()
    return jsonify(renRecord.createResponse(200))


def parseRetRenewal(dbRenewal):
    if len(dbRenewal.registrations) == 0:
        return [SingleResponse.parseRenewal(dbRenewal, source=True)]

    registrations = []
    for reg in dbRenewal.registrations:
        registrations.append(SingleResponse.parseEntry(reg.cce, xml=True))
    return registrations
