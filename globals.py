import threading
import sys

from config import app_config

from events_collection import Events_Collection

from logging_module import (
    init_logging,
    LOG_LEVEL_INFO,
)

from PyQt5.QtWidgets import (
    QApplication
)

class app_globals:
    def __init__(self):
        self.config = app_config()

        self.logger = init_logging("gCalNotifier", "Main", self.config.log_level, LOG_LEVEL_INFO)
        self.events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)

        self.events_to_present = Events_Collection(self.logger, "events_to_present")
        self.displayed_events = Events_Collection(self.logger, "displayed_events")
        self.events_to_dismiss = Events_Collection(self.logger, "events_to_dismiss")
        self.events_to_snooze = Events_Collection(self.logger, "events_to_snooze")

        self.app = QApplication(sys.argv)

        self.reset_needed = False
        self.reset_needed_lock = threading.Lock()

    def resest_is_needed(self):
        with self.reset_needed_lock:
            self.reset_needed = True

    def is_reset_needed(self):
        with self.reset_needed_lock:
            return(self.reset_needed)
        
    def reset_done(self):
        with self.reset_needed_lock:
            self.reset_needed = False


