from flask_sqlalchemy import SQLAlchemy

from model.cce import CCE
from model.registration import Registration
from model.renewal import Renewal, RENEWAL_REG
from model.volume import Volume


db = SQLAlchemy()


class QueryManager():
    def __init__(self, session):
        self.session = session
    
    def registrationQuery(self, uuid):
        return self.session.query(CCE)\
                .outerjoin(Registration, RENEWAL_REG, Renewal)\
                .filter(CCE.uuid == uuid).one()
    
    def renewalQuery(self, uuid):
        return self.session.query(Renewal)\
            .outerjoin(RENEWAL_REG, Registration, CCE)\
            .filter(Renewal.uuid == uuid).one()
    
    def orphanRenewalQuery(self, uuid):
        return self.session.query(Renewal).filter(Renewal.uuid == uuid).one()