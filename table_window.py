from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton

class TableWindow(QWidget):
    def __init__(self, show_events_table_object):
        super().__init__()

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

        self.refresh_button = QPushButton('Refresh')
        self.main_layout.addWidget(self.refresh_button)

        self.refresh_button.clicked.connect(self.update_table_data)

        self.update_table_data()

    def update_table_data(self):
        data = self.show_events_table_object.get_data_into_table()

        # Clear old data
        while (self.table_widget.rowCount() > 0):
            self.table_widget.removeRow(0)
        
        for row in range(len(data)):
            self.table_widget.insertRow(row)

            for col in range(len(data[row])):
                self.table_widget.setItem(row, col, QTableWidgetItem(data[row][col]))

        total_columns_width = 0
        for col in range(len(data[0])):
            self.table_widget.resizeColumnToContents(col)
            total_columns_width = total_columns_width + self.table_widget.columnWidth(col)

        # Set the window width to match the table's width and keep the height flexible
        self.resize(total_columns_width + 45, self.height())  # Set window width to table's width, keep current height
    
class Show_Events_Table_Window():
    def __init__(self, get_events_object):
        self.get_events_object = get_events_object

        # The rest should be provided by child classes
        self.get_events_into_list_function = None
        self.table_header = []
        self.window_title = ""

    def handle_event_to_display(self, event_key_str, parsed_event, events_list):
        return
    
    def get_row_data(self, event_item):
        return []
    
    def get_sort_value(self, item):
        return None
        
    def open_window_with_events(self):        
        self.table_window = TableWindow(self)
        self.table_window.show()
        self.table_window.setWindowTitle(self.window_title)
        self.table_window.activateWindow()
        self.table_window.raise_()

    def get_data_into_table(self):
        events_list = []

        self.get_events_into_list_function(self.handle_event_to_display, events_list)

        # Sort by the event time
        events_list.sort(key=self.get_sort_value)

        data_for_table_widget = []
        
        #data_for_table_widget.append(self.table_header)
        
        for event_item in events_list:
            row_data = self.get_row_data(event_item)

            data_for_table_widget.append(row_data)
        
        return(data_for_table_widget)

class Show_Snoozed_Events_Table_Window(Show_Events_Table_Window):
    def __init__(self, get_events_object):
        super().__init__(get_events_object)

        self.get_events_into_list_function = self.get_events_object.get_snoozed_events_into_list
        self.table_header = ["Google Account", "Calendar Name", "Event Name", "Snoozed Until"]
        self.window_title = "Snoozed Events"
        
    def handle_event_to_display(self, event_key_str, parsed_event, events_list):
        snoozed_item = [
            parsed_event['google_account'],
            parsed_event['cal name'],
            parsed_event['event_name'],
            parsed_event['event_wakeup_time']
        ]

        events_list.append(snoozed_item)

    def get_sort_value(self, item):
        return(item[3]) # The event wakeup time

    def get_row_data(self, event_item):
        row_data = [
            event_item[0],
            event_item[1],
            event_item[2],
            str(event_item[3])
        ]

        return row_data
    
class Show_Dismissed_Events_Table_Window(Show_Events_Table_Window):
    def __init__(self, get_events_object):
        super().__init__(get_events_object)

        self.get_events_into_list_function = self.get_events_object.get_dismissed_events_into_list
        self.table_header = ["Google Account", "Calendar Name", "Event Name", "End Time"]
        self.window_title = "Dismissed Events"
        
    def handle_event_to_display(self, event_key_str, parsed_event, events_list):
        dismissed_item = [
            parsed_event['google_account'],
            parsed_event['cal name'],
            parsed_event['event_name'],
            parsed_event['end_date']
        ]

        events_list.append(dismissed_item)

    def get_sort_value(self, item):
        return(item[3]) # End date
    
    def get_row_data(self, event_item):
        row_data = [
            event_item[0],
            event_item[1],
            event_item[2],
            str(event_item[3])
        ]

        return row_data  
    