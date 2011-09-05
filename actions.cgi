#!/usr/bin/env python

"""
actions.cgi: interactions for the RHIT Mobile beta program
"""

import cgi
import ConfigParser
import datetime
import hashlib
import json
import os
import smtplib
import types
import urllib
import uuid

import MySQLdb

####### DEBUG #######
import cgitb
cgitb.enable()
#####################


class DBObject(object):
    conn = None
    curs = None
    username = None
    password = None

    def get_id(self):
        return self._id

    def set_id(self, new_id):
        self._id = new_id

    db_id = property(get_id, set_id)

class User(DBObject):

    @classmethod
    def _from_db_row(self, row):
        if row is None:
            return None
        user = User()
        user.db_id = row[0]
        user.name = row[1]
        user.email = row[2]
        user.created = row[3]
        user.verified = row[4]
        user.verification_code = row[5]
        user.name_change_code = row[6]
        return user

    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM users WHERE id = %s""",
                          (db_id,))
        return self._from_db_row(self.curs.fetchone())

    @classmethod 
    def from_email(self, email):
        self.curs.execute("""SELECT * FROM users WHERE email = %s""",
                          (email,))
        return self._from_db_row(self.curs.fetchone())

    @classmethod
    def from_verification_code(self, code):
        summed = sum_string(code)
        self.curs.execute("""SELECT * FROM users
                             WHERE verification_code LIKE %s""",
                          (str(summed) + '::%',))
        candidates = [self._from_db_row(row) for row in self.curs.fetchall()]
        match = filter(lambda d: d.is_correct_verification_code(code), candidates)
        return None if len(match) < 1 else match[0]


    @classmethod
    def from_name_change_code(self, code):
        summed = sum_string(code)
        self.curs.execute("""SELECT * FROM users
                             WHERE name_change_code LIKE %s""",
                          (str(summed) + '::%',))
        candidates = [self._from_db_row(row) for row in self.curs.fetchall()]
        match = filter(lambda d: d.is_correct_name_change_code(code), candidates)
        return None if len(match) < 1 else match[0]


    def __init__(self, new=False):
        if new:
            self.db_id = -1
            self.name = None
            self.email = None
            self.created = datetime.datetime.now()
            self.verified = False
            self.verification_code = str(uuid.uuid4())
            self.name_change_code = str(uuid.uuid4())
            self.devices = None
        else:
            self.db_id = -1
            self.name = None
            self.email = None
            self.created = None
            self.verified = False
            self.verification_code = None
            self.name_change_code = None
            self.devices = None

    def __str__(self):
        return 'User #%s: %s (%s)' % (self.db_id, self.email, self.name)

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    name = property(get_name, set_name)

    def get_email(self):
        return self._email

    def set_email(self, email):
        self._email = email

    email = property(get_email, set_email)

    def get_created_time(self):
        return self._created_time

    def set_created_time(self, created_time):
        self._created_time = created_time

    created_time = property(get_created_time, set_created_time)

    def get_verified(self):
        return self._verified

    def set_verified(self, verified):
        self._verified = verified

    verified = property(get_verified, set_verified)

    def get_verification_code(self):
        return self._clear_verification_code

    def set_verification_code(self, verification_code):
        if verification_code is None or verification_code.find('::') != -1:
            self._verification_code = verification_code
            self._clear_verification_code = None
        else:
            self._clear_verification_code = verification_code
            self._verification_code = hashify(verification_code, lookup=True)

    def is_correct_verification_code(self, verification_code):
        if self._verification_code is not None:
            return verify_hash(self._verification_code, verification_code, lookup=True)
        else:
            return False

    verification_code = property(get_verification_code, set_verification_code)

    def get_name_change_code(self):
        return self._clear_name_change_code

    def set_name_change_code(self, name_change_code):
        if name_change_code is None or name_change_code.find('::') != -1:
            self._name_change_code = name_change_code
            self._clear_name_change_code = None
        else:
            self._clear_name_change_code = name_change_code
            self._name_change_code = hashify(name_change_code, lookup=True)

    def is_correct_name_change_code(self, name_change_code):
        if self._name_change_code is not None:
            return verify_hash(self._name_change_code, name_change_code, lookup=True)
        else:
            return False

    name_change_code = property(get_name_change_code, set_name_change_code)

    def get_devices(self):
        if self._devices is None:
            self.curs.execute("""SELECT * FROM devices WHERE user = %s""", (self.db_id,))
            self._devices = [Device._from_db_row(r) for r in self.curs.fetchall()]
        return self._devices

    def set_devices(self, devices):
        self._devices = devices

    devices = property(get_devices, set_devices)

    def save(self):
        if self.db_id == -1:
            self.curs.execute("""INSERT INTO users (name, email, created, verified,
                                                    verification_code,
                                                    name_change_code)
                                     VALUES(%s, %s, %s, %s, %s, %s)""",
                               (self.name, self.email, self.created, self.verified,
                                self._verification_code, self._name_change_code))
            self.conn.commit()
            self.db_id = User.from_email(self.email).db_id
        else:
            self.curs.execute("""UPDATE users
                                 SET name = %s, email = %s, 
                                     created = %s, verified = %s,
                                     verification_code = %s,
                                     name_change_code = %s
                                 WHERE id = %s""", (self.name, self.email,
                                                    self.created, self.verified,
                                                    self._verification_code,
                                                    self._name_change_code,
                                                    self.db_id))
            self.conn.commit()


class Device(DBObject):
    
    @classmethod
    def _from_db_row(self, row):
        device = Device()
        device.db_id = row[0]
        device.unique_identifier = row[1]
        device.os_info = row[2]
        device.model = row[3]
        device.verified = row[4]
        device.verification_code = row[5]
        device.auth_token = row[6]
        device.user = row[7]
        device.carrier = row[8]
        device.current_build = row[9]
        device.platform = row[10]
        return device

    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM devices WHERE id = %s""",
                          (db_id,))
    @classmethod
    def from_user(self, user):
        self.curs.execute("""SELECT * FROM devices WHERE user = %s""", (user.db_id,))
        return [self._from_db_row(row) for row in self.curs.fetchall()]

    @classmethod
    def from_unique_identifier(self, unique_id):
        summed = sum_string(unique_id)
        self.curs.execute("""SELECT * FROM devices WHERE identifier LIKE %s""",
                          (str(summed) + '::%',))
        candidates = [self._from_db_row(row) for row in self.curs.fetchall()]
        match = filter(lambda d: d.is_correct_unique_identifier(unique_id), 
                       candidates)
        return None if len(match) < 1 else match[0]

    @classmethod
    def from_auth_token(self, token):
        summed = sum_string(token)
        self.curs.execute("""SELECT * FROM devices WHERE auth_token LIKE %s""",
                          (str(summed) + '::%',))
        candidates = [self._from_db_row(row) for row in self.curs.fetchall()]
        match = filter(lambda d: d.is_correct_auth_token(token), 
                       candidates)
        return None if len(match) < 1 else match[0]

    @classmethod
    def from_verification_code(self, code):
        summed = sum_string(code)
        self.curs.execute("""SELECT * FROM devices WHERE verification_code LIKE %s""",
                          (str(summed) + '::%',))
        candidates = [self._from_db_row(row) for row in self.curs.fetchall()]
        match = filter(lambda d: d.is_correct_verification_code(code), 
                       candidates)
        return None if len(match) < 1 else match[0]


    def __init__(self, new=False):
        if new:
            self.db_id = -1
            self.unique_identifier = None
            self.os_info = None
            self.model = None
            self.verified = False
            self.verification_code = str(uuid.uuid4())
            self.auth_token = str(uuid.uuid4())
            self.user = None
            self.carrier = None
            self.current_build = None
            self.platform = None
        else:
            self.db_id = -1
            self.unique_identifier = None
            self.os_info = None
            self.model = None
            self.verified = False
            self.verification_code = None
            self.auth_token = None
            self.user = None
            self.carrier = None
            self.current_build = None
            self.platform = None

    def get_unique_identifier(self):
        return self._clear_unique_identifier

    def set_unique_identifier(self, unique_identifier):
        if unique_identifier is None or unique_identifier.find('::') != -1:
            self._unique_identifier = unique_identifier
            self._clear_unique_identifier = None
        else:
            self._clear_unique_identifier = unique_identifier
            self._unique_identifier = hashify(unique_identifier, lookup=True)

    def is_correct_unique_identifier(self, unique_identifier):
        if self._unique_identifier is not None:
            return verify_hash(self._unique_identifier, unique_identifier,
                               lookup=True)
        else:
            return False

    unique_identifier = property(get_unique_identifier, set_unique_identifier)

    def get_os_info(self):
        return self._os_info

    def set_os_info(self, os_info):
        self._os_info = os_info

    os_info = property(get_os_info, set_os_info)

    def get_model(self):
        return self._model

    def set_model(self, model):
        self._model = model

    model = property(get_model, set_model)

    def get_verified(self):
        return self._verified

    def set_verified(self, verified):
        self._verified = verified

    verified = property(get_verified, set_verified)

    def get_verification_code(self):
        return self._clear_verification_code

    def set_verification_code(self, verification_code):
        if verification_code is None or verification_code.find('::') != -1:
            self._verification_code = verification_code
            self._clear_verification_code = None
        else:
            self._clear_verification_code = verification_code
            self._verification_code = hashify(verification_code, lookup=True)

    def is_correct_verification_code(self, verification_code):
        if self._verification_code is not None:
            return verify_hash(self._verification_code, verification_code, lookup=True)
        else:
            return False

    verification_code = property(get_verification_code, set_verification_code)

    def get_auth_token(self):
        return self._clear_auth_token

    def set_auth_token(self, auth_token):
        if auth_token is None or auth_token.find('::') != -1:
            self._auth_token = auth_token
            self._clear_auth_token = None
        else:
            self._clear_auth_token = auth_token
            self._auth_token = hashify(auth_token, lookup=True)

    def is_correct_auth_token(self, auth_token):
        if self._auth_token is not None:
            return verify_hash(self._auth_token, auth_token, lookup=True)
        else:
            return False

    auth_token = property(get_auth_token, set_auth_token)

    def get_user(self):
        return self._user

    def set_user(self, user):
        if type(user) == types.LongType:
            self._user = User.from_id(user)
        else:
            self._user = user

    user = property(get_user, set_user)

    def get_carrier(self):
        return self._carrier

    def set_carrier(self, carrier):
        if type(carrier) == types.LongType:
            self._carrier = Carrier.from_id(carrier)
        else:
            self._carrier = carrier

    carrier = property(get_carrier, set_carrier)

    def get_current_build(self):
        return self._current_build

    def set_current_build(self, build):
        if type(build) == types.LongType:
            self._current_build = Build.from_id(build)
        else:
            self._current_build = build

    current_build = property(get_current_build, set_current_build)

    def get_platform(self):
        return self._platform

    def set_platform(self, platform):
        if type(platform) == types.LongType:
            self._platform = Platform.from_id(platform)
        else:
            self._platform = platform

    platform = property(get_platform, set_platform)

    def save(self):
        if self.db_id == -1:
            self.curs.execute("""INSERT INTO devices (identifier, os_info,
                                     model, verified, verification_code,
                                     auth_token, user, carrier, build,
                                     platform)
                                 VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                              (self._unique_identifier, self.os_info, self.model,
                               self.verified, self._verification_code,
                               self._auth_token, 
                               self.user.db_id, 
                               None if self.carrier is None else self.carrier.db_id,
                               self.current_build.db_id,
                               self.platform.db_id))
            self.conn.commit()
            self.db_id = Device.from_unique_identifier(self.unique_identifier).db_id
        else:
            self.curs.execute("""UPDATE devices
                                 SET identifier = %s,
                                     os_info = %s,
                                     model = %s,
                                     verified = %s,
                                     verification_code = %s,
                                     auth_token = %s,
                                     user = %s,
                                     carrier = %s,
                                     build = %s,
                                     platform = %s
                                  WHERE id = %s""",
                              (self._unique_identifier,
                               self.os_info, self.model, self.verified,
                               self._verification_code, self._auth_token,
                               self.user.db_id,
                               None if self.carrier is None else self.carrier.db_id,
                               self.current_build.db_id,
                               self.platform.db_id,
                               self.db_id))
            self.conn.commit()


class Platform(DBObject):

    @classmethod
    def _from_db_row(self, row):
        if row is None:
            return None
        platform = Platform()
        platform.db_id = row[0]
        platform.name = row[1]
        platform.identifier = row[2]
        platform.owner_email = row[3]
        platform.publish_key = row[4]
        return platform

    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM platforms
                             WHERE id = %s""" % db_id)
        return self._from_db_row(self.curs.fetchone())

    @classmethod
    def from_identifier(self, identifier):
        self.curs.execute("""SELECT * FROM platforms
                             WHERE identifier = %s""", (identifier,))
        return self._from_db_row(self.curs.fetchone())

    @classmethod
    def from_publish_key(self, key):
        summed = sum_string(key)
        self.curs.execute("""SELECT * FROM platforms WHERE publish_key LIKE %s""",
                          (str(summed) + '::%',))
        candidates = [self._from_db_row(row) for row in self.curs.fetchall()]
        match = filter(lambda d: d.is_correct_publish_key(key), candidates)
        return None if len(match) < 1 else match[0]

    def __init__(self, new=False):
        self.db_id = -1
        self.name = None
        self.identifier = None
        self.owner_email = None
        self.publish_key = None
 
    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    name = property(get_name, set_name)

    def get_identifier(self):
        return self._identifier

    def set_identifier(self, identifier):
        self._identifier = identifier

    identifier = property(get_identifier, set_identifier)

    def get_owner_email(self):
        return self._owner_email

    def set_owner_email(self, email):
        self._owner_email = email

    owner_email = property(get_owner_email, set_owner_email)

    def get_publish_key(self):
        return self._clear_publish_key

    def set_publish_key(self, key):
        if key is None or key.find('::') != -1:
            self._publish_key = key
            self._clear_publish_key = None
        else:
            self._clear_publish_key = key
            self._publish_key = hashify(key, lookup=True)

    publish_key = property(get_publish_key, set_publish_key)

    def is_correct_publish_key(self, key):
        if self._publish_key is not None:
            return verify_hash(self._publish_key, key, lookup=True)
        else:
            return False

    def save(self):
        self.curs.execute("""UPDATE platforms
                             SET name = %s,
                                 identifier = %s,
                                 owner_email = %s,
                                 publish_key = %s
                             WHERE id = %s""", (self.name, self.identifier,
                                                self.owner_email,
                                                self._publish_key, self.db_id))
        self.conn.commit()


