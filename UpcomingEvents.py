#!/usr/bin/python3

import logging, time, traceback, os, sys
from datetime import datetime
from datetime import timedelta
from dateutil import tz
import urllib
import configparser
import requests
#import MySQLdb

from wildapricot_api import WaApiClient
# from mailer import MailBot

#from Database import Database

#os.chdir(config.get('files', 'installDirectory'))

WA_API = WaApiClient()

tzlocal = tz.gettz('CST')

class PayCalc():
	def __init__(self, api_key):		
		self.options = {"API_key":api_key}
		while(not WA_API.ConnectAPI(self.options["API_key"])):
			time.sleep(5)


script_start_time = datetime.now()
#db = Database()
#current_db = db.GetAll()
#for entry in current_db:
#	print (entry)
config = configparser.SafeConfigParser()
config.read('config.ini')
print(config.items('api'))
print(config.items('thresholds'))

time_format_string = '%B %d, %Y at %I:%M%p'
unpaid_cutoff = timedelta(days=config.getint('thresholds','unpaidCutOff'))
unpaid_buffer = timedelta(hours=config.getint('thresholds', 'unpaidBuffer'))
noshow_drop = timedelta(minutes=config.getint('thresholds','noShowDrop'))
poll_interval = config.getint('api','pollInterval')
nag_buffer = timedelta(minutes=config.getint('thresholds','nagBuffer'))
enforcement_date = datetime.strptime(config.get('thresholds','enforcementDate'),'%m-%d-%y %z')
reminders = len(config.get('thresholds', 'reminderDays').split(','))
reminders_days = []
#for r in config.get('thresholds', 'reminderDays').split(','):
#	reminders_days.append(timedelta(days=int(r)))

script = PayCalc(config.get('api','key'))
mb = MailBot(config.get('email','username'), config.get('email','password'))
mb.setDisplayName(config.get('email', 'displayName'))
mb.setAdminAddress(config.get('email', 'adminAddress'))

#Get all events for the past month
#for each event
	#Calculate total payment, non-member facility fees, MakeICT portion, Instructor Payment
		#free events - $5 non-memeber facility fee, no instructor payment
		#events with instructor fees - 75/25 non-member facility fee $5
		#Authorizations - free for members, $20 for non-members, instructor payment of $15/hour?
#Email info to treasurer

try:
	sys.exit()
	upcoming_events = WA_API.GetUpcomingEvents()
	upcoming_events = sorted(upcoming_events, key=lambda event: event['StartDate'])
	for event in upcoming_events:
		if not event['AccessLevel'] == 'AdminOnly':
			spots_available = event['RegistrationsLimit'] - event['ConfirmedRegistrationsCount']
			spots = None
			if spots_available > 0:
				spots = str(spots_available) + 'Register'
			else:
				spots = 'FULL'
			start_date = WA_API.ConvertWADate(event['StartDate'])
			print(start_date.strftime('%b %d') + ' | ' + start_date.strftime('%I:%M %p') + ' | ' + event['Name'] + ' | ' + '<a href="http://makeict.wildapricot.org/event-' + str(event['Id']) + '" target="_blank">Register</a><br />')
	sys.exit()
	registration_type = WA_API.GetRegistrationTypesByEventID(2802353)[1]
	print(registration_type)
	registration_type['BasePrice'] = 20
	result = WA_API.execute_request('EventRegistrationTypes/%s'%registration_type['Id'], registration_type, method='PUT')
	print(result)
#	WA_API.DeleteEvent(2757684)
#	event = WA_API.GetEventByID(2767008)
#	print(event)
	sys.exit()
	# logs = WA_API.GetLogItems()
	# invoice = WA_API.GetInvoiceByID('38574014')
	# print(invoice)

	# for log in logs:
	# 	print(log)
	# registrants = WA_API.GetRegistrationByID(20134708)
	# for registrant in registrants:
	# 	print(registrant)
except Exception as e:
	message = "The following exception was thrown:\r\n\r\n" + str(e) + "\r\n\r\n" + traceback.format_exc()
	mb.send([config.get('email', 'adminAddress')], "Registration Monitor Crash", message)
	raise

# if datetime.now() - script_start_time > timedelta(minutes=60):
# 	exit()
