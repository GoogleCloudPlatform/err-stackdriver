from errbot.backends.test import testbot  # noqa

from os import path

LOCAL_SERVACC = 'servacc.json'

extra_config = {'GOOGLE_SERVICE_ACCOUNT': LOCAL_SERVACC}
extra_plugin_dir = path.join(path.dirname(path.realpath(__file__)), '..')


def prepare(tb):
    """
    Disable the collection and set the latching project for the service account.

    :param tb: testbot
    """
    assert 'Collection of any usage statistics has been explicitely disabled.' in tb.exec_command('!collect disagree')
    assert 'Project errbot-1127 set.' in tb.exec_command('!project set errbot-1127')


def test_vm_list(testbot):
    prepare(testbot)
    assert 'Bucket errbot-graphs set.' in testbot.exec_command('!bucket set errbot-graphs')
    assert 'name' in testbot.exec_command('!vm list')


def test_add_remove_list_queries(testbot):
    prepare(testbot)
    assert 'Your query has been stored, you can execute it with !bq 0.' in testbot.exec_command(
                           "!bq addquery SELECT metadata.timestamp, protoPayload.resource AS version "
                           "FROM (TABLE_DATE_RANGE(version_logs.appengine_googleapis_com_request_log_, "
                           "DATE_ADD(CURRENT_TIMESTAMP(), -1, 'DAY'), CURRENT_TIMESTAMP()))")
    assert '0' in testbot.exec_command("!bq queries")
    assert '0 queries have been defined.' in testbot.exec_command("!bq delquery 0")
