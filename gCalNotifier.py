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

from EventWindow import EventWindow

from event_utils import (
    has_event_changed,
    parse_event,
    NO_POPUP_REMINDER
)

from events_collection import Events_Collection

def init_global_objects():
    global g_events_to_present
    global g_dismissed_events
    global g_snoozed_events
    global g_displayed_events
    global g_logger
    global g_log_level
    global g_mdi_window
    global g_events_logger

    g_logger = init_logging("gCalNotifier", "Main", g_log_level, LOG_LEVEL_INFO)
    g_events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)

    g_events_to_present = Events_Collection(g_logger, "g_events_to_present")
    g_dismissed_events = Events_Collection(g_logger, "g_dismissed_events")
    g_snoozed_events = Events_Collection(g_logger, "g_snoozed_events")
    g_displayed_events = Events_Collection(g_logger, "g_displayed_events", g_mdi_window.add_event_to_display_cb, g_mdi_window.remove_event_from_display_cb)

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

        need_to_notify = parse_event(g_logger, event, parsed_event)
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

def show_window_in_mdi(event_key_str, parsed_event):
    global g_logger
    global g_mdi_window
    global g_events_logger
    global g_dismissed_events
    global g_snoozed_events
    global g_displayed_events

    event_win = EventWindow(g_logger, g_events_logger, g_dismissed_events, g_snoozed_events, g_displayed_events, g_mdi_window)

    event_win.init_window_from_parsed_event(event_key_str, parsed_event)
    event_win.setFixedWidth(730)
    event_win.setFixedHeight(650)

    sub_win = QMdiSubWindow()
    sub_win.setWidget(event_win)
    g_mdi_window.mdi.addSubWindow(sub_win)
    sub_win.show()

    g_events_logger.info("Displaying event:" + parsed_event['event_name'])

    g_mdi_window.raise_()
    g_mdi_window.activateWindow()

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