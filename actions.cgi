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
    pass

class User(DBObject):
    pass

class Device(DBObject):
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
    print 'Content-Type: text/plain\n'
    actions = {'register_user': register_user,
               'verify_user': verify_user,
               'register_device': register_device,
               'submit_feedback': submit_feedback,
               'submit_test_results': submit_test_results,
               'notify_of_update': notify_of_update,
               'renew_auth_token': renew_auth_token}
    if 'action' not in args:
        error('You must specify an action')
    elif args.getvalue('action') not in actions:
        error('Invalid action: %s' % args.getvalue('action'))
    else:
        actions[args.getvalue('action')](args, **kw)


def error(*args):
    print json.dumps({'success': False, 'errors': args})

def success(vals={}):
    print json.dumps(dict(vals.items() + {'success': True}.items()))

def register_user(form, conn, curs, *args, **kw):
    errors = []
    if 'name' not in form:
        errors.append('You must specify a name')
    if 'email' not in form:
        errors.append('You must specify an email address')

    if len(errors) > 0:
        error(*errors)
    else:
        error('Register User not implemented')


def verify_user(form, *args, **kw):
    if 'verification_code' not in form:
        error('Verification code required')
    else:
        error('Verify User not implemented')


def register_device(*args, **kw):
    error('Register Device not implemented')


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
    db = {'conn': conn, 'curs':conn.cursor()}
    parse_and_execute(cgi.FieldStorage(), **db)
    conn.close()

if __name__ == '__main__': run_script()
