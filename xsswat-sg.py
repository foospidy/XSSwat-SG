#!/usr/bin/python

### configuration ################
FEED_LIMIT      = 100  # reddit's max is 100
GENERATE_JSON   = False
JSON_OUTPUT_DIR = './' # location of where to dump json file, default is current directory
DB_HOST         = 'localhost'
DB_NAME         = ''
DB_USER         = ''
DB_PASS         = ''  
##################################

import MySQLdb
import demjson
import feedparser
import urllib
import itertools
import hashlib
import logging
from BeautifulSoup import BeautifulSoup
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
from warnings import filterwarnings

mysqldb      = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
mysqlcur     = mysqldb.cursor()
feed_url     = 'http://www.reddit.com/r/xss/.rss?limit=' + str(FEED_LIMIT)
feed         = feedparser.parse(feed_url)
url          = ''
xephyr       = Display(visible=0, size=(320, 240)).start()
browser      = webdriver.Firefox()
LOG_FILENAME = 'xsswat.log'

logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
# suppress database warnings
filterwarnings('ignore', category = MySQLdb.Warning)

# if database table does not exist then create it
try:
	mysqlcur.execute("CREATE TABLE IF NOT EXISTS `signatures` ( `id` int(11) NOT NULL AUTO_INCREMENT, `published` varchar(45) DEFAULT NULL, `title` varchar(145) DEFAULT NULL, `link` text, `url` text, `request_signature` text, `hash_signature` varchar(45) DEFAULT NULL, `confirmed` tinyint(1) DEFAULT NULL, `created` datetime DEFAULT NULL, `modified` datetime DEFAULT NULL, PRIMARY KEY (`id`), UNIQUE KEY `SIGNATURE` (`hash_signature`) );")
	mysqldb.commit()
except Exception as e:
	logging.debug(str(e))
			
