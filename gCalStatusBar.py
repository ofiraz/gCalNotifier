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

import os
import sys
import subprocess

class gCalNotifier_Thread(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        #os.system("/Users/ofir/git/personal/gCalNotifier/gCalNotifier.sh")
        #self.proc = subprocess.Popen("/Users/ofir/git/personal/gCalNotifier/gCalNotifier.sh")
        out_file = open("/Users/ofir/git/personal/gCalNotifier/gCalNotifier.txt", "w")
        self.proc = subprocess.Popen(
            ["/Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9", "/Users/ofir/git/personal/gCalNotifier/gCalNotifier.py"],
            stdout=out_file,
            stderr=out_file)
        print("after")
        print(self.proc.pid)
        print("Waiting")
        self.proc.wait()
        print("Done")

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
        print("here")
        print(my_thread.proc.pid)

        my_thread.proc.terminate()
        my_thread.proc.wait()

    app.quit()


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# Create the icon
icon = QIcon('icons8-calendar-64.png')
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
