from PyQt5.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QAction
)

from PyQt5.QtGui import (
    QIcon
)

APP_ICON = 'icons8-calendar-64.png'

import sys

sys.path.insert(1, '/Users/ofir/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

from globals import app_globals

class app_system_tray:
    def __init__(self, globals, mdi_window):
        self.globals = globals
        self.mdi_window = mdi_window

        # Create the icon
        icon = QIcon(APP_ICON)

        # Create the system_tray
        self.system_tray = QSystemTrayIcon()
        self.system_tray.setIcon(icon)
        self.system_tray.setVisible(True)

        # Create the system_tray_menu
        self.system_tray_menu = QMenu()

        self.logs_menu_item = QAction("Logs")
        self.logs_menu_item.triggered.connect(self.open_logs_window)
        self.system_tray_menu.addAction(self.logs_menu_item)

        self.reset_menu_item = QAction("Clear dismissed and snoozed")
        self.reset_menu_item.triggered.connect(self.clear_dismissed_and_snoozed)
        self.system_tray_menu.addAction(self.reset_menu_item)

        # Add a Quit option to the menu.
        self.quit_menu_item = QAction("Quit")
        self.quit_menu_item.triggered.connect(self.quit_app)
        self.system_tray_menu.addAction(self.quit_menu_item)

        # Add the menu to the system_tray
        self.system_tray.setContextMenu(self.system_tray_menu)

    def open_logs_window(self):       
        self.logs_window = LogWidget(warn_before_close=False)

        filename = "/Users/ofir/git/personal/gCalNotifier/EventsLog.log"
        comm = "tail -f " + filename

        self.logs_window.setCommand(comm)

        self.logs_window.setWindowTitle("Logs")

        self.logs_window.setFixedWidth(730 + 100)
        self.logs_window.setFixedHeight(650 + 100)

        self.logs_window.show()

    def clear_dismissed_and_snoozed(self):      
        self.globals.events_logger.info("Clearing dismissed and snoozed")

        self.globals.resest_is_needed()

    def quit_app(self):
        # Let the MDI window know that the app is closing
        self.mdi_window.need_to_close_the_window()

        # Close the app
        self.globals.app.quit()

