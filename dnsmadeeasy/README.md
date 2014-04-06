update_ddns_dnsmadeeasy.py
==========================

Script to update dynamic DNS records at Dnsmadeeasy with HTTPS support.

Change globs to reflect your settings and set the script to run from cron.

Requires following non-core modules;
  * python-requests, https://pypi.python.org/pypi/requests/
  * python-dns, https://pypi.python.org/pypi/dnspython/


## To-Do
  * Implement debug-mode to include verbosity for error messages and traces
  * Replace inline glob-based confs with ConfigParser and/or argparse
