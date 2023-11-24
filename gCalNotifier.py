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
    global g_globals
    
    g_globals.events_logger.info("Clearing dismissed and snoozed")

    g_globals.resest_is_needed()

def quit_app():
    global g_globals
    global g_mdi_window

    # Let the MDI window know that the app is closing
    g_mdi_window.need_to_close_the_window()

    # Close the app
    g_globals.app.quit()

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

def create_and_show_mdi_window():
    global g_globals
    global g_mdi_window

    g_mdi_window = MDIWindow(g_globals)

    # Set the MDI window size to be a little more than the event window size
    g_mdi_window.setFixedWidth(730 + 100)
    g_mdi_window.setFixedHeight(650 + 100)

    # Show the window on the main monitor
    monitor = QDesktopWidget().screenGeometry(0)
    g_mdi_window.move(monitor.left(), monitor.top())

    g_mdi_window.show()

def prep_google_accounts_and_calendars():
    global g_globals

    for google_account in g_globals.config.google_accounts:
        get_calendar_list_for_account(g_globals.logger, google_account)

# Main
if __name__ == "__main__":
    g_globals = app_globals()

    prep_google_accounts_and_calendars()

    # Start a thread to look for events to display
    start_getting_events_to_display_main_loop_thread(g_globals)

    init_system_tray(g_globals.app)

    create_and_show_mdi_window()

    g_globals.app.exec_()