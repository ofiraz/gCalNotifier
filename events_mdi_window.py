from PyQt5.QtWidgets import (
    QMainWindow, 
    QMdiArea, 
    QMdiSubWindow,
    QDesktopWidget
)

from PyQt5 import QtCore

from EventWindow import EventWindow

from set_icon_with_number import set_icon_with_number

class MDIWindow(QMainWindow):
    c_num_of_displayed_events = 0
    count = 0
    want_to_close = False

    def need_to_close_the_window(self):
        self.want_to_close = True

    def __init__(self, globals):
        super().__init__()

        self.globals = globals

        self.globals.displayed_events.set_add_cb(self.add_event_to_display_cb)
        self.globals.displayed_events.set_remove_cb(self.remove_event_from_display_cb)
 
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        bar = self.menuBar()
 
        # Menus
        window_menu = bar.addMenu("Window")
        window_menu.addAction("Cascade")
        window_menu.addAction("Tiled")
        window_menu.triggered.connect(self.WindowMenuTrigger)

        self.update_mdi_title_and_icon()

        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowMinimizeButtonHint
        )

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.present_relevant_events_in_sub_windows) 

        # Set the MDI window size to be a little more than the event window size
        self.setFixedWidth(730 + 100)
        self.setFixedHeight(650 + 100)

        # Show the window on the main monitor
        monitor = QDesktopWidget().screenGeometry(0)
        self.move(monitor.left(), monitor.top())

        self.show()

    # Prevent the window from getting closed
    def closeEvent(self, event):
        if self.want_to_close:
            super(MDIWindow, self).closeEvent(event)
        else:
            event.ignore()


    def WindowMenuTrigger(self, p):
        if p.text() == "Cascade":
            self.mdi.cascadeSubWindows()
 
        elif p.text() == "Tiled":
            self.mdi.tileSubWindows()

    def show_window_in_mdi(self, event_key_str, parsed_event):
        event_win = EventWindow(self.globals, use_mdi=True, p_mdi_window=self)

        event_win.init_window_from_parsed_event(event_key_str, parsed_event)
        event_win.setFixedWidth(730)
        event_win.setFixedHeight(650)

        sub_win = QMdiSubWindow()
        sub_win.setWidget(event_win)
        self.mdi.addSubWindow(sub_win)
        sub_win.show()

        self.globals.events_logger.info("Displaying event:" + parsed_event['event_name'])

        self.raise_()
        self.activateWindow()

    def present_relevant_events(self):
        at_list_one_event_presented = False
        while True:
            event_key_str, parsed_event = self.globals.events_to_present.pop()
            if (event_key_str == None):
                # No more entries to present
                break
            
            if(self.globals.displayed_events.is_event_in(event_key_str)):
                # The event is already displayed with older data, switch it to show the new data
                self.globals.displayed_events[event_key_str]['event_window'].init_window_from_parsed_event(event_key_str, parsed_event)

            else: # A totaly new event
                # Add the new event to the displayed events list    
                at_list_one_event_presented = True       
                self.globals.displayed_events.add_event(event_key_str, parsed_event)
                self.show_window_in_mdi(event_key_str, parsed_event)

        if (at_list_one_event_presented):
            self.update_mdi_title_and_icon()

    def present_relevant_events_in_sub_windows(self):
        self.globals.logger.debug("Presenting relevant events")

        self.present_relevant_events()

        if ((self.c_num_of_displayed_events > 0) and self.isMinimized()):
            # There is now at least one event, and the MDI is minimized - restore the window
            self.showNormal()

        self.timer.start(int(self.globals.config.refresh_frequency/2) * 1000)

    def update_mdi_title_and_icon(self):
        self.setWindowTitle("[" + str(self.c_num_of_displayed_events) + "] gCalNotifier")
        set_icon_with_number(self.globals.app, self.c_num_of_displayed_events)

    def add_event_to_display_cb(self, parsed_event):
        self.globals.logger.debug("add_event_to_display_cb start")

        self.c_num_of_displayed_events = self.c_num_of_displayed_events + 1

        self.globals.logger.debug("add_event_to_display_cb update_mdi_title_and_icon")

        self.globals.logger.debug("add_event_to_display_cb end")

    def remove_event_from_display_cb(self, parse_event):
        self.globals.logger.debug("remove_event_from_display_cb start")

        self.c_num_of_displayed_events = self.c_num_of_displayed_events - 1

        self.globals.logger.debug("remove_event_from_display_cb update_mdi_title_and_icon")
        self.update_mdi_title_and_icon()

        if (self.c_num_of_displayed_events == 0):
            # No events to show
            self.globals.logger.debug("remove_event_from_display_cb showMinimized")

            self.showMinimized()

        self.globals.logger.debug("remove_event_from_display_cb end")

    def showEvent(self, event):
        # This method will be called when the main MDI window is shown
        super().showEvent(event)  # Call the base class showEvent first
        self.present_relevant_events_in_sub_windows()

