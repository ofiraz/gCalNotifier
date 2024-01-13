import sys
import logging
import json

class app_config:
    def __init__(self):
        with open("gCalNotifier.json") as f:
            l_config = json.load(f)

        self.google_accounts = l_config.get("google accounts")
        if (not self.google_accounts):
            print("No \'google accounts\' defined in the config file")
            sys.exit()

        for google_account in self.google_accounts:
            account_name = google_account.get("account name")
            if (not account_name):
                print ("No \'account name\' defined for a google account entry")
                sys.exit()
    
        self.log_level = l_config.get("log level")
        if (not self.log_level):
            self.log_level = logging.INFO

        self.refresh_frequency = l_config.get("refresh frequency")
        if (not self.refresh_frequency):
            self.refresh_frequency = 30

        self.do_debug = l_config.get("debug")
        if ((not self.do_debug) or (self.do_debug == 0)):
            self.do_debug = False

        else:
            # Need to do a debug of a specific event
            self.do_debug = True

            # Get the debug start and end time
            self.debug_start_time = l_config.get("debug start time")
            if (not self.debug_start_time):
                print ("No \'debug start time\' defined while \'debug\' is set")
                sys.exit()

            self.debug_end_time = l_config.get("debug end time")
            if (not self.debug_end_time):
                print ("No \'debug end time\' defined while \'debug\' is set")
                sys.exit()
