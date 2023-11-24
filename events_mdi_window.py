import sys

from PyQt5.QtWidgets import (
    QMainWindow, QMdiArea, QMdiSubWindow
)

from PyQt5 import QtCore

from EventWindow import EventWindow

sys.path.insert(1, '/Users/ofir/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

from set_icon_with_number import set_icon_with_number

class MDIWindow(QMainWindow):
    c_num_of_displayed_events = 0
    count = 0
    want_to_close = False

    def need_to_close_the_window(self):
        self.want_to_close = True

    def __init__(self, globals, app, refresh_frequency):
        super().__init__()

        self.globals = globals
        self.app = app
        self.refresh_frequency = refresh_frequency

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
        event_win = EventWindow(self.globals, self)

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
        while True:
            event_key_str, parsed_event = self.globals.displayed_events.pop_from_another_collection_and_add_this_one(self.globals.events_to_present)
            if (event_key_str == None):
                # No more entries to present
                return
            
            self.show_window_in_mdi(event_key_str, parsed_event)

    def present_relevant_events_in_sub_windows(self):
        self.globals.logger.debug("Presenting relevant events")

        self.present_relevant_events()

        if ((self.c_num_of_displayed_events > 0) and self.isMinimized()):
            # There is now at least one event, and the MDI is minimized - restore the window
            self.showNormal()

        self.timer.start(int(self.refresh_frequency/2) * 1000)

    def update_mdi_title_and_icon(self):
        self.setWindowTitle("[" + str(self.c_num_of_displayed_events) + "] gCalNotifier")
        set_icon_with_number(self.app, self.c_num_of_displayed_events)

    def add_event_to_display_cb(self):
        self.globals.logger.debug("add_event_to_display_cb start")

        self.c_num_of_displayed_events = self.c_num_of_displayed_events + 1

        self.globals.logger.debug("add_event_to_display_cb update_mdi_title_and_icon")
        self.update_mdi_title_and_icon()

        self.globals.logger.debug("add_event_to_display_cb end")

    def remove_event_from_display_cb(self):
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

