from events_collection import Events_Collection
import threading


class App_Events_Collections:
    def __init__(self, logger):
        self.events_to_present = Events_Collection(logger, self, "events_to_present")
        self.dismissed_events = Events_Collection(logger, self, "dismissed_events")
        self.snoozed_events = Events_Collection(logger, self, "snoozed_events")
        self.displayed_events = Events_Collection(logger, self, "displayed_events")
        self.events_to_dismiss = Events_Collection(logger, self, "events_to_dismiss")
        self.events_to_snooze = Events_Collection(logger, self, "events_to_snooze")
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
