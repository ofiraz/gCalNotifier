import datetime

from json_utils import nice_json

from datetime_utils import get_now_datetime

from deepdiff import DeepDiff

import re

def has_self_declined(event):
    # Check if the event was not declined by the current user
    if(event.get('attendees')):
        # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
        for attendee in event['attendees']:
            if(attendee.get('self') and attendee['self'] == True and attendee.get('responseStatus') and attendee['responseStatus'] == 'declined'):
                # The user declined the meeting. No need to display it
                return(True)

    # The event was not declined by the current user
    return(False)

NO_POPUP_REMINDER = -1

def get_max_reminder_in_minutes(p_event):
    max_minutes_before = NO_POPUP_REMINDER

    if (p_event['reminders'].get('useDefault') == True):
        max_minutes_before = 15
    else:
        override_rule = p_event['reminders'].get('overrides')
        if (override_rule):
            for override_entry in override_rule:
                if (override_entry['method'] == "popup"):
                    if int(override_entry['minutes']) > max_minutes_before:
                        max_minutes_before = int(override_entry['minutes'])

    return(max_minutes_before)

def has_raw_event_changed(p_logger, orig_event, new_event):
    p_logger.debug("Check for changes")

    diff_result = DeepDiff(orig_event, new_event)
    if (diff_result):

        p_logger.debug("Check if relevant changes")
        p_logger.debug(str(diff_result))

        for key in diff_result:
            if (key == 'values_changed'):
                for key1 in diff_result['values_changed']:
                    if (
                        key1 == "root['etag']" 
                        or key1 == "root['updated']" 
                        or key1 == "root['recurringEventId']"
                        or key1 == "root['conferenceData']['signature']"
                        or key1 == "root['iCalUID']"
                    ):
                        # Not relevant changes
                        continue

                    if re.search("root\['attendees'\]\[[0-9]+\]\['responseStatus'\]", key1):
                        # A change in the attendees response
                        if has_self_declined(new_event):
                            # The current user has declined the event
                            p_logger.info("The current user has declined")
                            return(True)

                        continue

                    if (key1 == "root['extendedProperties']['shared']['meetingParams']"):
                        # Compare the internal parameters
                        diff_extended_properties = DeepDiff(diff_result['values_changed'][key1]['new_value'], diff_result['values_changed'][key1]['old_value'])
                        for key2 in diff_extended_properties:
                            if (key2 == "invitees_hash"):
                                # Not relevant change
                                continue

                            # Found a change
                            p_logger.info("Found a relevant change")
                            p_logger.info(key2 + ":" + str(diff_extended_properties[key2]))
                            return(True)
                        
                        continue

                    if re.search("root\['reminders'\]", key1):
                        # A change in the reminders
                        # Compare the max minutes to notify before in both original and new event
                        orig_event_max_reminder_in_minutes = get_max_reminder_in_minutes(orig_event)
                        new_event_max_reminder_in_minutes = get_max_reminder_in_minutes(new_event)
                        
                        if (orig_event_max_reminder_in_minutes != new_event_max_reminder_in_minutes):
                            # The max reminder in minutes has changed
                            p_logger.info("The max reminder in minutes has changed")
                            return(True)

                        continue

                    # Found a change
                    p_logger.info("Found a relevant change")
                    p_logger.info(key1 + ":" + str(diff_result['values_changed'][key1]))
                    return(True)
                
                continue
            # key == 'values_changed'

            elif (key == 'iterable_item_added' or key == 'iterable_item_removed' or key == 'dictionary_item_added' or key == 'dictionary_item_removed'):
                for key1 in diff_result[key]:
                    if ((key1 == "root['conferenceData']['signature']")
                        #or (key1 == "root['organizer']['self']")
                        #or (key1 == "root['creator']['self']")
                        ):
                        # Not relevant changes
                        continue
                        
                    if re.search("root\['attendees'\]\[[0-9]+\]", key1):
                        # An attendee added - can be ignored
                        continue

                    if re.search("root\['reminders'\]", key1):
                        # A change in the reminders
                        # Compare the max minutes to notify before in both original and new event
                        orig_event_max_reminder_in_minutes = get_max_reminder_in_minutes(orig_event)
                        new_event_max_reminder_in_minutes = get_max_reminder_in_minutes(new_event)
                        
                        if (orig_event_max_reminder_in_minutes != new_event_max_reminder_in_minutes):
                            # The max reminder in minutes has changed
                            p_logger.info("The max reminder in minutes has changed")
                            return(True)

                        continue

                    # Found a change
                    p_logger.info("Found a relevant change")
                    p_logger.info(key1)
                    p_logger.info("orig_event")
                    p_logger.info(nice_json(orig_event))
                    p_logger.info("new_event")
                    p_logger.info(nice_json(new_event))

                    return(True)

                continue
            # key == 'iterable_item_added' or or key == 'iterable_item_removed'

            p_logger.info("Found a relevant change")
            p_logger.info(key + ":" + str(diff_result[key]))
            return(True)

    return(False)

