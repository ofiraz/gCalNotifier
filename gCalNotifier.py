from __future__ import print_function
import sys
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDesktopWidget, QTextBrowser, QMdiArea, QAction, QMdiSubWindow, QTextEdit
)

from PyQt5 import QtGui
from PyQt5 import QtCore
import logging

import datetime
import pytz

from logging_module import (
    init_logging,
    LOG_LEVEL_CRITICAL,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_INFO,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_NOTSET
)

from google_calendar_utilities import (
    get_calendar_list_for_account,
    get_events_from_google_cal_with_try,
    ConnectivityIssue
)

import threading
from multiprocessing import Process, Pipe

import json
import re

from json_utils import nice_json

from datetime_utils import get_now_datetime

from EventWindow import Window

from event_utils import (
    has_event_changed,
    get_max_reminder_in_minutes,
    has_self_declined,
    NO_POPUP_REMINDER
)

def init_global_objects():
    global g_events_to_present
    global g_dismissed_events
    global g_snoozed_events
    global g_displayed_events
    global g_logger
    global g_log_level
    global g_mdi_window
    global g_events_logger

    g_events_to_present = Events_Collection("g_events_to_present")
    g_dismissed_events = Events_Collection("g_dismissed_events")
    g_snoozed_events = Events_Collection("g_snoozed_events")
    g_displayed_events = Events_Collection("g_displayed_events", g_mdi_window.add_event_to_display_cb, g_mdi_window.remove_event_from_display_cb)

    g_logger = init_logging("gCalNotifier", "Main", g_log_level, LOG_LEVEL_INFO)
    g_events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)

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

def add_items_to_show_from_calendar(google_account, cal_name, cal_id):
    global g_events_to_present
    global g_dismissed_events
    global g_snoozed_events
    global g_displayed_events
    global g_logger

    g_logger.debug("add_items_to_show_from_calendar for " + google_account)

    # Get the next coming events from the google calendar
    try: # In progress - handling intermittent exception from the Google service
        events = get_events_from_google_cal_with_try(g_logger, google_account, cal_id)

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

        if (g_dismissed_events.is_event_in(event_key_str)):
            g_logger.debug("Skipping dismissed event")
            continue

        if (g_snoozed_events.is_event_in(event_key_str)):
            g_logger.debug("Skipping snoozed event")
            continue

        if (g_displayed_events.is_event_in(event_key_str)):
            g_logger.debug("Skipping displayed event")
            continue
        
        if (g_events_to_present.is_event_in(event_key_str)):
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

            g_events_to_present.add_event(event_key_str, parsed_event)

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

class Events_Collection:
    def __init__(self, collection_name, add_cb = None, remove_cb = None):
        self.c_events = {}
        self.c_lock = threading.Lock()
        self.c_collection_name = collection_name
        self.c_add_cb = add_cb
        self.c_remove_cb = remove_cb

    def is_event_in(self, event_key_str):
        global g_logger

        g_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            g_logger.debug("After lock for " + self.c_collection_name)

            return(event_key_str in self.c_events)       

    def add_event_safe(self, event_key_str, parsed_event):
        self.c_events[event_key_str] = parsed_event

        if (self.c_add_cb):
            self.c_add_cb()
        
    def add_event(self, event_key_str, parsed_event):
        global g_logger

        g_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            self.add_event_safe(event_key_str, parsed_event)

        g_logger.debug("After lock for " + self.c_collection_name)


    def remove_event_safe(self, event_key_str):
        global g_logger

        del self.c_events[event_key_str]

        if (self.c_remove_cb):
            self.c_remove_cb()

    def remove_event(self, event_key_str):
        global g_logger

        g_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            self.remove_event_safe(event_key_str)

        g_logger.debug("After lock for " + self.c_collection_name)

    def pop(self):
        global g_logger

        g_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            if (len(self.c_events) > 0):
                event_key_str = next(iter(self.c_events))
                parsed_event = self.c_events[event_key_str]
                self.remove_event_safe(event_key_str)

                g_logger.debug("After lock for " + self.c_collection_name)

                return(event_key_str, parsed_event)
            else:
                # Empty collection
                g_logger.debug("After lock for " + self.c_collection_name)

                return(None, None)

    def remove_events_based_on_condition(self, condition_function):
        global g_logger

        events_to_delete = []

        g_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            for event_key_str, parsed_event in self.c_events.items():
                if (condition_function(event_key_str, parsed_event)):
                    # The condition was met, need remove the item
                    events_to_delete.append(event_key_str)

            # Delete the events that were collected to be deleted
            while (len(events_to_delete) > 0):
                event_key_str = events_to_delete.pop()
                self.remove_event_safe(event_key_str)

        g_logger.debug("After lock for " + self.c_collection_name)

