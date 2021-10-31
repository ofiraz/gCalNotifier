from __future__ import print_function
import sys
import time

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox
)
from PyQt5.uic import loadUi

from test_ui import Ui_w_event

import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import validators

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

EXIT_REASON_NONE = 0
EXIT_REASON_DISMISS = 1
EXIT_REASON_SNOOZE = 2

class Window(QMainWindow, Ui_w_event):
    snooze_buttons = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()

        '''
        self.snooze_buttons = [
            {'button':self.pb_m10m, 'time':-10},
            {'button':self.pb_m5m, 'time':-5},
            {'button':self.pb_m2m, 'time':-2},
            {'button':self.pb_m1m, 'time':-1},
            {'button':self.pb_0m, 'time':0},
            {'button':self.pb_5m, 'time':5},
            {'button':self.pb_15m, 'time':15},
            {'button':self.pb_30m, 'time':30},
            {'button':self.pb_1h, 'time':60},
            {'button':self.pb_2h, 'time':120},
            {'button':self.pb_4h, 'time':240},
            {'button':self.pb_8h, 'time':480}
        ]
        '''

        self.snooze_buttons = {
            self.pb_m10m:-10,
            self.pb_m5m:-5,
            self.pb_m2m:-2,
            self.pb_m1m:-1,
            self.pb_0m:0,
            self.pb_5m:5,
            self.pb_15m:15,
            self.pb_30m:30,
            self.pb_1h:60,
            self.pb_2h:120,
            self.pb_4h:240,
            self.pb_8h:480
        }

    def connectSignalsSlots(self):
        self.pb_dismiss.clicked.connect(self.clickedDismiss)
        self.pb_m10m.clicked.connect(lambda: self.snooze_general(self.pb_m10m))
        self.pb_m5m.clicked.connect(lambda: self.snooze_general(self.pb_m5m))
        self.pb_m2m.clicked.connect(lambda: self.snooze_general(self.pb_m2m))
        self.pb_m1m.clicked.connect(lambda: self.snooze_general(self.pb_m1m))
        self.pb_0m.clicked.connect(lambda: self.snooze_general(self.pb_0m))
        self.pb_5m.clicked.connect(lambda: self.snooze_general(self.pb_5m))
        self.pb_15m.clicked.connect(lambda: self.snooze_general(self.pb_15m))
        self.pb_30m.clicked.connect(lambda: self.snooze_general(self.pb_30m))
        self.pb_1h.clicked.connect(lambda: self.snooze_general(self.pb_1h))
        self.pb_2h.clicked.connect(lambda: self.snooze_general(self.pb_2h))
        self.pb_4h.clicked.connect(lambda: self.snooze_general(self.pb_4h))
        self.pb_8h.clicked.connect(lambda: self.snooze_general(self.pb_8h))

    def clickedDismiss(self):
        global win_exit_reason
        
        win_exit_reason = EXIT_REASON_DISMISS

        self.close()

    def snooze_general(self, p_button):
        global win_exit_reason
        global snooze_time_in_minutes

        win_exit_reason = EXIT_REASON_SNOOZE
        if (p_button in self.snooze_buttons):
            snooze_time_in_minutes = self.snooze_buttons[p_button]

            print(snooze_time_in_minutes)

        else:
            print("Snooze button not found", p_button)
    
        self.close()

def identify_video_meeting(win_label, url, text_if_not_identified):
    if ("zoom.us" in url):
        label_text = "Zoom Link"
    elif ("webex.com" in url):
        label_text = "Webex Link"
    elif ("meet.google.com" in url):
        label_text = "Meet Link"
    elif ("bluejeans.com" in url):
        label_text = "BlueJeans"
    else:
        label_text = text_if_not_identified

    win_label.setText("<a href=\"" + url + "\">" + label_text + "</a>")
    win_label.setOpenExternalLinks(True)
    win_label.setToolTip(url)

