from __future__ import print_function
import sys
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow
)

from test_ui import Ui_w_event

import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import validators

import logging
from logging.handlers import RotatingFileHandler

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Exit reasons from the dialog
EXIT_REASON_NONE = 0
EXIT_REASON_DISMISS = 1
EXIT_REASON_SNOOZE = 2

# The notification window
class Window(QMainWindow, Ui_w_event):
    snooze_buttons = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()

        # Initialize the snooze buttons
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

    # Set the event handlers
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

            logger.debug("Snooze time in minuetes " + str(snooze_time_in_minutes))

        else:
            logger.error("Snooze button not found " + str(p_button))
    
        self.close()

def init_logging(module_name):
    global logger

    # create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # add formatter to ch
    console_handler.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(console_handler)

    # Create file handler
    log_file = module_name + ".log"
    max_log_file_size = 100 * 1024 * 1024
    file_handler = RotatingFileHandler(
        log_file,
        mode='a',
        maxBytes=max_log_file_size,
        backupCount=5,
        encoding='utf-8')

    file_handler.setLevel(logging.INFO)

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info("========")
    logger.info("Starting")
    logger.info("========")

    return logger

# Identify the video meeting softwate via its URL
def identify_video_meeting(win_label, url, text_if_not_identified):
    global logger

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

