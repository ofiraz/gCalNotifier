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
    msg = QMessageBox()
    msg.setWindowTitle("gCalNotifier Tray App")
    msg.setText(text)
    msg.setIcon(icon)
    msg.exec_()

def gCalNotifier_thread_exit():
    my_message_box(
        "The gCalNotifier app was closed, might not be on purpose!",
        QMessageBox.Critical)

def start_gCalNotifier():
    if (my_thread.isRunning()):
        my_message_box(
            "The gCalNotifier app is already running",
            QMessageBox.Information)
    
    else:
        my_thread.start()

def end_app():
    if (my_thread.isRunning()):
        print(my_thread.proc.pid)

        my_thread.proc.terminate()
        my_thread.proc.wait()

    app.quit()


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# Create the icon
icon = QIcon(APP_ICON)
app.setWindowIcon(icon)

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()

start_gCalNot = QAction("Start gCalNotifier")
start_gCalNot.triggered.connect(start_gCalNotifier)
menu.addAction(start_gCalNot)

# Add a Quit option to the menu.
quit = QAction("Quit")
quit.triggered.connect(end_app)
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

my_thread = gCalNotifier_Thread()
my_thread.finished.connect(gCalNotifier_thread_exit)

start_gCalNotifier()

app.exec_()
