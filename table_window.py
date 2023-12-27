# Following https://www.pythonguis.com/tutorials/qtableview-modelviews-numpy-pandas/

from PyQt5 import QtCore, QtWidgets
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

class TableWindow(QtWidgets.QMainWindow):
    def __init__(self, data):
        super().__init__()

        self.table = QtWidgets.QTableView()

        self.model = TableModel(data)
        self.table.setModel(self.model)

        total_column_width = self.resize_table_columns_to_contents()

        self.setFixedWidth(total_column_width + 50)

        self.setCentralWidget(self.table)

    def resize_table_columns_to_contents(self):
        header = self.table.horizontalHeader()

        total_column_width = 0

        for col in range(self.model.columnCount(0)):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
            total_column_width += self.table.columnWidth(col)

        return(total_column_width)
    
class Show_Events_Table_Window():
    def __init__(self, get_events_object):
        self.get_events_object = get_events_object

        # The rest should be provided by child classes
        self.get_events_into_list_function = None
        self.handle_event_to_display_function = None
        self.sort_key_function = None
        self.table_header = []
        self.window_title = ""

    def get_row_data(self, event_item):
        return []
        
    def open_window_with_events(self):
        events_list = []

        self.get_events_into_list_function(self.handle_event_to_display_function, events_list)

        # Sort by the event time
        events_list.sort(key=self.sort_key_function)

        data_for_table_widget = []
        
        data_for_table_widget.append(self.table_header)
        
        for event_item in events_list:
            row_data = self.get_row_data(event_item)

            data_for_table_widget.append(row_data)
        
        self.table_window = TableWindow(data_for_table_widget)
        self.table_window.show()
        self.table_window.setWindowTitle(self.window_title)

class snoozed_item_to_display:
    def __init__(self, parsed_event):
        self.google_account = parsed_event['google_account']
        self.cal_name = parsed_event['cal name']
        self.event_name = parsed_event['event_name']
        self.event_wakeup_time = parsed_event['event_wakeup_time']

def get_wakeup_time(snoozed_item):
    return snoozed_item.event_wakeup_time
        
class Show_Snoozed_Events_Table_Window(Show_Events_Table_Window):
    def __init__(self, get_events_object):
        super().__init__(get_events_object)

        self.get_events_into_list_function = self.get_events_object.get_snoozed_events_into_list
        self.handle_event_to_display_function = self.handle_snoozed_event_to_display
        self.sort_key_function = get_wakeup_time
        self.table_header = ["Google Account", "Calendar Name", "Event Name", "Snoozed Until"]
        self.window_title = "Snoozed Events"
        
    def handle_snoozed_event_to_display(self, event_key_str, parsed_event, snoozed_list):
        snoozed_item = snoozed_item_to_display(parsed_event)

        snoozed_list.append(snoozed_item)

    def get_row_data(self, event_item):
        row_data = [
            event_item.google_account,
            event_item.cal_name,
            event_item.event_name,
            str(event_item.event_wakeup_time)
        ]

        return row_data