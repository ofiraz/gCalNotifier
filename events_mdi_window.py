import sys

from PyQt5.QtWidgets import (
    QMainWindow, QMdiArea, QMdiSubWindow
)

from PyQt5 import QtCore

from EventWindow import EventWindow

sys.path.insert(1, '/Users/ofir/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

from events_collection import Events_Collection

from app_events_collections import App_Events_Collections

class MDIWindow(QMainWindow):
    c_num_of_displayed_events = 0
    count = 0

    def init_app_events_collections(self):
        self.app_events_collections = App_Events_Collections()

        self.app_events_collections.set_events_to_present(Events_Collection(self.logger, self.app_events_collections, "events_to_present"))
        self.app_events_collections.set_dismissed_events(Events_Collection(self.logger, self.app_events_collections, "dismissed_events"))
        self.app_events_collections.set_snoozed_events(Events_Collection(self.logger, self.app_events_collections, "snoozed_events"))
        self.app_events_collections.set_displayed_events(Events_Collection(self.logger, self.app_events_collections, "displayed_events", self.add_event_to_display_cb, self.remove_event_from_display_cb))

    def __init__(self, logger, events_logger, refresh_frequency):
        super().__init__()

        self.logger = logger
        self.events_logger = events_logger
        self.refresh_frequency = refresh_frequency

        self.init_app_events_collections()
 
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        bar = self.menuBar()
 
        file = bar.addMenu("File")
        file.addAction("Reset")
        file.addAction("Logs")
        file.addAction("Cascade")
        file.addAction("Tiled")
        file.triggered.connect(self.WindowTrig)
        self.update_mdi_title()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.present_relevant_events_in_sub_windows) 

    def show_window_in_mdi(self, event_key_str, parsed_event):
        event_win = EventWindow(self.logger, self.events_logger, self.app_events_collections, self)

        event_win.init_window_from_parsed_event(event_key_str, parsed_event)
        event_win.setFixedWidth(730)
        event_win.setFixedHeight(650)

        sub_win = QMdiSubWindow()
        sub_win.setWidget(event_win)
        self.mdi.addSubWindow(sub_win)
        sub_win.show()

        self.events_logger.info("Displaying event:" + parsed_event['event_name'])

        self.raise_()
        self.activateWindow()

    def present_relevant_events(self):
        while True:
            event_key_str, parsed_event = self.app_events_collections.events_to_present.pop()
            if (event_key_str == None):
                # No more entries to present
                return
            
            # Add the event to the presented events
            self.app_events_collections.displayed_events.add_event(event_key_str, parsed_event)
            
            self.show_window_in_mdi(event_key_str, parsed_event)

    def present_relevant_events_in_sub_windows(self):
        self.logger.debug("Presenting relevant events")

        self.present_relevant_events()

        if ((self.c_num_of_displayed_events > 0) and self.isMinimized()):
            # There is now at least one event, and the MDI is minimized - restore the window
            self.logger.info("Before showNormal")
            self.showNormal()
            self.logger.info("After showNormal")

        self.timer.start(int(self.refresh_frequency/2) * 1000)

    def update_mdi_title(self):
        self.setWindowTitle("[" + str(self.c_num_of_displayed_events) + "] gCalNotifier")

    def add_event_to_display_cb(self):
        self.logger.debug("add_event_to_display_cb start")

        self.c_num_of_displayed_events = self.c_num_of_displayed_events + 1

        self.logger.debug("add_event_to_display_cb update_mdi_title")
        self.update_mdi_title()

        self.logger.debug("add_event_to_display_cb end")

    def remove_event_from_display_cb(self):
        self.logger.debug("remove_event_from_display_cb start")

        self.c_num_of_displayed_events = self.c_num_of_displayed_events - 1

        self.logger.debug("remove_event_from_display_cb update_mdi_title")
        self.update_mdi_title()

        if (self.c_num_of_displayed_events == 0):
            # No events to show
            self.logger.debug("remove_event_from_display_cb showMinimized")

            self.showMinimized()

        self.logger.debug("remove_event_from_display_cb end")

    def reset_all_events(self):
        self.events_logger.info("Reseting the app")

    def showEvent(self, event):
        # This method will be called when the main MDI window is shown
        super().showEvent(event)  # Call the base class showEvent first
        self.present_relevant_events_in_sub_windows()

    def WindowTrig(self, p):
        if p.text() == "Reset":
            self.reset_all_events()

        elif p.text() == "Logs":
            window = LogWidget(warn_before_close=False)

            filename = "/Users/ofir/git/personal/gCalNotifier/EventsLog.log"
            comm = "tail -f " + filename

            window.setCommand(comm)

            sub = QMdiSubWindow()
            sub.setWidget(window)
            sub.setWindowTitle("Logs")
            self.mdi.addSubWindow(sub)
            sub.show()
 
        elif p.text() == "Cascade":
            self.mdi.cascadeSubWindows()
 
        elif p.text() == "Tiled":
            self.mdi.tileSubWindows()

