from __future__ import print_function
import sys
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDesktopWidget, QTextBrowser, QMdiArea, QAction, QMdiSubWindow, QTextEdit
)

from PyQt5 import QtGui
from PyQt5 import QtCore

from gCalNotifier_ui import Ui_w_event

import datetime
import pytz
from tzlocal import get_localzone
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import validators

from logging_module import (
    init_logging,
    LOG_LEVEL_CRITICAL,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_INFO,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_NOTSET
)

import threading
from multiprocessing import Process, Pipe

import json
import traceback

import re

import webbrowser

from deepdiff import DeepDiff

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Exit reasons from the dialog
EXIT_REASON_NONE = 0
EXIT_REASON_DISMISS = 1
EXIT_REASON_SNOOZE = 2

def init_global_objects():
    global g_config
    global g_events_to_present
    global g_events_to_present_lock
    global g_dismissed_events
    global g_dismissed_lock
    global g_snoozed_events
    global g_snoozed_lock
    global g_displayed_events
    global g_displayed_lock
    global g_logger
    global g_log_level
    global g_mdi_mode
    global g_mdi_window

    g_mdi_mode = False

    g_events_to_present = {}
    g_events_to_present_lock = threading.Lock()

    g_dismissed_events = {}
    g_dismissed_lock = threading.Lock()

    g_snoozed_events = {}
    g_snoozed_lock = threading.Lock()

    g_displayed_events = {}
    g_displayed_lock = threading.Lock()

    g_logger = init_logging("gCalNotifier", "Main", g_log_level, LOG_LEVEL_INFO)


def get_now_datetime():
    return(datetime.datetime.now().astimezone())

def nice_json(json_object):
    return(json.dumps(json_object, indent = 1))

def has_self_tentative(event):
    # Check if the current user is tentative for the evnet
    if(event.get('attendees')):
        # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
        for attendee in event['attendees']:
            if(attendee.get('self') and attendee['self'] == True and attendee.get('responseStatus') and attendee['responseStatus'] == 'tentative'):
                # The current user is tentative for the meeting.
                return(True)

    # The current user is not tentative for the meeting.
    return(False)

def has_self_declined(event):
    # Check if the event was not declined by the current user
    if(event.get('attendees')):
        # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
        for attendee in event['attendees']:
            if(attendee.get('self') and attendee['self'] == True and attendee.get('responseStatus') and attendee['responseStatus'] == 'declined'):
                # The user declined the meeting. No need to display it
                return(True)

    # The event was not declined by the current user
    return(False)

NO_POPUP_REMINDER = -1

def get_max_reminder_in_minutes(p_event):
    max_minutes_before = NO_POPUP_REMINDER

    if (p_event['reminders'].get('useDefault') == True):
        max_minutes_before = 15
    else:
        override_rule = p_event['reminders'].get('overrides')
        if (override_rule):
            for override_entry in override_rule:
                if (override_entry['method'] == "popup"):
                    if int(override_entry['minutes']) > max_minutes_before:
                        max_minutes_before = int(override_entry['minutes'])

    return(max_minutes_before)

