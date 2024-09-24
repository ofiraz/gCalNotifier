import datetime

from json_utils import nice_json

from datetime_utils import get_now_datetime

from deepdiff import DeepDiff

import re

def has_self_declined(raw_event):
    # Check if the event was not declined by the current user
    if(raw_event.get('attendees')):
        # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
        for attendee in raw_event['attendees']:
            if(attendee.get('self') and attendee['self'] == True and attendee.get('responseStatus') and attendee['responseStatus'] == 'declined'):
                # The user declined the meeting. No need to display it
                return(True)

    # The event was not declined by the current user
    return(False)

NO_POPUP_REMINDER = -1

def get_max_reminder_in_minutes(raw_event):
    max_minutes_before = NO_POPUP_REMINDER

    if (raw_event['reminders'].get('useDefault') == True):
        max_minutes_before = 15
    else:
        override_rule = raw_event['reminders'].get('overrides')
        if (override_rule):
            for override_entry in override_rule:
                if (override_entry['method'] == "popup"):
                    if int(override_entry['minutes']) > max_minutes_before:
                        max_minutes_before = int(override_entry['minutes'])

    return(max_minutes_before)

video_links_reg_exs = [
    "(https://[a-zA-Z0-9-]*[\.]*zoom\.us/j/[a-zA-Z0-9-_\.&?=/]*)", # Zoom
    "Click here to join the meeting<(https://teams.microsoft.com/l/meetup-join/.*)>", # Teams  
    "(https://teams.microsoft.com/l/meetup-join/[a-zA-Z0-9-%_./?=]*)", # Teams 
    "(https://gov.teams.microsoft.us/l/meetup-join/[a-zA-Z0-9-%_./?=]*)", # GOV Teams 
    "[<>](https://[a-zA-Z0-9-]*\.webex\.com/[a-zA-Z0-9-]*/j\.php\?MTID=[a-zA-Z0-9-]*)[<>]", # Webex
    "(https://[a-zA-Z0-9-]*\.webex\.com/meet/[a-zA-Z0-9-\.]*)", # https://rbcteams.webex.com/meet/julian.sequeira
    "(https://[a-zA-Z0-9-]*\.webex\.com/join/[a-zA-Z0-9-\.]*)", # https://rbcteams.webex.com/join/j
    "(https://chime.aws/[0-9]*)", # AWS Chimes
    "(https://meet.google.com/[a-z-]+)", # Google Meet
    "(https://app.gather.town/app/[a-zA-Z0-9-%_./?=]*)" # Gather
]

def look_for_video_link_in_meeting_description(p_meeting_description):
    for reg_ex in video_links_reg_exs:
        video_url_in_description = re.search(
            reg_ex,
            p_meeting_description)

        if video_url_in_description:
            return(video_url_in_description.group(1))

    # No known video link found
    return("No Video")

ACTION_DISPLAY_EVENT = 1
ACTION_SNOOOZE_EVENT = 2
ACTION_DISMISS_EVENT = 3

