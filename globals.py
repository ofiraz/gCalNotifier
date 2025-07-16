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

        self.app = QApplication(sys.argv)

        self.reset_needed = False
        self.reset_needed_lock = threading.Lock()

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


