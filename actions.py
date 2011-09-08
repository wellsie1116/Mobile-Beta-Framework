#!/usr/bin/env python

"""
actions.py: interactions for the RHIT Mobile beta program
"""

import cgi
import ConfigParser
import datetime
import hashlib
import json
import os
import smtplib
import time
import types
import urllib
import uuid

import sqlalchemy
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime, Boolean, Text, Sequence, Enum
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

####### DEBUG #######
import cgitb
cgitb.enable()
#####################

def initDatabase():
    config = ConfigParser.ConfigParser()
    config_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_dir, 'config.cfg')
    config.read(config_path)
    
    db_connection = config.get('Database', 'connection')

    global Base
    global engine
    global session

    Base = declarative_base()

    engine = sqlalchemy.create_engine(db_connection)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

initDatabase()

"""
Various helper functions
"""
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
        pass

    @classmethod
    def from_identifier(self, identifier):
        pass

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
        pass

    @classmethod
    def latest_for_platform(self, platform):
        pass

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

Base.metadata.create_all(engine)

class RequestHandler(object):

    def parse_and_execute(self, form):
        actions = {'register': self.register,
                   'verifyUser': self.verifyUser,
                   'verifyDevice': self.verifyDevice,
                   'changeUserName': self.changeUserName,
                   'submitFeedback': self.submitFeedback,
                   'submitTestResults': self.submitTestResults,
                   'notifyOfUpdate': self.notifyOfUpdate,
                   'getLatestBuilds': self.getLatestBuilds,
                   'publishBuild': self.publishBuild,
                   'renewPublishingKey': self.renewPublishingKey}
        if 'action' not in form:
            return self.error('You must specify an action')
        elif form.getvalue('action') not in actions:
            return self.error('Invalid action: %s' % form.getvalue('action'))
        else:
            actions[form.getvalue('action')](form=form)
    
    def error(self, *args):
        return 'Content-Type: text/plain\n\n' + json.dumps({'success': False, 'errors': args})
    
    def success(self, vals={}):
        return 'Content-Type: text/plain\n\n' + json.dumps(dict(vals.items() + {'success': True}.items()))
    
    def html(self, content):
        return ('Content-Type: text/html\n\n'
                '<!DOCTYPE html><html><head></head><body>%s</body></html>' % content)
    
    
    def register(form, *args, **kw):
        errors = []

        if 'email' not in form:
            errors.append('Email address is required')

        if 'deviceIdentifier' not in form:
            errors.append('Device identifier is required')

        if 'platform' not in form:
            errors.append('Platform is required')

        if 'buildNumber' not in form:
            errors.append('Build number is required')

        if len(errors) > 0:
            return self.error(*errors)

        testing = form.getvalue('test') is not None
        results = {}
        email = form.getvalue('email')
        name = form.getvalue('name')
        device_id = form.getvalue('deviceIdentifier')
        user = User.from_email(email)
        device = Device.from_unique_identifier(device_id)
        platform = Platform.from_identifier(form.getvalue('platform'))
        carrier = Carrier.from_string(form.getvalue('carrier'))
        os_info = form.getvalue('OSInfo')
        model = form.getvalue('model')
        build_number = form.getvalue('buildNumber')

        if platform is None:
            return self.error('Invalid platform')

        build = Build.from_build_number_and_platform(build_number, platform)

        if build is None:
            return self.error('Invalid build number')

        if user is None or testing:
            results['newUser'] = True
            user = User(new=True)

            if testing:
                user.email = uuid.uuid4()
            else:
                user.email = email

            user.name = name
            user.save()
            base_url = 'http://mobile.csse.rose-hulman.edu/beta/actions.cgi?'
            verify_args = {'action': 'verifyUser',
                           'verificationCode': user.verification_code}
            name_change_args = {'action': 'changeUserName',
                                'nameChangeCode': user.name_change_code}
            verify_url = base_url + urllib.urlencode(verify_args)
            name_change_url = base_url + urllib.urlencode(name_change_args)
            msg = ('Thank you for registering for the RHIT Mobile Beta program! '
                    'Please verify your email and devices by clicking this link:'
                    '\n\n%s\n\nThanks!\nThe RHIT Mobile Team') % verify_url
            send_email(email, platform.owner_email, 'Verify your email and devices', msg, testing) 
            name_msg = ('A new user has registered for your platform\'s beta '
                        'program:\n\nName: %s\nEmail: %s\n\nTo change this user\'s '
                        'name, use the following link:\n\n%s\n\nLet me know if '
                        'something breaks\nJimmy') % (user.name, user.email, name_change_url)
            send_email(platform.owner_email, 'theisje@rose-hulman.edu', 'New user %s registered' % user.email, name_msg, testing)
        else:
            results['newUser'] = False

        if device is None:
            results['newDevice'] = True
            device = Device(new=True)
            device.unique_identifier = device_id
            device.user = user
            device.platform = platform
            device.carrier = carrier
            device.os_info = os_info
            device.model = model
            device.current_build = build
            device.save()
            if not results['newUser']:
                base_url = 'http://mobile.csse.rose-hulman.edu/beta/actions.cgi?'
                verify_args = {'action': 'verifyDevice',
                               'verificationCode': device.verification_code}
                deviceUrl = base_url + urllib.urlencode(verify_args)
                msg = ('Thank you for registering another device for the RHIT Mobile '
                       'Beta Program! Please verify this new device by clicking the '
                       'link below.\n\nDevice: %s (%s)\n\n%s\n\nThanks!\nThe '
                       'RHIT Mobile Team') % (device.model, device.os_info, deviceUrl)
                send_email(email, platform.owner_email, 'Verify your new device', msg, testing)
            results['authToken'] = device.auth_token
        else:
            results['newDevice'] = False

            if device.user.email != email:
                return self.error('Device already registered to another user')

            device.auth_token = str(uuid.uuid4())
            device.platform = platform
            device.carrier = carrier
            device.os_info = os_info
            device.model = model
            device.build = build
            device.save()
            results['authToken'] = device.auth_token

        return self.success(results)
    
    
    def verifyUser(form, *args, **kw):
        errors = []
        if 'verificationCode' not in form:
            html('<h1>Verification Failed</h1>Verification code is required')
        ver_code = form.getvalue('verificationCode')
        user = User.from_verification_code(ver_code)
        if user is None:
            html('<h1>Verification Failed</h1>Invalid verification code')
        elif user.verified:
            html('<h1>Account already verified</h1>')
        else:
            user.verified = True
            user.save()
            devices = 'Devices also verified:<ul>'
            for device in user.devices:
                if not device.verified:
                    device.verified = True
                    devices += '<li>%s (%s)</li>' % (device.model, device.os_info)
                    device.save()
            devices += '</ul>'
            html('<h1>Account Verified</h1>' + devices)
    
    
    def verifyDevice(form, *args, **kw):
        errors = []
        if 'verificationCode' not in form:
            html('<h1>Verification Failed</h1>Verification code is required')
            return
        ver_code = form.getvalue('verificationCode')
        device = Device.from_verification_code(ver_code)
        if device is None:
            html('<h1>Verification Failed</h1>Invalid verification code')
            return
        elif device.verified:
            html('<h1>Device Already Verified</h1>')
            return
        else:
            device.verified = True
            device.save()
            html('<h1>Device Verified</h1>')
    
    
    def changeUserName(self, form):
        errors = []
        if 'nameChangeCode' not in form:
            return self.html('<h1>Name Change Failed</h1>Name change code required')

        code = form.getvalue('nameChangeCode')
        name = form.getvalue('name')
        user = User.from_name_change_code(code)

        if user is None:
            return self.html('<h1>Name Change Failed</h1>Invalid name change code')

        email = user.email

        if name is None:
            return self.html("""<h1>Change User's Name</h1>
                    <form action="/beta/actions.cgi" method="post">
                    <label for="email">Email:</label><br/>
                    <input type="text" name="email" value="%s" disabled="disabled"/><br/>
                    <label for="name">Name:</label><br/>
                    <input type="text" name="name" value="%s"/><br/>
                    <input type="hidden" name="nameChangeCode" value="%s"/>
                    <input type="hidden" name="action" value="changeUserName"/>
                    <input type="submit"/></form>""" % (user.email, user.name if user.name is not None else '', code))
        else:
            user.name = name
            user.save()
            return self.html('<h1>Name Changed Successfully</h1>')
    
    def sendEmail(self, to_addr, reply_addr, subject, msg):
        msg = ('From: RHIT Mobile Beta <rhitmobile@gmail.com>\r\n'
                'To: %s\r\n'
                'Reply-To: %s\r\n'
                'Subject: %s\r\n\r\n%s') % (to_addr, reply_addr, subject, msg)
    
        server = smtplib.SMTP('smtp.gmail.com:587')  
        server.starttls()  
        server.login(DBObject.username, DBObject.password)  
        try:
            server.sendmail('RHIT Mobile Beta Program', (to_addr,), msg)  
        except Exception:
            pass # JUST EAT IT
        server.quit()  
    
    
    def submitFeedback(form, *args, **kw):
        if 'authToken' not in form:
            return self.error('Auth Token is required')

        if 'content' not in form:
            return self.error('Content is required')

        device = Device.from_auth_token(form.getvalue('authToken'))

        if device is None:
            return self.error('Authentication failed')

        feedback = Feedback()
        feedback.device = device
        feedback.build = device.current_build
        feedback.content = form.getvalue('content')
        feedback.save()
        return self.success()
    
    
    def submitTestResults(self, form):
        if 'authToken' not in form:
            return self.error('Auth Token is required')

        if 'passed' not in form:
            return self.error('Pass Status is required')

        device = Device.from_auth_token(form.getvalue('authToken'))

        if device is None:
            return self.error('Authentication failed')

        passed = form.getvalue('passed').lower() == 'true'

        test = TestExecution()
        test.device = device
        test.build = device.current_build
        test.content = form.getvalue('content')
        test.passed = passed
        test.save()
        return self.success()
    
    
    def notifyOfUpdate(self, form):
        if 'authToken' not in form:
            return self.error('Auth Token is required')

        if 'toBuildNumber' not in form:
            return self.error('Destination Build is required')

        device = Device.from_auth_token(form.getvalue('authToken'))

        if device is None:
            return self.error('Authentication failed')

        to_build = Build.from_build_number_and_platform(form.getvalue('toBuildNumber'), device.platform)

        if to_build is None:
            return self.error('Invalid destination build number')

        update = Update()
        update.device = device
        update.to_build = to_build
        device.current_build = to_build
        update.save()
        device.save()
        return self.success()
    
    
    def getLatestBuilds(self, form):
        if 'platform' not in form:
            return self.error('Platform is required')

        platform = Platform.from_identifier(form.getvalue('platform'))

        if platform is None:
            return self.error('Invalid platform')

        rolling, nightly, beta, official = Build.latest(platform)

        result = {}
        if rolling is None:
            result['rolling'] = None
        else:
            result['rolling'] = {'buildNumber': rolling.number,
                                'viewURL': rolling.view_url,
                                'downloadURL': rolling.download_url}
        if official is None:
            result['official'] = None
        else:
            result['official'] = {'buildNumber': official.number,
                                  'viewURL': official.view_url,
                                  'downloadURL': official.download_url}
        return self.success(result)
    
    
    def publishBuild(self, form):
        if 'publisinghKey' not in form:
            return self.html('Publishing Key required')

        publish_key = form.getvalue('publishingKey')
        platform = Platform.from_publishing_key(publish_key)

        if platform is None:
            return self.html('Bad publishing key')
        if 'buildNumber' not in form:
            return self.html(('<h1>Publish New %s Build</h1>'
                  '<form action="/beta/actions.cgi" method="post">'
                  '<input type="hidden" name="publishKey" value="%s"/>'
                  '<input type="hidden" name="action" value="publishBuild"/>'
                  '<label for="buildNumber">Build Number</label><br/>'
                  '<input type="text" name="buildNumber"/><br/>'
                  '<input type="checkbox" name="official"/>'
                  '<label for="official">Official Build</label><br/>'
                  '<label for="viewURL">Viewing URL</label><br/>'
                  '<input type="text" name="viewURL"/><br/>'
                  '<label for="downloadURL">Download URL</label><br/>'
                  '<input type="text" name="downloadURL"/><br/>'
                  '<input type="submit"/></form>') % (platform.name, publish_key))
        else:
            build = Build(new=True)
            build.platform = platform
            build.number = form.getvalue('buildNumber')
            build.official = form.getvalue('official') in ('on', 'true')
            build.view_url = form.getvalue('viewURL')
            build.download_url = form.getvalue('downloadURL')
            build.save()
            return self.html('<h1>Build Published</h1>')
    
    
    def renewPublishingKey(self, form):
        if 'platform' not in form:
            return self.html('<h1>Renewal Failed</h1>Platform required')

        platform = Platform.from_identifier(form.getvalue('platform'))

        if platform is None:
            return self.html('<h1>Renewal Failed</h1>Invalid platform')

        platform.publishing_key = str(uuid.uuid4())
        platform.save()

        publish_args = {'action': 'publishBuild',
                        'publishKey': platform.publish_key}
        publish_url = self.base_url + urllib.urlencode(publish_args)
        msg = ('The publishing key for %s has been renewed. Use the link below to '
               'publish builds for %s from now on.\n\nPublishing Key: %s\n\n%s\n\n'
               'Thanks\nJimmy') % (platform.name, platform.name, platform.publish_key,
                                   publish_url)
        self.send_email(platform.owner_email, 'theisje@rose-hulman.edu', 'Publishing Key Renewed', msg)
        return self.html('<h1>Publishing Key Renewed</h1>')


def run_script():
    handler = RequestHandler()

    config = ConfigParser.ConfigParser()
    config_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_dir, 'config.cfg')
    config.read(config_path)

    email_username = config.get('Gmail', 'username')
    email_password = config.get('Gmail', 'password')

    base_url = config.get('Site', 'scriptURL')

    handler.email_username = email_username
    handler.email_password = email_password
    handler.base_url = base_url

    print handler.parse_and_execute(form=cgi.FieldStorage())

if __name__ == '__main__': run_script()
