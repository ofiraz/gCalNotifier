from __future__ import print_function
import sys
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDesktopWidget, QTextBrowser
)

from PyQt5 import QtGui
from PyQt5 import QtCore

from gCalNotifier_ui import Ui_w_event

import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import validators

import logging
from logging.handlers import RotatingFileHandler

import threading
from multiprocessing import Process, Pipe

import json
import traceback

import re

import webbrowser

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Exit reasons from the dialog
EXIT_REASON_NONE = 0
EXIT_REASON_DISMISS = 1
EXIT_REASON_SNOOZE = 2

def get_now_datetime():
    return(datetime.datetime.now().astimezone())

# The notification window
class Window(QMainWindow, Ui_w_event):
    c_snooze_buttons = {}
    c_parsed_event = {}
    c_hidden_all_snooze_before_buttons = False
    c_updated_label_post_start = False
    c_video_link = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.timer = QtCore.QTimer()

        self.connectSignalsSlots()

        # Initialize the snooze buttons
        self.c_snooze_buttons = {
            self.pb_m10m:-10,
            self.pb_m5m:-5,
            self.pb_m2m:-2,
            self.pb_m1m:-1,
            self.pb_0m:0,
            self.pb_1m:1,
            self.pb_5m:5,
            self.pb_15m:15,
            self.pb_30m:30,
            self.pb_1h:60,
            self.pb_2h:120,
            self.pb_4h:240,
            self.pb_8h:480
        }

    # Identify the video meeting softwate via its URL
    def identify_video_meeting_in_url(self, win_label, url, text_if_not_identified):
        global g_logger

        if ("zoom.us" in url):
            label_text = "Zoom Link"
        elif ("webex.com" in url):
            label_text = "Webex Link"
        elif ("meet.google.com" in url):
            label_text = "Google Meet Link"
        elif ("bluejeans.com" in url):
            label_text = "BlueJeans Link"
        elif ("chime.aws" in url):
            label_text = "AWS Chime Link"
        elif ("teams.microsoft.com" in url):
            label_text = "MS Teams Link"    
        else:
            label_text = text_if_not_identified

        win_label.setText("<a href=\"" + url + "\">" + label_text + "</a>")
        win_label.setOpenExternalLinks(True)
        win_label.setToolTip(url)


    def init_window_from_parsed_event(self, parsed_event):
        self.c_parsed_event = parsed_event

        self.setWindowTitle(parsed_event['event_name'])

        self.l_account.setText(parsed_event['google_account'])

        self.l_event_name.setText(parsed_event['event_name'])

        if parsed_event['all_day_event']:
            self.l_all_day.setText("An all day event")
        else:
            self.l_all_day.setHidden(True)

        self.l_event_start.setText('Starting at ' + str(parsed_event['start_date']))
        self.l_event_end.setText('Ending at ' + str(parsed_event['end_date']))

        self.l_event_link.setText("<a href=\"" + parsed_event['html_link'] + "\">Link to event in GCal</a>")
        self.l_event_link.setToolTip(parsed_event['html_link'])

        if (parsed_event['event_location'] == "No location"):
            self.l_location_or_video_link.setHidden(True)
        else:
            valid_url = validators.url(parsed_event['event_location'])
            if (valid_url):
                self.identify_video_meeting_in_url(
                    self.l_location_or_video_link,
                    parsed_event['event_location'],
                    "Link to location or to a video URL")

                self.c_video_link = parsed_event['event_location']

            else:
                self.l_location_or_video_link.setText('Location: ' + parsed_event['event_location'])

        if (parsed_event['video_link'] == "No Video"):
            self.l_video_link.setHidden(True)
        else:
            self.identify_video_meeting_in_url(
                self.l_video_link,
                parsed_event['video_link'],
                "Video Link")

            self.c_video_link = parsed_event['video_link']

        if (self.c_video_link is None):
            self.pb_open_video_and_snooze.setHidden(True)
            self.pb_open_video_and_dismiss.setHidden(True)

        if (parsed_event['description'] != "No description"):
            self.t_description.setHtml(parsed_event['description'])
        
        self.update_controls_based_on_event_time(True)

    # Set the event handlers
    def connectSignalsSlots(self):
        self.pb_dismiss.clicked.connect(self.clickedDismiss)
        self.pb_m10m.clicked.connect(lambda: self.snooze_general(self.pb_m10m))
        self.pb_m5m.clicked.connect(lambda: self.snooze_general(self.pb_m5m))
        self.pb_m2m.clicked.connect(lambda: self.snooze_general(self.pb_m2m))
        self.pb_m1m.clicked.connect(lambda: self.snooze_general(self.pb_m1m))
        self.pb_0m.clicked.connect(lambda: self.snooze_general(self.pb_0m))
        self.pb_1m.clicked.connect(lambda: self.snooze_general(self.pb_1m))
        self.pb_5m.clicked.connect(lambda: self.snooze_general(self.pb_5m))
        self.pb_15m.clicked.connect(lambda: self.snooze_general(self.pb_15m))
        self.pb_30m.clicked.connect(lambda: self.snooze_general(self.pb_30m))
        self.pb_1h.clicked.connect(lambda: self.snooze_general(self.pb_1h))
        self.pb_2h.clicked.connect(lambda: self.snooze_general(self.pb_2h))
        self.pb_4h.clicked.connect(lambda: self.snooze_general(self.pb_4h))
        self.pb_8h.clicked.connect(lambda: self.snooze_general(self.pb_8h))
        self.timer.timeout.connect(lambda: self.update_controls_based_on_event_time(False)) 
        self.pb_open_video_and_snooze.clicked.connect(self.open_video_and_snooze)
        self.pb_open_video_and_dismiss.clicked.connect(self.open_video_and_dismiss)

    def clickedDismiss(self):
        global g_win_exit_reason

        g_win_exit_reason = EXIT_REASON_DISMISS

        self.close()

    def snooze_general(self, p_button):
        global g_win_exit_reason
        global g_snooze_time_in_minutes

        g_win_exit_reason = EXIT_REASON_SNOOZE

        if (p_button in self.c_snooze_buttons):
            g_snooze_time_in_minutes = self.c_snooze_buttons[p_button]
    
        self.close()

    def get_one_event_from_google_cal(self, google_account, event_id):    
        # Connect to the Google Account
        creds = None
        Credentials_file = 'app_credentials.json'
        token_file = google_account + '_token.json'

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
        raw_event = service.events().get(
            calendarId='primary',
            eventId=str(event_id)).execute()

        return(raw_event)

    def get_one_event_from_google_cal_with_try(self, google_account, event_id):
        num_of_retries = 0
    
        while num_of_retries <= 2:
            try: # In progress - handling intermittent exception from the Google service
                raw_event = self.get_one_event_from_google_cal(google_account, event_id)
            except Exception as e:
                excType = str(e.__class__.__name__)
                excMesg = str(e)

                if ((excType == "ServerNotFoundError") 
                or (excType == "timeout") 
                or (excType == "TimeoutError") 
                or (excType == "ConnectionResetError")
                or (excType == "TransportError")
                or (excType == "OSError" and excMesg == "[Errno 51] Network is unreachable")
                ):
                    # Exceptions that chould be intermittent due to networking issues.
                    # We can wait for the next cycle and hope it will get resolved
                    break

                print("Error in get_events_from_google_cal for " + google_account)
                print('Exception type ' + excType)
                print('Exception msg ' + excMesg)

                print(traceback.format_exc())

                num_of_retries = num_of_retries + 1

                if (num_of_retries > 2):
                    raise
                else:
                    # Sleep for 2 seconds and retry
                    time.sleep(2)
            else:
                # Getting the event was successful
                return(raw_event)
                break

    def update_controls_based_on_event_time(self, p_changes_should_be_reflected):
        global g_win_exit_reason

        l_changes_should_be_reflected = p_changes_should_be_reflected

        # Let's first check that the event has not changed
        raw_event = self.get_one_event_from_google_cal_with_try(
            self.c_parsed_event['google_account'],
            self.c_parsed_event['raw_event']['id'])
        if((raw_event is None) or (raw_event['updated'] != self.c_parsed_event['raw_event']['updated'])):
            # The event has changed, closing the window to refresh the event
            g_win_exit_reason = EXIT_REASON_NONE
            self.close()
            return()

        now_datetime = get_now_datetime()

        if (self.c_parsed_event['start_date'] > now_datetime):
            # Event start did not arrive yet - hide all before snooze buttons that are not relevant anymore
            time_to_event_start = self.c_parsed_event['start_date'] - now_datetime
            time_to_event_in_minutes = time_to_event_start.seconds / 60

            longest_snooze_time_to_show = 0

            for pb_button, snooze_time in self.c_snooze_buttons.items():
                if (snooze_time <= 0 and abs(snooze_time) > time_to_event_in_minutes):
                    if (pb_button.isHidden() == False):
                        pb_button.setHidden(True)
                        l_changes_should_be_reflected = True
                else:
                    # Compute the closest time to wait until hiding any button
                    if (snooze_time < longest_snooze_time_to_show):
                        longest_snooze_time_to_show = snooze_time

            # Compute the time needed to snooze before checking again
            time_to_wait_in_seconds = time_to_event_start.seconds + (longest_snooze_time_to_show * 60)
        else:
            # Event start has passed

            # Hide all before snooze buttons if were not hidden yet
            if (self.c_hidden_all_snooze_before_buttons == False):
                for pb_button, snooze_time in self.c_snooze_buttons.items():
                    if (snooze_time <= 0):
                        if (pb_button.isHidden() == False):
                            pb_button.setHidden(True)
                            l_changes_should_be_reflected = True

                self.c_hidden_all_snooze_before_buttons = True

            # Change the start label if not changed yet
            if (self.c_updated_label_post_start == False):
                self.l_event_start.setText('Event started at ' + str(self.c_parsed_event['start_date']))
                self.c_updated_label_post_start = True

            if (self.c_parsed_event['end_date'] > now_datetime):
                # The event end did not arrive yet - set timer for that time
                time_to_event_end = self.c_parsed_event['end_date'] - now_datetime
                time_to_wait_in_seconds = time_to_event_end.seconds
            else:
                # Event has ended - just change the label and no need to trigger the event anymore
                self.l_event_end.setText('Event ended at ' + str(self.c_parsed_event['end_date']))

        # Set timer to wake up in half a minute
        self.timer.start(30 * 1000)

        if (l_changes_should_be_reflected):
            # There are changes that should be reflected - bring the window to the front
            self.raise_()
            self.activateWindow()

    def open_video_and_snooze(self):
        global g_win_exit_reason
        global g_snooze_time_in_minutes

        webbrowser.open(self.c_video_link)

        g_win_exit_reason = EXIT_REASON_SNOOZE

        g_snooze_time_in_minutes = 5
    
        self.close()

    def open_video_and_dismiss(self):
        global g_win_exit_reason

        webbrowser.open(self.c_video_link)

        g_win_exit_reason = EXIT_REASON_DISMISS
    
        self.close()

