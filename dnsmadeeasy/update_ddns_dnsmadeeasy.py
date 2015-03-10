#!/usr/bin/env python
#
# Script to update dynamic DNS records at Dnsmadeeasy with HTTPS support.
# Change globs to reflect your settings and set to run from cron.
#
# Requires following non-core modules;
#  * python-requests, https://pypi.python.org/pypi/requests/
#  * python-dns, https://pypi.python.org/pypi/dnspython/
#
# Author: Pekka Wallendahl <wyrmiyu@gmail.com>
# License: MIT, https://github.com/wyrmiyu/ddns-tools/blob/master/LICENSE

from __future__ import print_function
import json
import os
import sys
import requests
import dns.resolver


def error(*objs):
    print("ERROR:", *objs, file=sys.stderr)
    sys.exit(1)


def check_ssl(url):
    try:
        requests.get(url, verify=True)
        return True
    except requests.exceptions.SSLError:
        return error('The SSL certificate for {0} is not valid.'.format(url))


def get_current_ip(url=None):
    url = url or GET_IP_URL
    r = requests.get(url)
    ip = r.text.strip()
    return ip


def get_dns_ip(name=None, target='A'):
    name = name or RECORD_NAME
    q = dns.resolver.query(name, target)
    ip = str(q[0]).strip()
    return ip


def update_ip_to_dns(ip=False, url=None):
    url = url or UPDATE_IP_URL
    if not ip:
        return error('Could not determine the current IP.')
    if not check_ssl(url):
        return False
    params = {
        'username': USERNAME,
        'password': PASSWORD,
        'id': RECORD_ID,
        'ip': ip,
    }
    return requests.get(url, params=params)

BASE_DIR = os.path.dirname(__file__)

try:
    settings = json.loads(open(os.path.join(BASE_DIR, 'settings.json')).read())
except IOError:
    error('No `settings.json` file. Create one from the '
          '`settings.json.sample` file.')
except ValueError:
    error('Invalid `settings.json` file. Check the `settings.json.sample` '
          'file for an example.')

USERNAME = settings.get('USERNAME', None)
PASSWORD = settings.get('PASSWORD', None)
RECORD_ID = settings.get('RECORD_ID', None)
RECORD_NAME = settings.get('RECORD_NAME', None)
GET_IP_URL = settings.get('GET_IP_URL', 'http://www.dnsmadeeasy.com/myip.jsp')
UPDATE_IP_URL = settings.get('UPDATE_IP_URL',
                             'https://www.dnsmadeeasy.com/servlet/updateip')
QUIET = settings.get('QUIET', False)

for key in 'USERNAME', 'PASSWORD', 'RECORD_ID', 'RECORD_NAME':
    if not locals().get(key):
        error('Missing `%s` setting. Check `settings.json` file.' % key)

if __name__ == '__main__':
    current_ip = get_current_ip()
    ip_in_dns = get_dns_ip()
    if current_ip != ip_in_dns:
        print('Current IP differs with DNS record, attempting to update DNS.')
        request = update_ip_to_dns(current_ip)
        if request and request.text == 'success':
            msg = 'Updating record for {0} to {1} was succesful'.format(
                RECORD_NAME, current_ip)
            print(msg)
        else:
            msg = 'Updating record for {0} to {1} failed.'.format(
                RECORD_NAME, current_ip)
            error(msg)
    elif not QUIET:
        print('No changes for DNS record {0} to report.'.format(RECORD_NAME))