def show_window_in_mdi(event_key_str, parsed_event):
    global g_logger
    global g_mdi_window
    global g_events_logger
    global g_dismissed_events
    global g_snoozed_events
    global g_displayed_events

    win = Window(g_logger, g_events_logger, g_dismissed_events, g_snoozed_events, g_displayed_events, g_mdi_window)

    win.init_window_from_parsed_event(event_key_str, parsed_event)
    win.setFixedWidth(730)
    win.setFixedHeight(650)

    sub = QMdiSubWindow()
    sub.setWidget(win)
    g_mdi_window.mdi.addSubWindow(sub)
    sub.show()

    g_events_logger.info("Displaying event:" + parsed_event['event_name'])

    g_mdi_window.raise_()
    g_mdi_window.activateWindow()

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

def condition_function_for_removing_snoozed_events(event_key_str, parsed_event):
    global g_logger
    global g_events_to_present

    now_datetime = get_now_datetime()

    g_logger.debug("Snoozed event " + event_key_str + " " + str(parsed_event['event_wakeup_time']) + " " + str(now_datetime))

    if(has_event_changed(g_logger, parsed_event)):
        # The event has changed, we will let the system re-parse the event as new
        g_logger.info("event changed - set_items_to_present_from_snoozed")
        
    elif (now_datetime >= parsed_event['event_wakeup_time']):
        # Event needs to be woke up
        g_events_to_present.add_event(event_key_str, parsed_event)

    else:
        # No need to remove the evnet
        return(False)
    
    # Need to remove the evnet
    return(True)

def set_items_to_present_from_snoozed():
    global g_logger
    global g_snoozed_events

    g_snoozed_events.remove_events_based_on_condition(condition_function_for_removing_snoozed_events)

    return

def present_relevant_events():
    global g_events_to_present
    global g_displayed_events
    
    while True:
        event_key_str, parsed_event = g_events_to_present.pop()
        if (event_key_str == None):
            # No more entries to present
            return
        
        # Add the event to the presented events
        g_displayed_events.add_event(event_key_str, parsed_event)
        
        show_window_in_mdi(event_key_str, parsed_event)

def condition_function_for_removing_dismissed_events(event_key_str, parsed_event):
    global g_logger
    global g_dismissed_events

    now_datetime = get_now_datetime()

    g_logger.debug("Dismissed event " + event_key_str + " " + str(parsed_event['end_date']) + " " + str(now_datetime))

    if (now_datetime > parsed_event['end_date']):
        # The event has ended
        g_logger.debug("Event end date has passed - clear_dismissed_events_that_have_ended")
        g_logger.debug("Dismissed event end date" + str(parsed_event['end_date']))

    elif has_event_changed(g_logger, parsed_event):
        # The event has changed, we will let the system re-parse the event as new
        g_logger.info("event changed - clear_dismissed_events_that_have_ended")

    else:
        # No need to remove the evnet
        return(False)
    
    # Need to remove the evnet
    return(True)

def clear_dismissed_events_that_have_ended():

    g_dismissed_events.remove_events_based_on_condition(condition_function_for_removing_dismissed_events)

    return

def load_config():
    global g_google_accounts
    global g_log_level
    global g_refresh_frequency

    with open("gCalNotifier.json") as f:
        l_config = json.load(f)

    g_google_accounts = l_config.get("google accounts")
    if (not g_google_accounts):
        print("No \'google accounts\' defined in the config file")
        sys.exit()

    for google_account in g_google_accounts:
        account_name = google_account.get("account name")
        if (not account_name):
            print ("No \'account name\' defined for a google account entry")
            sys.exit()
 
    g_log_level = l_config.get("log level")
    if (not g_log_level):
        g_log_level = logging.INFO

    g_refresh_frequency = l_config.get("refresh frequency")
    if (not g_refresh_frequency):
        g_refresh_frequency = 30

