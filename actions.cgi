#!/usr/bin/python

"""
actions.cgi: interactions for the RHIT Mobile beta program
"""

import cgi
import json
import uuid

import MySQLdb

####### DEBUG #######
import cgitb
cgitb.enable()
#####################


class DBObject(object):
    conn = None
    curs = None

class User(DBObject):

    @classmethod
    def _from_db_row(self, row):
        return None

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

    def __init__(self, **kw):
        pass

    def get_id(self):
        return self._id

    def set_id(self, new_id):
        self._id = new_id

    db_id = property(get_id, set_id)

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
        return self._verification_code

    def set_verification_code(self, verification_code):
        self._verification_code = verification_code

    verification_code = property(get_verification_code, set_verification_code)

    def get_name_change_code(self):
        return self._name_change_code

    def set_name_change_code(self, name_change_code):
        self._name_change_code = name_change_code

    name_change_code = property(get_name_change_code, set_name_change_code)

    def save(self):
        pass


class Device(DBObject):
    
    @classmethod
    def _from_db_row(self, row):
        return None

    @classmethod
    def from_id(self, db_id):
        self.curs.execute("""SELECT * FROM devices WHERE id = %s""",
                          (db_id,))

    def get_id(self):
        return self._id

    def set_id(self, new_id):
        self._id = new_id

    db_id = property(get_id, set_id)

    def get_unique_identifier(self):
        return self._unique_identifier

    def set_unique_identifier(self, unique_identifier):
        self._unique_identifier = unique_identifier

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
        return self._verification_code

    def set_verification_code(self, verification_code):
        self._verification_code = verification_code

    verification_code = property(get_verification_code, set_verification_code)

    def get_auth_token(self):
        return self._auth_token

    def set_auth_token(self, auth_token):
        self._auth_token = auth_token

    auth_token = property(get_auth_token, set_auth_token)

    def get_user(self):
        return self._user

    def set_user(self, user):
        self._user = user

    user = property(get_user, set_user)

    def get_carrier(self):
        return self._carrier

    def set_carrier(self, carrier):
        self._carrier = carrier

    carrier = property(get_carrier, set_carrier)

    def get_current_build(self):
        return self._current_build

    def set_current_build(self, build):
        self._current_build = build

    current_build = property(get_current_build, set_current_build)

    def get_platform(self):
        return self._platform

    def set_platform(self, platform):
        self._platform = platform

    platform = property(get_platform, set_platform)

    def save(self):
        pass


class Platform(DBObject):
    pass


class Build(DBObject):
    pass


class Carrier(DBObject):
    pass


class Update(DBObject):
    pass


class Test(DBObject):
    pass


class Feedback(DBObject):
    pass


def parse_and_execute(args, **kw):
    actions = {'register': register,
               'verifyUser': verify_user,
               'submitFeedback': submit_feedback,
               'submitTestResults': submit_test_results,
               'notifyOfUpdate': notify_of_update,
               'renewAuthToken': renew_auth_token}
    if 'action' not in args:
        error('You must specify an action')
    elif args.getvalue('action') not in actions:
        error('Invalid action: %s' % args.getvalue('action'))
    else:
        actions[args.getvalue('action')](args, **kw)


def error(*args):
    print 'Content-Type: text/plain\n'
    print json.dumps({'success': False, 'errors': args})


def success(vals={}):
    print 'Content-Type: text/plain\n'
    print json.dumps(dict(vals.items() + {'success': True}.items()))


def html(content):
    print 'Content-Type: text/html\n'
    print content


def register(form, conn, curs, *args, **kw):
    #error('Register not implemented')
    error(str(User.from_email('theisje@rose-hulman.edu')))


def verify_user(form, *args, **kw):
    if 'verification_code' not in form:
        error('Verification code required')
    else:
        error('Verify User not implemented')


def submit_feedback(*args, **kw):
    error('Submit Feedback not implemented')


def submit_test_results(*args, **kw):
    error('Submit Test Results not implemented')


def notify_of_update(*args, **kw):
    error('Notify of Update not implemented')


def renew_auth_token(*args, **kw):
    error('Renew Auth Token not implemented')


def run_script():
    conn = MySQLdb.connect(host='localhost',
                           user='beta',
                           passwd='urQiHZOk4WBZFCO6HUzld7EZB7P7BAQA',
                           db='beta_testers')
    DBObject.conn = conn
    DBObject.curs = conn.cursor()
    db = {'conn': conn, 'curs':conn.cursor()}
    parse_and_execute(cgi.FieldStorage(), **db)
    conn.close()

if __name__ == '__main__': run_script()
