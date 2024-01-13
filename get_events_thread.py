import threading
import time
import json

from events_collection import Events_Collection

from google_calendar_utilities import (
    get_events_from_google_cal_with_try,
    ConnectivityIssue
)

from datetime_utils import get_now_datetime

from event_utils import (
    has_raw_event_changed,
    parse_event,
    get_action_for_parsed_event,
    ACTION_DISPLAY_EVENT,
    ACTION_SNOOOZE_EVENT,
    ACTION_DISMISS_EVENT
)

class Get_Events:
    def __init__(self, globals, start_time, end_time):
        self.globals = globals
        
        self.all_events = Events_Collection(self.globals.logger, "all_events")

        self.dismissed_events = Events_Collection(self.globals.logger, "dismissed_events", use_rw_lock=True)
        self.dismissed_events.set_add_cb(self.add_event_to_dismissed_cb)
        self.dismissed_events.set_remove_cb(self.remove_event_from_dismissed_cb)

        self.snoozed_events = Events_Collection(self.globals.logger, "snoozed_events", use_rw_lock=True)
        self.snoozed_events.set_add_cb(self.add_event_to_snoozed_cb)
        self.snoozed_events.set_remove_cb(self.remove_event_from_snoozed_cb)
 
        main_loop_thread = threading.Thread(
            target = self.get_events_to_display_main_loop,
            args = (start_time, end_time, ),
            daemon=True)
        
        main_loop_thread.start()

    def add_event_to_dismissed_cb(self, parsed_event):
        parsed_event['is_dismissed'] = True

    def remove_event_from_dismissed_cb(self, parsed_event):
        parsed_event['is_dismissed'] = False
    
    def add_event_to_snoozed_cb(self, parsed_event):
        parsed_event['is_snoozed'] = True

    def remove_event_from_snoozed_cb(self, parsed_event):
        parsed_event['is_snoozed'] = False
    
    def get_events_to_display_main_loop(self, start_time, end_time):           
        while True:
            self.set_events_to_be_displayed(start_time, end_time)

            self.globals.logger.debug("Going to sleep for " + str(self.globals.config.refresh_frequency) + " seconds")
            time.sleep(self.globals.config.refresh_frequency)

    def wakeup_event_if_needed(self, event_key_str, parsed_event):
        # It is a snoozed event, let's see if it needs to be woken
        now_datetime = get_now_datetime()

        if (now_datetime >= parsed_event['event_wakeup_time']):
            # Event needs to be woke up
            self.globals.events_to_present.add_event(event_key_str, parsed_event)
            self.snoozed_events.remove_event(event_key_str)

    def set_events_to_be_displayed(self, start_time, end_time):
        is_reset_needed = self.globals.is_reset_needed()
        if (is_reset_needed):
        # Need to reset the "system" by clearing all of the dismissed and snoozed events - will be done while parsing the events
            self.globals.reset_done()
        
        else:
            # Update the events that were dismissed or snoozed in the event windows
            self.move_events_to_dismiss_into_dismissed_events_collection()
            self.move_events_to_snooze_into_snoozed_events_collection()

        new_all_events = Events_Collection(self.globals.logger, "new_all_events")
        
        connectivity_issues = False
        for google_account in self.globals.config.google_accounts:
            for cal_for_account in google_account["calendar list"]:
                self.globals.logger.debug(google_account["account name"] + " " + str(cal_for_account))

                try:
                    self.add_items_to_show_from_calendar(
                        google_account["account name"], 
                        cal_for_account['calendar name'], 
                        cal_for_account['calendar id'],
                        new_all_events, 
                        is_reset_needed,
                        start_time,
                        end_time)

                except ConnectivityIssue:
                    # Having a connectivity issues - we will assume the events did not change in the g-cal
                    connectivity_issues = True

        # Check if there are still items in the orig events collection - if so it means that those events do not exist in the events fetched from the calendars
        now_datetime = get_now_datetime()

        while(True):
            event_key_str, parsed_event = self.all_events.pop()
            if (parsed_event == None):
                break

            if(is_reset_needed or ((not connectivity_issues) and (now_datetime < parsed_event['end_date']))):
                # Two options here:
                # 1. The user asked to reset all existing handling
                # or in the case there were no connection issues:
                # 2. The event end time did not arrive yet, but it does not exist - i.e. got deleted
                # In both cases we want to remove this event from all places and not add it again

                if (parsed_event['is_dismissed']):
                    # Unmarking all disimmsed events
                    self.dismissed_events.remove_event(event_key_str)
                
                elif(parsed_event['is_snoozed']):
                    # Unmarking all snoozed events
                    self.snoozed_events.remove_event(event_key_str)

                else:
                    # Marking all other events as deleted for the case they are being displayed, and then we want the window to close
                    parsed_event['deleted'] = True

            else:
                # The event has ended, and this is the reason we don't see it anymore - as our search is only for events from now on
                # It can also be due to connectivity issues where we could not get the events
                if ((not connectivity_issues) and parsed_event['is_dismissed']):
                    # The event was dismissed - we don't to manage it anymore
                    self.dismissed_events.remove_event(event_key_str)

                else: # If it is not dismissed - it is either snoozed or displayed, we will need to re look at it in the next loop
                    # It can also be that due to connectivity issues we didn't get new info about the event, we will assume the item did not change
                    new_all_events.add_event(event_key_str, parsed_event)

                    if(parsed_event['is_snoozed']):
                        # The event is snoozed, if needed wake it up
                        self.wakeup_event_if_needed(event_key_str, parsed_event)
                                       
        # Switch the old and the new event collections
        self.all_events = new_all_events

    def move_events_to_dismiss_into_dismissed_events_collection(self):
        while (True):
            event_key_str, parsed_event = self.dismissed_events.pop_from_another_collection_and_add_this_one(self.globals.events_to_dismiss)
            if (event_key_str == None):
                # No more entries to present
                return

    def move_events_to_snooze_into_snoozed_events_collection(self):
        while (True):
            event_key_str, parsed_event = self.snoozed_events.pop_from_another_collection_and_add_this_one(self.globals.events_to_snooze)
            if (event_key_str == None):
                # No more entries to present
                return

    def add_items_to_show_from_calendar(self, google_account, cal_name, cal_id, new_all_events, is_reset_needed, start_time, end_time):
        self.globals.logger.debug("add_items_to_show_from_calendar for " + google_account)

        # Get the next coming events from the google calendar
        events = get_events_from_google_cal_with_try(self.globals.logger, google_account, cal_id, start_time, end_time)

        for event in events:
            self.globals.logger.debug(str(event))
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
            self.globals.logger.debug("Event ID " + str(event_id))

            if (new_all_events.is_event_in(event_key_str)):
                # The same event can come from multiple calendars, we've already handled it from another calendar in this run
                continue

            event_from_all_events = self.all_events[event_key_str]
            if(event_from_all_events != None):
                if (google_account != event_from_all_events['google_account']):
                    # This is the same event but from a different account - we will wait to see the event in the account that was used to store the event
                    continue
                
                # We already handled this event in a previous run of the main loop
                event_changed = has_raw_event_changed(
                    self.globals.logger,
                    event_from_all_events['raw_event'],
                    event)
                
                if (event_changed == False):
                    # The event has not changed - moving from the current collection to the new one
                    new_all_events.add_event(event_key_str, event_from_all_events)
                    self.all_events.remove_event(event_key_str)

                    if (is_reset_needed):
                        # There is a need to reset

                        if (event_from_all_events['is_dismissed']):
                            # Remove the changed event from the dismissed events, so it will get parsed from scratch
                            self.dismissed_events.remove_event(event_key_str)

                        elif(event_from_all_events['is_snoozed']):
                            # Remove the changed event from the snoozed events, so it will get parsed from scratch
                            self.snoozed_events.remove_event(event_key_str)

                        else:
                            # The event is diaplyed and has not changed. Nothing needs to be done
                            continue

                        # Re compute the needed action for the event that was dismissed or snoozed before
                        event_action = get_action_for_parsed_event(self.globals.events_logger, event_from_all_events)

                        self.apply_action_on_parsed_event(
                            event_action,
                            event_key_str,
                            event_from_all_events)

                    elif(event_from_all_events['is_snoozed']):
                        self.wakeup_event_if_needed(event_key_str, event_from_all_events)
                        
                    continue

                else: # The event has changed
                    self.globals.logger.info("Event changed " + event_from_all_events['event_name'])

                    event_from_all_events['changed'] = True
                    
                    if (event_from_all_events['is_dismissed']):
                        # Remove the changed event from the dismissed events, so it will get parsed from scratch
                        self.dismissed_events.remove_event(event_key_str)

                    elif(event_from_all_events['is_snoozed']):
                        # Remove the changed event from the snoozed events, so it will get parsed from scratch
                        self.snoozed_events.remove_event(event_key_str)

                    # Removing from the old all_events, the next steps will add it to the new all_events
                    self.all_events.remove_event(event_key_str)

            # Event not in the any other list
            parsed_event['raw_event'] = event
            parsed_event['event_name'] = event.get('summary', '(No title)')
            parsed_event['google_account'] = google_account
            parsed_event['cal name'] = cal_name
            parsed_event['cal id'] = cal_id
            parsed_event['deleted'] = False
            parsed_event['changed'] = False
            parsed_event['is_dismissed'] = False
            parsed_event['is_snoozed'] = False

            self.globals.logger.debug("Event Name " + parsed_event['event_name'])

            event_action = parse_event(self.globals.logger, self.globals.events_logger, event, parsed_event)

            # Add the event to the new all-events
            new_all_events.add_event(event_key_str, parsed_event)

            self.apply_action_on_parsed_event(
                event_action,
                event_key_str,
                parsed_event)

    def apply_action_on_parsed_event(self, event_action, event_key_str, parsed_event):
        if (event_action == ACTION_DISPLAY_EVENT):
            # Event to get presented
            events_collection_to_add_the_event_to = self.globals.events_to_present

            self.globals.logger.debug(
                "Event to be presented - "
                + " " + parsed_event['event_name'] 
                + " " + parsed_event['google_account'] 
                + " " + parsed_event['cal id']
                + " " + parsed_event['raw_event']['id'])

        elif (event_action == ACTION_DISMISS_EVENT):
            # No need to present the event - add it to the dismissed events
            events_collection_to_add_the_event_to = self.dismissed_events
        
        elif(event_action == ACTION_SNOOOZE_EVENT):
            # Too early to present the event
            events_collection_to_add_the_event_to = self.snoozed_events

        else:
            # Unexpected type
            self.globals.logger.error("Unexpected event action -" + str(event_action))
            return

        # Add the event to the needed collection
        events_collection_to_add_the_event_to.add_event(event_key_str, parsed_event)

    def get_dismissed_events_into_list(self, event_handling_function, target_list):
        self.dismissed_events.ro_traverse_on_events(event_handling_function, additional_param = target_list)

    def get_snoozed_events_into_list(self, event_handling_function, target_list):
        self.snoozed_events.ro_traverse_on_events(event_handling_function, additional_param = target_list)