def prep_google_accounts_and_calendars():
    global g_google_accounts

    for google_account in g_google_accounts:
        get_calendar_list_for_account(g_logger, google_account)

class MDIWindow(QMainWindow):
    c_num_of_displayed_events = 0
    count = 0

    def present_relevant_events_in_sub_windows(self):
        global g_logger
        global g_refresh_frequency

        g_logger.debug("Presenting relevant events")

        present_relevant_events()

        if ((self.c_num_of_displayed_events > 0) and self.isMinimized()):
            # There is now at least one event, and the MDI is minimized - restore the window
            g_logger.info("Before showNormal")
            self.showNormal()
            g_logger.info("After showNormal")

        self.timer.start(int(g_refresh_frequency/2) * 1000)

    def update_mdi_title(self):
        self.setWindowTitle("[" + str(self.c_num_of_displayed_events) + "] gCalNotifier")

    def __init__(self):
        super().__init__()
 
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        bar = self.menuBar()
 
        file = bar.addMenu("File")
        file.addAction("Reset")
        file.addAction("New")
        file.addAction("Cascade")
        file.addAction("Tiled")
        file.triggered.connect(self.WindowTrig)
        self.update_mdi_title()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.present_relevant_events_in_sub_windows) 

    def add_event_to_display_cb(self):
        global g_logger

        g_logger.debug("add_event_to_display_cb start")

        self.c_num_of_displayed_events = self.c_num_of_displayed_events + 1

        g_logger.debug("add_event_to_display_cb update_mdi_title")
        self.update_mdi_title()

        g_logger.debug("add_event_to_display_cb end")

    def remove_event_from_display_cb(self):
        global g_logger

        g_logger.debug("remove_event_from_display_cb start")

        self.c_num_of_displayed_events = self.c_num_of_displayed_events - 1

        g_logger.debug("remove_event_from_display_cb update_mdi_title")
        self.update_mdi_title()

        if (self.c_num_of_displayed_events == 0):
            # No events to show
            g_logger.debug("remove_event_from_display_cb showMinimized")

            self.showMinimized()

        g_logger.debug("remove_event_from_display_cb end")

    def reset_all_events(self):
        global g_events_logger

        g_events_logger.info("Reseting the app")

    def showEvent(self, event):
        # This method will be called when the main MDI window is shown
        super().showEvent(event)  # Call the base class showEvent first
        self.present_relevant_events_in_sub_windows()

    def WindowTrig(self, p):
        if p.text() == "Reset":
            self.reset_all_events()

        elif p.text() == "New":
            MDIWindow.count = MDIWindow.count + 1
            sub = QMdiSubWindow()
            sub.setWidget(QTextEdit())
            sub.setWindowTitle("Sub Window" + str(MDIWindow.count))
            self.mdi.addSubWindow(sub)
            sub.show()
 
        elif p.text() == "Cascade":
            self.mdi.cascadeSubWindows()
 
        elif p.text() == "Tiled":
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
        target = get_events_to_display_main_loop,
        daemon=True)

    main_loop_thread.start()
    
# Main
if __name__ == "__main__":
    load_config()

    app = QApplication(sys.argv)
    g_mdi_window = MDIWindow()

    init_global_objects()

    prep_google_accounts_and_calendars()

    # Start a thread to look for events to display
    start_getting_events_to_display_main_loop_thread()

    app.setWindowIcon(QtGui.QIcon('icons8-calendar-64.png'))

    # Set the MDI window size to be a little more than the event window size
    g_mdi_window.setFixedWidth(730 + 100)
    g_mdi_window.setFixedHeight(650 + 100)

    g_mdi_window.show()

    # Show the window on the main monitor
    monitor = QDesktopWidget().screenGeometry(0)
    g_mdi_window.move(monitor.left(), monitor.top())

    app.exec_()