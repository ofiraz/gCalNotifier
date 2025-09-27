import threading
import sys

from config import app_config

from events_collection import Events_Collection

from logging_module import (
    init_logging,
    LOG_LEVEL_INFO,
)

from google_calendar_utilities import (
    get_calendar_list_for_account
)

from per_event_setting_db import Per_Event_Setting_DB

from PyQt5.QtWidgets import (
    QApplication
)

from PyQt5.QtCore import QEvent

# macOS Cocoa bridge
from Cocoa import NSApplication, NSMenu, NSMenuItem, NSObject
import objc

from table_window import Show_Snoozed_Events_Table_Window, Show_Dismissed_Events_Table_Window

sys.path.insert(1, '/Users/ofir_1/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

class DockMenuHandler(NSObject):
    """Objective-C class that owns the Dock menu actions"""

    def initWithApp_andWindow_(self, qt_app, globals):
        self = objc.super(DockMenuHandler, self).init()
        if self is None:
            return None
        self.qt_app = qt_app
        self.globals = globals
        return self

    # Display snoozed events
    @objc.IBAction
    def displaySnoozedEvents_(self, sender):
        self.globals.display_snoozed_events()

    # Display dismissed events
    @objc.IBAction
    def displayDismissedEvents_(self, sender):
        self.globals.display_dismissed_events()

    # Logs
    @objc.IBAction
    def displayLogs_(self, sender):
        self.globals.open_logs_window()

    @objc.IBAction
    def quitApp_(self, sender):
        print("👋 Quitting from Dock menu!")
        self.qt_app.quit()

    def build_menu(self):
        menu = NSMenu.alloc().init()

        # Display snoozed events
        display_snoozed_events_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Display snoozed events", "displaySnoozedEvents:", ""
        )
        display_snoozed_events_item.setTarget_(self)  # 🔑 explicitly set the target
        menu.addItem_(display_snoozed_events_item)

        # Display dismissed events
        display_dismissed_events_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Display dismissed events", "displayDismissedEvents:", ""
        )
        display_dismissed_events_item.setTarget_(self)  # 🔑 explicitly set the target
        menu.addItem_(display_dismissed_events_item)

        # Logs
        display_logs_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Logs", "displayLogs:", ""
        )
        display_logs_item.setTarget_(self)  # 🔑 explicitly set the target
        menu.addItem_(display_logs_item)

        # Separator
        menu.addItem_(NSMenuItem.separatorItem())

        # "Quit"
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", ""
        )
        quit_item.setTarget_(self)  # 🔑 explicitly set the target
        menu.addItem_(quit_item)

        return menu


def set_dock_menu(handler: DockMenuHandler):
    ns_app = NSApplication.sharedApplication()
    dock_menu = handler.build_menu()
    ns_app.setDockMenu_(dock_menu)

class MyApp(QApplication):
    def __init__(self, globals, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.globals = globals

    def event(self, e):
        if e.type() == QEvent.ApplicationActivate:
            # Show the window only when dock icon is clicked
            if (self.globals.multiple_events_window != None) and (not self.globals.multiple_events_window.isVisible()):
                self.globals.multiple_events_window.show_window()
        return super().event(e)

class app_globals:
    def __init__(self):
        self.config = app_config()

        self.logger = init_logging("gCalNotifier", "Main", self.config.log_level, LOG_LEVEL_INFO)
        self.events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)

        self.prep_google_accounts_and_calendars()

        self.events_to_present = Events_Collection(self.logger, "events_to_present")
        self.displayed_events = Events_Collection(self.logger, "displayed_events")
        self.events_to_dismiss = Events_Collection(self.logger, "events_to_dismiss")
        self.events_to_snooze = Events_Collection(self.logger, "events_to_snooze")

        self.per_event_setting_db = Per_Event_Setting_DB()

        self.app = MyApp(self, sys.argv)

        # Set the right click menu for the app from the dock icon
        self.handler = DockMenuHandler.alloc().initWithApp_andWindow_(self.app, self)
        set_dock_menu(self.handler)

        self.reset_needed = False
        self.reset_needed_lock = threading.Lock()

        self.multiple_events_window = None
        self.get_events_object = None

    def prep_google_accounts_and_calendars(self):
        for google_account in self.config.google_accounts:
            get_calendar_list_for_account(self.logger, google_account)

    def resest_is_needed(self):
        with self.reset_needed_lock:
            self.reset_needed = True

    def is_reset_needed(self):
        with self.reset_needed_lock:
            return(self.reset_needed)
        
    def reset_done(self):
        with self.reset_needed_lock:
            self.reset_needed = False

    def display_snoozed_events(self):
        self.show_snoozed_events_window = Show_Snoozed_Events_Table_Window(self, self.get_events_object)

        self.show_snoozed_events_window.open_window_with_events()

    def display_dismissed_events(self):
        self.show_dismissed_events_window = Show_Dismissed_Events_Table_Window(self, self.get_events_object)

        self.show_dismissed_events_window.open_window_with_events()

    def open_logs_window(self): 
        self.logs_window = LogWidget(warn_before_close=False)

        filename = "/Users/ofir_1/git/personal/gCalNotifier/EventsLog.log"
        comm = "tail -n 1000 -f " + filename

        self.logs_window.setCommand(comm)

        self.logs_window.setWindowTitle("Logs")

        self.logs_window.setFixedWidth(730 + 100)
        self.logs_window.setFixedHeight(650 + 100)

        self.logs_window.show()
        self.logs_window.activateWindow()
        self.logs_window.raise_()
