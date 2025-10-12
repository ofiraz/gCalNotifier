from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QTextBrowser, QMessageBox, QMenu, QAction, QWidgetAction #, QDesktopWidget
from PyQt5 import (QtCore, QtGui)
from PyQt5.QtCore import Qt, QPoint

import subprocess
from datetime_utils import get_now_datetime
import datetime
from tzlocal import get_localzone
from json_utils import nice_json
import threading
import re

# Setting names
EVENT_SETTING_SHOW_OS_NOTIFICATION = "show os notification"

class EventDisplayDetails():
    def update_snooze_times_for_event(self):
        self.event_has_snooze_before_items = False
        
        parsed_event = self.parsed_event
        self.snooze_times_before = [ 
            ( -5, "-5m" ) ,
            ( -2, "-2m" ) ,
            ( -1, "-1m" ) ,
            ( 0, "0" )
        ]

        self.snooze_times_future = [ 
            ( 1, "1m" ) ,
            ( 5, "5m" ) ,
            ( 15, "15m" ) ,
            ( 30, "30m" ) ,
            ( 60, "1h" ) ,
            ( 120, "2h" ) ,
            ( 240, "4h" ) ,
            ( 480, "8h" )
        ]

        self.snooze_times_strings_for_combo_box = []
        self.snooze_times_in_minutes = []

        self.default_snooze = parsed_event.default_snooze
        if (self.default_snooze):
            # Add the default snooze as the first item
            self.snooze_times_strings_for_combo_box.append("Default " + self.default_snooze + " minutes")
            self.snooze_times_in_minutes.append(int(self.default_snooze))

        now_datetime = get_now_datetime()
        if (parsed_event.start_date > now_datetime):
            # Event start did not arrive yet - add all needed before snooze buttons
            time_to_event_start = parsed_event.start_date - now_datetime
            time_to_event_in_minutes = int(time_to_event_start.seconds / 60)

            for index in range(len(self.snooze_times_before)):
                snooze_time = self.snooze_times_before[index][0]

                if (abs(snooze_time) < time_to_event_in_minutes):
                    if  (self.event_has_snooze_before_items == False):
                        self.event_has_snooze_before_items = True
                        self.next_time_to_update_buttons = parsed_event.start_date + datetime.timedelta(minutes=snooze_time)

                    self.snooze_times_strings_for_combo_box.append(self.snooze_times_before[index][1])
                    self.snooze_times_in_minutes.append(snooze_time)
            
        for index in range(len(self.snooze_times_future)):
            self.snooze_times_strings_for_combo_box.append(self.snooze_times_future[index][1])
            self.snooze_times_in_minutes.append(self.snooze_times_future[index][0])

    def __init__(self, globals, parsed_event):
        self.globals = globals
        self.parsed_event = parsed_event

        indicate_issues_with_the_event = False

        self.need_to_record_meeting = parsed_event.need_to_record_meeting
        if (self.need_to_record_meeting):
            indicate_issues_with_the_event = True
            self.snooze_time_in_minutes_for_open_video_and_snooze = 1

        else:
            self.snooze_time_in_minutes_for_open_video_and_snooze = 5


        self.cal_and_account_label_text = parsed_event.cal_name + " calendar in " + parsed_event.google_account

        self.all_day_event = parsed_event.all_day_event

        self.start_time_label_text = 'Starting at ' + str(parsed_event.start_date.astimezone(get_localzone()))
        self.end_time_label_text = 'Ending at ' + str(parsed_event.end_date.astimezone(get_localzone()))

        self.gcal_event_link_label_text = "<a href=\"" + parsed_event.html_link + "\">Link to event in GCal</a>"
        self.gcal_event_link_label_tooltip = parsed_event.html_link
   

        self.location_label_exits = parsed_event.display_location
        self.location_link_label_exists = parsed_event.display_location_as_url
        if (self.location_label_exits):
                self.location_label_text = 'Location: ' + parsed_event.event_location

        if (self.location_link_label_exists):
            self.location_link_label_tooltip = parsed_event.event_location
            self.location_link_label_text = "Event location (URL)"

        self.update_snooze_times_for_event()

        self.video_label_exists = False
        self.mulitple_attendees_and_video_link_missing = False
        self.consider_standing_up = False
        self.separate_video_link_from_description = parsed_event.separate_video_link_from_description
        self.separate_video_link_from_location = parsed_event.separate_video_link_from_location
        self.video_link = parsed_event.video_link
        if (self.video_link != "No Video"):
            self.video_label_exists = True
            
            self.video_link_label_text = "<a href=\"" + parsed_event.video_link + "\">Video URL</a>"
            self.video_link_label_tooltip = parsed_event.video_link

            if (self.need_to_record_meeting):
                self.open_video_and_snooze_text = "Open video link and snooze for 1 min"
            else:
                self.open_video_and_snooze_text = "Open video link and snooze for 5 min"

            if (self.separate_video_link_from_description):
                # The description has a separate video link, present it
                self.video_link_from_description_label_text = "<a href=\"" + parsed_event.video_link + "\">Video URL from description</a>"
                self.video_link_from_description_label_tooltip = parsed_event.video_link_in_description
                
            if (self.separate_video_link_from_location):
                # The description has a separate video link, present it
                self.video_link_from_location_label_text = "<a href=\"" + parsed_event.video_link + "\">Video URL from location</a>"
                self.video_link_from_location_label_tooltip = parsed_event.video_link_in_location

        else:
            # No video link   
            if (parsed_event.num_of_attendees > 1):
            # Num of attendees > 1 and no video link
                # We expect a video link as there are multiple attendees for this meeting

                # Let's check if we have our special sign
                is_no_video_ok = re.search( # Move to db_settings
                    'NO_VIDEO_OK',
                    parsed_event.description)

                if (not is_no_video_ok):
                    # We need to show the missing video message
                    self.mulitple_attendees_and_video_link_missing = True
                    indicate_issues_with_the_event = True

        self.event_name = parsed_event.event_name
        self.event_name_to_display = self.event_name

        self.is_tentative = parsed_event.is_tentative
        if (parsed_event.is_tentative):
            self.event_name_to_display = "Tentative - " + self.event_name_to_display

        if indicate_issues_with_the_event:
            self.event_name_to_display = "*** " + self.event_name_to_display

        # We want to suggest standing up, if the coming event is with other people
        self.consider_standing_up = parsed_event.num_of_attendees > 1

        self.send_os_notification = self.globals.per_event_setting_db.get_event_setting(
            self.event_name,
            EVENT_SETTING_SHOW_OS_NOTIFICATION,
            True)

