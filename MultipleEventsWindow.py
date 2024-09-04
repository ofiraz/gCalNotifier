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
'''

from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5 import QtCore
import subprocess
from datetime_utils import get_now_datetime

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

class MultipleEventsTable(QWidget):
    def __init__(self, parsed_event):
        super().__init__()

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

        # Create a button to present details on the event
        self.present_event_details_button = QPushButton("Present event details")
        self.present_event_details_button.clicked.connect(self.on_present_event_details_pressed)

        # Create a button to dismiss an event
        self.dismiss_event_button = QPushButton("Dismiss")
        self.dismiss_event_button.clicked.connect(self.on_dismiss_event_pressed)

        self.items_added_by_add_button = 0

        # Create a button to add a new event
        self.add_event_button = QPushButton("Add Event")
        self.add_event_button.clicked.connect(self.on_add_new_event_clicked)

        # Add the new event
        self.add_event(parsed_event)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.present_event_details_button)
        layout.addWidget(self.dismiss_event_button)
        layout.addWidget(self.add_event_button)

        self.setLayout(layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display_on_timer)

        # Set timer to wake up in a minute
        self.timer.start(60 * 1000)

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            print(f"Selected Row: {selected_row}")
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

    def select_event(self, row_number):
        self.table_widget.selectRow(row_number)

    def open_event_url(self, parsed_event):
        # Decide on the Chrome profile to use
        if (parsed_event['google_account'] == 'ofiraz@gmail.com'):
            profile_name = 'Profile 1'
        else:
            profile_name = 'Profile 9'

        subprocess.Popen(
            [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
                parsed_event['html_link'],
                '--profile-directory=' + profile_name
            ]
        ) 
    
    def on_present_event_details_pressed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            print(f"Presenting information about the item in row: {selected_row}")
            self.open_event_url(self.parsed_events[selected_row])
        else:
            print("Selected Row: None")

    def on_dismiss_event_pressed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if selected_row != -1:  # -1 means no row is selected
            print(f"Dismiss event in row: {selected_row}")
            self.table_widget.removeRow(selected_row)

            del self.parsed_events[selected_row]

        else:
            print("Selected Row: None")

    def on_add_new_event_clicked(self):
        self.items_added_by_add_button = self.items_added_by_add_button + 1

        event_name = "Event " + str(self.items_added_by_add_button)
        time_left = str(self.items_added_by_add_button) + " minutes"

        self.add_event(event_name, time_left)

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

        # Sleep for another minute
        self.timer.start(60 * 1000)

if __name__ == "__main__":
    app = QApplication([])
    demo = MultipleEventsTable("Name", "2 Minutes")
    demo.show()
    app.exec_()