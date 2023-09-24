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

from google_calendar_utilities import (
    get_calendar_list_for_account,
    get_events_from_google_cal_with_try,
    ConnectivityIssue
)

import threading
from multiprocessing import Process, Pipe

import json
import traceback

import re

import webbrowser

from deepdiff import DeepDiff

# Exit reasons from the dialog
EXIT_REASON_NONE = 0
EXIT_REASON_DISMISS = 1
EXIT_REASON_SNOOZE = 2
EXIT_REASON_CHANGED = 3

def init_global_objects():
    global g_events_to_present
    global g_dismissed_events
    global g_snoozed_events
    global g_displayed_events
    global g_logger
    global g_log_level
    global g_mdi_window

    g_events_to_present = Events_Collection()
    g_dismissed_events = Events_Collection()
    g_snoozed_events = Events_Collection()
    g_displayed_events = Events_Collection(g_mdi_window.add_event_to_display_cb, g_mdi_window.remove_event_from_display_cb)

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
            g_logger,
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
    def __init__(self, add_cb = None, remove_cb = None):
        self.c_events = {}
        self.c_lock = threading.Lock()
        self.c_add_cb = add_cb
        self.c_remove_cb = remove_cb

    def is_event_in(self, event_key_str):
        with self.c_lock:
            return(event_key_str in self.c_events)
        

    def add_event_safe(self, event_key_str, parsed_event):
        self.c_events[event_key_str] = parsed_event

        if (self.c_add_cb):
            self.c_add_cb()
        
    def add_event(self, event_key_str, parsed_event):
        with self.c_lock:
            self.add_event_safe(event_key_str, parsed_event)

    def remove_event_safe(self, event_key_str):
        del self.c_events[event_key_str]

        if (self.c_remove_cb):
            self.c_remove_cb()

    def remove_event(self, event_key_str):
        with self.c_lock:
            self.remove_event_safe(event_key_str)

    def lock(self):
        self.c_lock.acquire()

    def unlock(self):
        self.c_lock.release()

    def items(self):
        return(self.c_events.items())

    def pop(self):
        with self.c_lock:
            if (len(self.c_events) > 0):
                event_key_str = next(iter(self.c_events))
                parsed_event = self.c_events[event_key_str]
                self.remove_event_safe(event_key_str)
                return(event_key_str, parsed_event)
            else:
                # Empty collection
                return(None, None)

    def remove_events_based_on_condition(self, condition_function):
            events_to_delete = []

            with self.c_lock:
                for event_key_str, parsed_event in self.c_events.items():
                    if (condition_function(event_key_str, parsed_event)):
                        # The condition was met, need remove the item
                        events_to_delete.append(event_key_str)

                # Delete the events that were collected to be deleted
                while (len(events_to_delete) > 0):
                    event_key_str = events_to_delete.pop()
                    self.remove_event_safe(event_key_str)
    
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
    c_win_exit_reason = EXIT_REASON_NONE
    c_snooze_time_in_minutes = 0

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

    def showEvent(self, event):
        # This method will be called when the window is shown
        super().showEvent(event)  # Call the base class showEvent first

        # Make sure not button is clicked by mistake due to keyboard shortcuts
        self.pb_hidden_button.setFocus()
        self.pb_hidden_button.resize(0,0)

    def closeEvent(self, event):
        global g_logger

        super().closeEvent(event)  # Call the base class closeEvent first

        if (self.c_win_exit_reason == EXIT_REASON_NONE):
            self.c_snooze_time_in_minutes = 0
            self.c_window_closed = True

            self.handle_window_exit()
        
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
        self.c_win_exit_reason = EXIT_REASON_NONE
        self.c_snooze_time_in_minutes = 0

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

    def handle_window_exit(self):
        global g_logger
        global g_dismissed_events
        global g_snoozed_events
        global g_displayed_events

        if isinstance(self.parent(), QMdiSubWindow):
            # MDI mode

            now_datetime = get_now_datetime()

            if (self.c_win_exit_reason == EXIT_REASON_NONE):
                g_logger.debug("Cancel")

            elif (self.c_win_exit_reason == EXIT_REASON_CHANGED):
                g_logger.debug("Event changed")

            elif (self.c_win_exit_reason == EXIT_REASON_DISMISS):
                g_logger.debug("Dismiss")

                if (now_datetime < self.c_parsed_event['end_date']):
                    g_dismissed_events.add_event(self.c_event_key_str, self.c_parsed_event)

            elif (self.c_win_exit_reason == EXIT_REASON_SNOOZE):
                g_logger.debug("Snooze")
                if (self.c_snooze_time_in_minutes <= 0):
                    delta_diff = datetime.timedelta(minutes=abs(self.c_snooze_time_in_minutes))
                    self.c_parsed_event['event_wakeup_time'] = self.c_parsed_event['start_date'] - delta_diff
                else:
                    delta_diff = datetime.timedelta(minutes=self.c_snooze_time_in_minutes)
                    self.c_parsed_event['event_wakeup_time'] = now_datetime + delta_diff

                g_logger.debug("Snooze until " + str(self.c_parsed_event['event_wakeup_time']))
                    
                g_snoozed_events.add_event(self.c_event_key_str, self.c_parsed_event)

            else:
                g_logger.error("No exit reason")

            # Remove the event from the presented events
            g_displayed_events.remove_event(self.c_event_key_str)

            self.parent().close()

        else:
            g_logger.info("Are we supposed to get here?")
            self.close()

    def clickedDismiss(self):
        self.c_win_exit_reason = EXIT_REASON_DISMISS
        self.c_snooze_time_in_minutes = 0
        self.c_window_closed = True

        self.handle_window_exit()

    def snooze_general(self, p_button):
        self.c_win_exit_reason = EXIT_REASON_SNOOZE

        if (p_button in self.c_snooze_buttons):
            self.c_snooze_time_in_minutes = self.c_snooze_buttons[p_button]
    
        self.handle_window_exit()

    def update_controls_based_on_event_time(self):
        global g_logger
        global g_mdi_window

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
                self.c_win_exit_reason = EXIT_REASON_CHANGED

                self.handle_window_exit()
                
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

            g_mdi_window.raise_()
            g_mdi_window.activateWindow()

        if (self.c_updated_label_post_end == False):
        # Not all controls that could have changed have already changed
            # Set timer to wake up in half a minute
            self.timer.start(30 * 1000)

    def open_video(self):
        webbrowser.open(self.c_video_link)

    def open_video_and_snooze(self):
        self.open_video()

        self.c_win_exit_reason = EXIT_REASON_SNOOZE

        self.c_snooze_time_in_minutes = 5
    
        self.handle_window_exit()

    def open_video_and_dismiss(self):
        self.open_video()

        self.c_win_exit_reason = EXIT_REASON_DISMISS

        self.handle_window_exit()

def show_window_in_mdi(event_key_str, parsed_event):
    global g_logger
    global g_mdi_window

    win = Window()

    win.init_window_from_parsed_event(event_key_str, parsed_event)
    win.setFixedWidth(730)
    win.setFixedHeight(650)

    sub = QMdiSubWindow()
    sub.setWidget(win)
    g_mdi_window.mdi.addSubWindow(sub)
    sub.show()

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

    if(has_event_changed(parsed_event)):
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

    elif has_event_changed(parsed_event):
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

        self.timer.start(int(g_refresh_frequency/2) * 1000)

    def update_mdi_title(self):
        self.setWindowTitle("[" + str(self.c_num_of_displayed_events) + "] gCalNotifier")

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
        self.update_mdi_title()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.present_relevant_events_in_sub_windows) 

    def add_event_to_display_cb(self):
        self.c_num_of_displayed_events = self.c_num_of_displayed_events + 1

        self.update_mdi_title()

        # For the case the MDI window was minimized
        self.showMaximized()

    def remove_event_from_display_cb(self):
        self.c_num_of_displayed_events = self.c_num_of_displayed_events - 1

        self.update_mdi_title()

        if (self.c_num_of_displayed_events == 0):
            # No events to show
            self.showMinimized()

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