class ParsedEvent:
    def __init__(
            self,
            google_account,
            event_key_str,
            raw_event,
            event_name,
            cal_name):
        self.google_account = google_account
        self.event_key_str = event_key_str
        self.raw_event = raw_event
        self.event_name = event_name
        self.cal_name = cal_name
        self.changed = False
        self.deleted = False
        self.is_dismissed = False
        self.is_snoozed = False
        self.is_unsnoozed_or_undismissed = False
        self.need_to_record_meeting = False
        self.close_event_window_when_event_has_ended = False
        self.description = ''
