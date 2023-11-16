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

APP_ICON = 'icons8-calendar-64.png'

def open_logs_window():
    global logs_window
    
    logs_window = LogWidget(warn_before_close=False)

    filename = "/Users/ofir/git/personal/gCalNotifier/EventsLog.log"
    comm = "tail -f " + filename

    logs_window.setCommand(comm)

    logs_window.setWindowTitle("Logs")
    logs_window.show()
    
def init_system_tray(app):
    global system_tray
    global system_tray_menu
    global logs_menu_item
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

    # Add a Quit option to the menu.
    quit_menu_item = QAction("Quit")
    quit_menu_item.triggered.connect(app.quit)
    system_tray_menu.addAction(quit_menu_item)

    # Add the menu to the system_tray
    system_tray.setContextMenu(system_tray_menu)

def init_global_objects(log_level, refresh_frequency):
    global g_logger
    global g_events_logger
    global g_app
    global g_mdi_window
    global g_app_events_collections

    g_logger = init_logging("gCalNotifier", "Main", log_level, LOG_LEVEL_INFO)
    g_events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)

    g_app = QApplication(sys.argv)

    g_mdi_window = MDIWindow(g_logger, g_events_logger, g_app, refresh_frequency)

    g_app_events_collections = g_mdi_window.app_events_collections

def load_config():
    global g_google_accounts
    global g_log_level
    global g_refresh_frequency

    with open("gCalNotifier.json") as f:
        l_config = json.load(f)

    g_google_accounts = l_config.get("google accounts")
    if (not g_google_accounts):
        print("No \'google accounts\' defined in the config file")
        sys.exit()

    for google_account in g_google_accounts:
        account_name = google_account.get("account name")
        if (not account_name):
            print ("No \'account name\' defined for a google account entry")
            sys.exit()
 
    g_log_level = l_config.get("log level")
    if (not g_log_level):
        g_log_level = logging.INFO

    g_refresh_frequency = l_config.get("refresh frequency")
    if (not g_refresh_frequency):
        g_refresh_frequency = 30

def prep_google_accounts_and_calendars(logger, google_accounts):
    for google_account in google_accounts:
        get_calendar_list_for_account(logger, google_account)

# Main
if __name__ == "__main__":
    load_config()

    init_global_objects(g_log_level, g_refresh_frequency)

    prep_google_accounts_and_calendars(g_logger, g_google_accounts)

    # Start a thread to look for events to display
    start_getting_events_to_display_main_loop_thread(g_logger, g_refresh_frequency, g_google_accounts, g_app_events_collections)

    init_system_tray(g_app)

    # Set the MDI window size to be a little more than the event window size
    g_mdi_window.setFixedWidth(730 + 100)
    g_mdi_window.setFixedHeight(650 + 100)

    g_mdi_window.show()

    # Show the window on the main monitor
    monitor = QDesktopWidget().screenGeometry(0)
    g_mdi_window.move(monitor.left(), monitor.top())

    g_app.exec_()