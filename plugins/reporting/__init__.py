from actions import Action
from dbobjects import  TestExecution


class TestReports(Action):
    def __init__(self, username, password, url):
        Action.__init__(self, username, password, url)

    def execute(self, form):
        result = {'Failures':[]}
        tests = TestExecution.all()
        success = 0.0
        for test in tests:
            if test.passed:
                success += 1
                continue
            rslt = {'Device' : test.device.platform.name,
                    'Build' : test.build.build_number,
                    'Time' : str(test.time),
                    'Error' : test.content}
            result['Failures'].append(rslt)
        result['SuccessRate'] = "%.4f" % (success / len(tests))
        return self.success(result)


def getPlugins():
    return {'getTestReports' : TestReports}
