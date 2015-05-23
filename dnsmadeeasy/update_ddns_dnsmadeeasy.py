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
import ConfigParser

import socket
import logging
import sys
import requests
import dns.resolver


logging.basicConfig(format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

CONFIG = {}


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


def get_current_ip(url=None):
    url = url or CONFIG['get_ip_url']
    try:
        return requests.get(url).text.strip()
    except requests.ConnectionError:
        logger.debug(
            'Could not get the current'
            'IP from {0}'.format(CONFIG['get_ip_url']))


def get_dns_ip(name=None, target='A'):
    name = name or CONFIG['record_name']
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


def update_ip_to_dns(ip, url=None):
    url = url or CONFIG['update_ip_url']
    check_ssl(url)
    params = {
        'username': CONFIG['username'],
        'password': CONFIG['password'],
        'id': CONFIG['record_id'],
        'ip': ip,
    }
    return requests.get(url, params=params)


def read_config(config_filename):
    # Read configuration with provided defaults
    config_parser = ConfigParser.RawConfigParser(
        {
            'get_ip_url': 'http://www.dnsmadeeasy.com/myip.jsp',
            'update_ip_url': 'https://www.dnsmadeeasy.com/servlet/updateip',
            'log_level': 'INFO'
        }
    )

    try:
        config_parser.read(config_filename)
        CONFIG['username'] = config_parser.get('settings', 'USERNAME')
        CONFIG['password'] = config_parser.get('settings', 'PASSWORD')
        CONFIG['record_id'] = config_parser.get('settings', 'RECORD_ID')
        CONFIG['record_name'] = config_parser.get('settings', 'RECORD_NAME')
        CONFIG['get_ip_url'] = config_parser.get('settings', 'GET_IP_URL')
        CONFIG['update_ip_url'] = config_parser.get('settings', 'UPDATE_IP_URL')
        CONFIG['log_level'] = config_parser.get('settings', 'LOG_LEVEL')
    except ConfigParser.MissingSectionHeaderError:
        error('Invalid configuration file.')
    except ConfigParser.NoOptionError as e:
        error("Required option '{}' is not present in section '{}' of the "
              "'settings.ini' file.".format(e.option, e.section))

    try:
        logger.setLevel(getattr(logging, CONFIG['log_level']))
    except AttributeError:
        error('Invalid `log_level` setting. Check `settings.ini` file. Valid '
              'log levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL.')

if __name__ == '__main__':
    read_config('settings.ini')
    current_ip = get_current_ip()
    if current_ip:
        if current_ip != get_dns_ip():
            logger.debug('Current IP differs with DNS record, attempting to '
                         'update DNS.')
            request = update_ip_to_dns(current_ip)
            if request and request.text == 'success':
                logger.info('Updating record for {0} to {1} was '
                            'succesful.'.format(CONFIG['record_name'], current_ip))
            else:
                error('Updating record for {0} to {1}'
                      'failed.'.format(CONFIG['record_name'], current_ip))
        else:
            logger.debug(
                'No changes for DNS record {0} '
                'to report.'.format(CONFIG['record_name']))
