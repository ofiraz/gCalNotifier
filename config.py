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
