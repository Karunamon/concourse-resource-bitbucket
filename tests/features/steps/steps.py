import subprocess
import httpretty
import os
from behave import given, then


def good_dict():
    return {'source': {
                'bitbucket_url': 'https://test.bitbucket.local/',
                'debug': True,
                'username': 'ValidUser',
                'password': 'password',
            },
            'params': {
                'build_status': 'SUCCESSFUL'
            }
            }


def good_status_dict():
    build_url = "https://concourse.local/pipelines/testing/jobs/1/builds/1"
    return {
        "state": 'INPROGRESS',
        "key": os.environ["BUILD_JOB_NAME"],
        "name": os.environ["BUILD_NAME"],
        "url": build_url,
        "description": "Concourse build %s" % os.environ["BUILD_ID"]
    }


@given(u'I have used the "in" script')
def step_impl(context):
    context.inscript = "scripts/in"


@then(u'I should get back an empty JSON doc')
def step_impl(context):
    out = subprocess.check_output(context.inscript).strip()
    assert "{}" in str(out)


@given(u'I have used the "check" script')
def step_impl(context):
    context.checkscript = "scripts/check"


@then(u'I should get back an empty array')
def step_impl(context):
    out = subprocess.check_output(context.checkscript).strip()
    assert "[]" in str(out)


@given(u'I used incorrect credentials to access Bitbucket')
def step_impl(context):
    d = good_dict()
    d['source']['username'] = 'InvalidUser'
    context.bad_login = d
    context.good_build_url = d['source']['bitbucket_url'] + "rest/build-status/1.0/commits/6e6a15d3161fd761dcb67f49ff5d057a9e527406"


@then(u'I should get a 401 response and an error message')
def step_impl(context):
    d = context.bad_login
    assert d['source']['username'] != 'ValidUser'
    httpretty.enable()
    httpretty.register_uri(
            httpretty.POST,
            context.good_build_url,
            body='{"errors":[{"context":null,"message":"Authentication failed. Please check your credentials and try again.","exceptionName":"com.atlassian.bitbucket.auth.IncorrectPasswordAuthenticationException"}]}',
            status=401
    )
    from scripts.bitbucket import post_result, err
    result = post_result(context.good_build_url, d['source']['username'], d['source']['password'], False, good_status_dict(), True)
    assert result.status_code == 401
    httpretty.disable()
    httpretty.reset()



@given(u'I\'m trying to update the status of a repo I don\'t have rights to')
def step_impl(context):
    d = good_dict()
    context.good_login = d
    context.bad_build_url = d['source']['bitbucket_url'] + "rest/build-status/1.0/commits/6e6somethingicantaccess/"


@then(u'I should get a 403 response and an error message')
def step_impl(context):
    d = context.good_login
    assert context.good_login['source']['username'] == 'ValidUser'
    httpretty.enable()
    httpretty.register_uri(
            httpretty.POST,
            context.bad_build_url,
            body='{"errors":[{"context":null,"message":"You are not permitted to access this resource","exceptionName":"com.atlassian.bitbucket.AuthorisationException"}]}',
            status=403
    )
    from scripts.bitbucket import post_result, err
    result = post_result(context.bad_build_url, d['source']['username'], d['source']['password'], False, good_status_dict(), True)
    assert result.status_code == 403
    httpretty.disable()
    httpretty.reset()




@given(u'I have configured this resource correctly')
def step_impl(context):
    context.good_login = good_dict()
    context.good_build_url = context.good_login['source']['bitbucket_url'] + "rest/build-status/1.0/commits/6e6a15d3161fd761dcb67f49ff5d057a9e527406"

@then(u'I should get a 204 response')
def step_impl(context):
    d = context.good_login
    assert context.good_login['source']['username'] == 'ValidUser'
    assert 'somethingicantaccess' not in context.good_build_url
    httpretty.enable()
    httpretty.register_uri(
            httpretty.POST,
            context.good_build_url,
            status=204
    )
    from scripts.bitbucket import post_result, err
    result = post_result(context.good_build_url, d['source']['username'], d['source']['password'], False, good_status_dict(), True)
    assert result.status_code == 204
    context.goodresult = result