class Build(DBObject):
    
    @classmethod
    def _from_db_row(self, row):
        if row is None:
            return None
        build = Build()
        build.db_id = row[0]
        build.platform = row[1]
        build.number = row[2]
        build.published = row[3]
        build.official = row[4]
        build.view_url = row[5]
        build.download_url = row[6]
        return build

    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM builds WHERE id = %s""",
                          (db_id,))
        return self._from_db_row(self.curs.fetchone())

    @classmethod
    def from_build_number_and_platform(self, number, platform):
        self.curs.execute("""SELECT * FROM builds
                             WHERE platform = %s AND
                                   build_number = %s
                             ORDER BY published DESC""",
                           (platform.db_id, number))
        return self._from_db_row(self.curs.fetchone())

    @classmethod
    def latest(self, platform):
        self.curs.execute("""SELECT * FROM builds
                             WHERE platform = %s AND
                                   official = 1
                             ORDER BY published DESC""",
                          (platform.db_id))
        official = self._from_db_row(self.curs.fetchone())
        self.curs.execute("""SELECT * FROM builds
                             WHERE platform = %s AND
                                   official = 0
                              ORDER BY published DESC""",
                           (platform.db_id))
        latest = self._from_db_row(self.curs.fetchone())
        return official, latest

    def __init__(self, new=False):
        if new:
            self.db_id = -1
            self.platform = None
            self.number = -1
            self.published = datetime.datetime.now()
            self.official = False
            self.view_url = None
            self.download_url = None
        else:
            self.db_id = -1
            self.platform = None
            self.number = -1
            self.published = None
            self.official = False
            self.view_url = None
            self.download_url = None

    def get_platform(self):
        return self._platform

    def set_platform(self, platform):
        if type(platform) == types.LongType:
            self._platform = Platform.from_id(platform)
        else:
            self._platform = platform

    platform = property(get_platform, set_platform)

    def get_number(self):
        return self._number

    def set_number(self, number):
        self._number = number

    number = property(get_number, set_number)

    def get_published(self):
        return self._published

    def set_published(self, published):
        self._published = published

    published = property(get_published, set_published)

    def get_official(self):
        return self._official

    def set_official(self, official):
        self._official = official

    official = property(get_official, set_official)

    def get_view_url(self):
        return self._view_url

    def set_view_url(self, url):
        self._view_url = url

    view_url = property(get_view_url, set_view_url)

    def get_download_url(self):
        return self._download_url

    def set_download_url(self, url):
        self._download_url = url

    def save(self):
        if self.db_id == -1:
            self.curs.execute("""INSERT INTO builds
                                 (platform, build_number, published,
                                  official, view_url, download_url)
                                 VALUES(%s, %s, %s, %s, %s, %s)""",
                                 (self.platform.db_id, self.number,
                                  self.published, self.official, self.view_url, self.download_url))
            self.conn.commit()
        else:
            self.curs.execute("""UPDATE builds
                                 SET platform = %s,
                                     build_number = %s,
                                     published = %s,
                                     official = %s,
                                     view_url = %s,
                                     download_url = %s
                                 WHERE id = %s""", (self.platform.db_id, self.number,
                                                    self.published, self.view_url,
                                                    self.download_url))
            self.conn.commit()


class Carrier(DBObject):
    
    @classmethod
    def _from_db_row(self, row):
        if row is None:
            return None
        carrier = Carrier()
        carrier.db_id = row[0]
        carrier.name = row[1]
        carrier.identifier = row[2]
        return carrier

    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM carriers
                             WHERE id = %s""", (db_id,))
        return self._from_db_row(self.curs.fetchone())

    @classmethod
    def from_string(self, string):
        if string is None:
            return None
        space = string.find(' ')
        if space == -1:
            filtered = string.lower()
        else:
            filtered = string[:space].lower()
        filtered = filter(lambda c: c.isalpha(), filtered)
        self.curs.execute("""SELECT * FROM carriers
                             WHERE identifier = %s""", (filtered,))
        carrier = self._from_db_row(self.curs.fetchone())
        if carrier is None:
            carrier = Carrier()
            carrier.identifier = filtered
            carrier.name = string
            carrier.save()
        return carrier

    def __init__(self):
        self.db_id = -1
        self.name = None
        self.identifier = None

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    name = property(get_name, set_name)

    def get_identifier(self):
        return self._identifier

    def set_identifier(self, identifier):
        self._identifier = identifier

    identifier = property(get_identifier, set_identifier)

    def save(self):
        self.curs.execute("""INSERT INTO carriers (name, identifier)
                             VALUES(%s, %s)""",
                          (self.name, self.identifier))
        self.conn.commit()
        self.db_id = Carrier.from_string(self.identifier).db_id



