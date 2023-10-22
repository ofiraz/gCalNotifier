import threading
import time
import json

from google_calendar_utilities import (
    get_events_from_google_cal_with_try,
    ConnectivityIssue
)

from datetime_utils import get_now_datetime

from event_utils import (
    has_event_changed,
    parse_event,
    NO_POPUP_REMINDER
)

def add_items_to_show_from_calendar(logger, app_events_collections, google_account, cal_name, cal_id):
    logger.debug("add_items_to_show_from_calendar for " + google_account)

    # Get the next coming events from the google calendar
    try: # In progress - handling intermittent exception from the Google service
        events = get_events_from_google_cal_with_try(logger, google_account, cal_id)

    except ConnectivityIssue:
        # Having a connectivity issue - we will assume the event did not change in the g-cal
        events = []

    # Handled the snoozed events
    if not events:
        logger.debug('No upcoming events found')
        return

    for event in events:
        logger.debug(str(event))
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
        logger.debug("Event ID " + str(event_id))

        if (app_events_collections.dismissed_events.is_event_in(event_key_str)):
            logger.debug("Skipping dismissed event")
            continue

        if (app_events_collections.snoozed_events.is_event_in(event_key_str)):
            logger.debug("Skipping snoozed event")
            continue

        if (app_events_collections.displayed_events.is_event_in(event_key_str)):
            logger.debug("Skipping displayed event")
            continue
        
        if (app_events_collections.events_to_present.is_event_in(event_key_str)):
            logger.debug("Skipping event as it is already in the events to present")
            continue

        # Event not in the any other list
        parsed_event['raw_event'] = event
        parsed_event['event_name'] = event.get('summary', '(No title)')
        parsed_event['google_account'] = google_account
        parsed_event['cal name'] = cal_name
        parsed_event['cal id'] = cal_id
        logger.debug("Event Name " + parsed_event['event_name'])

        need_to_notify = parse_event(logger, event, parsed_event)
        if (need_to_notify == True):
            # Event to get presented
            logger.debug(str(event))

            app_events_collections.events_to_present.add_event(event_key_str, parsed_event)

            logger.debug(
                "Event to be presented - "
                + " " + parsed_event['event_name'] 
                + " " + parsed_event['google_account'] 
                + " " + parsed_event['cal id']
                + " " + parsed_event['raw_event']['id'])

def condition_function_for_removing_snoozed_events(logger, app_events_collections, event_key_str, parsed_event):
    now_datetime = get_now_datetime()

    logger.debug("Snoozed event " + event_key_str + " " + str(parsed_event['event_wakeup_time']) + " " + str(now_datetime))

    if(has_event_changed(logger, parsed_event)):
        # The event has changed, we will let the system re-parse the event as new
        logger.info("event changed - set_items_to_present_from_snoozed")
        
    elif (now_datetime >= parsed_event['event_wakeup_time']):
        # Event needs to be woke up
        app_events_collections.events_to_present.add_event(event_key_str, parsed_event)

    else:
        # No need to remove the evnet
        return(False)
    
    # Need to remove the evnet
    return(True)

def set_items_to_present_from_snoozed(app_events_collections):
    global g_logger
    global g_app_events_collections

    app_events_collections.snoozed_events.remove_events_based_on_condition(condition_function_for_removing_snoozed_events)

    return

def condition_function_for_removing_dismissed_events(logger, app_events_collections, event_key_str, parsed_event):
    global g_logger

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

def clear_dismissed_events_that_have_ended(app_events_collections):

    app_events_collections.dismissed_events.remove_events_based_on_condition(condition_function_for_removing_dismissed_events)

    return

def set_events_to_be_displayed(logger, google_accounts, app_events_collections):
    clear_dismissed_events_that_have_ended(app_events_collections)
    set_items_to_present_from_snoozed(app_events_collections)

    for google_account in google_accounts:
        for cal_for_account in google_account["calendar list"]:
            logger.debug(google_account["account name"] + " " + str(cal_for_account))
            add_items_to_show_from_calendar(
                logger,
                app_events_collections,
                google_account["account name"], 
                cal_for_account['calendar name'], 
                cal_for_account['calendar id'])

def get_events_to_display_main_loop(logger, refresh_frequency, google_accounts, app_events_collections):
    while True:
        set_events_to_be_displayed(logger, google_accounts, app_events_collections)

        logger.debug("Going to sleep for " + str(refresh_frequency) + " seconds")
        time.sleep(refresh_frequency)


def start_getting_events_to_display_main_loop_thread(logger, refresh_frequency,google_accounts, app_events_collections):
    main_loop_thread = threading.Thread(
        target = get_events_to_display_main_loop,
        args=(logger, refresh_frequency, google_accounts, app_events_collections),
        daemon=True)

    main_loop_thread.start()
    
