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

The update itself is done via the documented API provided by Dnsmadeeasy. Further the script ensures that the SSL certificate of dnsmadeeasy.com is valid one, before attempting the update.

#### TTL and cron

As the DNS TIme-To-Live value sets the caching time for your record, your DNS update won't show up for your script until the TTL has run off. Therefore you should see that cron and TTL are somewhat in sync in this matter, so that you won't end up having redundant updates to Dnsmadeeasy.

If you set the script to run from cron - for example - once per 10 minutes, then set your TTL to 600 seconds respectively.

### To-Do
  * Implement debug-mode to include verbosity for error messages and traces
  * Replace inline glob-based confs with ConfigParser and/or argparse
  * Take account of TTL in the script, so that cron can run more frequently and TTL does not need to be too low
  * Add support for a local IP history
  * Add support for determing current IP from a specified NIC.
  
  
