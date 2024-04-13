from PyQt5.QtWidgets import (
    QDesktopWidget, QWidget
)

from PyQt5 import (
    QtCore, QtGui
)

from gCalNotifier_ui import Ui_w_event

import validators

import datetime

import webbrowser

import re

from tzlocal import get_localzone

from json_utils import nice_json

from datetime_utils import get_now_datetime

# Exit reasons from the dialog
EXIT_REASON_NONE = 0
EXIT_REASON_DISMISS = 1
EXIT_REASON_SNOOZE = 2
EXIT_REASON_CHANGED = 3
EXIT_EVENT_ENDED_AND_NEED_TO_CLOSE_WINDOW = 4

# The notification window
class EventWindow(QWidget, Ui_w_event):
    c_snooze_buttons = {}
    c_parsed_event = {}
    c_event_key_str = ""
    c_is_first_display_of_window = False
    c_hidden_all_snooze_before_buttons = False
    c_updated_label_post_start = False
    c_updated_label_post_end = False
    c_video_link = ""
    c_window_closed = False
    c_win_exit_reason = EXIT_REASON_NONE
    c_snooze_time_in_minutes = 0

    def __init__(self, globals, parent=None):
        self.globals = globals

        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
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
        super().closeEvent(event)  # Call the base class closeEvent first

        if (self.c_win_exit_reason == EXIT_REASON_NONE):
            self.c_snooze_time_in_minutes = 0
            self.c_window_closed = True

            self.handle_window_exit()
        
    # Identify the video meeting softwate via its URL
    def identify_video_meeting_in_url(self, win_label, url, text_to_append_if_identified, text_if_not_identified):
        identified_as_a_video_meeting = True

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
        elif ("gather.town" in url):
            label_text = "Gather Link"    
        else:
            label_text = text_if_not_identified
            identified_as_a_video_meeting = False

        if (identified_as_a_video_meeting):
            # Add the text_to_append
            label_text = label_text + " from " + text_to_append_if_identified

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

        parsed_event['event_window'] = self

        self.setWindowTitle(parsed_event['event_name'])

        self.l_account.setText(parsed_event['cal name'] + " calendar in " + parsed_event['google_account'])

        self.l_event_name.setText(parsed_event['event_name'])

        self.globals.logger.debug("Notified for " + parsed_event['google_account'] + ": " + parsed_event['event_name'])

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
                    "location",
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
                "description",
                "Video Link")

            self.c_video_link = parsed_event['video_link']

        # Hide the missing video message - in the next section we will decide whether to show it
        is_hide_missing_video = True

        self.need_to_record_meeting = parsed_event.get('need_to_record_meeting', False)
        if (self.need_to_record_meeting):
            is_hide_missing_video = False

            self.pb_open_video_and_snooze.setText("and Snooze for 1m")
            self.l_missing_video.setText("Remember to record!!!")

        elif (self.c_video_link == ""):
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
        now_datetime = get_now_datetime()

        if (self.c_win_exit_reason == EXIT_REASON_NONE):
            self.globals.events_logger.info("Event windows was closed by user - not snoozed or dismissed, for event: " + self.c_parsed_event['event_name'])

        elif (self.c_win_exit_reason == EXIT_REASON_CHANGED):
            self.globals.events_logger.info("Event windows was closed because there was a change in the event, for event: " + self.c_parsed_event['event_name'])

        elif (self.c_win_exit_reason == EXIT_REASON_DISMISS):
            self.globals.events_logger.info("Event dismissed by user, for event: " + self.c_parsed_event['event_name'])

            if (now_datetime < self.c_parsed_event['end_date']):
                self.globals.events_to_dismiss.add_event(self.c_event_key_str, self.c_parsed_event)

        elif (self.c_win_exit_reason == EXIT_REASON_SNOOZE):
            self.globals.logger.debug("Snooze")
            if (self.c_snooze_time_in_minutes <= 0):
                delta_diff = datetime.timedelta(minutes=abs(self.c_snooze_time_in_minutes))
                self.c_parsed_event['event_wakeup_time'] = self.c_parsed_event['start_date'] - delta_diff
            else:
                delta_diff = datetime.timedelta(minutes=self.c_snooze_time_in_minutes)
                self.c_parsed_event['event_wakeup_time'] = now_datetime + delta_diff

            self.globals.events_logger.info("Event snoozed by user, for event: " + self.c_parsed_event['event_name'] + " until " + str(self.c_parsed_event['event_wakeup_time']))
                
            self.globals.events_to_snooze.add_event(self.c_event_key_str, self.c_parsed_event)

        elif (self.c_win_exit_reason == EXIT_EVENT_ENDED_AND_NEED_TO_CLOSE_WINDOW):
            self.globals.events_logger.info("Event windows was closed because the event has ended and it is set to automatically close at end, for event: " + self.c_parsed_event['event_name'])

        else:
            self.globals.events_logger.error("Event windows was closed without a reason, for event: " + self.c_parsed_event['event_name'])

        # Remove the event from the presented events
        self.globals.displayed_events.remove_event(self.c_event_key_str)

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
        if (self.c_window_closed):
            self.close()

            return

        # Let's first check that the event was not deleted
        if (self.c_parsed_event['deleted'] or self.c_parsed_event['changed']):
            # The event has changed, closing the window to refresh the event
            self.globals.logger.debug("event deleted or changed - update_controls_based_on_event_time")
            self.c_win_exit_reason = EXIT_REASON_CHANGED

            self.handle_window_exit()
            
            return()

        now_datetime = get_now_datetime()

        if (not self.c_updated_label_post_end and (self.c_parsed_event['end_date'] <= now_datetime)):
            # Event has ended

            if self.c_parsed_event['close_event_window_when_event_has_ended']:
                # We need to close the window automatically when the ecent ends
                self.c_win_exit_reason = EXIT_EVENT_ENDED_AND_NEED_TO_CLOSE_WINDOW

                self.handle_window_exit()
                
                return

            # No need to close the window - just change the label and no need to trigger the event anymore
            self.l_event_end.setText('Event ended at ' + str(self.c_parsed_event['end_time_in_loacal_tz']))
            self.c_updated_label_post_end = True

        if (self.c_is_first_display_of_window):
            l_changes_should_be_reflected = True
            self.c_is_first_display_of_window = False
        else:
            l_changes_should_be_reflected = False

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

        if (l_changes_should_be_reflected):
            # There are changes that should be reflected - bring the window to the front
            self.activateWindow()
            self.raise_()

            # Show the window on the main monitor
            monitor = QDesktopWidget().screenGeometry(0)
            self.move(monitor.left(), monitor.top())

        if (self.c_updated_label_post_end == False):
        # Not all controls that could have changed have already changed
            # Set timer to wake up in half a minute
            self.timer.start(30 * 1000)

    def open_video(self):
        webbrowser.open(self.c_video_link)

    def open_video_and_snooze(self):
        self.open_video()

        self.c_win_exit_reason = EXIT_REASON_SNOOZE

        if (self.need_to_record_meeting):
            self.c_snooze_time_in_minutes = 1
        else:
            self.c_snooze_time_in_minutes = 5
    
        self.handle_window_exit()

    def open_video_and_dismiss(self):
        self.open_video()

        self.c_win_exit_reason = EXIT_REASON_DISMISS

        self.handle_window_exit()
