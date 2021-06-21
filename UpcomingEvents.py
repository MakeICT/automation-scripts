#!/usr/bin/python3
import time
import traceback
from datetime import datetime
import configparser
import requests

from wildapricot_api import WaApiClient

WA_API = WaApiClient()

script_start_time = datetime.now()
config = configparser.SafeConfigParser()
config.read('config.ini')

try:
    while(not WA_API.ConnectAPI(config.get('api', 'key'))):
        time.sleep(5)

    upcoming_events = WA_API.GetUpcomingEvents()
    upcoming_events = sorted(upcoming_events, key=lambda event: event['StartDate'])
    events = []
    for event in upcoming_events:
        if not event['AccessLevel'] == 'AdminOnly':
            # spots_available = event['RegistrationsLimit'] - event['ConfirmedRegistrationsCount']
            # spots = None
            # if spots_available > 0:
            # 	spots = str(spots_available) + 'Register'
            # else:
            # 	spots = 'FULL'
            start_date = WA_API.WADateToDateTime(event['StartDate'])
            event_date = start_date.strftime('%b %d')
            event_details = {"time": f"{start_date.strftime('%I:%M %p')}", 
                             "name": f"{event['Name']}", 
                             "link": f"http://makeict.wildapricot.org/event-{str(event['Id'])}"}
            if(event_date not in [event["date"] for event in events]):
                events.append({"date": event_date, "events": []})
            for event in events:
                if event["date"] == event_date:
                    event["events"].append(event_details)

    variables = {"events": events}.__str__().replace("'", '"')
    print(variables)

    res = requests.post(
        f"https://api.mailgun.net/v3/{config.get('mailgun', 'site')}/messages",
        auth=("api", config.get('mailgun', 'api_key')),
        data={"from": "MakeICT Events <events@makeict.org>",
              "to": "test_mailing_list@mg.makeict.org",
              "subject": "Upcoming Events At MakeICT",
              "template": "upcoming_events",
              "h:X-Mailgun-Variables": variables})

    print(res, res.content)

except Exception as e:
    message = "The following exception was thrown:\r\n\r\n" + str(e) + "\r\n\r\n" + traceback.format_exc()
    raise
