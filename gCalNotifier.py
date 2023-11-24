import sys
import logging

from PyQt5.QtGui import (
    QIcon
)

from PyQt5.QtWidgets import (
    QApplication, 
    QDesktopWidget,
    QSystemTrayIcon,
    QMenu,
    QAction
)

from logging_module import (
    init_logging,
    LOG_LEVEL_INFO,
)

from google_calendar_utilities import (
    get_calendar_list_for_account
)

import json

from events_mdi_window import MDIWindow

from get_events_thread import start_getting_events_to_display_main_loop_thread

sys.path.insert(1, '/Users/ofir/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

from app_events_collections import App_Events_Collections

from globals import app_globals
from config import app_config

APP_ICON = 'icons8-calendar-64.png'

def open_logs_window():
    global logs_window
    
    logs_window = LogWidget(warn_before_close=False)

    filename = "/Users/ofir/git/personal/gCalNotifier/EventsLog.log"
    comm = "tail -f " + filename

    logs_window.setCommand(comm)

    logs_window.setWindowTitle("Logs")

    logs_window.setFixedWidth(730 + 100)
    logs_window.setFixedHeight(650 + 100)

    logs_window.show()

def clear_dismissed_and_snoozed():
    global g_events_logger
    
    g_events_logger.info("Clearing dismissed and snoozed")

    g_app_events_collections.resest_is_needed()

def quit_app():
    global g_app
    global g_mdi_window

    # Let the MDI window know that the app is closing
    g_mdi_window.need_to_close_the_window()

    # Close the app
    g_app.quit()

def init_system_tray(app):
    global system_tray
    global system_tray_menu
    global logs_menu_item
    global reset_menu_item
    global quit_menu_item
    
    #g_app.setQuitOnLastWindowClosed(False)

    # Create the icon
    icon = QIcon(APP_ICON)

    # Create the system_tray
    system_tray = QSystemTrayIcon()
    system_tray.setIcon(icon)
    system_tray.setVisible(True)

    # Create the system_tray_menu
    system_tray_menu = QMenu()

    logs_menu_item = QAction("Logs")
    logs_menu_item.triggered.connect(open_logs_window)
    system_tray_menu.addAction(logs_menu_item)

    reset_menu_item = QAction("Clear dismissed and snoozed")
    reset_menu_item.triggered.connect(clear_dismissed_and_snoozed)
    system_tray_menu.addAction(reset_menu_item)

    # Add a Quit option to the menu.
    quit_menu_item = QAction("Quit")
    quit_menu_item.triggered.connect(quit_app)
    system_tray_menu.addAction(quit_menu_item)

    # Add the menu to the system_tray
    system_tray.setContextMenu(system_tray_menu)

def init_global_objects():
    global g_globals
    global g_events_logger
    global g_app
    global g_mdi_window
    global g_app_events_collections

    g_events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)

    g_app = QApplication(sys.argv)

    g_app_events_collections = App_Events_Collections(g_globals.logger)

    g_mdi_window = MDIWindow(g_globals.logger, g_events_logger, g_app, g_globals.config.refresh_frequency, g_app_events_collections)

def prep_google_accounts_and_calendars(logger):
    global g_globals

    for google_account in g_globals.config.google_accounts:
        get_calendar_list_for_account(logger, google_account)

# Main
if __name__ == "__main__":
    #load_config()
    g_globals = app_globals()

    init_global_objects()

    prep_google_accounts_and_calendars(g_globals.logger)

    # Start a thread to look for events to display
    start_getting_events_to_display_main_loop_thread(g_events_logger, g_globals, g_app_events_collections)

    init_system_tray(g_app)

    # Set the MDI window size to be a little more than the event window size
    g_mdi_window.setFixedWidth(730 + 100)
    g_mdi_window.setFixedHeight(650 + 100)

    g_mdi_window.show()

    # Show the window on the main monitor
    monitor = QDesktopWidget().screenGeometry(0)
    g_mdi_window.move(monitor.left(), monitor.top())

    g_app.exec_()