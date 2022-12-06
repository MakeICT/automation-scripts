#!/usr/bin/python3

from automationscript import Script

from datetime import datetime, date
from datetime import timedelta

import time
import smartwaiver
from wildapricot_api import WaApiClient



class ChildScript(Script):
	def Setup(self):
		self.WA_API = WaApiClient()        
		while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
			time.sleep(5)

	def SetWaiverDate(self, contact_ID, date):
		self.WA_API.UpdateContactField(contact_ID, 'WaiverDate', date)
	
	def SetDOB(self, contact_ID, date):
		self.WA_API.UpdateContactField(contact_ID, 'DOB', date)

	def GetWaiverlessMembers(self):
		contacts = self.WA_API.GetAllContacts()
		waiverless_members=[]
		for contact in contacts:
			flattened_contact_fields = {field["SystemCode"]:field["Value"] for field in contact['FieldValues']}
			if flattened_contact_fields["IsMember"]:
				if flattened_contact_fields["MembershipLevelId"] != 813239:
					# check for oldWaiverLink, Waiverlink, and WaiverDate field, respectively
					# if not flattened_contact_fields["custom-7903153"]:
					if flattened_contact_fields["custom-7973495"].strip()=='' and flattened_contact_fields["custom-9876059"].strip()=='':
						waiverless_members.append(contact)
		for member in waiverless_members:
			print(member['FirstName'], member['LastName'])
		print (len(waiverless_members))

	def Run(self):
		# self.GetWaiverlessMembers()

		# assert 1==2, "math fail!"

		script_start_time = datetime.now()

		time_format_string = '%B %d, %Y at %I:%M%p'

		sw = smartwaiver.Smartwaiver(self.config.get('smartwaiver', 'api_key'))

		# templates = sw.get_waiver_templates()

		# for template in templates:
		# 	print(template.template_id + ': ' + template.title)

		# Get a list of recent signed waivers for this account

		from datetime import timezone
		# from_dt = datetime(2022, 7, 6, tzinfo=timezone.utc)
		# to_dt = datetime(2022, 10, 6, tzinfo=timezone.utc)

		to_dt = datetime.today().astimezone(timezone.utc)
		from_dt = to_dt - timedelta(days=14)
 
		while True:
			summaries = sw.get_waiver_summaries(100, from_dts=from_dt.isoformat(), to_dts=to_dt.isoformat())
			# summaries = sw.get_waiver_summaries(100)

			for summary in summaries:
				print("====================================")
				print(summary.waiver_id + ': ' + summary.title)

				WA_ID = None
				print(summary.first_name, summary.last_name)

				for tag in summary.tags:
					if tag.split(' ')[0]=='WA_ID':
						WA_ID = int(tag.split(' ')[1])

				sw_fails = 0
				while(1):
					try:
						waiver = sw.get_waiver(summary.waiver_id, True)
						break
					except (smartwaiver.exceptions.SmartwaiverHTTPException, smartwaiver.exceptions.SmartwaiverSDKException):
						print("Smartwaiver Error")
						sw_fails += 1
						if sw_fails > 3:
							raise
						else:
							time.sleep(5)
							continue


				contact=None
				
				if not WA_ID and summary.is_minor:
					print("Skipping untagged minor waiver")
					continue

				else:
					while(1):
						try:
							#Pull contact's info from WA if it exists
							if WA_ID:
								contact = self.WA_API.GetContactById(WA_ID)
							else:
								contact = self.WA_API.GetContactByEmail(waiver.email)[0]
								WA_ID = contact['Id']
							break
							#print(contact)

						#If query returns no contact
						except IndexError:
							print("Contact does not exist")
							break
						except TypeError:
							print("Failed to connect to WA")
							time.sleep(60)
							continue
				
				if not contact:
					continue
				#If waiver date is not newer than what is currently on the WA profile, don't update
				saved_waiver_date = [field['Value'] for field in contact['FieldValues'] if field['FieldName']=="WaiverDate"][0]
				waiver_date = datetime.strptime(summary.created_on, "%Y-%m-%d %H:%M:%S").astimezone(timezone.utc)
				if waiver_date > from_dt:
					from_dt = waiver_date
				print(contact)
				print(contact['Email'])
				print("saved waiver date:", saved_waiver_date)
				print("summary created_on date:", summary.created_on)
				if saved_waiver_date and  saved_waiver_date.strip() != '':
					saved_waiver_date = datetime.strptime(saved_waiver_date, "%Y-%m-%d %H:%M:%S").astimezone(timezone.utc)
					print("Has waiver date")
					if saved_waiver_date >= waiver_date:
						continue

				#update WA account waiver date with the current waiver's date
				print('.' + summary.dob + '.')
				waiver_DOB = datetime.strptime(summary.dob, "%Y-%m-%d")
				WA_DOB = waiver_DOB.strftime("%d %b %Y")
				#print(WA_DOB)
				#print(WA_ID, ":", waiver_date)
				#print(waiver_DOB)
				#print(type(WA_ID))
				#print(type(waiver_date))
				self.SetWaiverDate(WA_ID, summary.created_on)
				time.sleep(3)
				self.SetDOB(WA_ID, summary.dob)

				#print(waiver.pdf)

			# We retrieved less than 100 summaries, so there are no more to fetch
			if len(summaries) < 100:
				break

if __name__ == "__main__":
	s = ChildScript("Waiver Check")
	s.RunAndNotify()



	# Send waiver email if no waiver
	#   -When a new member signs up
	#   -When somebody registers for an event
	#   -Periodically when a member doesn't have a current waiver (rate limit)
