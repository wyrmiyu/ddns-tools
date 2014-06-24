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
import os
import itertools
import requests
import dns.resolver
import json

USERNAME = 'username '  # <- REPLACE (Actually this one is not needed)
PASSWORD = 'password'  # <- REPLACE

GET_IP_URL = 'http://www.dnsmadeeasy.com/myip.jsp'
UPDATE_IP_URL = 'https://www.dnsmadeeasy.com/servlet/updateip'

RECORD_ID = '11112233'  # <- REPLACE
RECORD_NAME = 'www.domain.com'  # <- REPLACE

# If the EXPORTJSONPATH param is set, the script will additionally for each domain json export file the record name,
# passwords and ids. You can export the JSON-Files from your DNSmadeeasy control-panel (under the tab "Reporting").
# This script supports different passwords for subdomains in each domain by creating a new Request for each unique PW.
EXPORTJSONPATH = None
#EXPORTJSONPATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "domains-exports/")


def get_record_name_from_json(path):
    with open(path) as json_data:
        data = json.load(json_data)
        return data['name']


def get_record_pw_and_id_from_json(path):
    with open(path) as json_data:
        data = json.load(json_data)
        idlist = []
        for i in data['records']:
            element = next((item for item in idlist if item["password"] == i['password']), None)
            if element:
                if len(element['records']) > 20:
                    print("WARNING: Update might fail. No more than 20 ID's per update-request!")
                element['records'].append(i['id'])
            else:
                iddict = {'password': i['password'], 'records': [i['id']]}
                idlist.append(iddict)
        return idlist


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


def get_dns_ip(name=RECORD_NAME, target='A'):
    q = dns.resolver.query(name, target)
    ip = str(q[0]).strip()
    return ip


def update_ip_to_dns(ip=None, url=UPDATE_IP_URL, password=PASSWORD, idstr=RECORD_ID):
    if not ip:
        return error('Could not determine the current IP.')
    if not check_ssl(url):
        return False
    params = {
        'username': USERNAME,
        'password': password,
        'id': idstr,
        'ip': ip,
    }
    return requests.get(url, params=params)


def request_call(password=PASSWORD, idstr=RECORD_ID):
    request = update_ip_to_dns(ip=current_ip, password=password, idstr=idstr)
    if request and request.text == 'success':
        msg = 'Updating record for {0} to {1} was succesful'.format(record_name, current_ip)
        print(msg)
        return True
    else:
        msg = 'Updating record for {0} to {1} failed. Error-Code: "{2}"'.format(
        record_name, current_ip, request.text)
        error(msg)
        return False


if __name__ == '__main__':

    exit_code = 0
    current_ip = get_current_ip()
    if EXPORTJSONPATH:
        iterator = itertools.chain('0', os.listdir(EXPORTJSONPATH))
    else:
        iterator = '0'
    for fn in iterator:
        if fn == '0' or fn.endswith('.json'):
            if fn == '0':
                filepath = None
                record_name = RECORD_NAME
                ip_in_dns = get_dns_ip()
            else:
                filepath = os.path.abspath(os.path.join(EXPORTJSONPATH, fn))
                record_name = get_record_name_from_json(filepath)
                ip_in_dns = get_dns_ip(name=record_name)

            if current_ip == ip_in_dns:
                print('No changes for DNS record {0} to report.'.format(record_name))
            else:
                print('Current IP differs with DNS record {0}, attempting to update DNS.'.format(record_name))
                if filepath:
                    idlist = get_record_pw_and_id_from_json(filepath)
                    for i in idlist:
                        idstring = ','.join(str(x) for x in i['records'])
                        if not request_call(password=i['password'], idstr=idstring):
                            exit_code = 1
                else:
                    if not request_call():
                        exit_code = 1
    sys.exit(exit_code)
