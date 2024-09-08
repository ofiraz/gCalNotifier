from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QTabWidget, QTextBrowser
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
        self.c_video_link = ""

        self.need_to_record_meeting = parsed_event.get('need_to_record_meeting', False)

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

class MultipleEventsTable(QWidget):
    def __init__(self, globals, parsed_event):
        super().__init__()

        self.globals = globals


        self.events_lock = threading.Lock()

        # Create QTableWidget with 1 row and 2 columns
        self.table_widget = QTableWidget(0, 2)

        self.parsed_events = []

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

        # Create a QComboBox for the available snooze items
        self.snooze_times_combo_box = QComboBox()

        # Create a button to snooze event
        self.snooze_event_button = QPushButton("Snooze Event")
        self.snooze_event_button.clicked.connect(self.on_snooze_event_clicked)

        # Create a button to dismiss an event
        self.dismiss_event_button = QPushButton("Dismiss")
        self.dismiss_event_button.clicked.connect(self.on_dismiss_event_pressed)

        self.event_widgets = []

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(self.table_widget)
        layout.addWidget(self.snooze_times_combo_box)
        layout.addWidget(self.snooze_event_button)
        layout.addWidget(self.dismiss_event_button)

        # Add the new event
        self.add_event(parsed_event)

        # Set the event to identify a new row selection
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display_on_timer)

        # Set timer to wake up in a minute
        self.timer.start(30 * 1000)

    def set_snooze_times_for_event(self, parsed_event):
        snooze_times_before = [ 
            ( -5, "5 minutes before start" ) ,
            ( -2, "2 minutes before start" ) ,
            ( -1, "1 minute before start" ) ,
            ( 0, "at start" )
        ]

        snooze_times_future = [ 
            ( 1, "For 1 minute" ) ,
            ( 5, "For 5 minutes" ) ,
            ( 15, "For 15 minutes" ) ,
            ( 30, "For 30 minutes" ) ,
            ( 60, "For 1 hour" ) ,
            ( 120, "For 2 hours" ) ,
            ( 240, "For 4 hours" ) ,
            ( 480, "For 8 hours" )
        ]

        snooze_times_strings_for_combo_box = []
        self.snooze_times_in_minutes = []

        default_snooze = parsed_event.get('default_snooze', False)
        if (default_snooze):
            # Add the default snooze as the first item
            snooze_times_strings_for_combo_box.append("Default " + default_snooze + " minutes")
            self.snooze_times_in_minutes.append(int(default_snooze))

        now_datetime = get_now_datetime()
        if (parsed_event['start_date'] > now_datetime):
            # Event start did not arrive yet - hide all before snooze buttons that are not relevant anymore
            time_to_event_start = parsed_event['start_date'] - now_datetime
            time_to_event_in_minutes = int(time_to_event_start.seconds / 60)

            for index in range(len(snooze_times_before)):
                snooze_time = snooze_times_before[index][0]

                if (abs(snooze_time) < time_to_event_in_minutes):
                    snooze_times_strings_for_combo_box.append(snooze_times_before[index][1])
                    self.snooze_times_in_minutes.append(snooze_time)

        for index in range(len(snooze_times_future)):
            snooze_times_strings_for_combo_box.append(snooze_times_future[index][1])
            self.snooze_times_in_minutes.append(snooze_times_future[index][0])

        self.snooze_times_combo_box.clear()
        self.snooze_times_combo_box.addItems(snooze_times_strings_for_combo_box)

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            self.add_event_details_widgets(self.parsed_events[selected_row])

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

            self.table_widget.setItem(row_count, 0, QTableWidgetItem(parsed_event['event_name']))
            self.table_widget.setItem(row_count, 1, QTableWidgetItem(self.get_time_until_event_start(parsed_event)))

            self.table_widget.resizeColumnToContents(0)
            self.table_widget.resizeColumnToContents(1)

            self.parsed_events.append(parsed_event)

            if (row_count == 0):
                self.select_event(0)
                self.add_event_details_widgets(self.parsed_events[0])

    def select_event(self, row_number):
        self.table_widget.selectRow(row_number)

    def remove_event_safe(self, row):
        self.globals.displayed_events.remove_event(self.parsed_events[row]['event_key_str'])

        self.table_widget.removeRow(row)

        del self.parsed_events[row]

        # Close the windows if there are no more events presneted
        if (self.table_widget.rowCount() == 0):
            self.close()

    def remove_event(self, row):
        with self.events_lock:
            # Hiding the details of the event if they were presented
            self.clear_event_details_widgets()

            self.remove_event_safe(row)

    def on_snooze_event_clicked(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            snooze_time_in_minutes = self.snooze_times_in_minutes[self.snooze_times_combo_box.currentIndex()]

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

                if (self.parsed_events[index]['deleted']):
                    self.remove_event_safe(index)
                    num_of_deleted_rows = num_of_deleted_rows + 1

            # Update the 2nd column width
            self.table_widget.resizeColumnToContents(1)

            # Update the displayed information for the selected row
            selected_row = self.table_widget.currentRow()

            if selected_row != -1:  # -1 means no row is selected
                self.add_event_details_widgets(self.parsed_events[selected_row])

            # Sleep for another minute
            self.timer.start(30 * 1000)

    def increase_window_height(self, pixels_to_add):
        current_size = self.size()  # Get the current window size
        new_height = current_size.height() + pixels_to_add  # Increase the height by 50 pixels
        self.resize(current_size.width(), new_height)  # Set the new window size

    def add_label(self, label_text, highlight = False):
        layout = self.layout()  # Retrieve the layout using layout()
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

    def add_link_label(self, label_text, tooltip_text):
        layout = self.layout()  # Retrieve the layout using layout()
        new_label = QLabel(label_text)  # Create a new QLabel
        new_label.setFixedHeight(16)
        new_label.setToolTip(tooltip_text)

        # Enable automatic opening of external links
        new_label.setOpenExternalLinks(True)

        self.add_widget(layout, new_label)

    def add_button(self, button_text, button_callback):
        layout = self.layout()  # Retrieve the layout using layout()
        new_button = QPushButton(button_text)  # Create a new button
        new_button.setFixedHeight(32)
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

            if (self.need_to_record_meeting):
                self.c_snooze_time_in_minutes = 1
            else:
                self.c_snooze_time_in_minutes = 5

            parsed_event = self.parsed_events[selected_row]
            now_datetime = get_now_datetime()

            delta_diff = datetime.timedelta(minutes=self.c_snooze_time_in_minutes)
            parsed_event['event_wakeup_time'] = now_datetime + delta_diff

            self.globals.events_logger.info("Event snoozed by user, for event: " + parsed_event['event_name'] + " until " + str(parsed_event['event_wakeup_time']))

            self.globals.events_to_snooze.add_event(self.parsed_events[selected_row]['event_key_str'], parsed_event)

            self.remove_event(selected_row)

    def add_widget(self, layout, widget):
        # Increase the windows's height by the hight of the widget plus some more for the spacing
        self.increase_window_height(widget.height() + 5)

        layout.addWidget(widget)  # Add the new tab widget to the layout

        self.event_widgets.append(widget)

    def add_tab_widget(self, parsed_event):
        layout = self.layout()  # Retrieve the layout using layout()
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
    
    def add_event_details_widgets(self, parsed_event):
        # Clear the previous details presented
        self.clear_event_details_widgets()

        self.event_display_details = EventDisplayDetails(parsed_event)

        if (self.event_display_details.mulitple_attendees_and_video_link_missing):
            # We need to show the missing video message
            self.add_label("There are multiple attendees in this meeting, but there is no video link!!!", highlight=True)

        if (self.event_display_details.need_to_record_meeting):
            self.add_label("Remember to record!!!", highlight=True)

        self.set_snooze_times_for_event(parsed_event)

        self.c_video_link = self.event_display_details.c_video_link

        self.add_label(self.event_display_details.cal_and_account_label_text)

        if self.event_display_details.all_day_event:
            self.add_label("An all day event")

        self.add_label(self.event_display_details.start_time_label_text)
        self.add_label(self.event_display_details.end_time_label_text)

        self.add_link_label(
            self.event_display_details.gcal_event_link_label_text,
            self.event_display_details.gcal_event_link_label_tooltip
        )

        if (self.event_display_details.location_label_exits):
            self.add_label(self.event_display_details.location_label_text)
        elif (self.event_display_details.location_link_label_exists):
            self.add_link_label(
                self.event_display_details.location_link_label_text,
                self.event_display_details.location_link_label_tooltip)
            
        if (self.event_display_details.video_label_exists):
            self.add_link_label(
                self.event_display_details.video_link_label_text,
                self.event_display_details.video_link_label_tooltip)

        if (self.c_video_link != ""):
            # There is a video link - add the needed buttons
            self.add_button(
                "Open Video",
                self.open_video
            )

            self.add_button(
                self.event_display_details.open_video_and_snooze_text,
                self.open_video_and_snooze
            )
    
        self.add_tab_widget(parsed_event)

    def clear_event_details_widgets(self):
        layout = self.layout()  # Retrieve the layout using layout()

        while self.event_widgets:
            event_widget = self.event_widgets.pop()

            layout.removeWidget(event_widget)
            event_widget.deleteLater()

            # Decrease the window height
            current_size = self.size()  # Get the current window size

            # Decrease the height the widget size and by an additional delta
            new_height = current_size.height() - event_widget.height() - 5  

            self.resize(current_size.width(), new_height)  # Set the new window size

    def update_event(self, parsed_event):
        with self.events_lock:
            # Find the modified event in the current list of events
            for row in range(self.table_widget.rowCount()):
                if (self.parsed_events[row]['event_key_str'] == parsed_event['event_key_str']):
                    # Found the event - update all of its fields
                    self.parsed_events[row] = parsed_event

                    self.update_table_cell(row, 0, parsed_event['event_name'])
                    self.update_table_cell(row, 1, self.get_time_until_event_start(parsed_event))

                    self.table_widget.resizeColumnToContents(0)
                    self.table_widget.resizeColumnToContents(1)

                    # Update the displayed information for the selected row
                    selected_row = self.table_widget.currentRow()

                    if (selected_row == row):  # -1 means no row is selected
                        self.add_event_details_widgets(self.parsed_events[row])


                    return

        # If we got here the event could not be found
        print("Couldnt find the event to change")
