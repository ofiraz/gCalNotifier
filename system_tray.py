from PyQt5.QtWidgets import QMainWindow

from PyQt5 import QtCore

from icon_manager import *

from MultipleEventsWindow import *

class app_system_tray(QMainWindow):
    def __init__(self, globals):
        super(app_system_tray, self).__init__()

        self.globals = globals
        self.globals.app_system_tray = self
        self.c_num_of_displayed_events = 0

        # Create the system_tray
        #self.system_tray = QSystemTrayIcon(self)

        # Set the app icon
        self.globals.icon_manager = icon_manager(self.globals.app) #, self.system_tray)

        #self.system_tray.setVisible(True)

        # Prevent the closing of the system tray when the last event window closes
        self.globals.app.setQuitOnLastWindowClosed(False) 

        self.globals.displayed_events.set_add_cb(self.add_event_to_display_cb)
        self.globals.displayed_events.set_remove_cb(self.remove_event_from_display_cb)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.present_relevant_events_in_windows) 
        self.timer.start(int(self.globals.config.refresh_frequency/2) * 1000)

        #self.system_tray.show()

    def add_event_to_display_cb(self, parsed_event):
        self.c_num_of_displayed_events = self.c_num_of_displayed_events + 1

    def remove_event_from_display_cb(self, parse_event):
        self.c_num_of_displayed_events = self.c_num_of_displayed_events - 1

    def show_window(self, parsed_event):
        if (self.globals.multiple_events_window == None):
            self.globals.multiple_events_window = MultipleEventsTable(self.globals, parsed_event)

        else:
            self.globals.multiple_events_window.add_event(parsed_event)

        self.globals.events_logger.debug("Displaying event:" + parsed_event.event_name)

    def present_relevant_events(self):
        while True:
            event_key_str, parsed_event = self.globals.events_to_present.pop()
            if (event_key_str == None):
                # No more entries to present
                break
            
            if(self.globals.displayed_events.is_event_in(event_key_str)):
                # The event is already displayed with older data, mark it so the new data will be reflected for the event
                if (self.globals.multiple_events_window):
                    self.globals.multiple_events_window.update_event(parsed_event)

            else: # A totaly new event
                # Add the new event to the displayed events list    
                self.globals.displayed_events.add_event(event_key_str, parsed_event)
                self.show_window(parsed_event)

    def present_relevant_events_in_windows(self):
        self.globals.logger.debug("Presenting relevant events")

        self.present_relevant_events()

        self.timer.start(int(self.globals.config.refresh_frequency/2) * 1000)
