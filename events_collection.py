import threading

class Events_Collection:
    def __init__(self, p_logger, collection_name, add_cb = None, remove_cb = None):
        self.c_logger = p_logger
        self.c_events = {}
        self.c_lock = threading.Lock()
        self.c_collection_name = collection_name
        self.c_add_cb = add_cb
        self.c_remove_cb = remove_cb

    def is_event_in(self, event_key_str):
        self.c_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            self.c_logger.debug("After lock for " + self.c_collection_name)

            return(event_key_str in self.c_events)       

    def add_event_safe(self, event_key_str, parsed_event):
        self.c_events[event_key_str] = parsed_event

        if (self.c_add_cb):
            self.c_add_cb()
        
    def add_event(self, event_key_str, parsed_event):
        self.c_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            self.add_event_safe(event_key_str, parsed_event)

        self.c_logger.debug("After lock for " + self.c_collection_name)


    def remove_event_safe(self, event_key_str):
        del self.c_events[event_key_str]

        if (self.c_remove_cb):
            self.c_remove_cb()

    def remove_event(self, event_key_str):
        self.c_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            self.remove_event_safe(event_key_str)

        self.c_logger.debug("After lock for " + self.c_collection_name)

    def pop(self):
        self.c_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            if (len(self.c_events) > 0):
                event_key_str = next(iter(self.c_events))
                parsed_event = self.c_events[event_key_str]
                self.remove_event_safe(event_key_str)

                self.c_logger.debug("After lock for " + self.c_collection_name)

                return(event_key_str, parsed_event)
            else:
                # Empty collection
                self.c_logger.debug("After lock for " + self.c_collection_name)

                return(None, None)

    def remove_events_based_on_condition(self, condition_function):
        events_to_delete = []

        self.c_logger.debug("Before lock for " + self.c_collection_name)

        with self.c_lock:
            for event_key_str, parsed_event in self.c_events.items():
                if (condition_function(event_key_str, parsed_event)):
                    # The condition was met, need remove the item
                    events_to_delete.append(event_key_str)

            # Delete the events that were collected to be deleted
            while (len(events_to_delete) > 0):
                event_key_str = events_to_delete.pop()
                self.remove_event_safe(event_key_str)

        self.c_logger.debug("After lock for " + self.c_collection_name)