def has_event_changed_internal(orig_event, new_event):
    global g_logger

    g_logger.debug("Check for changes")

    diff_result = DeepDiff(orig_event, new_event)
    if (diff_result):

        g_logger.debug("Check if relevant changes")
        g_logger.debug(str(diff_result))

        for key in diff_result:
            if (key == 'values_changed'):
                for key1 in diff_result['values_changed']:
                    if (
                        key1 == "root['etag']" 
                        or key1 == "root['updated']" 
                        or key1 == "root['recurringEventId']"
                        or key1 == "root['conferenceData']['signature']"
                        or key1 == "root['iCalUID']"
                    ):
                        # Not relevant changes
                        continue

                    if re.search("root\['attendees'\]\[[0-9]+\]\['responseStatus'\]", key1):
                        # A change in the attendees response
                        if has_self_declined(new_event):
                            # The current user has declined the event
                            g_logger.info("The current user has declined")
                            return(True)

                        continue

                    if (key1 == "root['extendedProperties']['shared']['meetingParams']"):
                        # Compare the internal parameters
                        diff_extended_properties = DeepDiff(diff_result['values_changed'][key1]['new_value'], diff_result['values_changed'][key1]['old_value'])
                        for key2 in diff_extended_properties:
                            if (key2 == "invitees_hash"):
                                # Not relevant change
                                continue

                            # Found a change
                            g_logger.info("Found a relevant change")
                            g_logger.info(key2 + ":" + str(diff_extended_properties[key2]))
                            return(True)
                        
                        continue

                    if re.search("root\['reminders'\]", key1):
                        # A change in the reminders
                        # Compare the max minutes to notify before in both original and new event
                        orig_event_max_reminder_in_minutes = get_max_reminder_in_minutes(orig_event)
                        new_event_max_reminder_in_minutes = get_max_reminder_in_minutes(new_event)
                        
                        if (orig_event_max_reminder_in_minutes != new_event_max_reminder_in_minutes):
                            # The max reminder in minutes has changed
                            g_logger.info("The max reminder in minutes has changed")
                            return(True)

                        continue

                    # Found a change
                    g_logger.info("Found a relevant change")
                    g_logger.info(key1 + ":" + str(diff_result['values_changed'][key1]))
                    return(True)
                
                continue
            # key == 'values_changed'

            elif (key == 'iterable_item_added' or key == 'iterable_item_removed' or key == 'dictionary_item_added' or key == 'dictionary_item_removed'):
                for key1 in diff_result[key]:
                    if (key1 == "root['conferenceData']['signature']"):
                        # Not relevant changes
                        continue
                        
                    if re.search("root\['attendees'\]\[[0-9]+\]", key1):
                        # An attendee added - can be ignored
                        continue

                    if re.search("root\['reminders'\]", key1):
                        # A change in the reminders
                        # Compare the max minutes to notify before in both original and new event
                        orig_event_max_reminder_in_minutes = get_max_reminder_in_minutes(orig_event)
                        new_event_max_reminder_in_minutes = get_max_reminder_in_minutes(new_event)
                        
                        if (orig_event_max_reminder_in_minutes != new_event_max_reminder_in_minutes):
                            # The max reminder in minutes has changed
                            g_logger.info("The max reminder in minutes has changed")
                            return(True)

                        continue

                    # Found a change
                    g_logger.info("Found a relevant change")
                    g_logger.info(key1)
                    return(True)

                continue
            # key == 'iterable_item_added' or or key == 'iterable_item_removed'

            g_logger.info("Found a relevant change")
            g_logger.info(key + ":" + str(diff_result[key]))
            return(True)

    return(False)

def has_event_changed(orig_event):
    global g_logger

    try:
        # First check if the event still exists
        raw_event = get_events_from_google_cal_with_try(
            orig_event['google_account'],
            orig_event['cal id'],
            orig_event['raw_event']['id'])

    except ConnectivityIssue:
        # Having a connectivity issue - we will assume the event did not change in the g-cal
        return False

    if(raw_event is None):
        # The event does not exist anymore
        g_logger.info("event does not exist anymore - strange")
        g_logger.info("*********** " + orig_event['event_name'] + " ***********")

        return True

    if (has_event_changed_internal(orig_event['raw_event'], raw_event)):
        g_logger.info("*********** " + orig_event['event_name'] + " ***********")
        return(True)

    return(False)

def get_events_from_google_cal(google_account, cal_id, event_id = None):
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

    if (event_id is None):
        # Get the next 10 events
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        g_logger.debug('Getting the upcoming 10 events')

        events_result = service.events().list(
            calendarId=cal_id, 
            timeMin=now,
            #timeMin='2023-08-17T14:00:00-07:00', 
            #timeMax='2023-08-17T15:00:00-07:00',
            maxResults=10, 
            singleEvents=True,
            orderBy='startTime').execute()

        events = events_result.get('items', [])

        return(events)

    else:
        # Get a specitic event
        raw_event = service.events().get(
        calendarId=cal_id,
        eventId=str(event_id)).execute()

        return(raw_event)

class ConnectivityIssue(Exception):
    pass

