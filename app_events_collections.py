from events_collection import Events_Collection

class App_Events_Collections:
    def __init__(self, logger):
        self.events_to_present = Events_Collection(logger, self, "events_to_present")
        self.dismissed_events = Events_Collection(logger, self, "dismissed_events")
        self.snoozed_events = Events_Collection(logger, self, "snoozed_events")
        self.displayed_events = Events_Collection(logger, self, "displayed_events")