for entry in feed['entries']:
	logging.debug(entry['published'] + ' ' + entry['title'] + ' (' + entry['link'] + ')')

	# parse description by <br /> to get links
	soup = BeautifulSoup(entry['summary'].split('<br />')[1])

	# the first <a href> is the one we want
	url = soup.a.get('href')
	
	url_base            = ''
	request_signatures  = []
	query_parameters    = ''
	query_names         = []
	hash_parameters     = ''
	hash_names          = []
	hash_signature      = ''
	confirmed           = True
	not_clean_parse     = False
	likely_post_request = False
	
	# determine if the entry is a post request, or if parsing was not clean
	if 'post:' in entry['summary'].lower():
		likely_post_request = True # looks like this was a post request based xss
		not_clean_parse     = True # claiming not clean parse since post are not supported yet
	elif url.startswith('http://www.reddit.com'):
		not_clean_parse = True
	elif url.startswith('https://www.reddit.com'):
		not_clean_parse = True
	elif url.startswith('http://reddit.com'):
		not_clean_parse = True
	elif url.startswith('https://reddit.com'):
		not_clean_parse = True

	if not not_clean_parse:
		# ignore hash parameters if they exist and get query parameters
		tmp                   = url.split('#', 2)[0]
		url_parts             = tmp.split('?', 2);
		query_parameter_count = 0
		
		# get query parameters
		if 2 == len(url_parts):
			url_base              = url_parts[0]
			query_parameters      = url_parts[1]
			parameters            = query_parameters.split('&')
			query_parameter_count = len(parameters)
			query_parameter_names = []
			hash_parameter_names  = []
	
			for parameter in parameters:
				parameter_parts = parameter.split('=', 2)
				query_parameter_names.append('?' + parameter_parts[0])

			query_names = itertools.permutations(query_parameter_names)
		
		# get hash parameters
		url_parts            = url.split('#', 2);
		hash_parameter_count = 0
	
		if 2 == len(url_parts):
			if 0 == len(url_base):
				url_base = url_parts[0]
	
			hash_parameters      = url_parts[1]
			parameters           = hash_parameters.split('&')
			hash_parameter_count = len(parameters)
			hash_parameter_names = []
	
			for parameter in parameters:
				parameter_parts = parameter.split('=', 2)
				hash_parameter_names.append('#' + parameter_parts[0])
			
			hash_names = itertools.permutations(hash_parameter_names)
		
		# determine if the number of parameters are to large to try and generate a request signature
		# for every possible permutation (order combinations)
		if(query_parameter_count + hash_parameter_count) > 6:
			# too many parameters so create one request signature
			logging.debug('Too many parameters, not generating permutations: ' + url)
			request_signatures.append(''.join(query_parameter_names) + ''.join(hash_parameter_names))
		else:
			# not too many parameters so generate a request signature for every permutation
			string_to_append = None
			query_array      = []
			hash_array       = []
			
			for i in query_names:
				query_array.append(i)
			
			for i in hash_names:
				hash_array.append(i)
			
			if len(query_array) > 0 :
				for i in query_array:
					string_to_append = ''.join(i)
					h_list           = list(hash_names)
				
					if len(hash_array) > 0:
						for j in range(0, len(hash_array)):
							request_signatures.append(string_to_append + ''.join(hash_array[j]))
					else:
						request_signatures.append(string_to_append)
			
			elif len(hash_array) > 0:
				for i in range(0, len(hash_array)):
					request_signatures.append(''.join(hash_array[i]))
			
			# if zero lenth then set request signature to base url_part
			if 0 == len(request_signatures):
					url_base = url_parts[0]
	
		logging.debug('URL: ' + url)

		# test xss
		try:
			browser.get(url)
		
		except UnexpectedAlertPresentException as e:
			print 'unexpected: ' + str(e)
		except Exception as e:
			print 'exception:' + str(e)
		
		try:
			WebDriverWait(browser, 3).until(EC.alert_is_present(), 'Timed out waiting for PA creation confirmation popup to appear.')
		
			alert = browser.switch_to_alert()
			alert.accept()
			
			confirmed = True
			logging.debug('Detected: Alert!')
	
		except TimeoutException:
			confirmed = False
			logging.debug('Detected: No Alert.')

		for signature in request_signatures:
			# generate has signature
			hash_signature =  hashlib.md5(url_base + signature).hexdigest()
			logging.debug('Request Signature: ' + url_base + signature + ' (' + hash_signature  + ')')
			print url_base + signature + ' [' + hash_signature + ']'
			
			# rather than checking if records exist to determine if an update or insert is required,
			# blindly insert ignore and update for each hash signature
			#
			# insert ignore, ignore is based on unique key of hash_signature
			params = [entry['published'], entry['title'], entry['link'], url, url_base + signature, hash_signature, confirmed]
			mysqlcur.execute("INSERT IGNORE INTO signatures (published, title, link, url, request_signature, hash_signature, confirmed, created, modified) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());", params)
			mysqldb.commit()
			logging.debug('Insert: Confirmed: ' + str(confirmed) + ' Hash Signature: ' + hash_signature)
			
			# update
			params = [confirmed, hash_signature]
			mysqlcur.execute("UPDATE signatures SET confirmed=%s, modified=NOW() WHERE hash_signature=%s;", params)
			mysqldb.commit()
			logging.debug('Update: Confirmed: ' + str(confirmed) + ' Hash Signature: ' + hash_signature)
		
		"""
		# does record exist?
		params = [hash_signature]
		mysqlcur.execute("SELECT hash_signature FROM signatures WHERE hash_signature=%s LIMIT 1;", params)
		rows = mysqlcur.fetchall()
		
		# Yes so update
		if 1 == len(rows):
			params = [confirmed, hash_signature]
			mysqlcur.execute("UPDATE signatures SET confirmed=%s, modified=NOW() WHERE hash_signature=%s;", params)
			mysqldb.commit()
			logging.debug('Update: Confirmed: ' + str(confirmed) + ' Hash Signature: ' + hash_signature)
		
		# No so insert
		else:
			params = [entry['published'], entry['title'], entry['link'], url, request_signature, hash_signature, confirmed]
			mysqlcur.execute("INSERT IGNORE INTO signatures (published, title, link, url, request_signature, hash_signature, confirmed, created, modified) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());", params)
			mysqldb.commit()
			logging.debug('Insert: Confirmed: ' + str(confirmed) + ' Hash Signature: ' + hash_signature)
		"""
	else:
		if likely_post_request:
			logging.debug('POST REQUEST: ' + url)
		else:
			logging.debug('COULD NOT PARSE CLEANLY: ' + url)

browser.quit()

if GENERATE_JSON:
	mysqlcur.execute("SELECT * FROM signatures;")
	rows = mysqlcur.fetchall()

	f = open(JSON_OUTPUT_DIR + 'xss.json', 'w')
	f.write(demjson.encode(rows))
	f.close()