def get_events_from_google_cal_with_try(google_account, cal_id, event_id = None):
    global g_logger

    num_of_retries = 0
    none_networking_known_exception = False

    while True:
        try: # In progress - handling intermittent exception from the Google service
            raw_events = get_events_from_google_cal(google_account, cal_id, event_id)
        except Exception as e:
            excType = str(e.__class__.__name__)
            excMesg = str(e)

            if ((excType == "ServerNotFoundError") 
            or (excType == "timeout") 
            or (excType == "TimeoutError") 
            or (excType == "ConnectionResetError")
            or (excType == "TransportError")
            or (excType == "SSLCertVerificationError")
            or (excType == "SSLEOFError")
            or (excType == "OSError" and excMesg == "[Errno 51] Network is unreachable")
            ):
                # Exceptions that chould be intermittent due to networking issues.

                g_logger.debug('Networking issue with Exception type ' + excType)

            else:
                # Not a known exception

                none_networking_known_exception = True

                g_logger.info("Error in get_events_from_google_cal_with_try for " + google_account)
                g_logger.info('Exception type ' + excType)
                g_logger.info('Exception msg ' + excMesg)

                g_logger.info(traceback.format_exc())

            num_of_retries = num_of_retries + 1

            if (num_of_retries > 2):
                if (none_networking_known_exception):
                    # An unknown exception has happened
                    raise
                else:
                    # Only known connectivity issues have happend
                    g_logger.info('Only known connectivity issues have happend')
                    raise ConnectivityIssue()

            else:
                # Sleep for 2 seconds and retry
                time.sleep(2)
        else:
            # Getting the event was successful
            return(raw_events)

def add_items_to_show_from_calendar(google_account, cal_name, cal_id):
    global g_events_to_present
    global g_events_to_present_lock
    global g_dismissed_events
    global g_dismissed_lock
    global g_snoozed_events
    global g_snoozed_lock
    global g_displayed_events
    global g_displayed_lock
    global g_logger

    g_logger.debug("add_items_to_show_from_calendar for " + google_account)

    # Get the next coming events from the google calendar
    try: # In progress - handling intermittent exception from the Google service
        events = get_events_from_google_cal_with_try(google_account, cal_id)

    except ConnectivityIssue:
        # Having a connectivity issue - we will assume the event did not change in the g-cal
        events = []

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
            # 'google_account' : google_account,
            # 'cal_id' : cal_id,
            'event_id' : event_id
        }
        event_key_str = json.dumps(event_key)
        g_logger.debug("Event ID " + str(event_id))

        with g_dismissed_lock:
            if (event_key_str in g_dismissed_events):
                g_logger.debug("Skipping dismissed event")
                continue

        with g_snoozed_lock:
            if (event_key_str in g_snoozed_events):
                g_logger.debug("Skipping snoozed event")
                continue

        with g_displayed_lock:
            if (event_key_str in g_displayed_events):
                g_logger.debug("Skipping displayed event")
                continue
        
        with g_events_to_present_lock:
            if (event_id in g_events_to_present):
                g_logger.debug("Skipping event as it is already in the events to present")
                continue

        # Event not in the any other list
        parsed_event['raw_event'] = event
        parsed_event['event_name'] = event.get('summary', '(No title)')
        parsed_event['google_account'] = google_account
        parsed_event['cal name'] = cal_name
        parsed_event['cal id'] = cal_id
        g_logger.debug("Event Name " + parsed_event['event_name'])

        need_to_notify = parse_event(event, parsed_event)
        if (need_to_notify == True):
            # Event to get presented
            g_logger.debug(str(event))

            with g_events_to_present_lock:
                g_events_to_present[event_key_str] = parsed_event

            g_logger.debug(
                "Event to be presented - "
                + " " + parsed_event['event_name'] 
                + " " + parsed_event['google_account'] 
                + " " + parsed_event['cal id']
                + " " + parsed_event['raw_event']['id'])

def set_events_to_be_displayed():
    global g_google_accounts
    global g_logger

    clear_dismissed_events_that_have_ended()
    set_items_to_present_from_snoozed()

    for google_account in g_google_accounts:
        for cal_for_account in google_account["calendar list"]:
            g_logger.debug(google_account["account name"] + " " + str(cal_for_account))
            add_items_to_show_from_calendar(
                google_account["account name"], 
                cal_for_account['calendar name'], 
                cal_for_account['calendar id'])

