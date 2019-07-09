from lxml import etree
import uuid
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    Boolean
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.exc import NoResultFound

from model.core import Base, Core

from model.xml import XML
from model.author import Author
from model.publisher import Publisher
from model.lccn import LCCN
from model.registration import Registration


class CCE(Core, Base):
    __tablename__ = 'cce'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=False, nullable=False, index=True)
    page = Column(Integer)
    page_position = Column(Integer)
    title = Column(Unicode, index=True)
    copies = Column(Unicode)
    description = Column(Unicode)
    new_matter = Column(Boolean)
    pub_date = Column(Date)
    pub_date_text = Column(Unicode)
    copy_date = Column(Date)
    copy_date_text = Column(Unicode)
    aff_date = Column(Date)
    aff_date_text = Column(Unicode)

    volume_id = Column(Integer, ForeignKey('volume.id'))

    registrations = relationship('Registration', backref='cce')
    lccns = relationship('LCCN', backref='cce', cascade='all, delete-orphan')
    authors = relationship('Author', backref='cce', cascade='all, delete-orphan')
    publishers = relationship('Publisher', backref='cce', cascade='all, delete-orphan')

    def __repr__(self):
        return '<CCE(regnums={}, uuid={}, title={})>'.format(self.registrations, self.uuid, self.title)

    def addRelationships(self, volume, xml, lccn=[], authors=[], publishers=[], registrations=[]):
        self.volume = volume
        self.addLCCN(lccn)
        self.addAuthor(authors)
        self.addPublisher(publishers)
        self.addRegistration(registrations)
        self.addXML(xml)
    
    def addLCCN(self, lccns):
        self.lccns = [ LCCN(lccn=lccn) for lccn in lccns ]

    def addXML(self, xml):
        xmlString = etree.tostring(xml, encoding='utf-8').decode()
        self.xml_sources.append(XML(xml_source=xmlString))

    def addAuthor(self, authors):
        for auth in authors:
            if auth[0] is None:
                print('No author name! for {}'.format(self.uuid))
                continue
            self.authors.append(Author(name=auth[0], primary=auth[1]))
    
    def addPublisher(self, publishers):
        for pub in publishers:
            if pub[0] is None:
                print('No publisher name! for {}'.format(self.uuid))
                continue
            claimant = True if pub[1] == 'yes' else False
            self.publishers.append(Publisher(name=pub[0], claimant=claimant))
    
    def addRegistration(self, registrations):
        self.registrations = [
            Registration(
                regnum=reg['regnum'],
                category=reg['category'],
                reg_date=reg['regDate'],
                reg_date_text=reg['regDateText']
            )
            for reg in registrations
        ]
    
    def updateRelationships(self, xml, lccn=[], authors=[], publishers=[], registrations=[]):
        self.addXML(xml)
        self.updateLCCN(lccn)
        self.updateAuthors(authors)
        self.updatePublishers(publishers)
        self.updateRegistrations(registrations)
    
    def updateLCCN(self, lccns):
        currentLCCNs = [ l.lccn for l in self.lccns ]
        if lccns != currentLCCNs:
            self.lccns = [
                l for l in self.lccns
                if l.lccn in list(set(currentLCCNs) & set(lccns))
            ]
            for new in list(set(lccns) - set(currentLCCNs)):
                self.lccns.append(LCCN(lccn=new))
    
    def updateAuthors(self, authors):
        currentAuthors = [ (a.name, a.primary) for a in self.authors ]
        newAuthors = filter(lambda x: x[0] is None, authors)
        if newAuthors != currentAuthors:
            self.authors = [
                a for a in self.authors
                if a.name in list(set(currentAuthors) & set(newAuthors))
            ]
            for new in list(set(newAuthors) - set(currentAuthors)):
                self.authors.append(Author(name=new[0], primary=new[1]))
    
    def updatePublishers(self, publishers):
        currentPublishers = [ (a.name, a.claimant) for a in self.publishers ]
        newPublishers = [
            (p[0], True if p[1] == 'yes' else False)
            for p in filter(lambda x: x[0] is None, publishers)
        ]
        if newPublishers != currentPublishers:
            self.authors = [
                a for a in self.authors
                if a.name in list(set(currentPublishers) & set(newPublishers))
            ]
            for new in list(set(newPublishers) - set(currentPublishers)):
                self.publishers.append(Publisher(name=new[0], claimant=new[1]))
    
    def updateRegistrations(self, registrations):
        existingRegs = [
            self.updateReg(r, registrations) for r in self.registrations
            if r.regnum in [ n['regnum'] for n in registrations ]
        ]
        newRegs = [
            r for r in registrations
            if r['regnum'] not in [ n.regnum for n in existingRegs ]
        ]
        self.registrations = existingRegs + [
            Registration(
                regnum=reg['regnum'],
                category=reg['category'],
                reg_date=reg['regDate'],
                reg_date_text=reg['regDateText']
            )
            for reg in newRegs
        ]
    
    def updateReg(self, reg, registrations):
        newReg = CCE.getReg(reg.regnum, registrations)
        if newReg: reg.update(newReg)
        return reg
    
    def setParentCCE(self, parentID):
        self.parent_cce_id = parentID

    @staticmethod
    def getReg(regnum, newRegs):
        for new in newRegs:
            if regnum == new['regnum']: return new
