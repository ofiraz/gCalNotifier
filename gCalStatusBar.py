from PyQt5.QtGui import (
    QIcon
)

from PyQt5.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QMessageBox
)

from PyQt5.QtCore import QThread

import sys
import subprocess

sys.path.insert(1, '/Users/ofir/git/personal/pyqt-realtime-log-widget')
from pyqt_realtime_log_widget import LogWidget

LOG_FILE = "/Users/ofir/git/personal/gCalNotifier/gCalNotifier.txt"
PYTHON_BIN = "/Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9"
GCAL_PY = "/Users/ofir/git/personal/gCalNotifier/gCalNotifier.py"
APP_ICON = 'icons8-calendar-64.png'

class gCalNotifier_Thread(QThread):
    def run(self):
        out_file = open(LOG_FILE, "w")
        self.proc = subprocess.Popen(
            [PYTHON_BIN, GCAL_PY],
            stdout=out_file,
            stderr=out_file)
        self.proc.wait()

def my_message_box(text, icon):
    global msg

    msg = QMessageBox()
    msg.setWindowTitle("gCalNotifier Tray App")
    msg.setText(text)
    msg.setIcon(icon)
    msg.show()

def gCalNotifier_thread_exit():
    my_message_box(
        "The gCalNotifier app was closed, might not be on purpose!",
        QMessageBox.Critical)

def start_gCalNotifier():
    global g_gCalNotifier_thread

    if (g_gCalNotifier_thread.isRunning()):
        my_message_box(
            "The gCalNotifier app is already running",
            QMessageBox.Information)
    
    else:
        g_gCalNotifier_thread.start()

def end_app():
    global g_app
    global g_gCalNotifier_thread

    if (g_gCalNotifier_thread.isRunning()):
        print(g_gCalNotifier_thread.proc.pid)

        g_gCalNotifier_thread.proc.terminate()
        g_gCalNotifier_thread.proc.wait()

    g_app.quit()

def init_and_start_thread():
    global g_gCalNotifier_thread

    g_gCalNotifier_thread = gCalNotifier_Thread()

    g_gCalNotifier_thread.finished.connect(gCalNotifier_thread_exit)

    start_gCalNotifier()

def open_logs_window():
    global logs_window
    
    logs_window = LogWidget(warn_before_close=False)

    filename = "/Users/ofir/git/personal/gCalNotifier/EventsLog.log"
    comm = "tail -f " + filename

    logs_window.setCommand(comm)

    logs_window.setWindowTitle("Logs")
    logs_window.show()
    
def init_and_start_app():
    global g_app

    g_app = QApplication(sys.argv)

    g_app.setQuitOnLastWindowClosed(False)

    # Create the icon
    icon = QIcon(APP_ICON)
    g_app.setWindowIcon(icon)

    # Create the tray
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    # Create the menu
    menu = QMenu()

    start_gCalNot = QAction("Start gCalNotifier")
    start_gCalNot.triggered.connect(start_gCalNotifier)
    menu.addAction(start_gCalNot)

    logs_item = QAction("Logs")
    logs_item.triggered.connect(open_logs_window)
    menu.addAction(logs_item)

    # Add a Quit option to the menu.
    quit = QAction("Quit")
    quit.triggered.connect(end_app)
    menu.addAction(quit)

    # Add the menu to the tray
    tray.setContextMenu(menu)

    # Start the app
    g_app.exec_()

# Main
if __name__ == "__main__":
    init_and_start_thread()

    init_and_start_app()