class ParsedEvent:
    def has_event_changed(self, new_raw_event):
        fields_to_compare = [
            "all_day_event",
            "description",
            "end_date",
            "event_location",
            "event_name",
            "has_self_declined",
            "html_link",
            "minutes_before_to_notify",
            "no_popup_reminder",
            "start_date",
            "video_link"
        ]
        self.globals.logger.debug("Check for changes")

        if (self.updated != new_raw_event['updated']):
            self.globals.logger.info("Event updated field has changed for event - " + self.event_name)

            # Create a parsed event for the new raw event
            new_parsed_event = ParsedEvent(
                self.globals,
                self.google_account,
                self.event_key_str,
                new_raw_event,
                self.cal_name)
            
            for index in range(len(fields_to_compare)):
                if (getattr(self, fields_to_compare[index]) != getattr(new_parsed_event, fields_to_compare[index])):
                    self.globals.logger.info("The field - " + fields_to_compare[index] + " - changed for event - " + self.event_name)
            
                    return(True)
            
        # The event has not changed

        # We will update the updaated field in the case we couldn't identify a change, so we won't need to check it endlessly
        self.updated = new_raw_event['updated']

        return(False)

    def has_self_tentative(self):
        # Check if the current user is tentative for the evnet
        if(self.raw_event.get('attendees')):
            # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
            for attendee in self.raw_event['attendees']:
                if(attendee.get('self') and attendee['self'] == True and attendee.get('responseStatus') and attendee['responseStatus'] == 'tentative'):
                    # The current user is tentative for the meeting.
                    return(True)

        # The current user is not tentative for the meeting.
        return(False)

    def get_number_of_attendees(self):
        self.num_of_attendees = 0

        if(self.raw_event.get('attendees')):
            # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
            for attendee in self.raw_event['attendees']:
                self.num_of_attendees = self.num_of_attendees + 1

    def parse_event_description(self, meeting_description):
        if (meeting_description):
            self.description = meeting_description

            # Check if the event has gCalNotifier config
            need_to_record_meeting = re.search(
                "record:yes", 
                meeting_description) 
            if need_to_record_meeting:
                self.need_to_record_meeting = True

            close_event_window_when_event_has_ended = re.search(
                "close_event_window_when_event_has_ended:yes", 
                meeting_description) 
            if close_event_window_when_event_has_ended:
                self.close_event_window_when_event_has_ended = True

            default_snoozed = re.search(
                "default_snooze:([0-9]+)", 
                meeting_description) 
            if default_snoozed:
                self.default_snooze = default_snoozed.group(1)
        
        else:
            self.description = "No description"
            
    def get_snoozed_or_display_action_for_parsed_event_based_on_current_time(self):
        delta_diff = datetime.timedelta(minutes = self.minutes_before_to_notify)
        reminder_time = self.start_date - delta_diff
        now_datetime = get_now_datetime()
        if(now_datetime < reminder_time):
            # Not the time to remind yet
            self.event_wakeup_time = reminder_time

            self.globals.events_logger.debug("Event automatically snoozed as there is time until it should be notified for the first time. For event: " + self.event_name + " until " + str(self.event_wakeup_time))

            return(ACTION_SNOOOZE_EVENT)

        # The event needs to be notified
        return(ACTION_DISPLAY_EVENT)

    def get_action_for_parsed_event(self):
        if (self.has_self_declined):
            self.globals.events_logger.debug("Event dismissed automatically as it was declined by me. For event: " + self.event_name)

            return(ACTION_DISMISS_EVENT)
        
        if (self.no_popup_reminder):
            # No notification reminders
            self.globals.events_logger.debug("Event dismissed automatically as it does not have any reminders set. For event: " + self.event_name)

            return(ACTION_DISMISS_EVENT)

        # Check if the time to remind about the event had arrived
        return(self.get_snoozed_or_display_action_for_parsed_event_based_on_current_time())

    def parse_event(self):
        self.globals.logger.debug(nice_json(self.raw_event))

        self.event_name = self.raw_event.get('summary', '(No title)')

        if (self.has_self_tentative()):
            # The current user is Tentative fot this event
            self.event_name = "Tentative - " + self.event_name

        self.globals.logger.debug("Event Name " + self.event_name)

        self.updated = self.raw_event['updated']

        start_day = self.raw_event['start'].get('dateTime')
        if not start_day:
            # An all day event
            self.all_day_event = True
            start_day = self.raw_event['start'].get('date')
            end_day = self.raw_event['end'].get('date')
            self.start_date=datetime.datetime.strptime(start_day, '%Y-%m-%d').astimezone()
            self.end_date=datetime.datetime.strptime(end_day, '%Y-%m-%d').astimezone()
        else:
            # Not an all day event
            self.all_day_event = False
            end_day = self.raw_event['end'].get('dateTime')
            self.start_date=datetime.datetime.strptime(start_day, '%Y-%m-%dT%H:%M:%S%z').astimezone()
            self.end_date=datetime.datetime.strptime(end_day, '%Y-%m-%dT%H:%M:%S%z').astimezone()

        # Check if the event was not declined by the current user
        if has_self_declined(self.raw_event):
            self.globals.events_logger.debug("Event dismissed automatically as it was declined by me. For event: " + self.event_name)

            self.has_self_declined = True

            self.event_action = ACTION_DISMISS_EVENT

            return

        self.minutes_before_to_notify = get_max_reminder_in_minutes(self.raw_event)
        if (self.minutes_before_to_notify == NO_POPUP_REMINDER):
            # No notification reminders
            self.globals.events_logger.debug("Event dismissed automatically as it does not have any reminders set. For event: " + self.event_name)

            self.no_popup_reminder = True

            self.event_action = ACTION_DISMISS_EVENT
            
            return

        # Event needs to be reminded about, continue parsing the event
        self.html_link = self.raw_event['htmlLink']

        self.event_location = self.raw_event.get('location', "No location")

        meeting_description = self.raw_event.get('description')
        self.parse_event_description(meeting_description)

        # Get the video conf data
        self.video_link = "No Video"
        conf_data = self.raw_event.get('conferenceData')
        if (conf_data):
            entry_points = conf_data.get('entryPoints')
            if (entry_points):
                for entry_point in entry_points:
                    entry_point_type = entry_point.get('entryPointType')
                    if (entry_point_type and entry_point_type == 'video'):
                        uri = entry_point.get('uri')
                        if (uri):
                            self.video_link = uri

        if (self.video_link == "No Video"):
            # Didn't find a video link in the expected location, let's see if there is a video link in the 
            # description.
            if (meeting_description):
                self.video_link = look_for_video_link_in_meeting_description(meeting_description)

                if (self.video_link == self.event_location):
                    # The event location already contains the video link, no need to show it twice
                    self.video_link = "No Video"

        self.get_number_of_attendees()

        # Check if the time to remind about the event had arrived
        self.event_action = self.get_snoozed_or_display_action_for_parsed_event_based_on_current_time()

    def __init__(
            self,
            globals,
            google_account,
            event_key_str,
            raw_event,
            cal_name):
        self.globals = globals
        self.google_account = google_account
        self.event_key_str = event_key_str
        self.raw_event = raw_event
        self.cal_name = cal_name
        self.changed = False
        self.deleted = False
        self.is_dismissed = False
        self.is_snoozed = False
        self.is_unsnoozed_or_undismissed = False
        self.need_to_record_meeting = False
        self.close_event_window_when_event_has_ended = False
        self.description = ''
        self.default_snooze = False
        self.event_wakeup_time = ''
        self.has_self_declined = False
        self.no_popup_reminder = False
        self.minutes_before_to_notify = ''
        self.html_link = ''
        self.event_location = ''
        self.video_link = ''
        self.num_of_attendees = 0

        self.parse_event()
