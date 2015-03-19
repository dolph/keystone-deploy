"""Rerun the latest builds on Travis CI.

This is largely derived from:

    https://github.com/hansjorg/travis-python-client/

For Travis CI's API docs see:

    https://api.travis-ci.org/docs/

"""

import argparse
import json
import urllib2


TRAVIS_BASE = 'https://api.travis-ci.org'


def get_last_build_on_branch(owner_name, repo_name, branch):
    return call(
        '/repos/{}/{}/branches/{}'.format(owner_name, repo_name, branch))


def restart_build(travis_token, build_id):
    return call('/requests', travis_token, {'build_id': build_id})


def get_travis_token(github_token):
    """Get a Travis access token for use with secure endpoints.

    Requires a GitHub OAuth token with same or greater scope than used
    by Travis (public_repo).

    """

    token = None
    response = call(
        '/auth/github', data={'github_token': github_token})

    if 'access_token' in response:
        token = response['access_token']

    return token


def call(url, token=None, data=None):
    json_data = None
    if data:
        json_data = json.dumps(data)

    request = urllib2.Request(TRAVIS_BASE + url, json_data)

    if token:
        request.add_header('Authorization', 'token ' + token)
    request.add_header('Content-Type', 'application/json; charset=UTF-8')

    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        msg = e.read()

        print('Error response from Travis: ' + str(e.code))
        print(msg)

        if e.code == 403:
            raise AuthException(msg)
        return None

    response_data = response.read()

    result = None
    if response_data:
        encoding = response.headers.getparam('charset')

        if not encoding:
            encoding = 'utf-8'

        try:
            result = json.loads(response_data.decode(encoding))
        except ValueError:
            print('Unable to deserialize json. Response: "{}"'.
                  format(response_data))
    return result


class AuthException(Exception):
    pass


if __name__ == "__main__":
    owner_name = 'dolph'
    repo_name = 'keystone-deploy'
    branches = (
        'master',
        'fernet-tokens',
        'pki-tokens',
        'pkiz-tokens',
        'v3-only')

    parser = argparse.ArgumentParser()
    parser.add_argument('github_token')
    args = parser.parse_args()

    travis_token = get_travis_token(args.github_token)

    for branch in branches:
        last_build = get_last_build_on_branch(owner_name, repo_name, branch)
        result = restart_build(travis_token, last_build['branch']['id'])
        print('Restarting build for branch: %s' % branch)
        print(json.dumps(result, sort_keys=True, indent=2))
