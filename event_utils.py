from google_calendar_utilities import (
    get_events_from_google_cal_with_try,
    ConnectivityIssue
)

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

def has_event_changed_internal(p_logger, orig_event, new_event):
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
                    if (key1 == "root['conferenceData']['signature']"):
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
                    return(True)

                continue
            # key == 'iterable_item_added' or or key == 'iterable_item_removed'

            p_logger.info("Found a relevant change")
            p_logger.info(key + ":" + str(diff_result[key]))
            return(True)

    return(False)

def has_event_changed(p_logger, orig_event):
    try:
        # First check if the event still exists
        raw_event = get_events_from_google_cal_with_try(
            p_logger,
            orig_event['google_account'],
            orig_event['cal id'],
            orig_event['raw_event']['id'])

    except ConnectivityIssue:
        # Having a connectivity issue - we will assume the event did not change in the g-cal
        return False

    if(raw_event is None):
        # The event does not exist anymore
        p_logger.info("event does not exist anymore - strange")
        p_logger.info("*********** " + orig_event['event_name'] + " ***********")

        return True

    if (has_event_changed_internal(p_logger, orig_event['raw_event'], raw_event)):
        p_logger.info("*********** " + orig_event['event_name'] + " ***********")
        return(True)

    return(False)

