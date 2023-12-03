import threading
import faulthandler
import sys
import time

LOCK_TIMEOUT = 10

class Events_Collection:
    def __init__(self, p_logger, collection_name):
        self.c_logger = p_logger
        self.c_events = {}
        self.c_lock = threading.Lock()
        self.c_collection_name = collection_name
        self.c_add_cb = None
        self.c_remove_cb = None

    def set_add_cb(self, add_cb):
        self.c_add_cb = add_cb

    def set_remove_cb(self, remove_cb):
        self.c_remove_cb = remove_cb

    # Based on the discussion here https://stackoverflow.com/questions/16740104/python-lock-with-statement-and-timeout
    def lock_with_timeout(self):
        time_before_lock = time.time()
        res = self.c_lock.acquire(timeout=LOCK_TIMEOUT)
        time_after_lock = time.time()
        
        if (res):
            # The lock was aquired
            time_diff = time_after_lock - time_before_lock
            if (time_diff > 1):
                self.c_logger.info("The lock for " + self.c_collection_name + " was more than 1 second - " + str(time_diff))

            return
        
        else:
            # Failed to aquire the lock - crash the app with a proper stack trace
            self.c_logger.critical("Failed to aquire a lock")

            faulthandler.dump_traceback()
            sys.exit()

    def is_event_in(self, event_key_str):
        self.lock_with_timeout()

        return_value = event_key_str in self.c_events

        self.c_lock.release()

        return return_value

    def add_event_safe(self, event_key_str, parsed_event):
        self.c_events[event_key_str] = parsed_event

        if (self.c_add_cb):
            self.c_add_cb()
        
    def add_event(self, event_key_str, parsed_event):
        self.lock_with_timeout()

        self.add_event_safe(event_key_str, parsed_event)

        self.c_lock.release()

    def remove_event_safe(self, event_key_str):
        del self.c_events[event_key_str]

        if (self.c_remove_cb):
            self.c_remove_cb()

    def remove_event(self, event_key_str):
        self.lock_with_timeout()

        self.remove_event_safe(event_key_str)

        self.c_lock.release()

    def pop(self):
        self.lock_with_timeout()

        if (len(self.c_events) > 0):
            event_key_str = next(iter(self.c_events))
            parsed_event = self.c_events[event_key_str]
            self.remove_event_safe(event_key_str)

        else:
            # Empty collection
            event_key_str = None
            parsed_event = None

        self.c_lock.release()

        return(event_key_str, parsed_event)

    def remove_events_based_on_condition(self, condition_function, additional_param = None):
        events_to_delete = []

        self.lock_with_timeout()

        self.c_logger.debug("Before lock for " + self.c_collection_name)

        for event_key_str, parsed_event in self.c_events.items():
            if (condition_function(self.c_logger, event_key_str, parsed_event, additional_param)):
                # The condition was met, need remove the item
                events_to_delete.append(event_key_str)

        # Delete the events that were collected to be deleted
        while (len(events_to_delete) > 0):
            event_key_str = events_to_delete.pop()
            self.remove_event_safe(event_key_str)

        self.c_lock.release()

    def pop_from_another_collection_and_add_this_one(self, collection_to_pop_from):
        event_key_str, parsed_event = collection_to_pop_from.pop()

        if (event_key_str is not None):
            # Add the event to the presented events
            self.add_event(event_key_str, parsed_event)

        return(event_key_str, parsed_event) 