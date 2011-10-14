import os
import json
import threading
import smtplib

from dbobjects import  Build, Carrier, Device, Feedback, Platform, TestExecution, Update, User
import urllib
import uuid
import datetime


class RequestException(Exception):
    def __init__(self, *args):
        self.json = json.dumps({'success': False, 'errors': args})


class Action:
    def __init__(self, username, password, url):
        self.email_username = username
        self.email_password = password
        self.base_url = url

    def error(self, *args):
        raise RequestException(*args)

    def execute(self, form):
        pass

    def html(self, content):
        return ('<!DOCTYPE html><html><head></head><body>%s</body></html>' % content)

    def sendEmail(self, to_addr, reply_addr, subject, msg, username, password, url):
        class EmailSender(threading.Thread):
            @staticmethod
            def run():
                msg = ('From: RHIT Mobile Beta <rhitmobile@gmail.com>\r\n'
                       'To: %s\r\n'
                       'Reply-To: %s\r\n'
                       'Subject: %s\r\n\r\n%s') % (to_addr, reply_addr, subject, msg)

                server = smtplib.SMTP('smtp.gmail.com:587')
                server.starttls()
                server.login(username, password, url)
                try:
                    server.sendmail('RHIT Mobile Beta Program', (to_addr,), msg)
                except Exception:
                    pass # JUST EAT IT
                server.quit()

        EmailSender().start()

    def success(self, vals={}):
        return json.dumps(dict(vals.items() + {'success': True}.items()))


