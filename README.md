# XSSwat-SG
XSSwat Signature Generator

Generates the signatures that will be checked by the XSSwat Chrome extension (https://github.com/foospidy/XSSwat). Signatures are already generated and published at riskdiscovery.com (example: https://riskdiscovery.com/xsswat/9ab9c934e2329708df92a86781ba47b9). If you want to host your own signatures you will also need to modify the Chrome extension to point to your domain.

## Dependencies
MySQL
- apt-get install python-mysqldb

Demjson
- apt-get install python-demjson

Feedparser
- pip install feedparser

PyVirtualDisplay (https://pypi.python.org/pypi/PyVirtualDisplay)
- apt-get install xvfb
- pip install pyvirtualdisplay

Selenium (https://pypi.python.org/pypi/selenium)
- pip install -U selenium

BeautifulSoup
- pip install BeautifulSoup

Browser
- Either iceweasel or firefox
  -  apt-get install iceweasel
  -  for installing firefox see: http://superuser.com/questions/322376/how-to-install-the-real-firefox-on-debian

## Setup
1. create a database: ```mysql -u <db user> -p -e "create database <database name>;"```
2. Edit config section of xsswat-sg.py:
```
FEED_LIMIT      = 100  # reddit's max is 100
GENERATE_JSON   = False
JSON_OUTPUT_DIR = './' # location of where to dump json file, default is current directory
DB_HOST         = 'localhost'
DB_NAME         = ''
DB_USER         = ''
DB_PASS         = ''
```



