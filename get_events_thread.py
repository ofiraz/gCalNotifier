import threading
import time
import json

from globals import app_globals
from config import app_config

from events_collection import Events_Collection

from google_calendar_utilities import (
    get_events_from_google_cal_with_try,
    ConnectivityIssue
)

from datetime_utils import get_now_datetime

from event_utils import (
    has_event_changed,
    parse_event,
    NO_POPUP_REMINDER,
    ACTION_DISPLAY_EVENT,
    ACTION_SNOOOZE_EVENT,
    ACTION_DISMISS_EVENT
)

def is_event_already_in_a_collection(globals, event_key_str):
    global dismissed_events
    global snoozed_events

    for events_collection_to_check in [
        dismissed_events,
        globals.events_to_dismiss,
        snoozed_events,
        globals.events_to_snooze,
        globals.displayed_events,
        globals.events_to_present]:
        if (events_collection_to_check.is_event_in(event_key_str)):
            return(True)
        
    # The event is not in any of the collections
    return(False)

def add_items_to_show_from_calendar(globals, google_account, cal_name, cal_id):
    global dismissed_events
    global snoozed_events

    globals.logger.debug("add_items_to_show_from_calendar for " + google_account)

    # Get the next coming events from the google calendar
    try: # In progress - handling intermittent exception from the Google service
        events = get_events_from_google_cal_with_try(globals.logger, google_account, cal_id)

    except ConnectivityIssue:
        # Having a connectivity issue - we will assume the event did not change in the g-cal
        events = []

    # Handled the snoozed events
    if not events:
        globals.logger.debug('No upcoming events found')
        return

    for event in events:
        globals.logger.debug(str(event))
        parsed_event = {}
        now_datetime = get_now_datetime()
        a_snoozed_event_to_wakeup = False

        event_id = event['id']
        event_key = {          
            # 'google_account' : google_account,
            # 'cal_id' : cal_id,
            'event_id' : event_id
        }
        event_key_str = json.dumps(event_key)
        globals.logger.debug("Event ID " + str(event_id))

        if (is_event_already_in_a_collection(globals, event_key_str)):
            globals.logger.debug("Skipping event as it is already in one of the collections")
            continue

        # Event not in the any other list
        parsed_event['raw_event'] = event
        parsed_event['event_name'] = event.get('summary', '(No title)')
        parsed_event['google_account'] = google_account
        parsed_event['cal name'] = cal_name
        parsed_event['cal id'] = cal_id
        globals.logger.debug("Event Name " + parsed_event['event_name'])

        event_action = parse_event(globals.logger, globals.events_logger, event, parsed_event)
        if (event_action == ACTION_DISPLAY_EVENT):
            # Event to get presented
            globals.logger.debug(str(event))

            events_collection_to_add_the_event_to = globals.events_to_present

            globals.logger.debug(
                "Event to be presented - "
                + " " + parsed_event['event_name'] 
                + " " + parsed_event['google_account'] 
                + " " + parsed_event['cal id']
                + " " + parsed_event['raw_event']['id'])
        elif (event_action == ACTION_DISMISS_EVENT):
            # No need to present the event - add it to the dismissed events
            events_collection_to_add_the_event_to = dismissed_events
        
        elif(event_action == ACTION_SNOOOZE_EVENT):
            # Too early to present the event
            events_collection_to_add_the_event_to = snoozed_events

        else:
            # Unexpected type
            globals.logger.error("Unexpected event action -" + str(event_action))
            return

        # Add the event to the needed collection
        events_collection_to_add_the_event_to.add_event(event_key_str, parsed_event)

def condition_function_for_removing_snoozed_events(logger, event_key_str, parsed_event, events_to_present):
    now_datetime = get_now_datetime()

    logger.debug("Snoozed event " + event_key_str + " " + str(parsed_event['event_wakeup_time']) + " " + str(now_datetime))

    if(has_event_changed(logger, parsed_event)):
        # The event has changed, we will let the system re-parse the event as new
        logger.info("event changed - set_items_to_present_from_snoozed")
        
    elif (now_datetime >= parsed_event['event_wakeup_time']):
        # Event needs to be woke up
        events_to_present.add_event(event_key_str, parsed_event)

    else:
        # No need to remove the evnet
        return(False)
    
    # Need to remove the evnet
    return(True)

