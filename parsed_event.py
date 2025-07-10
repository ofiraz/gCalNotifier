import datetime

from json_utils import nice_json

from datetime_utils import get_now_datetime

import re

import validators

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
    "(https://.*.teams.microsoft.us/l/meetup-join/[a-zA-Z0-9-%_./?=]*)", # GOV/DOD Teams 
    "(https://[a-zA-Z0-9-]*\.webex\.com/[a-zA-Z0-9-]*/j\.php\?MTID=[a-zA-Z0-9-]*)", # Webex
    "(https://[a-zA-Z0-9-]*\.webex\.com/meet/[a-zA-Z0-9-\.]*)", # https://rbcteams.webex.com/meet/julian.sequeira
    "(https://[a-zA-Z0-9-]*\.webex\.com/join/[a-zA-Z0-9-\.]*)", # https://rbcteams.webex.com/join/j
    "(https://chime.aws/[0-9]*)", # AWS Chimes
    "(https://meet.google.com/[a-z-]+)", # Google Meet
    "(https://app.gather.town/app/[a-zA-Z0-9-%_./?=]*)" # Gather
]

def look_for_video_link_in_string(text):
    if (text):
        for reg_ex in video_links_reg_exs:
            video_url_in_description = re.search(
                reg_ex,
                text)

            if video_url_in_description:
                return True, video_url_in_description.group(1)

    # No known video link found
    return False, ''

ACTION_DISPLAY_EVENT = 1
ACTION_SNOOOZE_EVENT = 2
ACTION_DISMISS_EVENT = 3