def handle_window_exit(event_key_str, parsed_event, win_exit_reason, snooze_time_in_minutes):
    global g_logger
    global g_dismissed_lock
    global g_dismissed_events
    global g_snoozed_lock
    global g_snoozed_events    

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

# The notification window
class Window(QMainWindow, Ui_w_event):
    c_snooze_buttons = {}
    c_parsed_event = {}
    c_event_key_str = ""
    c_is_first_display_of_window = False
    c_hidden_all_snooze_before_buttons = False
    c_updated_label_post_start = False
    c_updated_label_post_end = False
    c_video_link = None
    c_window_closed = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
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


    def init_window_from_parsed_event(self, event_key_str, parsed_event):
        global g_win_exit_reason 
        global g_snooze_time_in_minutes 

        g_win_exit_reason = EXIT_REASON_NONE
        g_snooze_time_in_minutes = 0

        self.c_event_key_str = event_key_str
        self.c_parsed_event = parsed_event
        self.c_is_first_display_of_window = True
        self.c_window_closed = False

        self.setWindowTitle(parsed_event['event_name'])

        self.l_account.setText(parsed_event['cal name'] + " calendar in " + parsed_event['google_account'])

        self.l_event_name.setText(parsed_event['event_name'])

        g_logger.info("Nofied for " + parsed_event['google_account'] + ": " + parsed_event['event_name'])

        if parsed_event['all_day_event']:
            self.l_all_day.setText("An all day event")
        else:
            self.l_all_day.setHidden(True)

        parsed_event['start_time_in_loacal_tz'] = str(parsed_event['start_date'].astimezone(get_localzone()))
        parsed_event['end_time_in_loacal_tz'] = str(parsed_event['end_date'].astimezone(get_localzone()))

        self.l_event_start.setText('Starting at ' + parsed_event['start_time_in_loacal_tz'])
        self.l_event_end.setText('Ending at ' + parsed_event['end_time_in_loacal_tz'])

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

        # Hide the missing video message - in the next section we will decide whether to show it
        is_hide_missing_video = True

        need_to_record_meeting = parsed_event.get('need_to_record_meeting', False)
        if (need_to_record_meeting):
            is_hide_missing_video = False

            self.l_missing_video.setText("Remember to record!!!")

        elif (self.c_video_link is None):
            self.pb_open_video.setHidden(True)
            self.pb_open_video_and_snooze.setHidden(True)
            self.pb_open_video_and_dismiss.setHidden(True)

            if (parsed_event['num_of_attendees'] > 1):
            # Num of attendees > 1 and no video link
                # We expect a video link as there are multiple attendees for this meeting

                # Let's check if we have our special sign
                is_no_video_ok = re.search(
                    'NO_VIDEO_OK',
                    parsed_event['description'])

                if (not is_no_video_ok):
                    # We need to show the missing video message
                    is_hide_missing_video = False

        if (is_hide_missing_video):
            self.l_missing_video.setHidden(True)
        else:
            self.l_missing_video.setAutoFillBackground(True) # This is important!!
            color  = QtGui.QColor(233, 10, 150)
            alpha  = 140
            values = "{r}, {g}, {b}, {a}".format(r = color.red(),
                                                g = color.green(),
                                                b = color.blue(),
                                                a = alpha
                                                )
            self.l_missing_video.setStyleSheet("QLabel { background-color: rgba("+values+"); }")


        if (parsed_event['description'] != "No description"):
            self.t_description.setHtml(parsed_event['description'])

        self.t_raw_event.setText(nice_json(parsed_event['raw_event']))
        self.tabWidget.setCurrentIndex(0)
        
        self.update_controls_based_on_event_time()

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
        self.timer.timeout.connect(self.update_controls_based_on_event_time) 
        self.pb_open_video.clicked.connect(self.open_video)
        self.pb_open_video_and_snooze.clicked.connect(self.open_video_and_snooze)
        self.pb_open_video_and_dismiss.clicked.connect(self.open_video_and_dismiss)

    def handle_window_exit_from_within_window(self):
        global g_win_exit_reason
        global g_snooze_time_in_minutes

        if isinstance(self.parent(), QMdiSubWindow):
            # MDI mode
            handle_window_exit(
                self.c_event_key_str,
                self.c_parsed_event,
                g_win_exit_reason,
                g_snooze_time_in_minutes)
            
            self.parent().close()
        else:
            self.close()

    def clickedDismiss(self):
        global g_win_exit_reason
        global g_snooze_time_in_minutes

        g_win_exit_reason = EXIT_REASON_DISMISS
        g_snooze_time_in_minutes = 0
        self.c_window_closed = True

        self.handle_window_exit_from_within_window()

    def snooze_general(self, p_button):
        global g_win_exit_reason
        global g_snooze_time_in_minutes

        g_win_exit_reason = EXIT_REASON_SNOOZE

        if (p_button in self.c_snooze_buttons):
            g_snooze_time_in_minutes = self.c_snooze_buttons[p_button]
    
        self.handle_window_exit_from_within_window()

    def update_controls_based_on_event_time(self):
        global g_win_exit_reason
        global g_logger

        if (self.c_window_closed):
            if isinstance(self.parent(), QMdiSubWindow):
                self.parent().close()
            else:
                self.close()

            return

        if (self.c_is_first_display_of_window):
            l_changes_should_be_reflected = True
            self.c_is_first_display_of_window = False
        else:
            l_changes_should_be_reflected = False

            # Let's first check that the event has not changed
            if(has_event_changed(self.c_parsed_event)):
                # The event has changed, closing the window to refresh the event
                g_logger.debug("event changed - update_controls_based_on_event_time")
                g_win_exit_reason = EXIT_REASON_NONE

                self.handle_window_exit_from_within_window()
                
                return()

        now_datetime = get_now_datetime()

        if (self.c_parsed_event['start_date'] > now_datetime):
            # Event start did not arrive yet - hide all before snooze buttons that are not relevant anymore
            time_to_event_start = self.c_parsed_event['start_date'] - now_datetime
            time_to_event_in_minutes = time_to_event_start.seconds / 60

            self.l_time_left.setText(str(int(time_to_event_in_minutes) + 1) + ' minutes left until the event starts')

            for pb_button, snooze_time in self.c_snooze_buttons.items():
                if (snooze_time <= 0 and abs(snooze_time) > time_to_event_in_minutes):
                    if (pb_button.isHidden() == False):
                        pb_button.setHidden(True)
                        l_changes_should_be_reflected = True
        else:
            # Event start has passed

            self.l_time_left.setHidden(True)

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
                self.l_event_start.setText('Event started at ' + self.c_parsed_event['start_time_in_loacal_tz'])
                self.c_updated_label_post_start = True

            if (self.c_parsed_event['end_date'] <= now_datetime):
                # Event has ended - just change the label and no need to trigger the event anymore
                self.l_event_end.setText('Event ended at ' + str(self.c_parsed_event['end_time_in_loacal_tz']))
                self.c_updated_label_post_end = True

        if (l_changes_should_be_reflected):
            # There are changes that should be reflected - bring the window to the front
            self.raise_()
            self.activateWindow()

        if (self.c_updated_label_post_end == False):
        # Not all controls that could have changed have already changed
            # Set timer to wake up in half a minute
            self.timer.start(30 * 1000)

    def open_video(self):
        webbrowser.open(self.c_video_link)

    def open_video_and_snooze(self):
        global g_win_exit_reason
        global g_snooze_time_in_minutes

        self.open_video()

        g_win_exit_reason = EXIT_REASON_SNOOZE

        g_snooze_time_in_minutes = 5
    
        self.handle_window_exit_from_within_window()

    def open_video_and_dismiss(self):
        global g_win_exit_reason

        self.open_video()

        g_win_exit_reason = EXIT_REASON_DISMISS

        self.handle_window_exit_from_within_window()

