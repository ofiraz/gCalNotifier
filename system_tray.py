from PyQt5.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QAction
)

from PyQt5.QtGui import (
    QIcon
)

APP_ICON = 'icons8-calendar-64.png'

import sys

sys.path.insert(1, '/Users/ofir/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

from table_window import TableWindow

class snoozed_item_to_display:
    def __init__(self, parsed_event):
        self.google_account = parsed_event['google_account']
        self.cal_name = parsed_event['cal name']
        self.event_name = parsed_event['event_name']
        self.event_wakeup_time = parsed_event['event_wakeup_time']

def get_wakeup_time(snoozed_item):
    return snoozed_item.event_wakeup_time
        
class dismissed_item_to_display:
    def __init__(self, parsed_event):
        self.google_account = parsed_event['google_account']
        self.cal_name = parsed_event['cal name']
        self.event_name = parsed_event['event_name']
        self.event_end_time = parsed_event['end_date']

def get_end_time(snoozed_item):
    return snoozed_item.event_end_time

class app_system_tray:
    def __init__(self, globals, mdi_window, get_events_object):
        self.globals = globals
        self.mdi_window = mdi_window
        self.get_events_object = get_events_object

        # Create the icon
        icon = QIcon(APP_ICON)

        # Create the system_tray
        self.system_tray = QSystemTrayIcon()
        self.system_tray.setIcon(icon)
        self.system_tray.setVisible(True)

        # Create the system_tray_menu
        self.system_tray_menu = QMenu()

        self.display_snoozed_menu_item = QAction("Display snoozed events")
        self.display_snoozed_menu_item.triggered.connect(self.display_snoozed_events)
        self.system_tray_menu.addAction(self.display_snoozed_menu_item)

        self.display_dismissed_menu_item = QAction("Display dismissed events")
        self.display_dismissed_menu_item.triggered.connect(self.display_dismissed_events)
        self.system_tray_menu.addAction(self.display_dismissed_menu_item)

        self.logs_menu_item = QAction("Logs")
        self.logs_menu_item.triggered.connect(self.open_logs_window)
        self.system_tray_menu.addAction(self.logs_menu_item)

        self.reset_menu_item = QAction("Clear dismissed and snoozed")
        self.reset_menu_item.triggered.connect(self.clear_dismissed_and_snoozed)
        self.system_tray_menu.addAction(self.reset_menu_item)

        # Add a Quit option to the menu.
        self.quit_menu_item = QAction("Quit")
        self.quit_menu_item.triggered.connect(self.quit_app)
        self.system_tray_menu.addAction(self.quit_menu_item)

        # Add the menu to the system_tray
        self.system_tray.setContextMenu(self.system_tray_menu)

    def handle_snoozed_event_to_display(self, event_key_str, parsed_event, snoozed_list):
        snoozed_item = snoozed_item_to_display(parsed_event)

        snoozed_list.append(snoozed_item)

    def display_snoozed_events(self):
        snoozed_list = []

        self.get_events_object.get_snoozed_events_into_list(self.handle_snoozed_event_to_display, snoozed_list)

        # Sort by the event time
        snoozed_list.sort(key=get_wakeup_time)

        data_for_table_widget = []
        
        table_header = ["Google Account", "Calendar Name", "Event Name", "Snoozed Until"]
        data_for_table_widget.append(table_header)
        
        for snoozed_item in snoozed_list:
            row_data = [
                snoozed_item.google_account,
                snoozed_item.cal_name,
                snoozed_item.event_name,
                str(snoozed_item.event_wakeup_time)
            ]

            data_for_table_widget.append(row_data)
        
        self.table_window = TableWindow(data_for_table_widget)
        self.table_window.show()
        self.table_window.setWindowTitle("Snoozed Events")

    def handle_dismissed_event_to_display(self, event_key_str, parsed_event, dismissed_list):
        dismissed_item = dismissed_item_to_display(parsed_event)

        dismissed_list.append(dismissed_item)

    def display_dismissed_events(self):
        dismissed_list = []

        self.get_events_object.get_dismissed_events_into_list(self.handle_dismissed_event_to_display, dismissed_list)

        # Sort by the event time
        dismissed_list.sort(key=get_end_time)

        data_for_table_widget = []
        
        table_header = ["Google Account", "Calendar Name", "Event Name", "End Time"]
        data_for_table_widget.append(table_header)
        
        for dismissed_item in dismissed_list:
            row_data = [
                dismissed_item.google_account,
                dismissed_item.cal_name,
                dismissed_item.event_name,
                str(dismissed_item.event_end_time)
            ]

            data_for_table_widget.append(row_data)
        
        self.table_window = TableWindow(data_for_table_widget)
        self.table_window.show()
        self.table_window.setWindowTitle("Dismissed Events")

    def open_logs_window(self):       
        self.logs_window = LogWidget(warn_before_close=False)

        filename = "/Users/ofir/git/personal/gCalNotifier/EventsLog.log"
        comm = "tail -f " + filename

        self.logs_window.setCommand(comm)

        self.logs_window.setWindowTitle("Logs")

        self.logs_window.setFixedWidth(730 + 100)
        self.logs_window.setFixedHeight(650 + 100)

        self.logs_window.show()

    def clear_dismissed_and_snoozed(self):      
        self.globals.events_logger.info("Clearing dismissed and snoozed")

        self.globals.resest_is_needed()

    def quit_app(self):
        # Let the MDI window know that the app is closing
        self.mdi_window.need_to_close_the_window()

        # Close the app
        self.globals.app.quit()