class Attachment:
    def __init__(self, file_url, title):
        self.file_url = file_url
        self.title = title

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
            "start_date",
            "video_link"
        ]
        self.globals.logger.debug("Check for changes")

        if (self.updated != new_raw_event['updated']):
            self.globals.logger.debug("Event updated field has changed for event - " + self.event_name)

            # Create a parsed event for the new raw event
            new_parsed_event = ParsedEvent(
                self.globals,
                self.google_account,
                self.event_key_str,
                new_raw_event,
                self.cal_name)
            
            for index in range(len(fields_to_compare)):
                field_name = fields_to_compare[index]
                value_before = getattr(self, field_name)
                value_after = getattr(new_parsed_event, field_name)

                if (value_before != value_after):
                    self.globals.logger.info(
                        "The field - " + field_name + " - changed for event - " + self.event_name + ". "
                        + "Value before - " + str(value_before) + ". " 
                        + "Value after - " + str(value_after))
            
                    return(True)
                
            # Compare the attachments
            if (len(self.attachments) != len(new_parsed_event.attachments)):
                self.globals.logger.info(
                    "The number of attachments changed for event - " + self.event_name + ". "
                    + "Number of attachments before - " + str(len(self.attachments)) + ". " 
                    + "Number of attachments after - " + str(len(new_parsed_event.attachments)))
                
                return(True)
            
            for index in range(len(self.attachments)):
                if (self.attachments[index].file_url != new_parsed_event.attachments[index].file_url):
                    self.globals.logger.info(
                        "The file url of attachment - " + self.attachments[index].file_url + " - changed for event - " + self.event_name)
                    
                    return(True)
                
                if (self.attachments[index].title != new_parsed_event.attachments[index].title):
                    self.globals.logger.info(
                        "The title of attachment - " + self.attachments[index].title + " - changed for event - " + self.event_name)
                    
                    return(True)
                
            # Event though we couldn't identify a change according to the fields that we are scanning, we will update the updated field, 
            # so we won't need to check it endlessly
            self.updated = new_raw_event['updated']
       
        else:
            '''
            The updated field does not change if the notifications data changes. Per ChatGPT:
            In Google Calendar, the updated field for an event reflects changes to the event’s primary properties that impact the event itself, 
            such as the title, description, start/end time, location, or attendees. However, reminders are considered per-user settings rather 
            than event-level properties. These settings are personal and do not affect the actual event, so they do not update the updated 
            timestamp.
            '''
            # However, if the event has self declined, there is no value to compare the notification time, as it is not relevant
            if (not self.has_self_declined):
                new_event_minutes_before_to_notify = get_max_reminder_in_minutes(new_raw_event)
                if (new_event_minutes_before_to_notify != self.minutes_before_to_notify):
                    self.globals.logger.info(
                        "The minutes before to notify - changed for event - " + self.event_name + ". "
                        + "Value before - " + str(self.minutes_before_to_notify) + ". " 
                        + "Value after - " + str(new_event_minutes_before_to_notify))
                    
                    return(True)
            
        # The event has not changed
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

    def parse_attachments(self):
        if(self.raw_event.get('attachments')):
            for attachment in self.raw_event['attachments']:
                self.attachments.append(Attachment(attachment['fileUrl'], attachment['title']))

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

            dont_send_os_notification = re.search(
                "send_os_notification:no", 
                meeting_description)
            if dont_send_os_notification:
                self.send_os_notification = False
 
            
    def get_snoozed_or_display_action_for_parsed_event_based_on_current_time(self):
        delta_diff = datetime.timedelta(minutes = self.minutes_before_to_notify)
        reminder_time = self.start_date - delta_diff
        now_datetime = get_now_datetime()
        if(now_datetime < reminder_time):
            # Not the time to remind yet
            self.event_wakeup_time = reminder_time

            self.globals.events_logger.debug("Event automatically snoozed as there is time until it should be notified for the first time. For event: " + self.event_name + " until " + str(self.event_wakeup_time))

            self.automatically_snoozed_dismissed = True

            return(ACTION_SNOOOZE_EVENT)

        # The event needs to be notified
        return(ACTION_DISPLAY_EVENT)

    def get_action_for_parsed_event(self):
        if (self.has_self_declined):
            self.globals.events_logger.debug("Event dismissed automatically as it was declined by me. For event: " + self.event_name)

            self.automatically_snoozed_dismissed = True

            return(ACTION_DISMISS_EVENT)
        
        if (self.no_popup_reminder):
            # No notification reminders
            self.globals.events_logger.debug("Event dismissed automatically as it does not have any reminders set. For event: " + self.event_name)

            self.automatically_snoozed_dismissed = True

            return(ACTION_DISMISS_EVENT)

        # Check if the time to remind about the event had arrived
        return(self.get_snoozed_or_display_action_for_parsed_event_based_on_current_time())

    def identify_video_and_location_data(self):
        self.video_link = "No Video"

        # Look for a video link in the video entry point
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

        if (self.description != ''):
            # Look for a video link in the description
            valid_video_link_in_description, self.video_link_in_description = look_for_video_link_in_string(self.description)

            if (valid_video_link_in_description):
                if (self.video_link == "No Video"):
                    self.video_link = self.video_link_in_description
                elif (self.video_link != self.video_link_in_description):
                    self.separate_video_link_from_description = True

        # Get the event location
        self.event_location = self.raw_event.get('location', "No location")
                
        if (self.event_location != "No location"):
            # Look for a video link in the location
            valid_video_link_in_location, self.video_link_in_location = look_for_video_link_in_string(self.event_location)

            if (valid_video_link_in_location):
                if (self.video_link == "No Video"):
                    self.video_link = self.video_link_in_location
                elif ((self.video_link != self.video_link_in_location) and (self.video_link_in_description != self.video_link_in_location)):
                    self.separate_video_link_from_location = True

            # Check if the event location conains a URL
            valid_url = validators.url(self.event_location)
            if (valid_url):
                if (self.event_location != self.video_link_in_location):
                    # This means that the URL in the location is not a video URL
                    self.display_location_as_url = True
                
                # Otherwise we don't want to show the location URL, as we will have it as a video URL from the location
            else:
                # The event location is not a URL, we would like to show its data as such
                self.display_location = True

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

            self.automatically_snoozed_dismissed = True

            self.event_action = ACTION_DISMISS_EVENT

            return

        self.minutes_before_to_notify = get_max_reminder_in_minutes(self.raw_event)
        if (self.minutes_before_to_notify == NO_POPUP_REMINDER):
            # No notification reminders
            self.globals.events_logger.debug("Event dismissed automatically as it does not have any reminders set. For event: " + self.event_name)

            self.no_popup_reminder = True

            self.automatically_snoozed_dismissed = True

            self.event_action = ACTION_DISMISS_EVENT
            
            return

        # Event needs to be reminded about, continue parsing the event
        self.html_link = self.raw_event['htmlLink']
      
        meeting_description = self.raw_event.get('description')
        self.parse_event_description(meeting_description)

        # Get the video conf data and the location data
        self.identify_video_and_location_data()

        self.get_number_of_attendees()

        self.parse_attachments()

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
        self.send_os_notification = True
        self.description = ''
        self.default_snooze = False
        self.event_wakeup_time = ''
        self.has_self_declined = False
        self.no_popup_reminder = False
        self.minutes_before_to_notify = ''
        self.html_link = ''
        self.event_location = ''
        self.display_location = False
        self.display_location_as_url = False
        self.video_link = ''
        self.video_link_in_description = ''
        self.separate_video_link_from_description = False
        self.video_link_in_location = ''
        self.separate_video_link_from_location = False
        self.num_of_attendees = 0
        self.automatically_snoozed_dismissed = False
        self.attachments = []

        self.parse_event()