def set_items_to_present_from_snoozed(globals):
    global snoozed_events

    snoozed_events.remove_events_based_on_condition(
        condition_function_for_removing_snoozed_events, 
        additional_param = globals.events_to_present)

    return

def condition_function_for_removing_dismissed_events(logger, event_key_str, parsed_event, additional_param):
    now_datetime = get_now_datetime()

    logger.debug("Dismissed event " + event_key_str + " " + str(parsed_event['end_date']) + " " + str(now_datetime))

    if (now_datetime > parsed_event['end_date']):
        # The event has ended
        logger.debug("Event end date has passed - clear_dismissed_events_that_have_ended")
        logger.debug("Dismissed event end date" + str(parsed_event['end_date']))

    elif has_event_changed(logger, parsed_event):
        # The event has changed, we will let the system re-parse the event as new
        logger.info("event changed - clear_dismissed_events_that_have_ended")

    else:
        # No need to remove the evnet
        return(False)
    
    # Need to remove the evnet
    return(True)

def move_events_to_dismiss_into_dismissed_events_collection(globals):
    global dismissed_events

    while (True):
        event_key_str, parsed_event = dismissed_events.pop_from_another_collection_and_add_this_one(globals.events_to_dismiss)
        if (event_key_str == None):
            # No more entries to present
            return

def move_events_to_snooze_into_snoozed_events_collection(globals):
    global snoozed_events

    while (True):
        event_key_str, parsed_event = snoozed_events.pop_from_another_collection_and_add_this_one(globals.events_to_snooze)
        if (event_key_str == None):
            # No more entries to present
            return

def clear_dismissed_events_that_have_ended():
    global dismissed_events

    dismissed_events.remove_events_based_on_condition(condition_function_for_removing_dismissed_events)

    return

def condition_function_to_clear_all_events(logger, event_key_str, parsed_event, additional_param):
    # Need to remove the evnet
    return(True)

def set_events_to_be_displayed(globals):
    global dismissed_events
    global snoozed_events

    if (globals.is_reset_needed()):
    # Need to reset the "system" by clearing all of the dismissed and snoozed events
        dismissed_events.remove_events_based_on_condition(condition_function_to_clear_all_events)
        snoozed_events.remove_events_based_on_condition(condition_function_to_clear_all_events)

        globals.reset_done()
    
    else:
        # Update the events that were dismissed or snoozed in the event windows
        move_events_to_dismiss_into_dismissed_events_collection(globals)
        move_events_to_snooze_into_snoozed_events_collection(globals)

        clear_dismissed_events_that_have_ended()
        set_items_to_present_from_snoozed(globals)
    
    for google_account in globals.config.google_accounts:
        for cal_for_account in google_account["calendar list"]:
            globals.logger.debug(google_account["account name"] + " " + str(cal_for_account))
            add_items_to_show_from_calendar(
                globals,
                google_account["account name"], 
                cal_for_account['calendar name'], 
                cal_for_account['calendar id'])

def get_events_to_display_main_loop(globals):
    global dismissed_events
    global snoozed_events

    dismissed_events = Events_Collection(globals.logger, "dismissed_events")
    snoozed_events = Events_Collection(globals.logger, "snoozed_events")

    while True:
        set_events_to_be_displayed(globals)

        globals.logger.debug("Going to sleep for " + str(globals.config.refresh_frequency) + " seconds")
        time.sleep(globals.config.refresh_frequency)


def start_getting_events_to_display_main_loop_thread(globals):
    main_loop_thread = threading.Thread(
        target = get_events_to_display_main_loop,
        args=(globals,),
        daemon=True)

    main_loop_thread.start()
    
