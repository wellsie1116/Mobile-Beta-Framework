
from actions import *

ACTION_FILTER = ['test', 'builds']
    
def error(*args):
    raise RequestException(*args)

def success(vals={}):
    return json.dumps(dict(vals.items() + {'success': True}.items()))

def performAction(action, form):
    if action == 'test':
        return "This is from a plugin!"
        #return json.dumps(dict(vals.items() + {'success': True}.items()))
        #return True
    elif action == 'builds':
        if 'platform' not in form:
            return error('Platform is required')
        platform = Platform.from_identifier(form.getvalue('platform'))
        if platform is None:
            return error('Invalid platform')
        rolling, nightly, beta, official = Build.latest_for_platform(platform)
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
        return success(result)
