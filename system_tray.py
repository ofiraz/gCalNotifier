from PyQt5.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QAction,
    QMainWindow,
    QDesktopWidget
)

from PyQt5 import QtCore

from set_icon_with_number import set_icon_with_number

import sys

sys.path.insert(1, '/Users/ofir/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

from table_window import Show_Snoozed_Events_Table_Window, Show_Dismissed_Events_Table_Window

from MultipleEventsWindow import *

class app_system_tray(QMainWindow):
    def __init__(self, globals, get_events_object):
        super(app_system_tray, self).__init__()

        self.globals = globals
        self.globals.app_system_tray = self
        self.get_events_object = get_events_object
        self.c_num_of_displayed_events = 0

        self.multiple_events_windows = None

        # Create the system_tray
        self.system_tray = QSystemTrayIcon(self)

        # Set the app icon
        self.update_app_icon()

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

        self.reset_menu_item = QAction("Reset")
        self.reset_menu_item.triggered.connect(self.clear_dismissed_and_snoozed)
        self.system_tray_menu.addAction(self.reset_menu_item)

        # Add a Quit option to the menu.
        self.quit_menu_item = QAction("Quit")
        self.quit_menu_item.triggered.connect(self.quit_app)
        self.system_tray_menu.addAction(self.quit_menu_item)

        # Add the menu to the system_tray
        self.system_tray.setContextMenu(self.system_tray_menu)

        # Prevent the closing of the system tray when the last event window closes
        self.globals.app.setQuitOnLastWindowClosed(False) 

        self.globals.displayed_events.set_add_cb(self.add_event_to_display_cb)
        self.globals.displayed_events.set_remove_cb(self.remove_event_from_display_cb)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.present_relevant_events_in_windows) 
        self.timer.start(int(self.globals.config.refresh_frequency/2) * 1000)

        self.system_tray.show()

    def add_event_to_display_cb(self, parsed_event):
        self.c_num_of_displayed_events = self.c_num_of_displayed_events + 1

    def remove_event_from_display_cb(self, parse_event):
        self.c_num_of_displayed_events = self.c_num_of_displayed_events - 1

        self.update_app_icon()

    def show_window(self, parsed_event):
        if (self.multiple_events_windows == None):
            self.multiple_events_windows = MultipleEventsTable(self.globals, parsed_event)

        else:
            self.multiple_events_windows.add_event(parsed_event)

        self.multiple_events_windows.setFixedWidth(730)

        # Show the window on the main monitor
        monitor = QDesktopWidget().screenGeometry(0)
        self.multiple_events_windows.move(0,0)

        self.multiple_events_windows.show()
        #self.multiple_events_windows.activateWindow()
        #self.multiple_events_windows.raise_()      

        self.globals.events_logger.debug("Displaying event:" + parsed_event.event_name)

    def present_relevant_events(self):
        at_list_one_event_presented = False
        while True:
            event_key_str, parsed_event = self.globals.events_to_present.pop()
            if (event_key_str == None):
                # No more entries to present
                break
            
            if(self.globals.displayed_events.is_event_in(event_key_str)):
                # The event is already displayed with older data, mark it so the new data will be reflected for the event
                if (self.multiple_events_windows):
                    self.multiple_events_windows.update_event(parsed_event)

            else: # A totaly new event
                # Add the new event to the displayed events list    
                at_list_one_event_presented = True       
                self.globals.displayed_events.add_event(event_key_str, parsed_event)
                self.show_window(parsed_event)

        if (at_list_one_event_presented):
            self.update_app_icon()

    def present_relevant_events_in_windows(self):
        self.globals.logger.debug("Presenting relevant events")

        self.present_relevant_events()

        self.timer.start(int(self.globals.config.refresh_frequency/2) * 1000)

    def display_snoozed_events(self):
        self.show_snoozed_events_window = Show_Snoozed_Events_Table_Window(self.globals, self.get_events_object)

        self.show_snoozed_events_window.open_window_with_events()

    def display_dismissed_events(self):
        self.show_dismissed_events_window = Show_Dismissed_Events_Table_Window(self.globals, self.get_events_object)

        self.show_dismissed_events_window.open_window_with_events()

    def open_logs_window(self):       
        self.logs_window = LogWidget(warn_before_close=False)

        filename = "/Users/ofir/git/personal/gCalNotifier/EventsLog.log"
        comm = "tail -n 1000 -f " + filename

        self.logs_window.setCommand(comm)

        self.logs_window.setWindowTitle("Logs")

        self.logs_window.setFixedWidth(730 + 100)
        self.logs_window.setFixedHeight(650 + 100)

        self.logs_window.show()
        self.logs_window.activateWindow()
        self.logs_window.raise_()

    def clear_dismissed_and_snoozed(self):      
        self.globals.events_logger.debug("Clearing dismissed and snoozed")

        self.globals.resest_is_needed()

    def quit_app(self):
        # Close the app
        self.globals.app.quit()

    def pop_up_nofitication(self, message):
        self.system_tray.showMessage(
            "gCalNotifier",
            message,
            QSystemTrayIcon.Information,
            0
        )

    def update_app_icon(self):
        set_icon_with_number(self.globals.app, self.c_num_of_displayed_events, sys_tray=self.system_tray, show_number_in_icon = True)