def show_window(event_key_str, parsed_event, pipe_conn, log_level):
    global g_win_exit_reason
    global g_snooze_time_in_minutes
    global g_logger

    g_logger = init_logging("gCalNotifier", "Window", log_level, LOG_LEVEL_DEBUG)

    app = QApplication(sys.argv)

    win = Window()

    win.init_window_from_parsed_event(event_key_str, parsed_event)

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

def show_window_in_mdi(event_key_str, parsed_event):
    global g_win_exit_reason
    global g_snooze_time_in_minutes
    global g_logger

    win = Window()

    win.init_window_from_parsed_event(event_key_str, parsed_event)
    win.setFixedWidth(730)
    win.setFixedHeight(650)

    sub = QMdiSubWindow()
    sub.setWidget(win)
    #sub.setWidget(QTextEdit())
    #sub.setWindowTitle(parsed_event['event_name'])
    g_mdi_window.mdi.addSubWindow(sub)
    sub.show()

    return

    app = QApplication(sys.argv)

    win = Window()

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
    global g_events_to_present
    global g_events_to_present_lock
    global g_dismissed_events
    global g_dismissed_lock
    global g_snoozed_events
    global g_snoozed_lock
    global g_displayed_events
    global g_displayed_lock
    global g_logger
    global g_log_level
    global g_mdi_window
    global g_mdi_mode

    if (g_mdi_mode):
        show_window_in_mdi(event_key_str, parsed_event)
        return
    
    parent_conn, child_conn = Pipe()
    proc = Process(
        target = show_window,
        args = (event_key_str, parsed_event, child_conn, g_log_level))
    proc.start()
    proc.join()

    data_from_child = parent_conn.recv()
    win_exit_reason = data_from_child[0]
    snooze_time_in_minutes = data_from_child[1]

    # Look at the window exit reason
    g_logger.debug("win_exit_reason " + str(win_exit_reason))
    g_logger.debug("snooze_time_in_minutes " + str(snooze_time_in_minutes))

    handle_window_exit(
        event_key_str,
        parsed_event,
        win_exit_reason,
        snooze_time_in_minutes)