def get_events_from_google_cal(google_account):
    global logger

    # Connect to the Google Account
    creds = None
    token_file = google_account + '/token.json'
    Credentials_file = google_account + '/credentials.json'
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

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    logger.debug('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    return(events)

def get_now_datetime():
    return(datetime.datetime.now().astimezone())

def show_window_and_parse_exit_status(event_id, parsed_event):
    global win_exit_reason
    global dismissed_events
    global snoozed_events
    global snooze_time_in_minutes
    global logger

    win = Window()

    win.l_account.setText(parsed_event['google_account'])

    win.l_event_name.setText(parsed_event['event_name'])

    if parsed_event['all_day_event']:
        win.l_all_day.setText("An all day event")
    else:
        win.l_all_day.setText("Not an all day event")

    win.l_event_start.setText('Starting on ' + str(parsed_event['start_date']))
    win.l_event_end.setText('Ending on ' + str(parsed_event['end_date']))

    logger.debug("HTML Link " + parsed_event['html_link'])
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

        else:
            win.l_location_or_video_link.setText('Location: ' + parsed_event['event_location'])

    if (parsed_event['video_link'] == "No Video"):
        win.l_video_link.setHidden(True)
    else:
        identify_video_meeting(
            win.l_video_link,
            parsed_event['video_link'],
            "Video Link"
        )

    # Hide the uneeded snooze buttons
    now_datetime = get_now_datetime()
    if (parsed_event['start_date'] > now_datetime):
        time_to_event_start = parsed_event['start_date'] - now_datetime
        time_to_event_in_minutes = time_to_event_start.seconds / 60
    else:
        time_to_event_in_minutes = -1
    
    logger.debug("Time to event in minutes " + str(time_to_event_in_minutes))
    for pb_button, snooze_time in win.snooze_buttons.items():
        if (snooze_time <= 0 and abs(snooze_time) > time_to_event_in_minutes):
            pb_button.setHidden(True)

    win_exit_reason = EXIT_REASON_NONE

    # Show the window and bring it to the front
    win.show()
    getattr(win, "raise")()
    win.activateWindow()
    app.exec()

    # Look at the window exit reason
    if (win_exit_reason == EXIT_REASON_NONE):
        logger.debug("Cancel")
    elif (win_exit_reason == EXIT_REASON_DISMISS):
        logger.debug("Dismiss")
        dismissed_events[event_id] = parsed_event['end_date']
    elif (win_exit_reason == EXIT_REASON_SNOOZE):
        logger.debug("Snooze")
        if (snooze_time_in_minutes <= 0):
            delta_diff = datetime.timedelta(minutes=abs(snooze_time_in_minutes))
            parsed_event['event_wakeup_time'] = parsed_event['start_date'] - delta_diff
        else:
            delta_diff = datetime.timedelta(minutes=snooze_time_in_minutes)
            parsed_event['event_wakeup_time'] = now_datetime + delta_diff

        logger.debug("Snooze until " + str(parsed_event['event_wakeup_time']))
            
        snoozed_events[event_id] = parsed_event
    else:
        logger.error("No exit reason")

def clear_dismissed_and_snoozed_events():
    global dismissed_events
    global snoozed_events
    global logger

    now_datetime = get_now_datetime()

    # Clear dismissed events that have ended
    dismissed_events_to_delete = []
    for k, v in dismissed_events.items():
        logger.debug("Dismissed event " + str(k) + " " + str(v) + " " + str(now_datetime))
        if (now_datetime > v):
            dismissed_events_to_delete.append(k)

    while (len(dismissed_events_to_delete) > 0):
        k = dismissed_events_to_delete.pop()
        logger.debug("Deleteing event id " + str(k) + " from dismissed")
        del dismissed_events[k]

    # Clear snoozed events that have ended
    snoozed_events_to_delete = []
    for k, v in snoozed_events.items():
        logger.debug("Snoozed event " + str(k) + " " + str(v['end_date']) + " " + str(now_datetime))
        if (now_datetime > v['end_date']):
            snoozed_events_to_delete.append(k)

    while (len(snoozed_events_to_delete) > 0):
        k = snoozed_events_to_delete.pop()
        logger.debug("Deleteing event id " + str(k) + " from snoozed")
        del snoozed_events[k]

def parse_event(event, parsed_event):
    global logger

    if (event['reminders'].get('useDefault') == True):
        minutes_before = 15
    else:
        override_rule = event['reminders'].get('overrides')
        if (override_rule):
            override_set = override_rule[0]
            minutes_before = override_set['minutes']
        else:
            logger.debug("No need to remind")
            return(False)

    # Event needs to be reminded, check if it is the time to remind
    start_day = event['start'].get('dateTime')
    if not start_day:
        # An all day event
        parsed_event['all_day_event'] = True
        start_day = event['start'].get('date')
        end_day = event['end'].get('date')
        parsed_event['start_date']=datetime.datetime.strptime(start_day, '%Y-%m-%d').astimezone()
        parsed_event['end_date']=datetime.datetime.strptime(end_day, '%Y-%m-%d').astimezone()
    else:
        # Not an all day event
        parsed_event['all_day_event'] = False
        end_day = event['end'].get('dateTime')
        parsed_event['start_date']=datetime.datetime.strptime(start_day, '%Y-%m-%dT%H:%M:%S%z')
        parsed_event['end_date']=datetime.datetime.strptime(end_day, '%Y-%m-%dT%H:%M:%S%z')

    # Compute the time to wake up
    delta_diff = datetime.timedelta(minutes=minutes_before)
    reminder_time = parsed_event['start_date'] - delta_diff
    now_datetime = get_now_datetime()
    if(now_datetime < reminder_time):
        # Not the time to remind yet
        return(False)

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

    # The event needs to be notified
    return(True)

def notify_on_needed_calendar_events(google_account):
    global dismissed_events
    global snoozed_events
    global logger

    logger.debug("notify_on_needed_calendar_events for " + google_account)

    # Get the next coming events from the google calendar
    events = get_events_from_google_cal(google_account)

    # Handled the snoozed events
    if not events:
        logger.debug('No upcoming events found')

    for event in events:
        logger.debug(event)
        parsed_event = {}
        now_datetime = get_now_datetime()
        a_snoozed_event_to_wakeup = False

        event_id = event['id']
        logger.debug("Event ID " + str(event_id))

        parsed_event['event_name'] = event['summary']
        parsed_event['google_account'] = google_account
        logger.debug("Event Name " + parsed_event['event_name'])

        if (event_id in dismissed_events):
            logger.debug("Skipping dismissed event")
            continue

        if (event_id in snoozed_events):
            # A snoozed event
            snoozed_event = snoozed_events[event_id]

            if (snoozed_event['event_wakeup_time'] > now_datetime):
                # The time of the snoozed event has not arrived yet
                logger.debug("Skipping snoozed event that should not be woke up yet")
                continue
            else:
                # Its time to wake up the snoozed even
                logger.debug("Time to wake up the snoozed event")
                a_snoozed_event_to_wakeup = True
                parsed_event = snoozed_event

                del snoozed_events[event_id]

        if (a_snoozed_event_to_wakeup == False):                
            # Not a snoozed event - check if the event needs to be reminded, and if so, when
            need_to_notify = parse_event(event, parsed_event)
            if (need_to_notify == False):
                continue

        # Show the window with the data
        show_window_and_parse_exit_status(event_id, parsed_event)

    clear_dismissed_and_snoozed_events()

if __name__ == "__main__":
    # Init
    app = QApplication(sys.argv)

    dismissed_events = {}
    snoozed_events = {}

    # Init the logger
    logger = init_logging("gCalNotifier")    

    # Loop forever
    while True:
        notify_on_needed_calendar_events('ofir_anjuna_io')
        notify_on_needed_calendar_events('ofiraz_gmail_com')

        logger.debug("Going to sleep for 30 seconds")
        time.sleep(30)