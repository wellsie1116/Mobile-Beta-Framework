#!/usr/bin/env python

"""
actions.py: interactions for the RHIT Mobile beta program
"""

import sys
import cgi
import ConfigParser
import json
import os


from dbobjects import initDatabase
from actions import loadPlugins, RequestException, ACTIONS
from urlparse import parse_qs


####### DEBUG #######
import cgitb
cgitb.enable()
#####################


def getDbConnection():
    global config
    config = ConfigParser.ConfigParser()
    config_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_dir, 'config.cfg')
    config.read(config_path)
    return config.get('Database', 'connection')


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

#if __name__ == '__main__': run_script()


class QueryStringArgs:
    def __init__(self, args):
        self.args = parse_qs(args)
    def getvalue(self, key):
        if key not in self.args:
            return None
        return self.args[key][0]
    def __contains__(self, key):
        return key in self.args


class RequestHandler(object):
    def __init__(self, username, password, url):
        self.email_username = username
        self.email_password = password
        self.base_url = url

    def parse_and_execute(self, form):
        if 'action' not in form:
            return self.error('You must specify an action')
        action_name = form.getvalue('action')

        if action_name not in ACTIONS.keys():
            return self.error('Invalid action: %s' % (action_name))

        action = ACTIONS[action_name](self.email_username, self.email_password, self.base_url)
        return action.execute(form)


def application(environ, start_response):
    email_username = config.get('Gmail', 'username')
    email_password = config.get('Gmail', 'password')
    base_url = config.get('Site', 'scriptURL')

    handler = RequestHandler(email_username, email_password, base_url)

    args = QueryStringArgs(environ['QUERY_STRING'])

    try:
        status = '200 OK'
        output = handler.parse_and_execute(form=args)
        response_headers = [('Content-type', 'text/html'),
                            ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
    except RequestException as ex:
        status = "400 Bad Request"
        response_headers = [("content-type", "text/plain")]
        start_response(status, response_headers, sys.exc_info())
        return [ex.json]
    except:
        status = "500 Internal Server Error"
        response_headers = [("content-type", "text/plain")]
        start_response(status, response_headers, sys.exc_info())
        print sys.exc_info()
        return [json.dumps({'success': False, 'errors': 'Internal Server Error'})]


session = initDatabase(getDbConnection())
loadPlugins()

if __name__ == '__main__':
    from paste import httpserver
    httpserver.serve(application, host="localhost", port='8080')
