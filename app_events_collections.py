from events_collection import Events_Collection

class App_Events_Collections:
    def set_events_to_present(self, events_to_present):
        self.events_to_present = events_to_present

    def set_dismissed_events(self, dismissed_events):
        self.dismissed_events = dismissed_events

    def set_snoozed_events(self, snoozed_events):
        self.snoozed_events = snoozed_events

    def set_displayed_events(self, displayed_events):
        self.displayed_events = displayed_events