class Register(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
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

        build = Build.from_number_and_platform(build_number, platform)

        if build is None:
            return self.error('Invalid build number')

        if user is None:
            results['newUser'] = True

            user = User()
            user.name = name
            user.email = email
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
            self.sendEmail(email, platform.owner_email, 'Verify your email and devices', msg, self.email_username, self.email_password)
            name_msg = ('A new user has registered for your platform\'s beta '
                        'program:\n\nName: %s\nEmail: %s\n\nTo change this user\'s '
                        'name, use the following link:\n\n%s\n\nLet me know if '
                        'something breaks\nJimmy') % (user.name, user.email, name_change_url)
            self.sendEmail(platform.owner_email, 'theisje@rose-hulman.edu', 'New user %s registered' % user.email, name_msg, self.email_username, self.email_password)
        else:
            results['newUser'] = False

        if device is None:
            results['newDevice'] = True
            device = Device()
            device.unique_identifier = device_id
            device.owner = user
            device.platform = platform
            device.carrier = carrier
            device.operating_system = os_info
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
                self.send_email(email, platform.owner_email, 'Verify your new device', msg, self.email_username, self.email_password)
            results['authToken'] = device.auth_token
        else:
            results['newDevice'] = False

            if device.owner.email != email:
                return self.error('Device already registered to another user')

            device.auth_token = str(uuid.uuid4())
            device.platform = platform
            device.carrier = carrier
            device.os_info = os_info
            device.model = model
            device.current_build = build
            device.save()
            results['authToken'] = device.auth_token

        return self.success(results)


class LatestBuilds(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'platform' not in form:
            return self.error('Platform is required')
        platform = Platform.from_identifier(form.getvalue('platform'))
        if platform is None:
            return self.error('Invalid platform')
        rolling, nightly, beta, official = Build.latest_for_platform(platform) #@UnusedVariable
        result = {}
        if rolling is None:
            result['rolling'] = None
        else:
            result['rolling'] = {'buildNumber': rolling.build_number,
                                'viewURL': rolling.view_url,
                                'downloadURL': rolling.download_url}
        if official is None:
            result['official'] = None
        else:
            result['official'] = {'buildNumber': official.build_number,
                                  'viewURL': official.view_url,
                                  'downloadURL': official.download_url}
        return self.success(result)


class NotificationUpdate(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'authToken' not in form:
            return self.error('Auth Token is required')
        if 'toBuildNumber' not in form:
            return self.error('Destination Build is required')
        device = Device.from_auth_token(form.getvalue('authToken'))
        if device is None:
            return self.error('Authentication failed')
        to_build = Build.from_number_and_platform(form.getvalue('toBuildNumber'), device.platform)
        if to_build is None:
            return self.error('Invalid destination build number')
        update = Update()
        update.device = device
        update.to_build = to_build
        device.current_build = to_build
        update.time = datetime.datetime.now()
        update.save()
        device.save()
        return self.success()


class UserVerification(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'verificationCode' not in form:
            return self.html('<h1>Verification Failed</h1>Verification code is required')
        ver_code = form.getvalue('verificationCode')
        user = User.from_verification_code(ver_code)
        if user is None:
            return self.html('<h1>Verification Failed</h1>Invalid verification code')
        if user.verified:
            return self.html('<h1>Account already verified</h1>')
        user.verified = True
        user.save()
        devices = 'Devices also verified:<ul>'
        for device in user.devices:
            if not device.verified:
                device.verified = True
                devices += '<li>%s (%s)</li>' % (device.model, device.operating_system)
                device.save()
        devices += '</ul>'
        return self.html('<h1>Account Verified</h1>' + devices)


class DeviceVerification(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'verificationCode' not in form:
            return self.html('<h1>Verification Failed</h1>Verification code is required')
        ver_code = form.getvalue('verificationCode')
        device = Device.from_verification_code(ver_code)
        if device is None:
            return self.html('<h1>Verification Failed</h1>Invalid verification code')
        if device.verified:
            return self.html('<h1>Device Already Verified</h1>')
        device.verified = True
        device.save()
        return self.html('<h1>Device Verified</h1>')


class UserNameChange(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'verificationCode' not in form:
            return self.html('<h1>Verification Failed</h1>Verification code is required')
        ver_code = form.getvalue('verificationCode')
        device = Device.from_verification_code(ver_code)
        if device is None:
            return self.html('<h1>Verification Failed</h1>Invalid verification code')
        if device.verified:
            return self.html('<h1>Device Already Verified</h1>')
        device.verified = True
        device.save()
        return self.html('<h1>Device Verified</h1>')


class FeedbackSubmission(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'authToken' not in form:
            return self.error('Auth Token is required')
        if 'content' not in form:
            return self.error('Content is required')
        device = Device.from_auth_token(form.getvalue('authToken'))
        if device is None:
            return self.error('Authentication failed')
        feedback = Feedback()
        feedback.build = device.current_build
        feedback.device = device
        feedback.content = form.getvalue('content')
        feedback.time = datetime.datetime.now()
        feedback.save()
        return self.success()


class TestResultsSubmission(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'authToken' not in form:
            return self.error('Auth Token is required')
        if 'passed' not in form:
            return self.error('Pass Status is required')
        device = Device.from_auth_token(form.getvalue('authToken'))
        if device is None:
            return self.error('Authentication failed')
        passed = form.getvalue('passed').lower() == 'true'
        test = TestExecution()
        test.build = device.current_build
        test.device = device
        test.content = form.getvalue('content')
        test.passed = passed
        test.time = datetime.datetime.now()
        test.save()
        return self.success()


class BuildPublication(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'publishingKey' not in form:
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
        build = Build()
        build.build_number = form.getvalue('buildNumber')
        build.platform = platform
        classification = form.getvalue('classification')
        if not classification: classification = 'official'
        build.classification = classification
        build.view_url = form.getvalue('viewURL')
        build.download_url = form.getvalue('downloadURL')
        build.save()
        return self.html('<h1>Build Published</h1>')


class PublishingKeyRenewal(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        if 'platform' not in form:
            return self.html('<h1>Renewal Failed</h1>Platform required')
        platform = Platform.from_identifier(form.getvalue('platform'))
        if platform is None:
            return self.html('<h1>Renewal Failed</h1>Invalid platform')
        platform.publishing_key = str(uuid.uuid4())
        platform.save()
        publish_args = {'action': 'publishBuild',
                        'publishKey': platform.publishing_key}
        publish_url = self.base_url + urllib.urlencode(publish_args)
        msg = ('The publishing key for %s has been renewed. Use the link below to '
               'publish builds for %s from now on.\n\nPublishing Key: %s\n\n%s\n\n'
               'Thanks\nJimmy') % (platform.name, platform.name, platform.publishing_key,
                                   publish_url)
        self.sendEmail(platform.owner_email, 'theisje@rose-hulman.edu', 'Publishing Key Renewed', msg, self.email_username, self.email_password)
        return self.html('<h1>Publishing Key Renewed</h1>')


ACTIONS = {
    'register': Register,
    'verifyUser': UserVerification,
    'verifyDevice': DeviceVerification,
    'changeUserName': UserNameChange,
    'submitFeedback': FeedbackSubmission,
    'submitTestResults': TestResultsSubmission,
    'notifyOfUpdate': NotificationUpdate,
    'getLatestBuilds': LatestBuilds,
    'publishBuild': BuildPublication,
    'renewPublishingKey': PublishingKeyRenewal,
    }


def loadPlugins():
    global plugins
    plugins = []

    # check subfolders
    modulePath = os.path.abspath(os.path.dirname(__file__))
    pluginsPath = modulePath + os.sep + "plugins"
    lst = os.listdir(pluginsPath)
    pluginDirectories = []
    for d in lst:
        s = pluginsPath + os.sep + d
        if os.path.isdir(s) and os.path.exists(s + os.sep + "__init__.py"):
            pluginDirectories.append(d)

    # load the modules
    for d in pluginDirectories:
        plugin = __import__("plugins." + d, fromlist=["*"])
        dict = plugin.getPlugins()
        for action_name, action in dict.items():
            ACTIONS[action_name] = action

if __name__ == '__main__':
    loadPlugins()
    print ACTIONS.items()
