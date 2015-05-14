# XSSwat-SG
XSSwat Signature Generator

Generates the signatures that will be checked against by the XSSwat Chrome extension (https://github.com/foospidy/XSSwat).

## Dependencies
MySQL
- apt-get install python-mysqldb

Demjson
- apt-get install python-demjson

PyVirtualDisplay (https://pypi.python.org/pypi/PyVirtualDisplay)
- apt-get install xvfb
- pip install pyvirtualdisplay

Selenium (https://pypi.python.org/pypi/selenium)
- pip install -U selenium

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