video_links_reg_exs = [
    "(https://[a-zA-Z0-9-]*[\.]*zoom\.us/j/[a-zA-Z0-9-_\.&?=/]*)", # Zoom
    "Click here to join the meeting<(https://teams.microsoft.com/l/meetup-join/.*)>", # Meet   
    "[<>](https://[a-zA-Z0-9-]*\.webex\.com/[a-zA-Z0-9-]*/j\.php\?MTID=[a-zA-Z0-9-]*)[<>]", # Webex
    "(https://chime.aws/[0-9]*)"
]

def look_for_video_link_in_meeting_description(p_meeting_description):
    for reg_ex in video_links_reg_exs:
        video_url_in_description = re.search(
            reg_ex,
            p_meeting_description)

        if video_url_in_description:
            return(video_url_in_description.group(1))

    # No known video link found
    return("No Video")

    # Look for a Zoom link
    zoom_url_in_description = re.search(
        "(https://[a-zA-Z0-9-]*[\.]*zoom\.us/[a-zA-Z0-9-\.&?=/]*)", 
        p_meeting_description) 
    if zoom_url_in_description:
        return(zoom_url_in_description.group())

    # Look for a Meet link
    teams_url_in_description = re.search(
        "Click here to join the meeting<(https://teams.microsoft.com/l/meetup-join/.*)>",
        p_meeting_description) 

    if teams_url_in_description:
        return(teams_url_in_description.group(1))

    # Look for a Webex link
    webex_url_in_description = re.search(
        ">(https://[a-zA-Z0-9-]*\.webex\.com/[a-zA-Z0-9-]*/j\.php\?MTID=[a-zA-Z0-9-]*)<",
        p_meeting_description)

    if webex_url_in_description:
        return(webex_url_in_description.group(1))

    # No known video link found
    return("No Video")

def get_number_of_attendees(event):
    num_of_attendees = 0

    if(event.get('attendees')):
        # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
        for attendee in event['attendees']:
            num_of_attendees = num_of_attendees + 1

    return(num_of_attendees)

def parse_event_description(meeting_description, parsed_event):
    global g_logger

    # Check if the event has gCalNotifier config
    need_to_record_meeting = re.search(
        "record:yes", 
        meeting_description) 
    if need_to_record_meeting:
        parsed_event['need_to_record_meeting'] = True
        g_logger.debug("Need to record meeting")
        
    else:
        parsed_event['need_to_record_meeting'] = False
        g_logger.debug("No need to record meeting")

