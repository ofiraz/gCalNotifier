from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QTabWidget, QTextBrowser
from PyQt5 import (QtCore, QtGui)
import subprocess
from datetime_utils import get_now_datetime
import datetime
import validators
from tzlocal import get_localzone
from json_utils import nice_json
import threading
import re

class EventDisplayDetails():
    def update_snooze_times_for_event(self):
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

        self.default_snooze = parsed_event.get('default_snooze', False)
        if (self.default_snooze):
            # Add the default snooze as the first item
            self.snooze_times_strings_for_combo_box.append("Default " + self.default_snooze + " minutes")
            self.snooze_times_in_minutes.append(int(self.default_snooze))

        now_datetime = get_now_datetime()
        if (parsed_event['start_date'] > now_datetime):
            # Event start did not arrive yet - hide all before snooze buttons that are not relevant anymore
            time_to_event_start = parsed_event['start_date'] - now_datetime
            time_to_event_in_minutes = int(time_to_event_start.seconds / 60)

            for index in range(len(self.snooze_times_before)):
                snooze_time = self.snooze_times_before[index][0]

                if (abs(snooze_time) < time_to_event_in_minutes):
                    self.snooze_times_strings_for_combo_box.append(self.snooze_times_before[index][1])
                    self.snooze_times_in_minutes.append(snooze_time)
            
        for index in range(len(self.snooze_times_future)):
            self.snooze_times_strings_for_combo_box.append(self.snooze_times_future[index][1])
            self.snooze_times_in_minutes.append(self.snooze_times_future[index][0])

    
    # Identify the video meeting softwate via its URL
    def identify_video_meeting_in_url(self, url, text_to_append_if_identified, text_if_not_identified):
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

        return identified_as_a_video_meeting, label_text

    def __init__(self, parsed_event):
        self.parsed_event = parsed_event

        indicate_issues_with_the_event = False

        self.c_video_link = ""

        self.need_to_record_meeting = parsed_event.get('need_to_record_meeting', False)
        if (self.need_to_record_meeting):
            indicate_issues_with_the_event = True
            self.snooze_time_in_minutes_for_open_video_and_snooze = 1

        else:
            self.snooze_time_in_minutes_for_open_video_and_snooze = 5


        self.cal_and_account_label_text = parsed_event['cal name'] + " calendar in " + parsed_event['google_account']

        self.all_day_event = parsed_event['all_day_event']

        self.start_time_label_text = 'Starting at ' + str(parsed_event['start_date'].astimezone(get_localzone()))
        self.end_time_label_text = 'Ending at ' + str(parsed_event['end_date'].astimezone(get_localzone()))

        self.gcal_event_link_label_text = "<a href=\"" + parsed_event['html_link'] + "\">Link to event in GCal</a>"
        self.gcal_event_link_label_tooltip = parsed_event['html_link']
   
        self.location_label_exits = False
        self.location_link_label_exists = False
        if (parsed_event['event_location'] != "No location"):
            valid_url = validators.url(parsed_event['event_location'])
            if (valid_url):
                self.location_link_label_exists = True
                self.location_link_label_tooltip = parsed_event['event_location']

                identified_as_a_video_meeting, self.location_link_label_text = self.identify_video_meeting_in_url(
                    parsed_event['event_location'],
                    "location",
                    "Link to location or to a video URL")
                
                if(identified_as_a_video_meeting):
                    self.c_video_link = parsed_event['event_location']

            else:
                self.location_label_exits = True

                self.location_label_text = 'Location: ' + parsed_event['event_location']

        self.update_snooze_times_for_event()

        self.video_label_exists = False
        if (parsed_event['video_link'] != "No Video"):
            self.video_label_exists = True

            identified_as_a_video_meeting, self.video_link_label_text = self.identify_video_meeting_in_url(
                parsed_event['video_link'],
                "description",
                "Video Link")
            
            self.video_link_label_tooltip = parsed_event['video_link']
            
            self.c_video_link = parsed_event['video_link']

        if (self.c_video_link != ""):
            # There is a video link

            if (self.need_to_record_meeting):
                self.open_video_and_snooze_text = "and snooze for 1 min"
            else:
                self.open_video_and_snooze_text = "and snooze for 5 min"
    
        self.mulitple_attendees_and_video_link_missing = False
        if ((self.c_video_link == "") and (parsed_event['num_of_attendees'] > 1)):
        # Num of attendees > 1 and no video link
            # We expect a video link as there are multiple attendees for this meeting

            # Let's check if we have our special sign
            is_no_video_ok = re.search(
                'NO_VIDEO_OK',
                parsed_event['description'])

            if (not is_no_video_ok):
                # We need to show the missing video message
                self.mulitple_attendees_and_video_link_missing = True
                indicate_issues_with_the_event = True

        if indicate_issues_with_the_event:
            self.event_name = "*** " + parsed_event['event_name']
        else:
            self.event_name = parsed_event['event_name']

