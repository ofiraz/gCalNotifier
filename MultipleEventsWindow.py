'''
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QWidget

class TableWidgetDemo(QWidget):
    def __init__(self):
        super().__init__()

        self.table_widget = QTableWidget(4, 4)
        for row in range(4):
            for column in range(4):
                item = QTableWidgetItem(f"Item {row},{column}")
                self.table_widget.setItem(row, column, item)

        # Make the QTableWidget read-only
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set the selection behavior to select entire rows
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        # Hide the column headers (horizontal headers)
        self.table_widget.horizontalHeader().setVisible(False)

        # Hide the row headers (vertical headers)
        self.table_widget.verticalHeader().setVisible(False)

        self.table_widget.itemClicked.connect(self.on_item_clicked)

        # Button to change the content of a specific item
        self.change_button = QPushButton("Change Content of Row 1, Column 2")
        self.change_button.clicked.connect(self.change_item_content)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.change_button)
        self.setLayout(layout)

    def on_item_clicked(self, item):
        print(f"Clicked on: {item.text()} at Row: {item.row()}, Column: {item.column()}")

    def change_item_content(self):
        row = 1  # Second row (index 1)
        column = 2  # Third column (index 2)

        # Access the item at the specified position
        item = self.table_widget.item(row, column)
        if item:
            # Change the text of the item
            item.setText("New Content")

if __name__ == "__main__":
    app = QApplication([])
    demo = TableWidgetDemo()
    demo.show()
    app.exec_()


from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLabel

class TableWidgetDemo(QWidget):
    def __init__(self):
        super().__init__()

        # Create QTableWidget with 4 rows and 4 columns
        self.table_widget = QTableWidget(4, 4)
        for row in range(4):
            for column in range(4):
                item = QTableWidgetItem(f"Item {row},{column}")
                self.table_widget.setItem(row, column, item)

        # Create a label to display the selected row
        self.label = QLabel("Selected Row: None")

        # Connect the itemSelectionChanged signal to the custom slot
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            self.label.setText(f"Selected Row: {selected_row}")
        else:
            self.label.setText("Selected Row: None")

if __name__ == "__main__":
    app = QApplication([])
    demo = TableWidgetDemo()
    demo.show()
    app.exec_()

class TableWidgetDemo(QWidget):
    def __init__(self):
        super().__init__()

        # Create QTableWidget with 4 rows and 4 columns
        self.table_widget = QTableWidget(4, 4)
        for row in range(4):
            for column in range(4):
                item = QTableWidgetItem(f"Item {row},{column}")
                self.table_widget.setItem(row, column, item)

        # Make the QTableWidget read-only
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set the selection behavior to select entire rows
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        # Hide the column headers (horizontal headers)
        self.table_widget.horizontalHeader().setVisible(False)

        # Hide the row headers (vertical headers)
        self.table_widget.verticalHeader().setVisible(False)

        # Create a button to select the second row
        select_row_button = QPushButton("Select Row 2")
        select_row_button.clicked.connect(self.select_row)

        # Button to delete a specific row
        delete_button = QPushButton("Delete Row 2")
        delete_button.clicked.connect(self.delete_row)

                # Button to change the content of a specific item
        change_button = QPushButton("Change Content of Row 1, Column 2")
        change_button.clicked.connect(self.change_item_content)

        # Create a button to add a new row
        add_row_button = QPushButton("Add New Row")
        add_row_button.clicked.connect(self.add_new_row)

        # Create a label to display the selected row
        self.label = QLabel("Selected Row: None")

        # Connect the itemSelectionChanged signal to the custom slot
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(select_row_button)
        layout.addWidget(delete_button)
        layout.addWidget(change_button)
        layout.addWidget(self.label)
        layout.addWidget(add_row_button)

        self.setLayout(layout)

        self.table_widget.itemClicked.connect(self.on_item_clicked)

    def change_item_content(self):
        row = 1  # Second row (index 1)
        column = 2  # Third column (index 2)

        # Access the item at the specified position
        item = self.table_widget.item(row, column)
        if item:
            # Change the text of the item
            item.setText("New Content")

    def delete_row(self):
        row_to_delete = 2  # For example, delete the third row (index 2)
        self.table_widget.removeRow(row_to_delete)

    def on_item_clicked(self, item):
        print(f"Clicked on: {item.text()} at Row: {item.row()}, Column: {item.column()}")

    def select_row(self):
        # Select the second row (index 1, because indexes are 0-based)
        self.table_widget.selectRow(1)

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            self.label.setText(f"Selected Row: {selected_row}")
        else:
            self.label.setText("Selected Row: None")

    def add_new_row(self):
        # Get the current row count
        row_count = self.table_widget.rowCount()
        row_count = 0

        # Insert a new row at the end of the table
        self.table_widget.insertRow(row_count)

        # Populate the new row with items
        for column in range(self.table_widget.columnCount()):
            new_item = QTableWidgetItem(f"New Item {row_count},{column}")
            self.table_widget.setItem(row_count, column, new_item)
'''

