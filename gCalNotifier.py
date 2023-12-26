from google_calendar_utilities import (
    get_calendar_list_for_account
)

from events_mdi_window import MDIWindow

from get_events_thread import Get_Events

from globals import app_globals

from system_tray import app_system_tray

def prep_google_accounts_and_calendars(gloabls):
    for google_account in gloabls.config.google_accounts:
        get_calendar_list_for_account(gloabls.logger, google_account)

# Main
if __name__ == "__main__":
    g_globals = app_globals()

    prep_google_accounts_and_calendars(g_globals)

    # Start a thread to look for events to display
    get_events_object = Get_Events(g_globals)

    g_mdi_window = MDIWindow(g_globals)

    sys_tray = app_system_tray(g_globals, g_mdi_window, get_events_object)

    g_globals.app.exec_()