def parse_event(event, parsed_event):
    global g_logger

    g_logger.debug(nice_json(event))

    # Check if the event was not declined by the current user
    if has_self_declined(event):
        return(False)

    minutes_before_to_notify = get_max_reminder_in_minutes(event)
    if (minutes_before_to_notify == NO_POPUP_REMINDER):
        # No notification reminders
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
    delta_diff = datetime.timedelta(minutes=minutes_before_to_notify)
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
        parse_event_description(meeting_description, parsed_event)

    else:
        parsed_event['description'] = "No description"

    if (has_self_tentative(event)):
        # The current user is Tentative fot this event
        parsed_event['event_name'] = "Tentative - " + parsed_event['event_name']

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
            parsed_event['video_link'] = look_for_video_link_in_meeting_description(meeting_description)

            if (parsed_event['video_link'] == parsed_event['event_location']):
                # The event location already contains the video link, no need to show it twice
                parsed_event['video_link'] = "No Video"

    parsed_event['num_of_attendees'] = get_number_of_attendees(event)

    # The event needs to be notified
    return(True)

def set_items_to_present_from_snoozed():
    global g_logger
    global g_snoozed_events
    global g_snoozed_lock

    now_datetime = get_now_datetime()

    # Identified the snoozed evnets that need to wake up
    snoozed_events_to_delete = []

    with g_snoozed_lock:
        for event_key_str, snoozed_event in g_snoozed_events.items():
            g_logger.debug("Snoozed event " + event_key_str + " " + str(snoozed_event['event_wakeup_time']) + " " + str(now_datetime))

            if(has_event_changed(snoozed_event)):
                # The event has changed, we will let the system re-parse the event as new
                g_logger.info("event changed - set_items_to_present_from_snoozed")
                snoozed_events_to_delete.append(event_key_str)

            elif (now_datetime >= snoozed_event['event_wakeup_time']):
                # Event needs to be woke up
                with g_events_to_present_lock:
                    g_events_to_present[event_key_str] = snoozed_event
                snoozed_events_to_delete.append(event_key_str)

        # Clear the snoozed events that were woken up from the snoozed list
        while (len(snoozed_events_to_delete) > 0):
            k = snoozed_events_to_delete.pop()
            g_logger.debug("Deleteing event id " + str(k) + " from snoozed")
            del g_snoozed_events[k]

def present_relevant_events():
    global g_events_to_present
    global g_events_to_present_lock
    global g_displayed_events
    global g_displayed_lock
    global g_mdi_mode

    
    while True:  
        with g_events_to_present_lock:
            if (len(g_events_to_present) > 0):
                event_key_str = next(iter(g_events_to_present))
                parsed_event = g_events_to_present[event_key_str]
                del g_events_to_present[event_key_str]
            else:
                # No more entries to present
                return
        
        # Add the event to the presented events
        with g_displayed_lock:
            g_displayed_events[event_key_str] = parsed_event
        
        if (g_mdi_mode):
            show_window_and_parse_exit_status(event_key_str, parsed_event)
        else:
            # Show the windows in a separate thread and process
            win_thread = threading.Thread(
                target = show_window_and_parse_exit_status,
                args = (event_key_str, parsed_event, ))

            win_thread.start()

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
                # The event has ended
                g_logger.debug("Event end date has passed - clear_dismissed_events_that_have_ended")
                g_logger.debug("Dismissed event end date" + str(parsed_event['end_date']))

                dismissed_events_to_delete.append(k)

            elif has_event_changed(parsed_event):
                # The event has changed, we will let the system re-parse the event as new
                g_logger.info("event changed - clear_dismissed_events_that_have_ended")
                dismissed_events_to_delete.append(k)

        while (len(dismissed_events_to_delete) > 0):
            k = dismissed_events_to_delete.pop()
            g_logger.debug("Deleteing event id " + str(k) + " from dismissed")
            del g_dismissed_events[k]

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

    for google_account in g_google_accounts:
        account_name = google_account.get("account name")
        if (not account_name):
            print ("No \'account name\' defined for a google account entry")
            sys.exit()
 
    g_log_level = g_config.get("log level")
    if (not g_log_level):
        g_log_level = logging.INFO

    g_refresh_frequency = g_config.get("refresh frequency")
    if (not g_refresh_frequency):
        g_refresh_frequency = 30

