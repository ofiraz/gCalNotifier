from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QRadioButton

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

        # Radio buttons to select wheter to show the non automatic or automatic snoosed/dismissed events
        self.radio_buttons_h_layout = QHBoxLayout()
        self.main_layout.addLayout(self.radio_buttons_h_layout)

        self.radio_non_automtic = QRadioButton("Non automatic")
        self.radio_buttons_h_layout.addWidget(self.radio_non_automtic)
        self.radio_non_automtic.setChecked(True)
        self.radio_non_automtic.toggled.connect(self.on_rb_non_automatic_selected)

        self.radio_automtic = QRadioButton("Automatic")
        self.radio_buttons_h_layout.addWidget(self.radio_automtic)
        self.radio_automtic.toggled.connect(self.on_rb_automatic_selected)
        
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

            self.globals.logger.debug("Act on event " + str(selected_row) + " with key " + event_key_str)

            self.show_events_table_object.act_on_event_cb(event_key_str)

            self.table_widget.removeRow(selected_row)
            del self.data[selected_row]
       
        else:
            self.globals.logger.debug("No row selected")

    def update_table_data(self):
        self.data = self.show_events_table_object.get_data_into_table(show_non_automatic = self.radio_non_automtic.isChecked())

        # Clear old data
        while (self.table_widget.rowCount() > 0):
            self.table_widget.removeRow(0)
        
        if (len(self.data) > 0):
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

    def on_rb_non_automatic_selected(self):
        if self.radio_non_automtic.isChecked():
            self.update_table_data()
    
    def on_rb_automatic_selected(self):
        if self.radio_automtic.isChecked():
            self.update_table_data()
    
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

        self.show_non_automatic = True

    def get_event_data_item_into_structure(self, parsed_event):
        return
    
    def handle_event_to_display(self, parsed_event, events_list):
        if ((self.show_non_automatic and not parsed_event.automatically_snoozed_dismissed)
            or (not self.show_non_automatic and parsed_event.automatically_snoozed_dismissed)):
            item = self.get_event_data_item_into_structure(parsed_event)

            events_list.append(item)
    
    def get_sort_value(self, item):
        return None
        
    def open_window_with_events(self):        
        self.table_window = TableWindow(self.globals, self)
        self.table_window.show()
        self.table_window.setWindowTitle(self.window_title)
        self.table_window.activateWindow()
        self.table_window.raise_()

    def get_data_into_table(self, show_non_automatic):
        events_list = []

        self.show_non_automatic = show_non_automatic

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

        
    def get_event_data_item_into_structure(self, parsed_event):
        snoozed_item = [
            parsed_event.event_key_str,
            parsed_event.google_account,
            parsed_event.cal_name,
            parsed_event.event_name,
            parsed_event.event_wakeup_time
        ]

        return(snoozed_item)

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

        
    def get_event_data_item_into_structure(self, parsed_event):
        dismissed_item = [
            parsed_event.event_key_str,
            parsed_event.google_account,
            parsed_event.cal_name,
            parsed_event.event_name,
            parsed_event.end_date
        ]

        return(dismissed_item)

    def get_sort_value(self, item):
        return(item[4]) # End date
