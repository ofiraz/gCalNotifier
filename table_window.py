from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton

class TableWindow(QWidget):
    def __init__(self, globals, show_events_table_object):
        super().__init__()

        self.globals = globals

        self.show_events_table_object = show_events_table_object

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.number_of_columns_in_table = len(self.show_events_table_object.table_header)
        self.table_widget = QTableWidget(0, self.number_of_columns_in_table)

        # Make the QTableWidget read-only
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set the selection behavior to select entire rows
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        # Prevent muliple selection
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)

        # Set the table headers
        self.table_widget.setHorizontalHeaderLabels(self.show_events_table_object.table_header)

        # Hide the row headers (vertical headers)
        self.table_widget.verticalHeader().setVisible(False)

        self.main_layout.addWidget(self.table_widget)

        self.action_button = QPushButton(self.show_events_table_object.act_button_text)
        self.main_layout.addWidget(self.action_button)

        self.action_button.clicked.connect(self.act_on_event)

        self.refresh_button = QPushButton('Refresh')
        self.main_layout.addWidget(self.refresh_button)

        self.refresh_button.clicked.connect(self.update_table_data)

        self.update_table_data()

    def act_on_event(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()

        if ((selected_row != -1) and (self.table_widget.item(selected_row, 0).isSelected())):
            event_key_str = self.data[selected_row][0]

            print("Act on event " + str(selected_row) + " with key " + event_key_str)

            self.show_events_table_object.act_on_event_cb(event_key_str)

            self.table_widget.removeRow(selected_row)
       
        else:
            print("No row selected")

    def update_table_data(self):
        self.data = self.show_events_table_object.get_data_into_table()

        # Clear old data
        while (self.table_widget.rowCount() > 0):
            self.table_widget.removeRow(0)
        
        for row in range(len(self.data)):
            self.table_widget.insertRow(row)

            for col in range(1, len(self.data[row])): # Skipping the event key value
                self.table_widget.setItem(row, col - 1, QTableWidgetItem(str(self.data[row][col])))

        total_columns_width = 0
        for col in range(1, len(self.data[0])): # Skipping the event key value
            self.table_widget.resizeColumnToContents(col - 1)
            total_columns_width = total_columns_width + self.table_widget.columnWidth(col - 1)

        # Set the window width to match the table's width and keep the height flexible
        self.resize(total_columns_width + 45, self.height())  # Set window width to table's width, keep current height
    
class Show_Events_Table_Window():
    def __init__(self, globals, get_events_object):
        self.globals = globals
        self.get_events_object = get_events_object

        # The rest should be provided by child classes
        self.get_events_into_list_function = None
        self.table_header = []
        self.window_title = ""
        self.act_button_text = ""
        self.act_on_event_cb = None

    def handle_event_to_display(self, event_key_str, parsed_event, events_list):
        return
    
    def get_sort_value(self, item):
        return None
        
    def open_window_with_events(self):        
        self.table_window = TableWindow(self.globals, self)
        self.table_window.show()
        self.table_window.setWindowTitle(self.window_title)
        self.table_window.activateWindow()
        self.table_window.raise_()

    def get_data_into_table(self):
        events_list = []

        self.get_events_into_list_function(self.handle_event_to_display, events_list)

        # Sort by the event time
        events_list.sort(key=self.get_sort_value)

        return(events_list)

class Show_Snoozed_Events_Table_Window(Show_Events_Table_Window):
    def __init__(self, globals, get_events_object):
        super().__init__(globals, get_events_object)

        self.get_events_into_list_function = self.get_events_object.get_snoozed_events_into_list
        self.table_header = ["Google Account", "Calendar Name", "Event Name", "Snoozed Until"]
        self.window_title = "Snoozed Events"
        self.act_button_text = "Unsnooze"
        self.act_on_event_cb = self.globals.snoozed_events.unsnooze_or_undismiss_event

        
    def handle_event_to_display(self, event_key_str, parsed_event, events_list):
        snoozed_item = [
            event_key_str,
            parsed_event.google_account,
            parsed_event.cal_name,
            parsed_event.event_name,
            parsed_event.event_wakeup_time
        ]

        events_list.append(snoozed_item)

    def get_sort_value(self, item):
        return(item[4]) # The event wakeup time

class Show_Dismissed_Events_Table_Window(Show_Events_Table_Window):
    def __init__(self, globals, get_events_object):
        super().__init__(globals, get_events_object)

        self.get_events_into_list_function = self.get_events_object.get_dismissed_events_into_list
        self.table_header = ["Google Account", "Calendar Name", "Event Name", "End Time"]
        self.window_title = "Dismissed Events"
        self.act_button_text = "Undismiss"
        self.act_on_event_cb = self.globals.dismissed_events.unsnooze_or_undismiss_event

        
    def handle_event_to_display(self, event_key_str, parsed_event, events_list):
        dismissed_item = [
            event_key_str,
            parsed_event.google_account,
            parsed_event.cal_name,
            parsed_event.event_name,
            parsed_event.end_date
        ]

        events_list.append(dismissed_item)

    def get_sort_value(self, item):
        return(item[4]) # End date