from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox
from PyQt5 import QtCore
import subprocess
from datetime_utils import get_now_datetime
from EventWindow import *
import datetime
import validators


class MultipleEventsTable(QWidget):
    def __init__(self, globals, parsed_event):
        super().__init__()

        self.globals = globals

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

        # Set the event to identify a new row selection
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)

        # Create a QComboBox for the available snooze items
        self.snooze_times_combo_box = QComboBox()

        # Create a button to snooze event
        self.snooze_event_button = QPushButton("Snooze Event")
        self.snooze_event_button.clicked.connect(self.on_snooze_event_clicked)

        # Create a button to present details on the event
        self.present_event_details_button = QPushButton("Present event details")
        self.present_event_details_button.clicked.connect(self.on_present_event_details_pressed)

        # Create a button to dismiss an event
        self.dismiss_event_button = QPushButton("Dismiss")
        self.dismiss_event_button.clicked.connect(self.on_dismiss_event_pressed)

        # Create a clear event button - when we snooze or dismiss in the event window - to be removed eventually
        self.clear_event_button = QPushButton("Clear")
        self.clear_event_button.clicked.connect(self.on_clear_event_pressed)

        # Create a button to show or hide the details on the event
        self.show_event_details = False
        self.show_hide_event_details_button = QPushButton("Show event details")
        self.show_hide_event_details_button.clicked.connect(self.on_show_hide_event_details_pressed)


        self.items_added_by_add_button = 0

        # Add the new event
        self.add_event(parsed_event)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.snooze_times_combo_box)
        layout.addWidget(self.snooze_event_button)
        layout.addWidget(self.present_event_details_button)
        layout.addWidget(self.dismiss_event_button)
        layout.addWidget(self.clear_event_button)
        layout.addWidget(self.show_hide_event_details_button)

        self.setLayout(layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display_on_timer)

        # Set timer to wake up in a minute
        self.timer.start(60 * 1000)

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

    def hide_event_details_if_needed(self):
        if (self.show_event_details == True):
            self.hide_event_details()

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            print(f"Selected Row: {selected_row}")

            # Hiding the details of the previously selected event
            self.hide_event_details_if_needed()

            self.set_snooze_times_for_event(self.parsed_events[selected_row])

        else:
            print("Selected Row: None")

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
        print(now_datetime)

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
            self.set_snooze_times_for_event(self.parsed_events[0])

    def select_event(self, row_number):
        self.table_widget.selectRow(row_number)

    def on_present_event_details_pressed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            print(f"Presenting information about the item in row: {selected_row}")

            event_win = EventWindow(self.globals)

            event_win.init_window_from_parsed_event(self.parsed_events[selected_row]['event_key_str'], self.parsed_events[selected_row])
            event_win.setFixedWidth(730)
            event_win.setFixedHeight(650)

            event_win.show()
            event_win.activateWindow()
            event_win.raise_()

        else:
            print("Selected Row: None")

    def remove_event(self, selected_row):
        # Hiding the details of the event if they were presented
        self.hide_event_details_if_needed()

        self.table_widget.removeRow(selected_row)

        del self.parsed_events[selected_row]

        # Close the windows if there are no more events presneted
        if (self.table_widget.rowCount() == 0):
            self.close()

    def on_clear_event_pressed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            print(f"Clear event in row: {selected_row}")

            self.remove_event(selected_row)

        else:
            print("Selected Row: None")

    def on_snooze_event_clicked(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            print(self.snooze_times_combo_box.currentText())

            snooze_time_in_minutes = self.snooze_times_in_minutes[self.snooze_times_combo_box.currentIndex()]
            print(snooze_time_in_minutes)

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

            self.globals.displayed_events.remove_event(self.parsed_events[selected_row]['event_key_str'])

            self.remove_event(selected_row)

        else:
            print("Selected Row: None")

    def on_dismiss_event_pressed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            print(f"Dismiss event in row: {selected_row}")

            now_datetime = get_now_datetime()

            parsed_event = self.parsed_events[selected_row]

            if (now_datetime < parsed_event['end_date']):
                self.globals.events_to_dismiss.add_event(parsed_event['event_key_str'], parsed_event)

            self.globals.displayed_events.remove_event(parsed_event['event_key_str'])

            self.remove_event(selected_row)

        else:
            print("Selected Row: None")

    def update_display_on_timer(self):
        for row in range(self.table_widget.rowCount()):
            time_until_event_start = self.get_time_until_event_start(self.parsed_events[row])

            # Access the item at the specified position
            item = self.table_widget.item(row, 1)
            if item:
                # Change the text of the item
                item.setText(time_until_event_start)

        # Update the 2nd column width
        self.table_widget.resizeColumnToContents(1)

        # Update the snooze times in the combo box for the selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            self.set_snooze_times_for_event(self.parsed_events[selected_row])

        # Sleep for another minute
        self.timer.start(60 * 1000)

    def increase_window_height(self):
        current_size = self.size()  # Get the current window size
        new_height = current_size.height() + 25  # Increase the height by 50 pixels
        self.resize(current_size.width(), new_height)  # Set the new window size

    def add_label(self, label_text, highlight = False):
        self.increase_window_height()

        layout = self.layout()  # Retrieve the layout using layout()
        new_label = QLabel(label_text)  # Create a new QLabel

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

        layout.addWidget(new_label)  # Add the new label to the layout

        self.event_widgets.append(new_label)

    def add_link_label(self, label_text, tooltip_text):
        self.increase_window_height()

        layout = self.layout()  # Retrieve the layout using layout()
        new_label = QLabel(label_text)  # Create a new QLabel
        new_label.setToolTip(tooltip_text)

        # Enable automatic opening of external links
        new_label.setOpenExternalLinks(True)

        layout.addWidget(new_label)  # Add the new label to the layout

        self.event_widgets.append(new_label)

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

        self.add_link_label(
            "<a href=\"" + url + "\">" + label_text + "</a>",
            url
        )

    def add_button(self, button_text, button_callback):
        self.increase_window_height()

        layout = self.layout()  # Retrieve the layout using layout()
        new_button = QPushButton(button_text)  # Create a new button
        new_button.clicked.connect(button_callback)

        layout.addWidget(new_button)  # Add the new button to the layout

        self.event_widgets.append(new_button)

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

        else:
            print("Selected Row: None")

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

            self.globals.displayed_events.remove_event(self.parsed_events[selected_row]['event_key_str'])

            self.remove_event(selected_row)

        else:
            print("Selected Row: None")
        

    def present_event_details(self, parsed_event):
        self.event_widgets = []

        self.c_video_link = ""

        self.need_to_record_meeting = parsed_event.get('need_to_record_meeting', False)
        if (self.need_to_record_meeting):
            self.add_label("Remember to record!!!", highlight=True)

        self.add_label(parsed_event['cal name'] + " calendar in " + parsed_event['google_account'])

        if parsed_event['all_day_event']:
            self.add_label("An all day event")

        parsed_event['start_time_in_loacal_tz'] = str(parsed_event['start_date'].astimezone(get_localzone()))
        parsed_event['end_time_in_loacal_tz'] = str(parsed_event['end_date'].astimezone(get_localzone()))

        self.add_label('Starting at ' + parsed_event['start_time_in_loacal_tz'])
        self.add_label('Ending at ' + parsed_event['end_time_in_loacal_tz'])

        self.add_link_label(
            "<a href=\"" + parsed_event['html_link'] + "\">Link to event in GCal</a>",
            parsed_event['html_link']
        )

        if (parsed_event['event_location'] != "No location"):
            valid_url = validators.url(parsed_event['event_location'])
            if (valid_url):
                self.identify_video_meeting_in_url(
                    parsed_event['event_location'],
                    "location",
                    "Link to location or to a video URL")

                self.c_video_link = parsed_event['event_location']

            else:
                self.add_label('Location: ' + parsed_event['event_location'])

        if (parsed_event['video_link'] != "No Video"):
            self.identify_video_meeting_in_url(
                parsed_event['video_link'],
                "description",
                "Video Link")

            self.c_video_link = parsed_event['video_link']

            self.add_button(
                "Open Video",
                self.open_video
            )

            if (self.need_to_record_meeting):
                open_video_and_snooze_text = "and snooze for 1 min"
            else:
                open_video_and_snooze_text = "and snooze for 5 min"

            self.add_button(
                open_video_and_snooze_text,
                self.open_video_and_snooze
            )

        if ((self.c_video_link == "") and (parsed_event['num_of_attendees'] > 1)):
        # Num of attendees > 1 and no video link
            # We expect a video link as there are multiple attendees for this meeting

            # Let's check if we have our special sign
            is_no_video_ok = re.search(
                'NO_VIDEO_OK',
                parsed_event['description'])

            if (not is_no_video_ok):
                # We need to show the missing video message
                self.add_label("There are multiple attendees in this meeting, but there is no video link!!!", highlight=True)


    def hide_event_details(self):
        self.show_hide_event_details_button.setText("Show event details")
        self.show_event_details = False

        layout = self.layout()  # Retrieve the layout using layout()

        while self.event_widgets:
            event_widget = self.event_widgets.pop()

            layout.removeWidget(event_widget)
            event_widget.deleteLater()

            # Decrease the window height
            current_size = self.size()  # Get the current window size
            new_height = current_size.height() - 25  # Increase the height by 50 pixels
            self.resize(current_size.width(), new_height)  # Set the new window size

    def on_show_hide_event_details_pressed(self):
        if (self.show_event_details == False):
            # Get the index of the current selected row
            selected_row = self.table_widget.currentRow()

            if selected_row != -1:  # -1 means no row is selected
                self.show_hide_event_details_button.setText("Hide event details")
                self.show_event_details = True

                parsed_event = self.parsed_events[selected_row]

                self.present_event_details(parsed_event)          

            else:
                print("Selected Row: None")

        else:
            self.hide_event_details()

if __name__ == "__main__":
    app = QApplication([])
    demo = MultipleEventsTable("Name", "2 Minutes")
    demo.show()
    app.exec_()