def get_calendar_list_for_account(google_account):
    global g_logger

    google_account_name = google_account["account name"]
    additional_calendars = google_account.get("additional calenadars")

    # Init the list
    calendar_list_for_account = [
        {
            'calendar name' : "Primary",
            'calendar id' : "primary"
        }
    ]
    
    # Connect to the Google Account
    creds = None
    Credentials_file = 'app_credentials.json'
    token_file = google_account_name + '_token.json'

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
            g_logger.info("Creating a token for " + google_account_name)
            flow = InstalledAppFlow.from_client_secrets_file(
                Credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    g_logger.info("Printing calendars for " + google_account_name)
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()

        for calendar_list_entry in calendar_list['items']:
            prefix_text = "Don't include - "
            if(additional_calendars and (calendar_list_entry['summary'] in additional_calendars)):
                prefix_text = "*** Include - "
                calendar_list_entry_to_add = {
                    'calendar name' : calendar_list_entry['summary'],
                    'calendar id' : calendar_list_entry['id']
                }
                calendar_list_for_account.append(calendar_list_entry_to_add)
            g_logger.info(prefix_text + " " + calendar_list_entry['summary'] + " " + calendar_list_entry['id'])

        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    google_account["calendar list"] = calendar_list_for_account
    g_logger.info("The calendar list for " + google_account_name + ":")
    g_logger.info(str(calendar_list_for_account))

def prep_google_accounts_and_calendars():
    global g_google_accounts

    for google_account in g_google_accounts:
        get_calendar_list_for_account(google_account)

class MDIWindow(QMainWindow):
    count = 0

    def present_relevant_events_in_sub_windows(self):
        global g_logger
        global g_refresh_frequency

        g_logger.debug("Presenting relevant events")

        present_relevant_events()

        self.timer.start(int(g_refresh_frequency/2) * 1000)

    def __init__(self):
        super().__init__()
 
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        bar = self.menuBar()
 
        file = bar.addMenu("File")
        file.addAction("New")
        file.addAction("cascade")
        file.addAction("Tiled")
        file.triggered[QAction].connect(self.WindowTrig)
        self.setWindowTitle("gCalNotifier")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.present_relevant_events_in_sub_windows) 

    def showEvent(self, event):
        # This method will be called when the main MDI window is shown
        super().showEvent(event)  # Call the base class showEvent first
        self.present_relevant_events_in_sub_windows()

    def WindowTrig(self, p):
        if p.text() == "New":
            MDIWindow.count = MDIWindow.count + 1
            sub = QMdiSubWindow()
            sub.setWidget(QTextEdit())
            sub.setWindowTitle("Sub Window" + str(MDIWindow.count))
            self.mdi.addSubWindow(sub)
            sub.show()
 
        if p.text() == "cascade":
            self.mdi.cascadeSubWindows()
 
        if p.text() == "Tiled":
            self.mdi.tileSubWindows()

def get_events_to_display_main_loop():
    global g_log_level
    global g_refresh_frequency

    while True:
        set_events_to_be_displayed()

        g_logger.debug("Going to sleep for " + str(g_refresh_frequency) + " seconds")
        time.sleep(g_refresh_frequency)

def start_getting_events_to_display_main_loop_thread():
    main_loop_thread = threading.Thread(
        target = get_events_to_display_main_loop)

    main_loop_thread.start()
    
# Main
if __name__ == "__main__":
    load_config()

    init_global_objects()

    prep_google_accounts_and_calendars()

    g_mdi_mode = False
    
    if (g_mdi_mode):
        # Start a thread to look for events to display
        start_getting_events_to_display_main_loop_thread()

        app = QApplication(sys.argv)
        g_mdi_window = MDIWindow()
        g_mdi_window.show()
        app.exec_()
    else:
        # Loop forever
        while True:
            set_events_to_be_displayed()

            present_relevant_events()

            g_logger.debug("Going to sleep for " + str(g_refresh_frequency) + " seconds")
            time.sleep(g_refresh_frequency)