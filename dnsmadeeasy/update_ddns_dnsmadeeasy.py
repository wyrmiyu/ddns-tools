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
import sys
import requests
from dns.resolver import Resolver

USERNAME = 'your_username'  # <- REPLACE
PASSWORD = 'dns_record_password'  # <- REPLACE
RECORD_ID = 'dns_record_id'  # <- REPLACE
RECORD_NAME = 'recordname.example.com'  # <- REPLACE
RECORD_NAMESERVERS = ('0.0.0.0',)  # <- REPLACE
GET_IP_URL = 'http://www.dnsmadeeasy.com/myip.jsp'
UPDATE_IP_URL = 'https://www.dnsmadeeasy.com/servlet/updateip'


def error(*objs):
    print("ERROR:", *objs, file=sys.stderr)
    return False


def check_ssl(url):
    try:
        requests.get(url, verify=True)
        return True
    except requests.exceptions.SSLError:
        return error('The SSL certificate for {0} is not valid.'.format(url))


def get_current_ip(url=GET_IP_URL):
    r = requests.get(url)
    ip = r.text.strip()
    return ip


def get_dns_ip(name=RECORD_NAME, target='A', nameservers=RECORD_NAMESERVERS):
    resolver = Resolver(configure=False)
    resolver.nameservers = RECORD_NAMESERVERS
    q = resolver.query(name, target)
    ip = str(q[0]).strip()
    return ip


def update_ip_to_dns(ip=False, url=UPDATE_IP_URL):
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

if __name__ == '__main__':
    exit_code = 0
    current_ip = get_current_ip()
    ip_in_dns = get_dns_ip()
    if current_ip == ip_in_dns:
        print('No changes for DNS record {0} to report.'.format(RECORD_NAME))
    else:
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
            exit_code = 1
    sys.exit(exit_code)