class Update(DBObject):
    
    @classmethod
    def _from_db_row(self, row):
        if row is None:
            return None
        update = Update()
        update.db_id = row[0]
        update.device = row[1]
        update.from_build = row[2]
        update.to_build = row[3]
        update.time = row[4]

    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM updates WHERE id = %s""",
                          (db_id,))
        return self._from_db_row(self.curs.fetchone())

    def __init__(self):
        self.device = None
        self.from_build = None
        self.to_build = None
        self.time = datetime.datetime.now()

    def get_device(self):
        return self._device

    def set_device(self, device):
        if type(device) == types.LongType:
            self._device = Device.from_id(device)
        else:
            self._device = device

    device = property(get_device, set_device)

    def get_from_build(self):
        return self._from_build

    def set_from_build(self, build):
        if type(build) == types.LongType:
            self._from_build = Build.from_id(build)
        else:
            self._from_build = build

    from_build = property(get_from_build, set_from_build)

    def get_to_build(self):
        return self._to_build

    def set_to_build(self, build):
        if type(build) == types.LongType:
            self._to_build = Build.from_id(build)
        else:
            self._to_build = build

    to_build = property(get_to_build, set_to_build)

    def get_time(self):
        return self._time

    def set_time(self, time):
        self._time = time

    time = property(get_time, set_time)

    def save(self):
        self.curs.execute("""INSERT INTO updates (device, from_build, to_build, time)
                             VALUES (%s, %s, %s, %s)""",
                          (self.device.db_id,
                           None if self.from_build is None else self.from_build.db_id,
                           self.to_build.db_id,
                           self.time))
        self.conn.commit()


class Test(DBObject):
    
    @classmethod
    def _from_db_row(self, row):
        if row is None:
            return None
        test = Test()
        test.db_id = row[0]
        test.device = row[1]
        test.build = row[2]
        test.time = row[3]
        test.content = row[4]
        test.passed = row[5]
        return test
    
    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM test_results WHERE id = %s""",
                          (db_id,))
        return self._from_db_row(self.curse.fetchone())

    def __init__(self):
        self.device = None
        self.build = None
        self.time = datetime.datetime.now()
        self.content = None
        self.passed = False

    def get_device(self):
        return self._device

    def set_device(self, device):
        if type(device) == types.LongType:
            self._device = Device.from_id(device)
        else:
            self._device = device

    device = property(get_device, set_device)

    def get_build(self):
        return self._build

    def set_build(self, build):
        if type(build) == types.LongType:
            self._build = Build.from_id(build)
        else:
            self._build = build

    build = property(get_build, set_build)

    def get_time(self):
        return self._time

    def set_time(self, time):
        self._time = time

    time = property(get_time, set_time)

    def get_content(self):
        return self._content

    def set_content(self, content):
        self._content = content

    content = property(get_content, set_content)
    
    def get_pass(self):
        return self._pass

    def set_pass(self, passed):
        self._pass = passed

    passed = property(get_pass, set_pass)

    def save(self):
        self.curs.execute("""INSERT INTO test_results (device, build, time,
                                content, pass)
                             VALUES (%s, %s, %s, %s, %s)""",
                          (self.device.db_id, self.build.db_id, self.time, self.content, self.passed))
        self.conn.commit()

