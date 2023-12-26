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
    def __init__(self, globals):
        self.globals = globals
        
        self.all_events = Events_Collection(self.globals.logger, "all_events")
        
        main_loop_thread = threading.Thread(
            target = self.get_events_to_display_main_loop,
            daemon=True)
        
        main_loop_thread.start()
    
    def get_events_to_display_main_loop(self):           
        while True:
            self.set_events_to_be_displayed()

            self.globals.logger.debug("Going to sleep for " + str(self.globals.config.refresh_frequency) + " seconds")
            time.sleep(self.globals.config.refresh_frequency)

    def set_events_to_be_displayed(self):
        is_reset_needed = self.globals.is_reset_needed()
        if (is_reset_needed):
        # Need to reset the "system" by clearing all of the dismissed and snoozed events - will be done while parsing the events
            self.globals.reset_done()
        
        else:
            # Update the events that were dismissed or snoozed in the event windows
            self.move_events_to_dismiss_into_dismissed_events_collection()
            self.move_events_to_snooze_into_snoozed_events_collection()

        new_all_events = Events_Collection(self.globals.logger, "new_all_events")
        
        for google_account in self.globals.config.google_accounts:
            for cal_for_account in google_account["calendar list"]:
                self.globals.logger.debug(google_account["account name"] + " " + str(cal_for_account))
                self.add_items_to_show_from_calendar(
                    google_account["account name"], 
                    cal_for_account['calendar name'], 
                    cal_for_account['calendar id'],
                    new_all_events, 
                    is_reset_needed)

        # Check if there are still items in the orig events collection - if so it means that those events do not exist in the events fetched from the calendars
        now_datetime = get_now_datetime()

        while(True):
            event_key_str, parsed_event = self.all_events.pop()
            if (parsed_event == None):
                break

            if ((not is_reset_needed) and (now_datetime > parsed_event['end_date'])):
                # The event has ended

                if (self.globals.dismissed_events.is_event_in(event_key_str)):
                    # The event is a dismissed event - we can remove it from the list
                    self.globals.dismissed_events.remove_event(event_key_str)

                # If the event is snoozed - keep it, the user wanted it to be snoozed for a longer time than the event end and wanted to know about it
                # If the event is displayed - keep it, the user will close the event window when the time comes, or it will close itself if it is marked to do so
            
            else:
                # The event did not end yet - this means that the event got deleted
                parsed_event['deleted'] = True

                if (self.globals.dismissed_events.is_event_in(event_key_str)):
                    # The event is dismissed, we can remove it
                    self.globals.dismissed_events.remove_event(event_key_str)
                
                elif(self.globals.snoozed_events.is_event_in(event_key_str)):
                    # The event is snoozed, we can remove it
                    self.globals.snoozed_events.remove_event(event_key_str)

        # Switch the old and the new event collections
        self.all_events = new_all_events

    def move_events_to_dismiss_into_dismissed_events_collection(self):
        while (True):
            event_key_str, parsed_event = self.globals.dismissed_events.pop_from_another_collection_and_add_this_one(self.globals.events_to_dismiss)
            if (event_key_str == None):
                # No more entries to present
                return

    def move_events_to_snooze_into_snoozed_events_collection(self):
        while (True):
            event_key_str, parsed_event = self.globals.snoozed_events.pop_from_another_collection_and_add_this_one(self.globals.events_to_snooze)
            if (event_key_str == None):
                # No more entries to present
                return

    def add_items_to_show_from_calendar(self, google_account, cal_name, cal_id, new_all_events, is_reset_needed):
        self.globals.logger.debug("add_items_to_show_from_calendar for " + google_account)

        # Get the next coming events from the google calendar
        try: # In progress - handling intermittent exception from the Google service
            events = get_events_from_google_cal_with_try(self.globals.logger, google_account, cal_id)

        except ConnectivityIssue:
            # Having a connectivity issue - we will assume the event did not change in the g-cal
            events = []

        # Handled the snoozed events
        if not events:
            self.globals.logger.debug('No upcoming events found')
            return

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

                        if (self.globals.dismissed_events.is_event_in(event_key_str)):
                            # Remove the changed event from the dismissed events, so it will get parsed from scratch
                            self.globals.dismissed_events.remove_event(event_key_str)

                        elif(self.globals.snoozed_events.is_event_in(event_key_str)):
                            # Remove the changed event from the snoozed events, so it will get parsed from scratch
                            self.globals.snoozed_events.remove_event(event_key_str)

                        else:
                            # The event is diaplyed and has not changed. Nothing needs to be done
                            continue

                        # Re compute the needed action for the event that was dismissed or snoozed before
                        event_action = get_action_for_parsed_event(self.globals.events_logger, event_from_all_events)

                        self.apply_action_on_parsed_event(
                            event_action,
                            event_key_str,
                            event_from_all_events)

                    elif(self.globals.snoozed_events.is_event_in(event_key_str)):
                        # It is a snoozed event, let's see if it needs to be woken
                        now_datetime = get_now_datetime()

                        if (now_datetime >= event_from_all_events['event_wakeup_time']):
                            # Event needs to be woke up
                            self.globals.events_to_present.add_event(event_key_str, event_from_all_events)
                            self.globals.snoozed_events.remove_event(event_key_str)

                    continue

                else: # The event has changed
                    event_from_all_events['changed'] = True
                    
                    if (self.globals.dismissed_events.is_event_in(event_key_str)):
                        # Remove the changed event from the dismissed events, so it will get parsed from scratch
                        self.globals.dismissed_events.remove_event(event_key_str)

                    elif(self.globals.snoozed_events.is_event_in(event_key_str)):
                        # Remove the changed event from the snoozed events, so it will get parsed from scratch
                        self.globals.snoozed_events.remove_event(event_key_str)

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
            events_collection_to_add_the_event_to = self.globals.dismissed_events
        
        elif(event_action == ACTION_SNOOOZE_EVENT):
            # Too early to present the event
            events_collection_to_add_the_event_to = self.globals.snoozed_events

        else:
            # Unexpected type
            self.globals.logger.error("Unexpected event action -" + str(event_action))
            return

        # Add the event to the needed collection
        events_collection_to_add_the_event_to.add_event(event_key_str, parsed_event)

