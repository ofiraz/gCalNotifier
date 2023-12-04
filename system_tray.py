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
        
class app_system_tray:
    def __init__(self, globals, mdi_window):
        self.globals = globals
        self.mdi_window = mdi_window

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

        self.globals.snoozed_events.ro_traverse_on_events(self.handle_snoozed_event_to_display, additional_param = snoozed_list)

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

