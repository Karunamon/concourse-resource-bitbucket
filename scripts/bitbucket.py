#!/usr/bin/env python

import sys
import json
import requests
import os
import subprocess
from requests.auth import HTTPBasicAuth


# Convenience method for writing to stderr. Coerces input to a string.
def err(txt):
    sys.stderr.write(str(txt) + "\n")


# Convenience method for pretty-printing JSON
def json_pp(json_object):
    if isinstance(json_object, dict):
        json.dumps(json_object,
                   sort_keys=True,
                   indent=4,
                   separators=(',', ':')) + "\n"
    elif isinstance(json_object, str):
        json.dumps(json.loads(json_object),
                   sort_keys=True,
                   indent=4,
                   separators=(',', ':')) + "\n"
    else:
        raise NameError('Must be a dictionary or json-formatted string')


def parse_stdin():
    return json.loads(sys.stdin.read())


def post_result(url, user, password, verify, data, debug):
    r = requests.post(
        url,
        auth=HTTPBasicAuth(user, password),
        verify=verify,
        json=data
        )

    if debug:
        err("Request result: " + str(r))

    if r.status_code == 403:
        err("HTTP 403 Forbidden - Does your bitbucket user have rights to the repo?")
    elif r.status_code == 401:
        err("HTTP 401 Unauthorized - Are your bitbucket credentials correct?")

    # All other errors, just dump the JSON
    if r.status_code != 204:  # 204 is a success per Bitbucket docs
        err(json_pp(r.json()))

    return r

# Stop all this from executing if we were imported, say, for testing.
if 'scripts.bitbucket' != __name__:

    # Check and in are useless for this resource, so just return blank objects
    if 'check' in sys.argv[0]:
        print('[]')
        sys.exit(0)
    elif 'in' in sys.argv[0]:
        print('{}')
        sys.exit(0)

    j = parse_stdin()

    # Configuration vars
    url = j['source']['bitbucket_url'] + 'rest/build-status/1.0/commits/'
    verify_ssl = j['source'].get('verify_ssl', True)
    debug = j['source'].get('debug', False)
    username = j['source']['bitbucket_username']
    password = j['source']['bitbucket_password']
    repository_type = j['source'].get('repository_type', 'git')

    build_status = j['params']['build_status']
    artifact_dir = "%s/%s" % (sys.argv[1], j['params']['repo'])

    if debug:
        err("--DEBUG MODE--")

    if repository_type == 'git':
        # It is recommended not to parse the .git folder directly due to garbage
        # collection. It's more sustainable to just install git and parse the output.
        commit_sha = subprocess.check_output(
                ['git', '-C', artifact_dir, 'rev-parse', 'HEAD']
        ).strip()
    elif repository_type == 'mercurial':
        commit_sha = subprocess.check_output(
                ['hg', 'log', '--cwd', artifact_dir, '--limit', '1', '--rev', '.', '--template', "{node}"]
        ).strip()
    else:
        err("Invalid repository type, must be: git or mercurial")
        exit(1)

    if debug:
        err("Commit: " + str(commit_sha))

    # The build status can only be one of three things
    if 'INPROGRESS' not in build_status and \
                    'SUCCESSFUL' not in build_status and \
                    'FAILED' not in build_status:
        err("Invalid build status, must be: INPROGRESS, SUCCESSFUL, or FAILED")
        exit(1)

    # Squelch the nanny message if we disabled SSL
    if verify_ssl is False:
        requests.packages.urllib3.disable_warnings()
        if debug:
            err("SSL warnings disabled\n")

    # Construct the URL and JSON objects
    post_url = url + commit_sha
    if debug:
        err(json_pp(j))
        err("Notifying %s that build %s is in status: %s" %
            (post_url, os.environ["BUILD_NAME"], build_status))

    build_url = "{url}/pipelines/{pipeline}/jobs/{jobname}/builds/{buildname}".format(
            url=os.environ['ATC_EXTERNAL_URL'],
            pipeline=os.environ['BUILD_PIPELINE_NAME'],
            jobname=os.environ['BUILD_JOB_NAME'],
            buildname=os.environ['BUILD_NAME'],
    )

    # https://developer.atlassian.com/bitbucket/server/docs/latest/how-tos/updating-build-status-for-commits.html
    js = {
        "state": build_status,
        "key": os.environ["BUILD_JOB_NAME"],
        "name": os.environ["BUILD_NAME"],
        "url": build_url,
        "description": "Concourse build %s" % os.environ["BUILD_ID"]
    }

    if debug:
        err(json_pp(js))

    r = post_result(post_url, username, password, verify_ssl, js, debug)
    if r.status_code != 204:
        sys.exit(1)

    status_js = {"version": {"ref": commit_sha}}

    if debug:
        err("Returning to concourse:\n" + json_pp(status_js))

    print(json.dumps(status_js))
