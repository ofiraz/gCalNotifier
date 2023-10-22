from __future__ import print_function
import sys

from PyQt5.QtWidgets import (
    QApplication, QDesktopWidget, QTextBrowser, QAction, QTextEdit
)

from PyQt5 import QtGui
import logging

import datetime
import pytz

from logging_module import (
    init_logging,
    LOG_LEVEL_CRITICAL,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_INFO,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_NOTSET
)

from google_calendar_utilities import (
    get_calendar_list_for_account
)

from multiprocessing import Process, Pipe

import json
import re

from json_utils import nice_json

from events_collection import Events_Collection

from events_mdi_window import MDIWindow

from app_events_collections import App_Events_Collections

from get_events_thread import start_getting_events_to_display_main_loop_thread

def init_global_objects(log_level, refresh_frequency):
    global g_logger
    global g_events_logger
    global g_app
    global g_mdi_window
    global g_app_events_collections

    g_logger = init_logging("gCalNotifier", "Main", log_level, LOG_LEVEL_INFO)
    g_events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)

    g_app = QApplication(sys.argv)
    g_mdi_window = MDIWindow(g_logger, g_events_logger, refresh_frequency)

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

    # Set the MDI window size to be a little more than the event window size
    g_mdi_window.setFixedWidth(730 + 100)
    g_mdi_window.setFixedHeight(650 + 100)

    g_mdi_window.show()

    # Show the window on the main monitor
    monitor = QDesktopWidget().screenGeometry(0)
    g_mdi_window.move(monitor.left(), monitor.top())

    g_app.setWindowIcon(QtGui.QIcon('icons8-calendar-64.png'))
    g_app.exec_()