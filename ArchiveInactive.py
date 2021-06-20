#!/usr/bin/python3

from automationscript import Script

from datetime import datetime
from datetime import timedelta

from wildapricot_api import WaApiClient

import urllib, time

class ChildScript(Script):
    def Setup(self):
        self.WA_API = WaApiClient()        
        while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
            time.sleep(5)
        self.processed_filename = "followup_processed.txt"

    def Run(self):
        cutoff_date = self.WA_API.DateTimeToWADate(datetime.now() - timedelta(days=720))
        inactive_contacts = self.WA_API.GetFilteredContacts("'Archived'+eq+'False'+and+'Member'+eq+'False'+and+'Profile+last+updated'+le+%s+and+'Last+login+date'+le+%s"% (cutoff_date, cutoff_date))
        # for contact in inactive_contacts:
        #     print(contact, '\n')
        print(len(inactive_contacts))
        ids = [contact['Id'] for contact in inactive_contacts]
        print(ids)
        for id in ids:
            try:
                self.WA_API.UpdateContactField(int(id), "Archived",True)
            except Exception as e:
                print("issue with user id:", id )
                print(e)
                # print(sys.exc_info()[0])
if __name__ == "__main__":
    s = ChildScript("Archive Inactive WA Contacts")
    s.RunAndNotify()