def init_logging(module_name, file_log_level):
    global g_logger

    # create logger
    g_logger = logging.getLogger(module_name)
    g_logger.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - (%(threadName)-10s) - %(levelname)s - %(message)s')

    # create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # add formatter to ch
    console_handler.setFormatter(formatter)

    # add ch to logger
    g_logger.addHandler(console_handler)

    # Create file handler
    log_file = module_name + ".log"
    max_log_file_size = 100 * 1024 * 1024
    file_handler = RotatingFileHandler(
        log_file,
        mode='a',
        maxBytes=max_log_file_size,
        backupCount=5,
        encoding='utf-8')

    file_handler.setLevel(file_log_level)

    file_handler.setFormatter(formatter)

    g_logger.addHandler(file_handler)

    g_logger.info("========")
    g_logger.info("Starting")
    g_logger.info("========")

    return g_logger

def get_events_from_google_cal(google_account):
    global g_logger
    
    # Connect to the Google Account
    creds = None
    Credentials_file = 'app_credentials.json'
    token_file = google_account + '_token.json'

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
            g_logger.info("Creating a token for " + google_account)
            flow = InstalledAppFlow.from_client_secrets_file(
                Credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    g_logger.debug('Getting the upcoming 10 events')

    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()

    events = events_result.get('items', [])

    return(events)

def show_window(parsed_event, pipe_conn):
    global g_win_exit_reason
    global g_snooze_time_in_minutes

    app = QApplication(sys.argv)

    win = Window()

    win.init_window_from_parsed_event(parsed_event)

    # Show the window and bring it to the front
    g_win_exit_reason = EXIT_REASON_NONE
    g_snooze_time_in_minutes = 0

    app.setWindowIcon(QtGui.QIcon('icons8-calendar-64.png'))
    #win.windowHandle().setScreen(app.screens()[1])
    win.show()

    # Show the window on the main monitor
    monitor = QDesktopWidget().screenGeometry(0)
    win.move(monitor.left(), monitor.top())

    # Bring the windows to the front
    getattr(win, "raise")()
    win.activateWindow()

    app.exec()

    pipe_conn.send([g_win_exit_reason, g_snooze_time_in_minutes])

def show_window_and_parse_exit_status(event_key_str, parsed_event):
    global g_dismissed_events
    global g_dismissed_lock
    global g_snoozed_events
    global g_snoozed_lock
    global g_displayed_events
    global g_displayed_lock
    global g_logger

    parent_conn, child_conn = Pipe()
    proc = Process(
        target = show_window,
        args = (parsed_event, child_conn, ))
    proc.start()
    proc.join()

    data_from_child = parent_conn.recv()
    win_exit_reason = data_from_child[0]
    snooze_time_in_minutes = data_from_child[1]

    # Look at the window exit reason
    g_logger.debug("win_exit_reason " + str(win_exit_reason))
    g_logger.debug("snooze_time_in_minutes " + str(snooze_time_in_minutes))

    now_datetime = get_now_datetime()

    if (win_exit_reason == EXIT_REASON_NONE):
        g_logger.debug("Cancel")

    elif (win_exit_reason == EXIT_REASON_DISMISS):
        g_logger.debug("Dismiss")

        if (now_datetime < parsed_event['end_date']):
            with g_dismissed_lock:
                g_dismissed_events[event_key_str] = parsed_event

    elif (win_exit_reason == EXIT_REASON_SNOOZE):
        g_logger.debug("Snooze")
        if (snooze_time_in_minutes <= 0):
            delta_diff = datetime.timedelta(minutes=abs(snooze_time_in_minutes))
            parsed_event['event_wakeup_time'] = parsed_event['start_date'] - delta_diff
        else:
            delta_diff = datetime.timedelta(minutes=snooze_time_in_minutes)
            parsed_event['event_wakeup_time'] = now_datetime + delta_diff

        g_logger.debug("Snooze until " + str(parsed_event['event_wakeup_time']))
            
        with g_snoozed_lock:
            g_snoozed_events[event_key_str] = parsed_event

    else:
        g_logger.error("No exit reason")

    # Remove the event from the presented events
    with g_displayed_lock:
        del g_displayed_events[event_key_str]

def parse_event(event, parsed_event):
    global g_logger

    g_logger.debug(json.dumps(event, indent = 1))

    if (event['reminders'].get('useDefault') == True):
        minutes_before = 15
    else:
        override_rule = event['reminders'].get('overrides')
        if (override_rule):
            override_set = override_rule[0]
            minutes_before = override_set['minutes']
        else:
            g_logger.debug("No need to remind")
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

    meeting_description = event.get('description')
    if (meeting_description):
        parsed_event['description'] = meeting_description
    else:
        parsed_event['description'] = "No description"

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

    if (parsed_event['video_link'] == "No Video"):
        # Didn't find a video link in the expected location, let's see if there is a video link in the 
        # description.
        if (meeting_description):
            zoom_url_in_description = re.search(
                "(https://[a-zA-Z0-9]*\.zoom\.us/[a-zA-Z0-9?=/]*)", 
                meeting_description) 
            #print(zoom_url_in_description.group())
            if zoom_url_in_description:
                parsed_event['video_link'] = zoom_url_in_description.group()
            else:
                # Check if there is a Microsoft Teams link in the description
                teams_url_in_description = re.search(
                    "Click here to join the meeting<(https://teams.microsoft.com/l/meetup-join/.*)>",
                    meeting_description) 

                #print(teams_url_in_description.group(1))

                if teams_url_in_description:
                    parsed_event['video_link'] = teams_url_in_description.group(1)

            if (parsed_event['video_link'] == parsed_event['event_location']):
                # The event location already contains the Zoom link, no need to show it twice
                parsed_event['video_link'] = "No Video"

    # The event needs to be notified
    return(True)

def set_items_to_present_from_snoozed(events_to_present):
    global g_logger
    global g_snoozed_events
    global g_snoozed_lock

    now_datetime = get_now_datetime()

    # Identified the snoozed evnets that need to wake up
    snoozed_events_to_delete = []

    with g_snoozed_lock:
        for event_key_str, snoozed_event in g_snoozed_events.items():
            g_logger.debug("Snoozed event " + event_key_str + " " + str(snoozed_event['event_wakeup_time']) + " " + str(now_datetime))
            if (now_datetime >= snoozed_event['event_wakeup_time']):
                # Event needs to be woke up
                events_to_present[event_key_str] = snoozed_event
                snoozed_events_to_delete.append(event_key_str)

        # Clear the snoozed events that were woken up from the snoozed list
        while (len(snoozed_events_to_delete) > 0):
            k = snoozed_events_to_delete.pop()
            g_logger.debug("Deleteing event id " + str(k) + " from snoozed")
            del g_snoozed_events[k]

def add_items_to_show_from_calendar(google_account, events_to_present):
    global g_dismissed_events
    global g_dismissed_lock
    global g_snoozed_events
    global g_snoozed_lock
    global g_displayed_events
    global g_displayed_lock
    global g_logger

    g_logger.debug("add_items_to_show_from_calendar for " + google_account)

    # Get the next coming events from the google calendar
    num_of_retries = 0
    while num_of_retries <= 2:
        try: # In progress - handling intermittent exception from the Google service
            events = get_events_from_google_cal(google_account)
        except Exception as e:
            excType = str(e.__class__.__name__)
            excMesg = str(e)

            if ((excType == "ServerNotFoundError") 
            or (excType == "timeout") 
            or (excType == "TimeoutError") 
            or (excType == "ConnectionResetError")
            or (excType == "TransportError")
            or (excType == "OSError" and excMesg == "[Errno 51] Network is unreachable")
            ):
                # Exceptions that chould be intermittent due to networking issues.
                # We can wait for the next cycle and hope it will get resolved
                g_logger.debug("Networking issue (" + excType + ", " + excMesg + ") in get_events_from_google_cal for " + google_account + ". Retrying...")
                events = []
                break

            g_logger.error("Error in get_events_from_google_cal for " + google_account)
            g_logger.error('Exception type ' + excType)
            g_logger.error('Exception msg ' + excMesg)

            g_logger.error(traceback.format_exc())

            num_of_retries = num_of_retries + 1

            if (num_of_retries > 2):
                raise
            else:
                # Sleep for 2 seconds and retry
                time.sleep(2)
        else:
            # Getting the events was successful
            break

    # Handled the snoozed events
    if not events:
        g_logger.debug('No upcoming events found')
        return

    for event in events:
        g_logger.debug(str(event))
        parsed_event = {}
        now_datetime = get_now_datetime()
        a_snoozed_event_to_wakeup = False

        event_id = event['id']
        event_key = {
            'google_account' : google_account,
            'event_id' : event_id
        }
        event_key_str = json.dumps(event_key)
        g_logger.debug("Event ID " + str(event_id))

        with g_dismissed_lock:
            if (event_key_str in g_dismissed_events):
                if (g_dismissed_events[event_key_str]['raw_event']['updated'] == event['updated']):
                    g_logger.debug("Skipping dismissed event")
                    continue

                # Something in the event has changed - we want to remove it from the skipped events and parse it from scratch
                g_logger.debug("Dismissed event has changed after it was dismissed")
                del g_dismissed_events[event_key_str]

        with g_snoozed_lock:
            if (event_key_str in g_snoozed_events):
                if (g_snoozed_events[event_key_str]['raw_event']['updated'] == event['updated']):
                    g_logger.debug("Skipping snoozed event")
                    continue

                # Something in the event has changed - we want to remove it from the snoozed events and parse it from scratch
                g_logger.debug("Snoozed event has changed after it was dismissed")
                del g_snoozed_events[event_key_str]

        with g_displayed_lock:
            if (event_key_str in g_displayed_events):
                g_logger.debug("Skipping displayed event")
                continue
        
        if (event_id in events_to_present):
            g_logger.debug("Skipping event as it is already in the events to present")
            continue

        # Event not in the any other list
        parsed_event['raw_event'] = event
        parsed_event['event_name'] = event.get('summary', '(No title)')
        parsed_event['google_account'] = google_account
        g_logger.debug("Event Name " + parsed_event['event_name'])

        need_to_notify = parse_event(event, parsed_event)
        if (need_to_notify == True):
            # Event to get presented
            #print(event)
            events_to_present[event_key_str] = parsed_event

def present_relevant_events(events_to_present):
    global g_displayed_events
    global g_displayed_lock

    number_of_events_to_present = len(events_to_present)
    if (number_of_events_to_present > 0):
        for event_key_str, parsed_event in events_to_present.items():
            # Add the event to the presented events
            with g_displayed_lock:
                g_displayed_events[event_key_str] = parsed_event
            
            # Show the windows in a separate thread and process
            win_thread = threading.Thread(
                target = show_window_and_parse_exit_status,
                args = (event_key_str, parsed_event, ))

            win_thread.start()

        # Empty the dictionary
        events_to_present = {}

def clear_dismissed_events_that_have_ended():
    global g_dismissed_events
    global g_dismissed_lock
    global g_logger

    now_datetime = get_now_datetime()

    # Clear dismissed events that have ended
    dismissed_events_to_delete = []

    with g_dismissed_lock:
        for k, parsed_event in g_dismissed_events.items():
            g_logger.debug("Dismissed event " + str(k) + " " + str(parsed_event['end_date']) + " " + str(now_datetime))
            if (now_datetime > parsed_event['end_date']):
                dismissed_events_to_delete.append(k)

        while (len(dismissed_events_to_delete) > 0):
            k = dismissed_events_to_delete.pop()
            g_logger.debug("Deleteing event id " + str(k) + " from dismissed")
            del g_dismissed_events[k]

def init_global_objects():
    global g_config
    global g_dismissed_events
    global g_dismissed_lock
    global g_snoozed_events
    global g_snoozed_lock
    global g_displayed_events
    global g_displayed_lock
    global g_logger
    global g_log_level

    g_dismissed_events = {}
    g_dismissed_lock = threading.Lock()

    g_snoozed_events = {}
    g_snoozed_lock = threading.Lock()

    g_displayed_events = {}
    g_displayed_lock = threading.Lock()

    g_logger = init_logging("gCalNotifier", g_log_level)

def load_config():
    global g_config
    global g_google_accounts
    global g_log_level
    global g_refresh_frequency

    with open("gCalNotifier.json") as f:
        g_config = json.load(f)

    g_google_accounts = g_config.get("google accounts")
    if (not g_google_accounts):
        print("No \'google accounts\' defined in the config file")
        sys.exit()
    
    g_log_level = g_config.get("log level")
    if (not g_log_level):
        g_log_level = logging.INFO

    g_refresh_frequency = g_config.get("refresh frequency")
    if (not g_refresh_frequency):
        g_refresh_frequency = 30

if __name__ == "__main__":
    load_config()

    init_global_objects()

    # Loop forever
    while True:
        events_to_present = {}

        set_items_to_present_from_snoozed(events_to_present)

        for google_account in g_google_accounts:
            add_items_to_show_from_calendar(google_account, events_to_present)

        present_relevant_events(events_to_present)
        clear_dismissed_events_that_have_ended()

        g_logger.debug("Going to sleep for " + str(g_refresh_frequency) + " seconds")
        time.sleep(g_refresh_frequency)