def has_self_tentative(event):
    # Check if the current user is tentative for the evnet
    if(event.get('attendees')):
        # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
        for attendee in event['attendees']:
            if(attendee.get('self') and attendee['self'] == True and attendee.get('responseStatus') and attendee['responseStatus'] == 'tentative'):
                # The current user is tentative for the meeting.
                return(True)

    # The current user is not tentative for the meeting.
    return(False)

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

def get_number_of_attendees(event):
    num_of_attendees = 0

    if(event.get('attendees')):
        # The event has attendees - walk on the attendees and look for the attendee that belongs to the current account
        for attendee in event['attendees']:
            num_of_attendees = num_of_attendees + 1

    return(num_of_attendees)

def parse_event_description(p_logger, meeting_description, parsed_event):
    if (meeting_description):
        parsed_event.description = meeting_description

        # Check if the event has gCalNotifier config
        need_to_record_meeting = re.search(
            "record:yes", 
            meeting_description) 
        if need_to_record_meeting:
            parsed_event.need_to_record_meeting = True

        close_event_window_when_event_has_ended = re.search(
            "close_event_window_when_event_has_ended:yes", 
            meeting_description) 
        if close_event_window_when_event_has_ended:
            parsed_event.close_event_window_when_event_has_ended = True

        default_snoozed = re.search(
            "default_snooze:([0-9]+)", 
            meeting_description) 
        if default_snoozed:
            parsed_event.default_snooze = default_snoozed.group(1)
    
    else:
        parsed_event.description = "No description"
        
ACTION_DISPLAY_EVENT = 1
ACTION_SNOOOZE_EVENT = 2
ACTION_DISMISS_EVENT = 3

def get_snoozed_or_display_action_for_parsed_event_based_on_current_time(events_logger, parsed_event, minutes_before_to_notify):
    delta_diff = datetime.timedelta(minutes=minutes_before_to_notify)
    reminder_time = parsed_event.start_date - delta_diff
    now_datetime = get_now_datetime()
    if(now_datetime < reminder_time):
        # Not the time to remind yet
        parsed_event.event_wakeup_time = reminder_time

        events_logger.info("Event automatically snoozed as there is time until it should be notified for the first time. For event: " + parsed_event.event_name + " until " + str(parsed_event.event_wakeup_time))

        return(ACTION_SNOOOZE_EVENT)

    # The event needs to be notified
    return(ACTION_DISPLAY_EVENT)

def get_action_for_parsed_event(events_logger, parsed_event):
    if (parsed_event.has_self_declined):
        events_logger.info("Event dismissed automatically as it was declined by me. For event: " + parsed_event.event_name)

        return(ACTION_DISMISS_EVENT)
    
    if (parsed_event.no_popup_reminder):
        # No notification reminders
        events_logger.info("Event dismissed automatically as it does not have any reminders set. For event: " + parsed_event.event_name)

        return(ACTION_DISMISS_EVENT)

    # Check if the time to remind about the event had arrived
    return(get_snoozed_or_display_action_for_parsed_event_based_on_current_time(
        events_logger,
        parsed_event,
        parsed_event.minutes_before_to_notify))

class ParsedEvent:
    def parse_event(self):
        self.globals.logger.debug(nice_json(self.raw_event))

        self.event_name = self.raw_event.get('summary', '(No title)')
        self.globals.logger.debug("Event Name " + self.event_name)

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
            self.globals.events_logger.info("Event dismissed automatically as it was declined by me. For event: " + self.event_name)

            self.has_self_declined = True

            self.event_action = ACTION_DISMISS_EVENT

            return

        minutes_before_to_notify = get_max_reminder_in_minutes(self.raw_event)
        self.minutes_before_to_notify = minutes_before_to_notify
        if (minutes_before_to_notify == NO_POPUP_REMINDER):
            # No notification reminders
            self.globals.events_logger.info("Event dismissed automatically as it does not have any reminders set. For event: " + self.event_name)

            self.no_popup_reminder = True

            self.event_action = ACTION_DISMISS_EVENT
            
            return

        # Event needs to be reminded about, continue parsing the event
        self.html_link = self.raw_event['htmlLink']

        self.event_location = self.raw_event.get('location', "No location")

        meeting_description = self.raw_event.get('description')
        parse_event_description(self.globals.logger, meeting_description, self)

        if (has_self_tentative(self.raw_event)):
            # The current user is Tentative fot this event
            self.event_name = "Tentative - " + self.event_name

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

        self.num_of_attendees = get_number_of_attendees(self.raw_event)

        # Check if the time to remind about the event had arrived
        self.event_action = get_snoozed_or_display_action_for_parsed_event_based_on_current_time(
            self.globals.events_logger,
            self,
            minutes_before_to_notify)

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
