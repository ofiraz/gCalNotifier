from PyQt5.QtWidgets import (
    QDesktopWidget
)

from logging_module import (
    init_logging,
    LOG_LEVEL_INFO,
)

from google_calendar_utilities import (
    get_calendar_list_for_account
)

from events_mdi_window import MDIWindow

from get_events_thread import start_getting_events_to_display_main_loop_thread

from globals import app_globals

from system_tray import app_system_tray

def create_and_show_mdi_window():
    global g_globals
    global g_mdi_window

    g_mdi_window = MDIWindow(g_globals)

    # Set the MDI window size to be a little more than the event window size
    g_mdi_window.setFixedWidth(730 + 100)
    g_mdi_window.setFixedHeight(650 + 100)

    # Show the window on the main monitor
    monitor = QDesktopWidget().screenGeometry(0)
    g_mdi_window.move(monitor.left(), monitor.top())

    g_mdi_window.show()

def prep_google_accounts_and_calendars():
    global g_globals

    for google_account in g_globals.config.google_accounts:
        get_calendar_list_for_account(g_globals.logger, google_account)

# Main
if __name__ == "__main__":
    g_globals = app_globals()

    prep_google_accounts_and_calendars()

    # Start a thread to look for events to display
    start_getting_events_to_display_main_loop_thread(g_globals)

    create_and_show_mdi_window()

    sys_tray = app_system_tray(g_globals, g_mdi_window)

    g_globals.app.exec_()