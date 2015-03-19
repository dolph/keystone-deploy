"""Rerun the latest builds on Travis CI.

This is largely derived from:

    https://github.com/hansjorg/travis-python-client/

For Travis CI's API docs see:

    https://api.travis-ci.org/docs/

"""

import argparse
import json
import requests


TRAVIS_ENDPOINT = 'https://api.travis-ci.org'


def get_last_build_on_branch(owner_name, repo_name, branch):
    return GET(
        '/repos/{}/{}/branches/{}'.format(owner_name, repo_name, branch))


def restart_build(travis_token, build_id):
    return POST('/requests', travis_token, data={'build_id': build_id})


def get_travis_token(github_token):
    """Get a Travis access token for use with secure endpoints.

    Requires a GitHub OAuth token with same or greater scope than used
    by Travis (public_repo).

    """

    r = POST(
        '/auth/github',
        data={'github_token': github_token})
    return r['access_token']


def request(method, path, headers=None, data=None):
    if headers is None:
        headers = {}

    headers['Accept'] = 'application/vnd.travis-ci.2+json'

    r = requests.request(
        method=method,
        url=TRAVIS_ENDPOINT + path,
        headers=headers,
        data=json.dumps(data) if data else None)

    return r.json()

def GET(path):
    """Send a GET request to the Travis CI API."""
    return request('GET', path)


def POST(path, token=None, data=None):
    """Send a POST request to the Travis CI API."""
    headers = {
        'Content-Type': 'application/json; charset=UTF-8'}

    if token:
        headers['Authorization'] = 'token ' + token

    return request('POST', path, headers, data)


if __name__ == "__main__":
    owner_name = 'dolph'
    repo_name = 'keystone-deploy'
    branches = (
        'master',
        'fernet-tokens',
        'pki-tokens',
        'pkiz-tokens',
        'v3-only',)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'github_token', help='The Github token used to authenticate with Travis CI.')
    args = parser.parse_args()

    travis_token = get_travis_token(args.github_token)

    for branch in branches:
        last_build = get_last_build_on_branch(owner_name, repo_name, branch)
        result = restart_build(travis_token, last_build['branch']['id'])
        for flash in result['flash']:
            for key, value in flash.iteritems():
                print('%s (%s): %s' % (branch, key.upper(), value))
