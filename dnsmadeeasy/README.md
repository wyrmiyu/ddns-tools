## update_ddns_dnsmadeeasy.py

Script to update dynamic DNS records at Dnsmadeeasy with HTTPS support.

Change globs to reflect your settings and set the script to run from cron.

Requires following non-core modules:
  * python-requests, https://pypi.python.org/pypi/requests/
  * python-dns, https://pypi.python.org/pypi/dnspython/

### What it does?

Currently the script uses ["myip" web-page by Dnsmadeeasy](http://www.dnsmadeeasy.com/myip.jsp)
to determine client's current IP. It then compares it to the actual DNS record and in case
the IPs differ, the script will attempt to update the record. 

The update is attempted via the API (HTTPS) provided by Dnsmadeeasy.

### To-Do
  * Implement debug-mode to include verbosity for error messages and traces
  * Replace inline glob-based confs with ConfigParser and/or argparse
  * Add support for determing current IP from a specified NIC.
