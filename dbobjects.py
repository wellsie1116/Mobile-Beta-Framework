import datetime
import hashlib
import uuid

import sqlalchemy
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime, Boolean, Text, Sequence, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref


Base = declarative_base()


def initDatabase(connection):
    engine = sqlalchemy.create_engine(connection)

    global session
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)


def guid():
    return str(uuid.uuid4())


def secure_hash(string):
    return unicode(hashlib.sha256(string).hexdigest()) if string is not None else None


def verify_hash(string, hash_code):
    return secure_hash(string) == hash_code


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, Sequence('user_id_sequence'), primary_key=True)
    name = Column(String(length=10240))
    email = Column(String(length=10240), unique=True)
    created = Column(DateTime)
    verified = Column(Boolean)
    verification_code = Column(String(length=36))
    name_change_code = Column(String(length=36))

    clear_verification_code = None
    clear_name_change_code = None

    def __init__(self, name=None, email=None, devices=[]):
        self.name = name
        self.email = email
        self.created = datetime.datetime.now()
        self.verified = False
        self.verification_code = guid()
        self.name_change_code = guid()
        self.devices = devices

    def verify(self, verification_code):
        if verification_code == self.verification_code and not self.verified:
            self.verified = True
            return True
        elif self.verified:
            return True
        return False

    def changeName(self, name_change_code, name):
        if name_change_code == self.name_change_code:
            self.name = name
            return True
        return False

    @classmethod
    def all(self):
        return session.query(User).all()

    @classmethod
    def from_email(self, email):
        return session.query(User).filter(User.email == email).first()

    @classmethod
    def from_verification_code(self, code):
        return session.query(User).filter(User.verification_code == code).first()

    @classmethod
    def from_name_change_code(self, code):
        return session.query(User).filter(User.name_change_code == code).first()

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, Sequence('device_id_sequence'), primary_key=True)
    _unique_identifier = Column(String(length=64), name='unique_identifier_hashed', nullable=False)
    operating_system = Column(String(length=10240))
    model = Column(String(length=10240))
    additional_info = Column(Text(length=10240))
    verified = Column(Boolean, nullable=False)
    verification_code = Column(String(length=36), nullable=False)
    auth_token = Column(String(length=36), nullable=False)

    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', backref='devices')
    carrier_id = Column(Integer, ForeignKey('carriers.id'))
    carrier = relationship('Carrier', backref='devices')
    current_build_id = Column(Integer, ForeignKey('builds.id'), nullable=False)
    current_build = relationship('Build', backref='active_devices')
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False)
    platform = relationship('Platform', backref='active_devices')

    def __init__(self, unique_identifier=None, operating_system=None, additional_info=None,
                 model=None, owner=None, carrier=None, current_build=None, platform=None):
        self.unique_identifier = unique_identifier
        self.operating_system = operating_system
        self.additional_info = additional_info
        self.model = model
        self.verified = False
        self.verification_code = guid()
        self.auth_token = guid()
        self.owner = owner
        self.carrier = carrier
        self.current_build = current_build
        self.platform = platform

    def _get_unique_identifier(self):
        return self._clear_unique_identifier

    def _set_unique_identifier(self, unique_identifier):
        self._clear_unique_identifier = unique_identifier
        self._unique_identifier = secure_hash(unique_identifier)

    unique_identifier = property(_get_unique_identifier, _set_unique_identifier)

    def verify(self, verification_code):
        if verification_code == self.verification_code and not self.verified:
            self.verified = True
            return True
        elif self.verified:
            return True
        return False

    @classmethod
    def all(self):
        return session.query(Device).all()

    @classmethod
    def from_unique_identifier(self, unique_identifier):
        hashed = secure_hash(unique_identifier)
        return session.query(Device).filter(Device._unique_identifier == hashed).first()

    @classmethod
    def from_auth_token(self, auth_token):
        return session.query(Device).filter(Device.auth_token == auth_token).first()

    @classmethod
    def from_verification_code(self, code):
        return session.query(Device).filter(Device.verification_code == code).first()

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()


