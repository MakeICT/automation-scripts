#!/usr/bin/python3

import logging, time, traceback, os, sys
from datetime import datetime, date
from datetime import timedelta
from dateutil import tz
import urllib
import configparser
import csv

#import MySQLdb

# from WildApricotAPI.WildApricotAPI import WaApiClient
from wildapricot_api import WaApiClient
from mailer import MailBot
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
refund_cutoff = 7
refund_grace_hours = 24
refund_min_days = 1
#for r in config.get('thresholds', 'reminderDays').split(','):
#	reminders_days.append(timedelta(days=int(r)))

script = PayCalc(config.get('api','key'))
mb = MailBot(config.get('email','username'), config.get('email','password'),
						config.get('email','server'), config.get('email','port') )
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
	start_date = None
	end_date = None
	# Uncomment to specify date range. Defaults to most recent full month.
	# start_date = datetime(2022, 12, 1)
	# end_date = datetime(2023, 1, 1)

	if not start_date:
		start_date = datetime.today()
		start_date = start_date.replace(day=1, month=((start_date.month+10)%12)+1, hour=0, minute=0, second=0, microsecond=0)
		if start_date.month == 12:
			start_date = start_date.replace(year=start_date.year-1)
	if not end_date:
		end_month = start_date.month + 1
		if end_month == 13:
			end_month = 1
		end_date = start_date.replace(month=end_month)
		if end_date.month == 1:
			end_date = end_date.replace(year=end_date.year+1)

	print(f"{start_date} - {end_date}")



	# print("\n=================================================")
	# print("Voided Event Invoices")
	# print("=================================================")

	# invoice_start_date = start_date - timedelta(days=90)
	# s = invoice_start_date.strftime("%Y-%m-%d")
	# invoices = WA_API.GetInvoicesByDate(invoice_start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
	# void_event_invoices = []
	# for invoice in invoices:
	# 	try:
	# 		if invoice['OrderType'] == 'EventRegistration':
	# 			invoice_date = datetime.strptime(invoice['CreatedDate'], '%Y-%m-%dT%H:%M:%S')
	# 			void_date = datetime.strptime(invoice['VoidedDate'], '%Y-%m-%dT%H:%M:%S')
	# 			invoice_with_details = WA_API.GetInvoiceByID(invoice['Id'])
	# 			if "Registration was canceled" in invoice_with_details['Memo']:
	# 				for detail in invoice_with_details["OrderDetails"]:
	# 					# print(detail)
	# 					detail['Notes'].index("Registration for")
	# 					split_notes = detail['Notes'].split('(')
	# 					event_date = None
	# 					for possible_date in split_notes:
	# 						try:
	# 							event_date = datetime.strptime(possible_date.split(',')[0].split('-')[0].strip(), '%d %b %Y %H:%M %p')
	# 						except:
	# 							print(possible_date)

	# 					#print(event_date)
	# 				#print(void_date)
	# 				# print(type(event_date))
	# 				# print(event_date)
	# 				# print(type(start_date))
	# 				# print(type(end_date))
	# 				if event_date >= start_date and event_date <= end_date:
	# 					delta = event_date-void_date
	# 					cancel_delta = void_date - invoice_date
	# 					refundable = False

	# 					if (delta.days >= refund_cutoff) or ((cancel_delta.seconds + cancel_delta.days*24*60*60)  < refund_grace_hours*60*60):
	# 						if delta.days >= refund_min_days:
	# 							refundable = True
	# 					print("Refundable:", refundable)
	# 					print("Invoice ID:", invoice["Id"])
	# 					print("Invoice voided", delta, "before event start")
	# 					print("Invoice Amount:",invoice_with_details["OrderDetails"][0]["Value"])
	# 					print(invoice_with_details["OrderDetails"][0]["Notes"])
	# 					print("--------------------------------------------")


	# 					void_event_invoices.append(invoice)
					
		# except KeyError:
		# 	pass
	print('\n')


	print("\n=================================================")
	print("Instructor Payments Owed")
	print("=================================================")
	events = WA_API.GetEventsByDate(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
	# for event in events:
	# 	print(event['Name'])
	payment_summary = []
	unpaid_registrations = []
	for event in events:
	#event = WA_API.GetEventByID(2757871)
		print(event['Name'],event['StartDate'])
		registrants = WA_API.GetRegistrantsByEventID(event['Id'])
		total_owed = 0
		total_paid = 0
		total_instructor_fees = 0
		total_facility_fees = 0

		instructor_percentage = 0.75
		regular_facility_fee = 5
		safety_facility_fee = 20
		safety_hourly = 15

		safety_class = "safety class" in event['Name'].lower() or "woodshop authorization" in event['Name'].lower()

		instructor_name = None
		instructor_email = None

		for tag in event['Tags']:
			split_tag = tag.split(':')
			if split_tag[0] in ('instructor_name', 'host_name'):
				instructor_name = ' '.join(split_tag[1:])
			elif split_tag[0] in ('instructor_email', 'host_email'):
				instructor_email = ' '.join(split_tag[1:])

		for registrant in registrants:
			# print('')
			# print(registrant['Contact']['Name'],
			# 	  registrant['RegistrationFee'],
			# 	  registrant['PaidSum'],
			# 	  registrant['IsPaid'])

			# if(abs(registrant['RegistrationFee'] - registrant['PaidSum']) < 0.1):
			if registrant['RegistrationFee'] == registrant['PaidSum']:
				pass
				# print("Registration is paid")
			else:
				# print("NO SAME!!!!!!!!!!!!!!")
				# print(registrant['Contact']['Name'])
				# print(registrant['RegistrationFee'] - registrant['PaidSum'])
				unpaid_registrations.append(registrant)
			if not safety_class:
				if registrant['RegistrationType']['Name'].lower() == 'makeict members':
					total_instructor_fees += int(registrant['RegistrationFee'])
				elif registrant['RegistrationType']['Name'].lower() == 'non-members':
					if not safety_class:
						total_facility_fees += regular_facility_fee
						instructor_fee = int(registrant['RegistrationFee']) - regular_facility_fee
						if instructor_fee < 0:
							print("!!NEGATIVE INSTRUCTOR FEE!!")
							instructor_fee = 0
						total_instructor_fees += instructor_fee
					else:
						total_facility_fees += safety_facility_fee
				else:
					print("!!Unhandled Registration Type!!")

		
		class_duration = (WA_API.WADateToDateTime(event["EndDate"])-WA_API.WADateToDateTime(event["StartDate"]))/ timedelta(hours=1)

		# print('-----------------------------------------')
		# print(event["Name"])
		# print(safety_class)
		# print(class_duration)
		# print()
		# print('instructor name:', instructor_name)
		# print('instructor email:', instructor_email)

		# if(safety_class):
		# 	print('calculate safety class payment')

		# else:
		# 	print("class fees:",total_instructor_fees)
		# print("facility fees:",total_facility_fees)
		if not safety_class:
			instructor_payment = total_instructor_fees*instructor_percentage
		else:
			paid_hours = max(round(class_duration),1)
			instructor_payment = paid_hours * safety_hourly if len(registrants) else 0 

		# print("instructor payment:",instructor_payment)
		payment_summary.append({'event_name':event["Name"],
								'event_date':event["StartDate"][5:10],
								'instructor_name':instructor_name,
								'instructor_email':instructor_email,
								'payment':instructor_payment,
								})

	with open(f'Instructor Payments/Instructor Payments {start_date.strftime("%B")} {start_date.year}.csv', 'w') as csvfile:
		csv_writer = csv.writer(csvfile)
		csv_writer.writerow(['Name', 'Email', 'Date', 'Title', 'Amount'])

		instructor_emails = []
		for p in payment_summary:
			if p['instructor_email'] not in instructor_emails:
				instructor_emails.append(p['instructor_email'])
		for e in instructor_emails:
			instructor_name = [ps['instructor_name'] for ps in payment_summary if ps['instructor_email'] == e][0]
			if e:
				print(instructor_name,':',e)
				# csv_writer.writerow([instructor_name, e])
			else:
				print(["-INSTRUCTOR UNKNOWN-"])
				# csv_writer.writerow(["-INSTRUCTOR UNKNOWN-"])
			total_payment = 0
			for p in payment_summary:
				if p['instructor_email'] == e:
					print(p['event_date'],p['event_name'],p['payment'])
					csv_writer.writerow([instructor_name, e ,p['event_date'],p['event_name'],p['payment']])
					total_payment += p['payment']
			csv_writer.writerow([instructor_name, e,'','Total:',total_payment])
			print('total due:',total_payment)
			print('--------------------------------')
			csv_writer.writerow([''])

		if unpaid_registrations:
			print("\n=================================================")
			print("The following registrations have not been paid:")
			print("=================================================")
			for r in unpaid_registrations:
				print('Event Name:', r['Event']['Name'])
				print('Contact Name:',r['Contact']['Name'])
				print('Money Owed:',r['RegistrationFee'] - r['PaidSum'])
				print('Attended Event:', r['IsCheckedIn'])
				print('-------------------------------------------------')

except Exception as e:
	message = "The following exception was thrown:\r\n\r\n" + str(e) + "\r\n\r\n" + traceback.format_exc()
	mb.send([config.get('email', 'adminAddress')], "Payment Calculator Crash", message)
	raise

# if datetime.now() - script_start_time > timedelta(minutes=60):
# 	exit()


