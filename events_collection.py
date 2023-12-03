import threading
import faulthandler
import sys
import time
from readerwriterlock import rwlock 

LOCK_TIMEOUT = 10

class Events_Collection:
    def __init__(self, p_logger, collection_name, use_rw_lock = False):
        self.c_logger = p_logger
        self.c_events = {}
        self.c_collection_name = collection_name
        self.c_add_cb = None
        self.c_remove_cb = None

        self.use_rw_lock = use_rw_lock
        if (self.use_rw_lock == False):
            self.c_lock = threading.Lock()

        else:
            self.c_rw_lock = rwlock.RWLockFair()

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

    def lock_collection(self, lock_for_read):       
        if (self.use_rw_lock == False):
            # Not a RW lock
            self.lock_with_timeout()
            return None
        
        # A RW lock
        if lock_for_read:
            r_lock = self.c_rw_lock.gen_rlock()
            r_lock.acquire()

            return r_lock
        
        # Lock for write
        w_lock = self.c_rw_lock.gen_wlock()
        w_lock.acquire()

        return w_lock
    
    def release_collection(self, lock):
        if (self.use_rw_lock == False):
            # Not a RW lock
            self.c_lock.release()

        else:
            # A RW lock
            lock.release()

    def is_event_in(self, event_key_str):
        lock = self.lock_collection(lock_for_read=True)

        return_value = event_key_str in self.c_events

        self.release_collection(lock)

        return return_value

    def add_event_safe(self, event_key_str, parsed_event):
        self.c_events[event_key_str] = parsed_event

        if (self.c_add_cb):
            self.c_add_cb()
        
    def add_event(self, event_key_str, parsed_event):
        lock = self.lock_collection(lock_for_read=False)

        self.add_event_safe(event_key_str, parsed_event)

        self.release_collection(lock)

    def remove_event_safe(self, event_key_str):
        del self.c_events[event_key_str]

        if (self.c_remove_cb):
            self.c_remove_cb()

    def remove_event(self, event_key_str):
        lock = self.lock_collection(lock_for_read=False)

        self.remove_event_safe(event_key_str)

        self.release_collection(lock)

    def pop(self):
        lock = self.lock_collection(lock_for_read=False)

        if (len(self.c_events) > 0):
            event_key_str = next(iter(self.c_events))
            parsed_event = self.c_events[event_key_str]
            self.remove_event_safe(event_key_str)

        else:
            # Empty collection
            event_key_str = None
            parsed_event = None

        self.release_collection(lock)

        return(event_key_str, parsed_event)

    def remove_events_based_on_condition(self, condition_function, additional_param = None):
        if (self.use_rw_lock == False):
            self.c_logger.critical("A critical programing error - this function should be used only for collections that are using a RW lock")

            faulthandler.dump_traceback()
            sys.exit()

        events_to_delete = []

        lock = self.lock_collection(lock_for_read=True)

        self.c_logger.debug("Before lock for " + self.c_collection_name)

        for event_key_str, parsed_event in self.c_events.items():
            if (condition_function(self.c_logger, event_key_str, parsed_event, additional_param)):
                # The condition was met, need remove the item
                events_to_delete.append(event_key_str)

        self.release_collection(lock)

        # Delete the events that were collected to be deleted
        while (len(events_to_delete) > 0):
            event_key_str = events_to_delete.pop()

            self.remove_event(event_key_str)

    def ro_traverse_on_events(self, cb_function, additional_param = None):
        if (self.use_rw_lock == False):
            self.c_logger.critical("A critical programing error - this function should be used only for collections that are using a RW lock")

            faulthandler.dump_traceback()
            sys.exit()

        lock = self.lock_collection(lock_for_read=True)

        for event_key_str, parsed_event in self.c_events.items():
            cb_function(self.c_logger, event_key_str, parsed_event, additional_param)

        self.release_collection(lock)

    def pop_from_another_collection_and_add_this_one(self, collection_to_pop_from):
        event_key_str, parsed_event = collection_to_pop_from.pop()

        if (event_key_str is not None):
            # Add the event to the presented events
            self.add_event(event_key_str, parsed_event)

        return(event_key_str, parsed_event) 