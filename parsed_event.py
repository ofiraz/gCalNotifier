class ParsedEvent:
    def __init__(
            self,
            google_account,
            event_key_str,
            raw_event,
            cal_name):
        self.google_account = google_account
        self.event_key_str = event_key_str
        self.raw_event = raw_event
        self.cal_name = cal_name

        self.event_name = raw_event.get('summary', '(No title)')

        self.changed = False
        self.deleted = False
        self.is_dismissed = False
        self.is_snoozed = False
        self.is_unsnoozed_or_undismissed = False
        self.need_to_record_meeting = False
        self.close_event_window_when_event_has_ended = False
        self.description = ''
        self.default_snooze = False
        self.start_date = ''
        self.end_date = ''
        self.event_wakeup_time = ''
        self.has_self_declined = False
        self.no_popup_reminder = False
        self.all_day_event = False
        self.minutes_before_to_notify = ''
        self.html_link = ''
        self.event_location = ''
        self.video_link = ''
        self.num_of_attendees = 0