WAKEUP_INTERVAL = 15

class DynamicWidgetDetails():
    def __init__(self, layout, widget):
        self.layout = layout
        self.widget = widget

ACTION_ADD = 1
ACTION_UPDATE = 2
ACTION_REMOVE = 3
ACTION_TIMER = 4

BOUNCE_ICON_ACTIONS = {ACTION_ADD, ACTION_UPDATE, ACTION_TIMER}
UPDATE_ICON_ACTIONS = {ACTION_ADD, ACTION_UPDATE, ACTION_REMOVE}

MINUTES_BETWEEN_BOUNCE_ON_TIMER = 1

class MultipleEventsTable(QWidget):
    def add_dynamic_layout(self, layout):
        self.main_layout.addLayout(layout)
        self.dynamic_layouts.append(layout)

    def __init__(self, globals, parsed_event):
        super().__init__()

        self.globals = globals

        self.events_lock = threading.Lock()

        # Create QTableWidget with 1 row and 2 columns
        self.table_widget = QTableWidget(0, 2)
        
        self.table_widget.setFixedHeight(310)

        self.parsed_events = []
        self.events_display_details = []

        self.num_of_notification_events = 0
        self.num_of_no_notification_events = 0

        self.last_icon_bounce_time = datetime.datetime.now()

        # Make the QTableWidget read-only
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set the selection behavior to select entire rows
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        # Prevent muliple selection
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)

        # Hide the column headers (horizontal headers)
        self.table_widget.horizontalHeader().setVisible(False)

        # Hide the row headers (vertical headers)
        self.table_widget.verticalHeader().setVisible(False)

        # Enable custom context menu
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(self.table_widget)

        self.dynamic_layouts = []

        self.warnings_layout = QVBoxLayout()
        self.add_dynamic_layout(self.warnings_layout)

        # Add the default snooze button
        self.default_snooze_button = self.add_button(
            self.main_layout,
            "Default Snooze", # Will change later on per the specific event
            self.on_snooze_general,
            pass_button_to_cb=True,
            size_button_according_to_text=False)

        self.open_video_and_snooze_layout = QVBoxLayout()
        self.add_dynamic_layout(self.open_video_and_snooze_layout)

        # Crate the horizontal box layout for the rest of the snooze buttons
        self.additional_snooze_buttons_layout = QHBoxLayout()
        self.add_dynamic_layout(self.additional_snooze_buttons_layout)

        # Add the dismiss button
        self.add_button(
            self.main_layout,
            "Dismiss",
            self.on_dismiss_event_pressed,
            size_button_according_to_text=False)
        
        self.account_label = self.add_label(
            self.main_layout,
            "Initial text - to replaced with the initial event text")

        self.all_day_event_layout = QVBoxLayout()
        self.add_dynamic_layout(self.all_day_event_layout)

        self.start_time_label = self.add_label(
            self.main_layout,
            "Initial text - to replaced with the initial event text")
        
        self.end_time_label = self.add_label(
            self.main_layout,
            "Initial text - to replaced with the initial event text")
        
        self.potential_links_layout = QVBoxLayout()
        self.add_dynamic_layout(self.potential_links_layout)

        self.event_link_label = self.add_link_label(
            self.main_layout,
            "Initial text - to replaced with the initial event text",
            "Initial text - to replaced with the initial event text")
        
        self.add_empty_tab_widget(self.main_layout)
        
        # Add the new event
        self.add_event(parsed_event)

        # Set the event to identify a new row selection
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display_on_timer)

        self.setWindowTitle("gCalNofitifier - Starting...")

        # Set timer to wake up in a minute
        self.timer.start(WAKEUP_INTERVAL * 1000)

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            self.add_event_details_widgets(selected_row)

    def get_time_diff_in_string(self, time_diff):
        total_minutes = time_diff.total_seconds() / 60
        if (total_minutes <= 60):
            return(str(int(total_minutes)) + " minutes")
        
        total_hours = total_minutes / 60
        if (total_hours <= 24):
            return(str(int(total_hours)) + " hours")
        
        total_days = total_hours / 24
        return(str(int(total_days)) + " days")

    def get_time_until_event_start(self, parsed_event):
        time_string = ""

        now_datetime = get_now_datetime()

        if (parsed_event.start_date > now_datetime):
            # Event start did not arrive yet
            time_to_event_start = parsed_event.start_date - now_datetime

            time_string = self.get_time_diff_in_string(time_to_event_start) + " until start"

        elif (parsed_event.end_date <= now_datetime):
            # Event has ended
            # time_since_event_ended = now_datetime - parsed_event.end_date
            
            time_string = "Ended" # self.get_time_diff_in_string(time_since_event_ended) + " since event ended"

        else:
            # Event started but did not end yet
            # time_since_event_started = now_datetime - parsed_event.start_date
           
            time_string = "Started" # self.get_time_diff_in_string(time_since_event_started) + " since event started"

        return(time_string)

    def add_event(self, parsed_event):
        with self.events_lock:
            row_count = self.table_widget.rowCount()

            # Insert a new row at the end of the table
            self.table_widget.insertRow(row_count)

            event_display_details = EventDisplayDetails(self.globals, parsed_event)

            self.table_widget.setItem(row_count, 0, QTableWidgetItem(event_display_details.event_name_to_display))
            self.table_widget.setItem(row_count, 1, QTableWidgetItem(self.get_time_until_event_start(parsed_event)))

            self.table_widget.resizeColumnToContents(0)
            self.table_widget.resizeColumnToContents(1)

            self.parsed_events.append(parsed_event)
            self.events_display_details.append(event_display_details)

            if (event_display_details.send_os_notification):
                self.globals.logger.debug("Added a notficagtion event")

                # We should have a notification due to this event
                self.num_of_notification_events += 1
            else:
                self.globals.logger.debug("Added a non notficagtion event")

                # This event does not require a notification
                self.num_of_no_notification_events += 1

            self.globals.logger.debug(f"witn notification {self.num_of_notification_events} without {self.num_of_no_notification_events}")

            if (row_count == 0):
                self.select_event(0)
                self.add_event_details_widgets(0)

            self.visibly_reflect_events(
                ACTION_ADD,
                event_display_details.send_os_notification,
                event_display_details.event_name_to_display)

    def select_event(self, row_number):
        self.table_widget.selectRow(row_number)

    def remove_event_safe(self, row):
        self.globals.displayed_events.remove_event(self.parsed_events[row].event_key_str)

        self.table_widget.removeRow(row)

        if (self.events_display_details[row].send_os_notification):
            self.globals.logger.debug("Removed a notficagtion event")
            # This event required a notification
            self.num_of_notification_events -= 1
        else:
            self.globals.logger.debug("Removed a no notficagtion event")
            # This event did not require a notification
            self.num_of_no_notification_events -= 1

        self.globals.logger.debug(f"witn notification {self.num_of_notification_events} without {self.num_of_no_notification_events}")

        del self.parsed_events[row]
        del self.events_display_details[row]

        self.visibly_reflect_events(ACTION_REMOVE)

        # Close the windows if there are no more events presneted
        if (self.table_widget.rowCount() == 0):
            self.close()

    def show_window(self):
        if (self.table_widget.rowCount() > 0):
            self.setFixedWidth(730)

            # Show the window on the main monitor
            #monitor = QDesktopWidget().screenGeometry(0)
            self.move(0,0)

            self.show()

            #self.globals.multiple_events_window.activateWindow()
            #self.globals.multiple_events_window.raise_()      

    def remove_event(self, row):
        with self.events_lock:
            self.delete_widgets_in_dynamic_layouts()

            self.remove_event_safe(row)

    def snooze_event(self, snooze_time_in_minutes):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            parsed_event = self.parsed_events[selected_row]

            self.globals.logger.debug("Snooze")

            now_datetime = get_now_datetime()

            if (snooze_time_in_minutes <= 0):
                delta_diff = datetime.timedelta(minutes=abs(snooze_time_in_minutes))
                parsed_event.event_wakeup_time = parsed_event.start_date - delta_diff
            else:
                delta_diff = datetime.timedelta(minutes=snooze_time_in_minutes)
                parsed_event.event_wakeup_time = now_datetime + delta_diff

            self.globals.events_logger.debug("Event snoozed by user, for event: " + parsed_event.event_name + " until " + str(parsed_event.event_wakeup_time))
                
            self.globals.events_to_snooze.add_event(self.parsed_events[selected_row].event_key_str, parsed_event)

            parsed_event.automatically_snoozed_dismissed = False

            self.remove_event(selected_row)

    def ask_for_confirmation_for_dismiss(self, event_name):
        # Create a QMessageBox
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            "Are you sure you want to dismiss '" + event_name + "'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        # Handle the user's response
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def on_dismiss_event_pressed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            parsed_event = self.parsed_events[selected_row]

            dismiss_confirmed = self.ask_for_confirmation_for_dismiss(parsed_event.event_name)

            if (dismiss_confirmed):
                parsed_event.automatically_snoozed_dismissed = False

                now_datetime = get_now_datetime()

                if (now_datetime < parsed_event.end_date):
                    self.globals.events_to_dismiss.add_event(parsed_event.event_key_str, parsed_event)

                self.remove_event(selected_row)

    def update_table_cell(self, row, column, new_value):
        item = self.table_widget.item(row, column)
        if item:
            # Change the text of the item
            item.setText(new_value)

    def update_display_on_timer(self):
        num_of_deleted_rows = 0

        now_datetime = get_now_datetime()

        with self.events_lock:
            for row in range(self.table_widget.rowCount()):
                index = row - num_of_deleted_rows

                # Get the new time until the event, and update the row
                time_until_event_start = self.get_time_until_event_start(self.parsed_events[index])
                self.update_table_cell(index, 1, time_until_event_start)

                if (self.parsed_events[index].deleted or self.parsed_events[index].changed
                    or ((now_datetime > self.parsed_events[index].end_date) and self.parsed_events[index].close_event_window_when_event_has_ended)):
                    self.remove_event_safe(index)
                    num_of_deleted_rows = num_of_deleted_rows + 1

            # Update the 2nd column width
            self.table_widget.resizeColumnToContents(1)

            # Update the displayed information for the selected row
            selected_row = self.table_widget.currentRow()

            if selected_row != -1:  # -1 means no row is selected
                self.update_event_details_widgets_on_timer(selected_row)

            self.visibly_reflect_events(ACTION_TIMER)

            # Sleep for another minute
            self.timer.start(WAKEUP_INTERVAL * 1000)

    def add_label(self, layout, label_text, highlight = False):
        new_label = QLabel(label_text)  # Create a new QLabel
        new_label.setFixedHeight(16)

        if (highlight):
            new_label.setAutoFillBackground(True) # This is important!!
            color  = QtGui.QColor(233, 10, 150)
            alpha  = 140
            values = "{r}, {g}, {b}, {a}".format(r = color.red(),
                                                g = color.green(),
                                                b = color.blue(),
                                                a = alpha
                                                )
            new_label.setStyleSheet("QLabel { background-color: rgba("+values+"); }")

        layout.addWidget(new_label)  # Add the new tab widget to the layout

        return new_label

    def update_label(self, label, new_label_text, new_tooltip_text=None):
        label.setText(new_label_text)

        if (new_tooltip_text):
            label.setToolTip(new_tooltip_text)

    def add_link_label(self, layout, label_text, tooltip_text):
        new_label = QLabel(label_text)  # Create a new QLabel
        new_label.setFixedHeight(16)
        new_label.setToolTip(tooltip_text)

        # Enable automatic opening of external links
        new_label.setOpenExternalLinks(True)

        layout.addWidget(new_label)  # Add the new tab widget to the layout

        return new_label

    def update_button(self, button, new_button_text, additional_data):
        button.setText(new_button_text)

        button.setProperty("customData", additional_data)
        
    def add_button(
            self, 
            layout, 
            button_text, 
            button_callback, 
            additional_data = None, 
            pass_button_to_cb = False, 
            size_button_according_to_text = True):
        new_button = QPushButton(button_text)  # Create a new button

        if (additional_data):
            new_button.setProperty("customData", additional_data)

        #new_button.setFixedWidth(button_width)
        new_button.setFixedHeight(32)
        #new_button.adjustSize()

        if (size_button_according_to_text):
            # Calculate the width needed to fit the text
            font_metrics = new_button.fontMetrics()
            text_width = font_metrics.width(new_button.text())

            # Add some padding to make it look better
            padding = 30
            new_button.setFixedWidth(text_width + padding)

        if (pass_button_to_cb):
            new_button.clicked.connect(lambda: button_callback(new_button))

        else:
            new_button.clicked.connect(button_callback)

        layout.addWidget(new_button)  # Add the new tab widget to the layout

        return new_button

    def open_video(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            # Decide on the Chrome profile to use
            if (self.parsed_events[selected_row].google_account == 'ofiraz@gmail.com'):
                profile_name = 'Profile 1'
            else:
                profile_name = 'Profile 9'

            subprocess.Popen(
                [
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
                    self.video_link,
                    '--profile-directory=' + profile_name
                ]
            ) 

    def open_video_and_snooze(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            self.open_video()

            parsed_event = self.parsed_events[selected_row]
            event_display_details = self.events_display_details[selected_row]

            now_datetime = get_now_datetime()

            delta_diff = datetime.timedelta(minutes=event_display_details.snooze_time_in_minutes_for_open_video_and_snooze)
            parsed_event.event_wakeup_time = now_datetime + delta_diff

            self.globals.events_logger.debug("Event snoozed by user, for event: " + parsed_event.event_name + " until " + str(parsed_event.event_wakeup_time))

            self.globals.events_to_snooze.add_event(self.parsed_events[selected_row].event_key_str, parsed_event)

            self.remove_event(selected_row)

    def add_empty_tab_widget(self, layout):
        self.tab_widget = QTabWidget()  # Create a new tab widget
        self.tab_widget.setFixedHeight(310)

        # Create a tab for the description
        self.description_tab = QTextBrowser()
        self.description_tab.setOpenExternalLinks(True)

        # Create the tab for the raw event
        self.raw_event_tab = QTextBrowser()
        self.raw_event_tab.setOpenExternalLinks(True)

        # Create the tab for the attachments
        self.attachments_tab = QTextBrowser()
        self.attachments_tab.setOpenExternalLinks(True)

        layout.addWidget(self.tab_widget)  # Add the new tab widget to the layout
            
    def build_html_for_the_attachments_tab(self, parsed_event):
        html_text = ""

        if (len(parsed_event.attachments) == 0):
            html_text = "No attachments"
        else:
            for attachment in parsed_event.attachments:
                html_text = html_text + "<p><a href=\"" + attachment.file_url + "\">" + attachment.title +"</a></p>"

        return html_text

    def update_tab_widget(self, parsed_event):
        if (len(parsed_event.attachments) > 0):
            # There are attachments - add the tab and its content
            self.tab_widget.addTab(self.attachments_tab, "Attachments")
            self.attachments_tab.setHtml(self.build_html_for_the_attachments_tab(parsed_event))

        if (parsed_event.description != ""):
            # There is a description - add the tab and its content
            self.tab_widget.addTab(self.description_tab, "Description")
            self.description_tab.setHtml(parsed_event.description)

        # Add the raw event tab and its content
        self.tab_widget.addTab(self.raw_event_tab, "Raw Event")
        self.raw_event_tab.setText(nice_json(parsed_event.raw_event))

    def on_snooze_general(self, button):
        minutes_to_snooze = int(button.property("customData"))

        self.snooze_event(minutes_to_snooze)

    def add_snooze_buttons(self, event_display_details):
        event_display_details.update_snooze_times_for_event()

        # Update the default snooze button to with the correct text and snooze time
        button_text = event_display_details.snooze_times_strings_for_combo_box[0]
        button_minutes = event_display_details.snooze_times_in_minutes[0]
        self.update_button(
            self.default_snooze_button,
            button_text,
            str(button_minutes))
        
        for index in range(1, len(event_display_details.snooze_times_strings_for_combo_box)):
            button_text = event_display_details.snooze_times_strings_for_combo_box[index]
            button_minutes = event_display_details.snooze_times_in_minutes[index]
            self.add_button(
                self.additional_snooze_buttons_layout,
                button_text,
                self.on_snooze_general,
                additional_data=str(button_minutes),
                pass_button_to_cb=True)

    def update_snooze_buttons(self, event_display_details):
        if (event_display_details.event_has_snooze_before_items):
            now_datetime = get_now_datetime()
            if (now_datetime >= event_display_details.next_time_to_update_buttons):
                # Clear the current dynamic snooze buttons
                self.delete_widgets_in_layout(self.additional_snooze_buttons_layout)

                self.add_snooze_buttons(event_display_details)         

    def remove_all_tabs(self):
        tab_count = self.tab_widget.count()
        for index in range(tab_count - 1, -1, -1):
            self.tab_widget.removeTab(index)

    def add_event_details_widgets(self, row):
        # Clear the previous dynamic details presented
        self.delete_widgets_in_dynamic_layouts()

        self.remove_all_tabs()

        parsed_event = self.parsed_events[row]
        event_display_details = self.events_display_details[row]

        if (event_display_details.mulitple_attendees_and_video_link_missing):
            # We need to show the missing video message
            self.add_label(
                self.warnings_layout,
                "There are multiple attendees in this meeting, but there is no video link!!!", 
                highlight=True)

        if (event_display_details.consider_standing_up):
            # The event has more than one participant, suggest standing up
            self.add_label(
                self.warnings_layout,
                "There are multiple attendees in this meeting, stand up, if you are not already?", 
                highlight=True)

        if (event_display_details.need_to_record_meeting):
            self.add_label(
                self.warnings_layout,
                "Remember to record!!!", 
                highlight=True)

        self.add_snooze_buttons(event_display_details)

        self.video_link = event_display_details.video_link
        if (self.video_link != "No Video"):
            # There is a video link - add the needed buttons
            self.add_button(
                self.open_video_and_snooze_layout,
                event_display_details.open_video_and_snooze_text,
                self.open_video_and_snooze,
                size_button_according_to_text=False)

        self.update_label(
            self.account_label,
            event_display_details.cal_and_account_label_text)

        if event_display_details.all_day_event:
            self.add_label(
            self.all_day_event_layout,
                "An all day event")

        self.update_label(
            self.start_time_label,
            event_display_details.start_time_label_text)
        
        self.update_label(
            self.end_time_label,
            event_display_details.end_time_label_text)

        if (event_display_details.location_label_exits):
            self.add_label(
                self.potential_links_layout,
                event_display_details.location_label_text)
            
        elif (event_display_details.location_link_label_exists):
            self.add_link_label(
                self.potential_links_layout,
                event_display_details.location_link_label_text,
                event_display_details.location_link_label_tooltip)
    
        if (event_display_details.video_label_exists):
            self.add_link_label(
                self.potential_links_layout,
                event_display_details.video_link_label_text,
                event_display_details.video_link_label_tooltip)
            
        if (event_display_details.separate_video_link_from_description):
            self.add_link_label(
                self.potential_links_layout,
                event_display_details.video_link_from_description_label_text,
                event_display_details.video_link_from_description_label_tooltip)
    
        if (event_display_details.separate_video_link_from_location):
            self.add_link_label(
                self.potential_links_layout,
                event_display_details.video_link_from_location_label_text,
                event_display_details.video_link_from_location_label_tooltip)
            
        self.update_label(
            self.event_link_label,
            event_display_details.gcal_event_link_label_text,
            event_display_details.gcal_event_link_label_tooltip
        )

        self.update_tab_widget(parsed_event)

    def update_event_details_widgets_on_timer(self, row):
        event_display_details = self.events_display_details[row]

        self.update_snooze_buttons(event_display_details)

    def delete_widgets_in_layout(self, layout):
        # Remove all widgets in the layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()  # Delete widget
            else:
                del item  # Delete empty space or layout

    def delete_widgets_in_dynamic_layouts(self):
        for index in range(len(self.dynamic_layouts)):
            self.delete_widgets_in_layout(self.dynamic_layouts[index])

    def update_event(self, parsed_event):       
        with self.events_lock:
            # Find the modified event in the current list of events
            for row in range(self.table_widget.rowCount()):
                if (self.parsed_events[row].event_key_str == parsed_event.event_key_str):
                    # Found the event - update all of its fields
                    self.parsed_events[row] = parsed_event

                    event_display_details = EventDisplayDetails(self.globals, parsed_event)
                    self.events_display_details[row] = event_display_details

                    self.update_table_cell(row, 0, event_display_details.event_name_to_display)
                    self.update_table_cell(row, 1, self.get_time_until_event_start(parsed_event))

                    self.table_widget.resizeColumnToContents(0)
                    self.table_widget.resizeColumnToContents(1)

                    # Update the displayed information for the selected row
                    selected_row = self.table_widget.currentRow()

                    if (selected_row == row):  # -1 means no row is selected
                        self.add_event_details_widgets(row)

                    self.visibly_reflect_events(
                        ACTION_UPDATE,
                        event_display_details.send_os_notification,
                        event_display_details.event_name_to_display)

                    return

        # If we got here the event could not be found - could be a race condition in the case it was removed due to the change marking in the refresh event
        self.globals.logger.info("Couldnt find the event to change, handling it as new")
        self.add_event(parsed_event)

    def create_context_menu_item_for_toggle_on_off(self, event_name, item_name, current_value, menu):
        if (current_value == True):
            title_toggle_value = "off"
        else:
            title_toggle_value = "on"

        menu_item_label = "Turn " + title_toggle_value + " " + item_name
        toggle_action = QAction(menu_item_label, self)
        toggle_action.triggered.connect(lambda: self.toggle_option(item_name, not current_value, event_name))
        menu.addAction(toggle_action)

    def show_context_menu(self, pos: QPoint):
        item = self.table_widget.itemAt(pos)
        if item is not None:
            row = item.row()
            event_display_details = self.events_display_details[row]

            menu = QMenu(self)

            # Add a title
            title_label = QLabel(event_display_details.event_name)
            title_label.setStyleSheet("font-weight: bold; padding: 4px;")

            title_widget = QWidgetAction(self)
            title_widget.setDefaultWidget(title_label)

            menu.addAction(title_widget)
            menu.addSeparator()

            # Add an action for controlling the OS notifications for the event
            self.create_context_menu_item_for_toggle_on_off(
                event_display_details.event_name,
                EVENT_SETTING_SHOW_OS_NOTIFICATION,
                event_display_details.send_os_notification,
                menu)

            # action1 = QAction("Option 1", self)
            # action1.triggered.connect(lambda: self.handle_action(row, "Option 1"))
            # action1.setCheckable(True)
            # action1.setChecked(True)  # ✅ This adds the checkmark

            # action2 = QAction("Option 2", self)
            # action2.triggered.connect(lambda: self.handle_action(row, "Option 2"))

            # menu.addAction(action1)
            # menu.addAction(action2)

            menu.exec_(self.table_widget.viewport().mapToGlobal(pos))

    def toggle_option(self, option_name, toggle_on, event_name):
        self.globals.logger.debug(f"Turn {option_name} to {toggle_on} for {event_name}")

        self.globals.per_event_setting_db.set_event_setting(
            event_name,
            option_name,
            toggle_on)
        
    def visibly_reflect_events(self, action, pop_up_notification = False, event_text = ""):
        # Decide a continuous bounce of the icon is needed
        if ((action in BOUNCE_ICON_ACTIONS) and  (self.num_of_notification_events > 0)):
            should_bounce = True

            # Bounce only every MINUTES_BETWEEN_BOUNCE_ON_TIMER minutes if the event is the timer event
            if (action == ACTION_TIMER):
                now = datetime.datetime.now()
                diff = now - self.last_icon_bounce_time

                if (diff < datetime.timedelta(minutes=MINUTES_BETWEEN_BOUNCE_ON_TIMER)):
                    should_bounce = False

            if should_bounce:
                self.globals.icon_manager.continuous_dock_icon_bounce()
                self.last_icon_bounce_time = datetime.datetime.now()

        # Update the icon 
        if (action in UPDATE_ICON_ACTIONS):
            self.globals.icon_manager.set_icon_with_events(
                self.num_of_notification_events, 
                self.num_of_no_notification_events)
