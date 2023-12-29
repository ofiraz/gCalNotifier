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

from table_window import Show_Snoozed_Events_Table_Window, Show_Dismissed_Events_Table_Window

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

        self.reset_menu_item = QAction("Reset")
        self.reset_menu_item.triggered.connect(self.clear_dismissed_and_snoozed)
        self.system_tray_menu.addAction(self.reset_menu_item)

        # Add a Quit option to the menu.
        self.quit_menu_item = QAction("Quit")
        self.quit_menu_item.triggered.connect(self.quit_app)
        self.system_tray_menu.addAction(self.quit_menu_item)

        # Add the menu to the system_tray
        self.system_tray.setContextMenu(self.system_tray_menu)

    def display_snoozed_events(self):
        self.show_snoozed_events_window = Show_Snoozed_Events_Table_Window(self.get_events_object)

        self.show_snoozed_events_window.open_window_with_events()

    def display_dismissed_events(self):
        self.show_dismissed_events_window = Show_Dismissed_Events_Table_Window(self.get_events_object)

        self.show_dismissed_events_window.open_window_with_events()

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