class Platform(Base):
    __tablename__ = 'platforms'

    id = Column(Integer, Sequence('platform_id_sequence'), primary_key=True)
    name = Column(String(length=10240), nullable=False)
    identifier = Column(String(length=10240), nullable=False)
    owner_email = Column(String(length=10240), nullable=False)
    publishing_key = Column(String(length=36), nullable=False)

    def __init__(self, name=None, identifier=None, owner_email=None):
        self.name = name
        self.identifier = identifier
        self.owner_email = owner_email
        self.publishing_key = guid()

    @classmethod
    def all(self):
        return session.query(Platform).all()

    @classmethod
    def from_publishing_key(self, key):
        return session.query(Platform).filter(Platform.publishing_key == key.strip().lower()).first()

    @classmethod
    def from_identifier(self, identifier):
        return session.query(Platform).filter(Platform.identifier == identifier.strip().lower()).first()

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()


class Build(Base):
    __tablename__ = 'builds'

    id = Column(Integer, Sequence('build_id_sequence'), primary_key=True)
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False)
    platform = relationship('Platform', backref='builds')
    build_number = Column(String(length=10240), nullable=False)
    published = Column(DateTime, nullable=False)
    classification = Column(Enum('rolling', 'nightly', 'beta', 'official'), nullable=False)
    view_url = Column(String(length=10240))
    download_url = Column(String(length=10240))

    def __init__(self, platform=None, build_number=None, classification=None, view_url=None, download_url=None):
        self.platform = platform
        self.build_number = build_number
        self.published = datetime.datetime.now()
        self.classification = classification
        self.view_url = view_url
        self.download_url = download_url

    @classmethod
    def all(self):
        return session.query(Build).all()

    @classmethod
    def from_number_and_platform(self, number, platform):
        return session.query(Build).filter(Build.build_number == number and Build.platform_id == platform.id).first()

    @classmethod
    def latest_for_platform(self, platform):
        official = session.query(Build).filter(Build.platform_id == platform.id and Build.classification == 'official').first()
        beta = session.query(Build).filter(Build.platform_id == platform.id and Build.classification == 'beta').first()
        nightly = session.query(Build).filter(Build.platform_id == platform.id and Build.classification == 'nightly').first()
        rolling = session.query(Build).filter(Build.platform_id == platform.id and Build.classification == 'rolling').first()
        return rolling, nightly, beta, official

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()


class Carrier(Base):
    __tablename__ = 'carriers'

    id = Column(Integer, Sequence('carrier_id_sequence'), primary_key=True)
    name = Column(String(length=10240), nullable=False)
    identifier = Column(String(length=10240), nullable=False)

    @classmethod
    def all(self):
        return session.query(Carrier).all()

    @classmethod
    def from_identifier(self, identifier):
        pass

    @classmethod
    def from_string(self, string):
        pass

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()


class Update(Base):
    __tablename__ = 'updates'

    id = Column(Integer, Sequence('update_id_sequence'), primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    device = relationship('Device', backref='updates')
    to_build_id = Column(Integer, ForeignKey('builds.id'), nullable=False)
    to_build = relationship('Build')
    time = Column(DateTime, nullable=False)

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()


class TestExecution(Base):
    __tablename__ = 'test_executions'

    id = Column(Integer, Sequence('test_execution_id_sequence'), primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    device = relationship('Device', backref='test_executions')
    build_id = Column(Integer, ForeignKey('builds.id'), nullable=False)
    build = relationship('Build', backref='test_executions')
    time = Column(DateTime, nullable=False)
    content = Column(Text(length=10240))
    passed = Column(Boolean, nullable=False)

    @classmethod
    def all(self):
        return session.query(TestExecution).all()

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()


class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, Sequence('feedback_id_sequence'), primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    device = relationship('Device', backref='feedback')
    build_id = Column(Integer, ForeignKey('builds.id'), nullable=False)
    build = relationship('Build', backref='feedback')
    time = Column(DateTime, nullable=False)
    content = Column(Text(length=10240), nullable=False)

    def save(self):
        if self not in session:
            session.add(self)
        session.commit()

    def destroy(self):
        session.delete(self)
        session.commit()