class Feedback(DBObject):

    @classmethod
    def _from_db_row(self, row):
        if row is None:
            return None
        feedback = Feedback()
        feedback.db_id = row[0]
        feedback.device = row[1]
        feedback.build = row[2]
        feedback.time = row[3]
        feedback.content = row[4]
        return feedback
    
    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM feedback WHERE id = %s""",
                          (db_id,))
        return self._from_db_row(self.curs.fetchone())

    def __init__(self):
        self.device = None
        self.build = None
        self.time = datetime.datetime.now()
        self.content = None

    def get_device(self):
        return self._device

    def set_device(self, device):
        if type(device) == types.LongType:
            self._device = Device.from_id(device)
        else:
            self._device = device

    device = property(get_device, set_device)

    def get_build(self):
        return self._build

    def set_build(self, build):
        if type(build) == types.LongType:
            self._build = Build.from_id(build)
        else:
            self._build = build

    build = property(get_build, set_build)

    def get_time(self):
        return self._time

    def set_time(self, time):
        self._time = time

    time = property(get_time, set_time)

    def get_content(self):
        return self._content

    def set_content(self, content):
        self._content = content

    content = property(get_content, set_content)
    
    def save(self):
        self.curs.execute("""INSERT INTO feedback (device, build, time, content)
                             VALUES (%s, %s, %s, %s)""",
                          (self.device.db_id, self.build.db_id, self.time, self.content))
        self.conn.commit()


def sum_string(string):
    return reduce(lambda s, c: s + ord(c), string, 0) % 100000000


def hashify(string, lookup=False):
    summed = sum_string(string)
    salt = str(uuid.uuid4())
    salted = '%s::%s' % (salt, string)
    hashed = hashlib.sha1(salted).hexdigest()
    return '%s::%s::%s' % (summed, salt, hashed)

    
def verify_hash(entry, string, lookup=False):
    if lookup:
        entry = entry[entry.find('::') + 2:]
    split = entry.partition('::')
    salt = split[0]
    answer = split[2]
    salted = '%s::%s' % (salt, string)
    return answer == hashlib.sha1(salted).hexdigest()


def parse_and_execute(form, **kw):
    actions = {'register': register,
               'verifyUser': verify_user,
               'verifyDevice': verify_device,
               'changeUserName': change_user_name,
               'submitFeedback': submit_feedback,
               'submitTestResults': submit_test_results,
               'notifyOfUpdate': notify_of_update,
               'getLatestBuilds': get_latest_builds,
               'publishBuild': publish_build,
               'renewPublishLink': renew_publish_link}
    if 'action' not in form:
        error('You must specify an action')
    elif form.getvalue('action') not in actions:
        error('Invalid action: %s' % form.getvalue('action'))
    else:
        actions[form.getvalue('action')](form=form, **kw)


def error(*args):
    print 'Content-Type: text/plain\n'
    print json.dumps({'success': False, 'errors': args})


def success(vals={}):
    print 'Content-Type: text/plain\n'
    print json.dumps(dict(vals.items() + {'success': True}.items()))


def html(content):
    print 'Content-Type: text/html\n'
    print '<!DOCTYPE html><html><head></head><body>%s</body></html>' % content


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
        error(*errors)
        return
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
        error('Invalid platform')
        return
    build = Build.from_build_number_and_platform(build_number, platform)
    if build is None:
        error('Invalid build number')
        return
    if user is None:
        results['newUser'] = True
        user = User(new=True)
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
        send_email(email, platform.owner_email, 'Verify your email and devices', msg) 
        name_msg = ('A new user has registered for your platform\'s beta '
                    'program:\n\nName: %s\nEmail: %s\n\nTo change this user\'s '
                    'name, use the following link:\n\n%s\n\nLet me know if '
                    'something breaks\nJimmy') % (user.name, user.email, name_change_url)
        send_email(platform.owner_email, 'theisje@rose-hulman.edu', 'New user %s registered' % user.email, name_msg)
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
            send_email(email, platform.owner_email, 'Verify your new device', msg)
        results['authToken'] = device.auth_token
    else:
        results['newDevice'] = False
        if device.user.email != email:
            error('Device already registered to another user')
            return
        device.auth_token = str(uuid.uuid4())
        device.platform = platform
        device.carrier = carrier
        device.os_info = os_info
        device.model = model
        device.build = build
        device.save()
        results['authToken'] = device.auth_token
    success(results)


def verify_user(form, *args, **kw):
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


def verify_device(form, *args, **kw):
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


def change_user_name(form, *args, **kw):
    errors = []
    if 'nameChangeCode' not in form:
        html('<h1>Name Change Failed</h1>Name change code required')
        return
    code = form.getvalue('nameChangeCode')
    name = form.getvalue('name')
    user = User.from_name_change_code(code)
    if user is None:
        html('<h1>Name Change Failed</h1>Invalid name change code')
        return
    email = user.email
    if name is None:
        html("""<h1>Change User's Name</h1>
                <form action="/beta/actions.cgi" method="post">
                <label for="email">Email:</label><br/>
                <input type="text" name="email" value="%s" disabled="disabled"/><br/>
                <label for="name">Name:</label><br/>
                <input type="text" name="name" value="%s"/><br/>
                <input type="hidden" name="nameChangeCode" value="%s"/>
                <input type="hidden" name="action" value="changeUserName"/>
                <input type="submit"/></form>""" % (user.email, user.name if user.name is not None else '', code))
        return
    else:
        user.name = name
        user.save()
        html('<h1>Name Changed Successfully</h1>')
        return

def send_email(to_addr, reply_addr, subject, msg):
    msg = ('From: RHIT Mobile Beta <rhitmobile@gmail.com>\r\n'
            'To: %s\r\n'
            'Reply-To: %s\r\n'
            'Subject: %s\r\n\r\n%s') % (to_addr, reply_addr, subject, msg)

    server = smtplib.SMTP('smtp.gmail.com:587')  
    server.starttls()  
    server.login(self.username, self.password)  
    try:
        server.sendmail('RHIT Mobile Beta Program', (to_addr,), msg)  
    except Exception:
        pass # JUST EAT IT
    server.quit()  


def submit_feedback(form, *args, **kw):
    if 'authToken' not in form:
        error('Auth Token is required')
        return
    if 'content' not in form:
        error('Content is required')
        return
    device = Device.from_auth_token(form.getvalue('authToken'))
    if device is None:
        error('Authentication failed')
        return
    feedback = Feedback()
    feedback.device = device
    feedback.build = device.current_build
    feedback.content = form.getvalue('content')
    feedback.save()
    success()


def submit_test_results(form, *args, **kw):
    if 'authToken' not in form:
        error('Auth Token is required')
        return
    if 'passed' not in form:
        error('Pass Status is required')
        return
    device = Device.from_auth_token(form.getvalue('authToken'))
    if device is None:
        error('Authentication failed')
        return
    passed = form.getvalue('passed').lower() == 'true'
    test = Test()
    test.device = device
    test.build = device.current_build
    test.content = form.getvalue('content')
    test.passed = passed
    test.save()
    success()


def notify_of_update(form, *args, **kw):
    if 'authToken' not in form:
        error('Auth Token is required')
        return
    if 'toBuildNumber' not in form:
        error('Destination Build is required')
        return
    device = Device.from_auth_token(form.getvalue('authToken'))
    if device is None:
        error('Authentication failed')
        return
    to_build = Build.from_build_number_and_platform(form.getvalue('toBuildNumber'),
                                                    device.platform)
    if to_build is None:
        error('Invalid destination build number')
        return
    from_build = device.current_build
    if to_build.number == from_build.number:
        error('Device is already running this build number')
        return
    update = Update()
    update.device = device
    update.to_build = to_build
    update.from_build = from_build
    device.current_build = to_build
    update.save()
    device.save()
    success()


def get_latest_builds(form, *args, **kw):
    if 'platform' not in form:
        error('Platform is required')
        return
    platform = Platform.from_identifier(form.getvalue('platform'))
    if platform is None:
        error('Invalid platform')
        return
    official, latest = Build.latest(platform)
    result = {}
    if latest is None:
        result['latest'] = None
    else:
        result['latest'] = {'buildNumber': latest.number,
                            'viewURL': latest.view_url,
                            'downloadURL': latest.download_url}
    if official is None:
        result['official'] = None
    else:
        result['official'] = {'buildNumber': official.number,
                              'viewURL': official.view_url,
                              'downloadURL': official.download_url}
    success(result)


def publish_build(form, *args, **kw):
    if 'publishKey' not in form:
        html('Publishing Key required')
        return
    publish_key = form.getvalue('publishKey')
    platform = Platform.from_publish_key(publish_key)
    if platform is None:
        html('Bad publishing key')
        return
    if 'buildNumber' not in form:
        html(('<h1>Publish New %s Build</h1>'
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
        return
    else:
        build = Build(new=True)
        build.platform = platform
        build.number = form.getvalue('buildNumber')
        build.official = form.getvalue('official') in ('on', 'true')
        build.view_url = form.getvalue('viewURL')
        build.download_url = form.getvalue('downloadURL')
        build.save()
        html('<h1>Build Published</h1>')


def renew_publish_link(form, *args, **kw):
    if 'platform' not in form:
        html('<h1>Renewal Failed</h1>Platform required')
        return
    platform = Platform.from_identifier(form.getvalue('platform'))
    if platform is None:
        html('<h1>Renewal Failed</h1>Invalid platform')
        return
    platform.publish_key = str(uuid.uuid4())
    platform.save()
    base_url = 'http://mobile.csse.rose-hulman.edu/beta/actions.cgi?'
    publish_args = {'action': 'publishBuild',
                    'publishKey': platform.publish_key}
    publish_url = base_url + urllib.urlencode(publish_args)
    msg = ('The publishing key for %s has been renewed. Use the link below to '
           'publish builds for %s from now on.\n\nPublishing Key: %s\n\n%s\n\n'
           'Thanks\nJimmy') % (platform.name, platform.name, platform.publish_key,
                               publish_url)
    send_email(platform.owner_email, 'theisje@rose-hulman.edu', 'Publishing Key Renewed', msg)
    html('<h1>Publishing Key Renewed</h1>')


def run_script():
    config = ConfigParser.ConfigParser()
    config_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_dir, 'config.cfg')
    config.read(config_path)

    db_host = config.get('Database', 'host')
    db_user = config.get('Database', 'user')
    db_password = config.get('Database', 'password')
    db_database = config.get('Database', 'db')

    email_username = config.get('Gmail', 'username')
    email_password = config.get('Gmail', 'password')

    conn = MySQLdb.connect(host=db_host,
                           user=db_user,
                           passwd=db_password,
                           db=db_database)
    DBObject.conn = conn
    DBObject.curs = conn.cursor()
    DBObject.username = email_username
    DBObject.password = email_password

    parse_and_execute(form=cgi.FieldStorage())
    conn.close()

if __name__ == '__main__': run_script()
