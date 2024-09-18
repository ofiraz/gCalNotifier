# Following https://www.pythonguis.com/tutorials/qtableview-modelviews-numpy-pandas/

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QTableView, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QTextBrowser
from PyQt5.QtCore import Qt

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

class TableWindow(QWidget):
    def __init__(self, show_events_table_object, use_table_view = True):
        super().__init__()

        self.show_events_table_object = show_events_table_object
        self.use_table_view = use_table_view

        if (use_table_view):
            self.table = QTableView(self)

            self.refresh_button = QPushButton('Refresh',self)

            self.refresh_button.move(0, 0)

            self.refresh_button.clicked.connect(self.update_table_data)

        else:
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

    def resize_table_columns_to_contents(self):
        header = self.table.horizontalHeader()

        total_column_width = 0

        for col in range(self.model.columnCount(0)):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
            total_column_width += self.table.columnWidth(col)

        return(total_column_width)
    
    def update_table_data(self):
        data = self.show_events_table_object.get_data_into_table()

        if (self.use_table_view):
            self.model = TableModel(data)
            self.table.setModel(self.model)

            total_column_width = self.resize_table_columns_to_contents()

            self.setFixedWidth(total_column_width + 50)

            self.setCentralWidget(self.table)

        else:
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
        self.table_window = TableWindow(self, use_table_view=False)
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
    