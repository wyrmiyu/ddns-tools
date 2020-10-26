#!/usr/bin/env python
#
# Script to update dynamic DNS records at Dnsmadeeasy with HTTPS support.
# Put your settings in settings.json in the same folder with the script 
# and set to run from cron.
#
# Requires following non-core modules;
#  * python-requests, https://pypi.python.org/pypi/requests/
#  * python-dns, https://pypi.python.org/pypi/dnspython/
#
# Author: Pekka Wallendahl <wyrmiyu@gmail.com>
# License: MIT, https://github.com/wyrmiyu/ddns-tools/blob/master/LICENSE

from __future__ import print_function

import socket
import json
import logging
import os
import sys
import requests
import dns.resolver

logging.basicConfig(format='%(levelname)s: %(message)s')

logger = logging.getLogger(__name__)

BASE_DIR   = os.path.dirname(__file__)

DEFAULT_LOG_LEVEL = 'INFO'

def error(message):
    """
    Log an error and exit.
    """
    logger.error(message)
    sys.exit(1)


def check_ssl(url):
    try:
        requests.get(url, verify=True)
    except requests.exceptions.SSLError:
        error('The SSL certificate for {0} is not valid.'.format(url))


class DME_Account:
    def __init__(self, username, password,
            url = 'http://myip.dnsmadeeasy.com/'):
        # Initialise DME account
        self.records = []
        self.USERNAME = settings.get('USERNAME', None)
        self.PASSWORD = settings.get('PASSWORD', None)
        self.LOG_LEVEL  = settings.get('LOG_LEVEL',
                DEFAULT_LOG_LEVEL)
        self.GET_IP_URL = url
        # Validate mandatory account parameters
        for opt in 'USERNAME', 'PASSWORD':
            if not self.__dict__[opt]:
                error('Missing `{0}` setting. Check `settings.json` file.'.format(opt))
        # Make sure we are setting a sane log level
        try:
            formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            screen_handler = logging.StreamHandler(stream=sys.stdout)
            screen_handler.setFormatter(formatter)
            logger.setLevel(getattr(logging, self.LOG_LEVEL))
            logger.addHandler(screen_handler)
        except AttributeError:
            error('Invalid `LOG_LEVEL` setting. Check `settings.json` file. Valid '
                  'log levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL.')

    def get_current_ip(self, check_ip_url=None):
        url = check_ip_url or self.GET_IP_URL
        logger.debug('Using {0} to obtain current IP address'.format(url))
        try:
            return requests.get(url).text.strip()
        except requests.ConnectionError:
            logger.debug('Could not get the current IP from {0}'.format(url))

    def add_record(self, settings):
        record = DME_Record(setting, account=self)
        self.records.append(record)
        return record


class DME_Record:

    def __init__(self, settings, account):
        # Initialise DME record
        self.RECORD_ID = settings.get('RECORD_ID', None)
        self.RECORD_NAME = settings.get('RECORD_NAME', None)
        self.account = account
        # Validate mandatory record parameters
        for opt in 'RECORD_ID', 'RECORD_NAME':
            if not self.__dict__[opt]:
                error('Missing `{0}` setting. Check `settings.json` file.'.format(opt))


    def get_dns_ip(self, name=None, target='A'):
        name = name or self.RECORD_NAME
        bits = name.split('.')
        while bits:
            try:
                ns = str(dns.resolver.query('.'.join(bits), 'NS')[0])
            except:
                bits.pop(0)
            else:
                ns = socket.gethostbyname(ns)
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [ns]
                q = resolver.query(name, target)
                ip = str(q[0]).strip()
                return ip
        error('Could not get the authoritative name server for {0}.'.format(name))


    def update_ip_to_dns(self, ip, url=None):
        url = url or self.account.GET_IP_URL
        check_ssl(url)
        params = {
            'username': self.account.USERNAME,
            'password': self.account.PASSWORD,
            'id': self.RECORD_ID,
            'ip': ip,
        }
        return requests.get(url, params=params)

    def do_update(self, current_ip):
            if current_ip != self.get_dns_ip():
                logger.debug('Current IP differs with DNS record, attempting to update DNS.')
                response = self.update_ip_to_dns(current_ip)
                if response and response.text == 'success':
                    logger.info('Updating record for {0} to {1} was '
                                'succesful.'.format(self.RECORD_NAME, current_ip))
                else:
                    error('Updating record for {0} to {1} failed: {2}'.format(
                        self.RECORD_NAME, current_ip, response.text))
            else:
                logger.debug( 'No changes for DNS record {0} to report.'.format(record.RECORD_NAME))






if __name__ == '__main__':
    # Load settings from JSON file
    try:
        settings = json.loads(open(os.path.join(BASE_DIR, 'settings.json')).read())
    except IOError:
        error('No `settings.json` file. Create one from the '
              '`settings.json.sample` file.')
    except ValueError:
        error('Invalid `settings.json` file. Check the `settings.json.sample` '
              'file for an example.')

    # Process and validate top-level settings
    USERNAME = settings.get('USERNAME', None)
    PASSWORD = settings.get('PASSWORD', None)
    UPDATE_IP_URL = settings.get('UPDATE_IP_URL', 'https://www.dnsmadeeasy.com/servlet/updateip')

    dme = DME_Account(username=USERNAME, password=PASSWORD)

    current_ip = dme.get_current_ip()
    logger.debug('Current IP address is {0}.'.format(current_ip))
    if current_ip:
        # Process each record separately
        for setting in settings['records']:
            logger.debug("Processing record {0}.".format(setting['RECORD_NAME']))
            record = dme.add_record(setting)
            record.do_update(current_ip)