WAKEUP_INTERVAL = 15

class DynamicWidgetDetails():
    def __init__(self, layout, widget):
        self.layout = layout
        self.widget = widget

class MultipleEventsTable(QWidget):
    def __init__(self, globals, parsed_event):
        super().__init__()

        self.globals = globals

        self.events_lock = threading.Lock()

        # Create QTableWidget with 1 row and 2 columns
        self.table_widget = QTableWidget(0, 2)
        
        self.table_widget.setFixedHeight(310)

        self.parsed_events = []
        self.events_display_details = []

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

        # Create a button to dismiss an event
        self.dismiss_event_button = QPushButton("Dismiss")
        self.dismiss_event_button.clicked.connect(self.on_dismiss_event_pressed)

        self.event_widgets = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add a horizontal layout to the snooze buttons
        self.h_layout = QHBoxLayout()
                
        layout.addWidget(self.table_widget)
        layout.addLayout(self.h_layout)
        layout.addWidget(self.dismiss_event_button)

        # Add the new event
        self.add_event(parsed_event)

        # Set the event to identify a new row selection
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display_on_timer)

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

        if (parsed_event['start_date'] > now_datetime):
            # Event start did not arrive yet
            time_to_event_start = parsed_event['start_date'] - now_datetime

            time_string = self.get_time_diff_in_string(time_to_event_start) + " until start"

        elif (parsed_event['end_date'] <= now_datetime):
            # Event has ended
            time_since_event_ended = now_datetime - parsed_event['end_date']
            
            time_string = self.get_time_diff_in_string(time_since_event_ended) + " since event ended"

        else:
            # Event started but did not end yet
            time_since_event_started = now_datetime - parsed_event['start_date']
           
            time_string = self.get_time_diff_in_string(time_since_event_started) + " since event started"

        return(time_string)

    def add_event(self, parsed_event):
        with self.events_lock:
            row_count = self.table_widget.rowCount()

            # Insert a new row at the end of the table
            self.table_widget.insertRow(row_count)

            event_display_details = EventDisplayDetails(parsed_event)

            self.table_widget.setItem(row_count, 0, QTableWidgetItem(event_display_details.event_name))
            self.table_widget.setItem(row_count, 1, QTableWidgetItem(self.get_time_until_event_start(parsed_event)))

            self.table_widget.resizeColumnToContents(0)
            self.table_widget.resizeColumnToContents(1)

            self.parsed_events.append(parsed_event)
            self.events_display_details.append(event_display_details)

            if (row_count == 0):
                self.select_event(0)
                self.add_event_details_widgets(0)

    def select_event(self, row_number):
        self.table_widget.selectRow(row_number)

    def remove_event_safe(self, row):
        self.globals.displayed_events.remove_event(self.parsed_events[row]['event_key_str'])

        self.table_widget.removeRow(row)

        del self.parsed_events[row]
        del self.events_display_details[row]

        # Close the windows if there are no more events presneted
        if (self.table_widget.rowCount() == 0):
            self.close()

    def remove_event(self, row):
        with self.events_lock:
            # Hiding the details of the event if they were presented
            self.clear_event_details_widgets()

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
                parsed_event['event_wakeup_time'] = parsed_event['start_date'] - delta_diff
            else:
                delta_diff = datetime.timedelta(minutes=snooze_time_in_minutes)
                parsed_event['event_wakeup_time'] = now_datetime + delta_diff

            self.globals.events_logger.info("Event snoozed by user, for event: " + parsed_event['event_name'] + " until " + str(parsed_event['event_wakeup_time']))
                
            self.globals.events_to_snooze.add_event(self.parsed_events[selected_row]['event_key_str'], parsed_event)

            self.remove_event(selected_row)

    def on_dismiss_event_pressed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            now_datetime = get_now_datetime()

            parsed_event = self.parsed_events[selected_row]

            if (now_datetime < parsed_event['end_date']):
                self.globals.events_to_dismiss.add_event(parsed_event['event_key_str'], parsed_event)

            self.remove_event(selected_row)

    def update_table_cell(self, row, column, new_value):
        item = self.table_widget.item(row, column)
        if item:
            # Change the text of the item
            item.setText(new_value)

    def update_display_on_timer(self):
        num_of_deleted_rows = 0

        with self.events_lock:
            for row in range(self.table_widget.rowCount()):
                index = row - num_of_deleted_rows

                # Get the new time until the event, and update the row
                time_until_event_start = self.get_time_until_event_start(self.parsed_events[index])
                self.update_table_cell(index, 1, time_until_event_start)

                if (self.parsed_events[index]['deleted'] or self.parsed_events[index]['changed']):
                    self.remove_event_safe(index)
                    num_of_deleted_rows = num_of_deleted_rows + 1

            # Update the 2nd column width
            self.table_widget.resizeColumnToContents(1)

            # Update the displayed information for the selected row
            selected_row = self.table_widget.currentRow()

            if selected_row != -1:  # -1 means no row is selected
                self.add_event_details_widgets(selected_row)

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

        self.add_widget(layout, new_label)

    def add_link_label(self, layout, label_text, tooltip_text):
        new_label = QLabel(label_text)  # Create a new QLabel
        new_label.setFixedHeight(16)
        new_label.setToolTip(tooltip_text)

        # Enable automatic opening of external links
        new_label.setOpenExternalLinks(True)

        self.add_widget(layout, new_label)

    def add_button(self, layout, button_text, button_callback, additional_data = None, pass_button_to_cb = False):
        new_button = QPushButton(button_text)  # Create a new button

        if (additional_data):
            new_button.setProperty("customData", str(additional_data))

        #new_button.setFixedWidth(button_width)
        new_button.setFixedHeight(32)
        #new_button.adjustSize()

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

        self.add_widget(layout, new_button)

    def open_video(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            # Decide on the Chrome profile to use
            if (self.parsed_events[selected_row]['google_account'] == 'ofiraz@gmail.com'):
                profile_name = 'Profile 1'
            else:
                profile_name = 'Profile 9'

            subprocess.Popen(
                [
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
                    self.c_video_link,
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
            parsed_event['event_wakeup_time'] = now_datetime + delta_diff

            self.globals.events_logger.info("Event snoozed by user, for event: " + parsed_event['event_name'] + " until " + str(parsed_event['event_wakeup_time']))

            self.globals.events_to_snooze.add_event(self.parsed_events[selected_row]['event_key_str'], parsed_event)

            self.remove_event(selected_row)

    def add_widget(self, layout, widget):
        layout.addWidget(widget)  # Add the new tab widget to the layout

        self.event_widgets.append(DynamicWidgetDetails(layout, widget))

    def add_tab_widget(self, layout, parsed_event):
        new_tab_widget = QTabWidget()  # Create a new tab widget
        new_tab_widget.setFixedHeight(310)

        if (parsed_event['description'] != "No description"):
            # Create a tab for the description
            description_tab = QTextBrowser()
            description_tab.setHtml(parsed_event['description'])
            description_tab.setOpenExternalLinks(True)


            # Add the tab to the tab widget
            new_tab_widget.addTab(description_tab, "Description")

        # Create the tab for the raw event
        raw_event_tab = QTextBrowser()
        raw_event_tab.setText(nice_json(parsed_event['raw_event']))

        # Add the tab to the tab widget
        new_tab_widget.addTab(raw_event_tab, "Raw Event")

        self.add_widget(layout, new_tab_widget)

    def on_snooze_general(self, button):
        minutes_to_snooze = int(button.property("customData"))

        self.snooze_event(minutes_to_snooze)

    def add_snooze_buttons(self, event_display_details):
        event_display_details.update_snooze_times_for_event()

        for index in range(len(event_display_details.snooze_times_strings_for_combo_box)):
            button_text = event_display_details.snooze_times_strings_for_combo_box[index]
            button_minutes = event_display_details.snooze_times_in_minutes[index]
            self.add_button(
                self.h_layout,
                button_text,
                self.on_snooze_general,
                additional_data=button_minutes,
                pass_button_to_cb=True)

    def add_event_details_widgets(self, row):
        # Clear the previous details presented
        self.clear_event_details_widgets()

        parsed_event = self.parsed_events[row]
        event_display_details = self.events_display_details[row]

        layout = self.layout()  # Retrieve the layout using layout()

        if (event_display_details.mulitple_attendees_and_video_link_missing):
            # We need to show the missing video message
            self.add_label(
                layout,
                "There are multiple attendees in this meeting, but there is no video link!!!", 
                highlight=True)

        if (event_display_details.need_to_record_meeting):
            self.add_label(
                layout,
                "Remember to record!!!", 
                highlight=True)

        self.add_snooze_buttons(event_display_details)

        self.c_video_link = event_display_details.c_video_link

        self.add_label(
            layout,
            event_display_details.cal_and_account_label_text)

        if event_display_details.all_day_event:
            self.add_label(
                layout,
                "An all day event")

        self.add_label(
            layout,
            event_display_details.start_time_label_text)
        
        self.add_label(
            layout,
            event_display_details.end_time_label_text)

        self.add_link_label(
            layout,
            event_display_details.gcal_event_link_label_text,
            event_display_details.gcal_event_link_label_tooltip
        )

        if (event_display_details.location_label_exits):
            self.add_label(
                layout,
                event_display_details.location_label_text)
            
        elif (event_display_details.location_link_label_exists):
            self.add_link_label(
                layout,
                event_display_details.location_link_label_text,
                event_display_details.location_link_label_tooltip)
            
        if (event_display_details.video_label_exists):
            self.add_link_label(
                layout,
                event_display_details.video_link_label_text,
                event_display_details.video_link_label_tooltip)

        if (self.c_video_link != ""):
            # There is a video link - add the needed buttons
            self.add_button(
                layout,
                "Open Video",
                self.open_video
            )

            self.add_button(
                layout,
                event_display_details.open_video_and_snooze_text,
                self.open_video_and_snooze
            )
    
        self.add_tab_widget(layout, parsed_event)

    def clear_event_details_widgets(self):
        while self.event_widgets:
            event_widget = self.event_widgets.pop()

            event_widget.layout.removeWidget(event_widget.widget)

            event_widget.widget.deleteLater()

    def update_event(self, parsed_event):       
        with self.events_lock:
            # Find the modified event in the current list of events
            for row in range(self.table_widget.rowCount()):
                if (self.parsed_events[row]['event_key_str'] == parsed_event['event_key_str']):
                    # Found the event - update all of its fields
                    self.parsed_events[row] = parsed_event

                    event_display_details = EventDisplayDetails(parsed_event)
                    self.events_display_details[row] = event_display_details

                    self.update_table_cell(row, 0, event_display_details.event_name)
                    self.update_table_cell(row, 1, self.get_time_until_event_start(parsed_event))

                    self.table_widget.resizeColumnToContents(0)
                    self.table_widget.resizeColumnToContents(1)

                    # Update the displayed information for the selected row
                    selected_row = self.table_widget.currentRow()

                    if (selected_row == row):  # -1 means no row is selected
                        self.add_event_details_widgets(row)

                    return

        # If we got here the event could not be found - could be a race condition in the case it was removed due to the change marking in the refresh event
        print("Couldnt find the event to change, handling it as new")
        self.add_event(parsed_event)