def gCalMain(token_path):
    global win_exit_reason
    global dismissed_events
    global snooze_time_in_minutes
    global snoozed_events

    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    token_file = token_path + '/token.json'
    Credentials_file = token_path + '/credentials.json'
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                Credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Handled the snoozed events
    now_datetime = datetime.datetime.now().astimezone()
    events_to_notify = {}

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')

    for event in events:
        #print(event)
        parsed_event = {}
        now_datetime = datetime.datetime.now().astimezone()
        a_snoozed_event_to_wakeup = False

        event_id = event['id']
        #print(event_id)

        parsed_event['event_name'] = event['summary']
        #print(parsed_event['event_name'])

        if (event_id in dismissed_events):
            #print("Skipping dismissed event")
            continue

        if (event_id in snoozed_events):
            # A snoozed event
            snoozed_event = snoozed_events[event_id]

            if (snoozed_event['event_wakeup_time'] > now_datetime):
                # The time of the snoozed event has not arrived yet
                #print("Skipping snoozed event that should not be woke up yet")
                continue
            else:
                # Its time to wake up the snoozed even
                #print("Time to wake up the snoozed event")
                a_snoozed_event_to_wakeup = True
                parsed_event = snoozed_event

                del snoozed_events[event_id]

        if (a_snoozed_event_to_wakeup == False):                
            # Check if the event needs to be reminded, and if so, when
            if (event['reminders'].get('useDefault') == True):
                minutes_before = 15
            else:
                override_rule = event['reminders'].get('overrides')
                if (override_rule):
                    override_set = override_rule[0]
                    minutes_before = override_set['minutes']
                else:
                    #print("No need to remind")
                    continue

            # Event needs to be reminded, check if it is the time to remind
            start_day = event['start'].get('dateTime')
            if not start_day:
                parsed_event['all_day_event'] = True
                start_day = event['start'].get('date')
                end_day = event['end'].get('date')
                parsed_event['start_date']=datetime.datetime.strptime(start_day, '%Y-%m-%d').astimezone()
                parsed_event['end_date']=datetime.datetime.strptime(end_day, '%Y-%m-%d').astimezone()
            else:
                parsed_event['all_day_event'] = False
                end_day = event['end'].get('dateTime')
                parsed_event['start_date']=datetime.datetime.strptime(start_day, '%Y-%m-%dT%H:%M:%S%z')
                parsed_event['end_date']=datetime.datetime.strptime(end_day, '%Y-%m-%dT%H:%M:%S%z')

            delta_diff = datetime.timedelta(minutes=minutes_before)
            reminder_time = parsed_event['start_date'] - delta_diff
            if(now_datetime >= reminder_time):
                print("Time to remind")
            else:
                time_to_reminder =  now_datetime - reminder_time
                #print("Time until reminding " + str(time_to_reminder))
                continue;

            parsed_event['html_link'] = event['htmlLink']

            parsed_event['event_location'] = event.get('location', "No location")

            # Get the video conf data
            parsed_event['video_link'] = "No Video"
            conf_data = event.get('conferenceData')
            if (conf_data):
                entry_points = conf_data.get('entryPoints')
                if (entry_points):
                    for entry_point in entry_points:
                        entry_point_type = entry_point.get('entryPointType')
                        if (entry_point_type and entry_point_type == 'video'):
                            uri = entry_point.get('uri')
                            if (uri):
                                parsed_event['video_link'] = uri

            # parsed_event['event_meet_link'] = event.get('hangoutLink', "No Meet")

        win = Window()

        #if(now_datetime >= parsed_event['start_date']):
            # Don't show the time until options for snooze
            #win.rb_snooze_until.setHidden(True)
            #win.cb_snooze_time_until.setHidden(True)
            #win.l_label_until.setHidden(True)

            # Set the RB of Snooze For to be selected
            #win.rb_snooze_for.setChecked(True)
        #else:
            # Set the RB of Snooze Until to be selected
            #win.rb_snooze_until.setChecked(True)

        win.l_account.setText(token_path)

        win.l_event_name.setText(parsed_event['event_name'])

        if parsed_event['all_day_event']:
            win.l_all_day.setText("An all day event")
        else:
            win.l_all_day.setText("Not an all day event")


        win.l_event_start.setText('Starting on ' + str(parsed_event['start_date']))
        win.l_event_end.setText('Ending on ' + str(parsed_event['end_date']))

        #print(html_link)
        win.l_event_link.setText("<a href=\"" + parsed_event['html_link'] + "\">Link to event in GCal</a>")
        win.l_event_link.setToolTip(parsed_event['html_link'])

        if (parsed_event['event_location'] == "No location"):
            win.l_location_or_video_link.setHidden(True)
        else:
            valid_url = validators.url(parsed_event['event_location'])
            if (valid_url):
                identify_video_meeting(
                    win.l_location_or_video_link,
                    parsed_event['event_location'],
                    "Link to location or to a video URL"
                )
                '''
                win.l_location_or_video_link.setText("<a href=\"" + parsed_event['event_location'] + "\">Link to location or to a video URL</a>")
                win.l_location_or_video_link.setOpenExternalLinks(True)
                win.l_location_or_video_link.setToolTip(parsed_event['event_location'])
                '''

            else:
                win.l_location_or_video_link.setText('Location: ' + parsed_event['event_location'])

        if (parsed_event['video_link'] == "No Video"):
            win.l_video_link.setHidden(True)
        else:
            identify_video_meeting(
                win.l_video_link,
                parsed_event['video_link'],
                "Video link"
            )

        # Hide the uneeded snooze buttons
        if (parsed_event['start_date'] > now_datetime):
            time_to_event_start = parsed_event['start_date'] - now_datetime
            time_to_event_in_minutes = time_to_event_start.seconds / 60
        else:
            time_to_event_in_minutes = -1
        
        #print(time_to_event_in_minutes)
        for pb_button, snooze_time in win.snooze_buttons.items():
            if (snooze_time <= 0 and abs(snooze_time) > time_to_event_in_minutes):
                pb_button.setHidden(True)

        '''
        win.l_video_link.setText("<a href=\"" + parsed_event['video_link'] + "\">Video link</a>")
        win.l_video_link.setOpenExternalLinks(True)
        win.l_video_link.setToolTip(parsed_event['video_link'])
        '''

        '''
        if (parsed_event['event_meet_link'] == "No Meet"):
            win.l_meet_link.setHidden(True)
        else:
            win.l_meet_link.setText("<a href=\"" + parsed_event['event_meet_link'] + "\">Meet link</a>")
            win.l_meet_link.setOpenExternalLinks(True)
            win.l_meet_link.setToolTip(parsed_event['event_meet_link'])
        '''

        win_exit_reason = EXIT_REASON_NONE
        win.show()
        getattr(win, "raise")()
        win.activateWindow()
        app.exec()

        if (win_exit_reason == EXIT_REASON_NONE):
            print("Cancel")
        elif (win_exit_reason == EXIT_REASON_DISMISS):
            #print("Dismiss")
            dismissed_events[event_id] = parsed_event['end_date']
        elif (win_exit_reason == EXIT_REASON_SNOOZE):
            #print("Snooze")
            if (snooze_time_in_minutes <= 0):
                delta_diff = datetime.timedelta(minutes=abs(snooze_time_in_minutes))
                parsed_event['event_wakeup_time'] = parsed_event['start_date'] - delta_diff
            else:
                delta_diff = datetime.timedelta(minutes=snooze_time_in_minutes)
                parsed_event['event_wakeup_time'] = now_datetime + delta_diff

            #print("Snooze until", parsed_event['event_wakeup_time'])
                
            snoozed_events[event_id] = parsed_event
        else:
            print("No exit reason")

    # Clear dismissed events that have ended
    dismissed_events_to_delete = []
    for k, v in dismissed_events.items():
        print(k, v, now_datetime)
        if (now_datetime > v):
            dismissed_events_to_delete.append(k)

    while (len(dismissed_events_to_delete) > 0):
        k = dismissed_events_to_delete.pop()
        print("Deleteing event id", k, "from dismissed")
        del dismissed_events[k]

    # Clear snoozed events that have ended
    snoozed_events_to_delete = []
    for k, v in snoozed_events.items():
        #print(k, v['end_date'], now_datetime)
        if (now_datetime > v['end_date']):
            snoozed_events_to_delete.append(k)

    while (len(snoozed_events_to_delete) > 0):
        k = snoozed_events_to_delete.pop()
        #print("Deleteing event id", k, "from snoozed")
        del snoozed_events[k]

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dismissed_events = {}
    snoozed_events = {}
    while True:
        gCalMain('ofir_anjuna_io')
        gCalMain('ofiraz_gmail_com')

        print("Going to sleep for 30 seconds")
        time.sleep(30)


    sys.exit()
