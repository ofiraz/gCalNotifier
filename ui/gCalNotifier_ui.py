# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gCalNotifier.ui'
##
## Created by: Qt User Interface Compiler version 6.1.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_w_event(object):
    def setupUi(self, w_event):
        if not w_event.objectName():
            w_event.setObjectName(u"w_event")
        w_event.setEnabled(True)
        w_event.resize(715, 649)
        self.l_event_name = QLabel(w_event)
        self.l_event_name.setObjectName(u"l_event_name")
        self.l_event_name.setGeometry(QRect(70, 10, 581, 31))
        self.l_event_name.setTextFormat(Qt.MarkdownText)
        self.l_event_name.setAlignment(Qt.AlignCenter)
        self.l_event_name.setWordWrap(True)
        self.l_event_name.setOpenExternalLinks(True)
        self.pb_dismiss = QPushButton(w_event)
        self.pb_dismiss.setObjectName(u"pb_dismiss")
        self.pb_dismiss.setGeometry(QRect(590, 290, 100, 32))
        self.layoutWidget = QWidget(w_event)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(40, 250, 346, 32))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.pb_m10m = QPushButton(self.layoutWidget)
        self.pb_m10m.setObjectName(u"pb_m10m")

        self.horizontalLayout.addWidget(self.pb_m10m)

        self.pb_m5m = QPushButton(self.layoutWidget)
        self.pb_m5m.setObjectName(u"pb_m5m")

        self.horizontalLayout.addWidget(self.pb_m5m)

        self.pb_m2m = QPushButton(self.layoutWidget)
        self.pb_m2m.setObjectName(u"pb_m2m")

        self.horizontalLayout.addWidget(self.pb_m2m)

        self.pb_m1m = QPushButton(self.layoutWidget)
        self.pb_m1m.setObjectName(u"pb_m1m")

        self.horizontalLayout.addWidget(self.pb_m1m)

        self.pb_0m = QPushButton(self.layoutWidget)
        self.pb_0m.setObjectName(u"pb_0m")

        self.horizontalLayout.addWidget(self.pb_0m)

        self.layoutWidget1 = QWidget(w_event)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(40, 290, 503, 32))
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.pb_1m = QPushButton(self.layoutWidget1)
        self.pb_1m.setObjectName(u"pb_1m")

        self.horizontalLayout_2.addWidget(self.pb_1m)

        self.pb_5m = QPushButton(self.layoutWidget1)
        self.pb_5m.setObjectName(u"pb_5m")

        self.horizontalLayout_2.addWidget(self.pb_5m)

        self.pb_15m = QPushButton(self.layoutWidget1)
        self.pb_15m.setObjectName(u"pb_15m")

        self.horizontalLayout_2.addWidget(self.pb_15m)

        self.pb_30m = QPushButton(self.layoutWidget1)
        self.pb_30m.setObjectName(u"pb_30m")

        self.horizontalLayout_2.addWidget(self.pb_30m)

        self.pb_1h = QPushButton(self.layoutWidget1)
        self.pb_1h.setObjectName(u"pb_1h")

        self.horizontalLayout_2.addWidget(self.pb_1h)

        self.pb_2h = QPushButton(self.layoutWidget1)
        self.pb_2h.setObjectName(u"pb_2h")

        self.horizontalLayout_2.addWidget(self.pb_2h)

        self.pb_4h = QPushButton(self.layoutWidget1)
        self.pb_4h.setObjectName(u"pb_4h")

        self.horizontalLayout_2.addWidget(self.pb_4h)

        self.pb_8h = QPushButton(self.layoutWidget1)
        self.pb_8h.setObjectName(u"pb_8h")

        self.horizontalLayout_2.addWidget(self.pb_8h)

        self.l_icon = QLabel(w_event)
        self.l_icon.setObjectName(u"l_icon")
        self.l_icon.setGeometry(QRect(20, 10, 81, 71))
        self.l_icon.setPixmap(QPixmap(u"../../../../code/gCalNotifier/icons8-calendar-64.png"))
        self.l_icon.setScaledContents(True)
        self.l_icon.setOpenExternalLinks(True)
        self.layoutWidget2 = QWidget(w_event)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(40, 80, 651, 162))
        self.verticalLayout = QVBoxLayout(self.layoutWidget2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.l_account = QLabel(self.layoutWidget2)
        self.l_account.setObjectName(u"l_account")

        self.verticalLayout.addWidget(self.l_account)

        self.l_all_day = QLabel(self.layoutWidget2)
        self.l_all_day.setObjectName(u"l_all_day")

        self.verticalLayout.addWidget(self.l_all_day)

        self.l_event_start = QLabel(self.layoutWidget2)
        self.l_event_start.setObjectName(u"l_event_start")

        self.verticalLayout.addWidget(self.l_event_start)

        self.l_event_end = QLabel(self.layoutWidget2)
        self.l_event_end.setObjectName(u"l_event_end")

        self.verticalLayout.addWidget(self.l_event_end)

        self.l_event_link = QLabel(self.layoutWidget2)
        self.l_event_link.setObjectName(u"l_event_link")
        self.l_event_link.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.l_event_link)

        self.l_location_or_video_link = QLabel(self.layoutWidget2)
        self.l_location_or_video_link.setObjectName(u"l_location_or_video_link")

        self.verticalLayout.addWidget(self.l_location_or_video_link)

        self.l_video_link = QLabel(self.layoutWidget2)
        self.l_video_link.setObjectName(u"l_video_link")

        self.verticalLayout.addWidget(self.l_video_link)

        self.pb_open_video_and_snooze = QPushButton(w_event)
        self.pb_open_video_and_snooze.setObjectName(u"pb_open_video_and_snooze")
        self.pb_open_video_and_snooze.setGeometry(QRect(550, 210, 141, 32))
        self.pb_open_video_and_dismiss = QPushButton(w_event)
        self.pb_open_video_and_dismiss.setObjectName(u"pb_open_video_and_dismiss")
        self.pb_open_video_and_dismiss.setGeometry(QRect(460, 210, 101, 32))
        self.tabWidget = QTabWidget(w_event)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(40, 330, 651, 311))
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabWidget.setTabShape(QTabWidget.Rounded)
        self.tabWidget.setElideMode(Qt.ElideRight)
        self.tabWidget.setUsesScrollButtons(False)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.t_description = QTextBrowser(self.tab)
        self.t_description.setObjectName(u"t_description")
        self.t_description.setGeometry(QRect(0, 0, 641, 271))
        self.t_description.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.t_description.setAutoFormatting(QTextEdit.AutoAll)
        self.t_description.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.t_description.setOpenExternalLinks(True)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.t_raw_event = QTextBrowser(self.tab_2)
        self.t_raw_event.setObjectName(u"t_raw_event")
        self.t_raw_event.setGeometry(QRect(10, 10, 631, 261))
        self.tabWidget.addTab(self.tab_2, "")
        self.l_time_left = QLabel(w_event)
        self.l_time_left.setObjectName(u"l_time_left")
        self.l_time_left.setGeometry(QRect(260, 130, 421, 20))
        self.l_time_left.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.pb_open_video = QPushButton(w_event)
        self.pb_open_video.setObjectName(u"pb_open_video")
        self.pb_open_video.setGeometry(QRect(370, 210, 101, 32))
        self.l_missing_video = QLabel(w_event)
        self.l_missing_video.setObjectName(u"l_missing_video")
        self.l_missing_video.setGeometry(QRect(170, 60, 371, 16))
        font = QFont()
        font.setPointSize(17)
        font.setBold(True)
        self.l_missing_video.setFont(font)
        self.pb_hidden_button = QPushButton(w_event)
        self.pb_hidden_button.setObjectName(u"pb_hidden_button")
        self.pb_hidden_button.setGeometry(QRect(40, 10, 100, 32))

        self.retranslateUi(w_event)

        self.pb_hidden_button.setDefault(True)


        QMetaObject.connectSlotsByName(w_event)
    # setupUi

    def retranslateUi(self, w_event):
        w_event.setWindowTitle(QCoreApplication.translate("w_event", u"Event Name", None))
        self.l_event_name.setText(QCoreApplication.translate("w_event", u"Event Name", None))
        self.pb_dismiss.setText(QCoreApplication.translate("w_event", u"Dismiss", None))
        self.pb_m10m.setText(QCoreApplication.translate("w_event", u"-10m", None))
        self.pb_m5m.setText(QCoreApplication.translate("w_event", u"-5m", None))
        self.pb_m2m.setText(QCoreApplication.translate("w_event", u"-2m", None))
        self.pb_m1m.setText(QCoreApplication.translate("w_event", u"-1m", None))
        self.pb_0m.setText(QCoreApplication.translate("w_event", u"0m", None))
        self.pb_1m.setText(QCoreApplication.translate("w_event", u"1m", None))
        self.pb_5m.setText(QCoreApplication.translate("w_event", u"5m", None))
        self.pb_15m.setText(QCoreApplication.translate("w_event", u"15m", None))
        self.pb_30m.setText(QCoreApplication.translate("w_event", u"30m", None))
        self.pb_1h.setText(QCoreApplication.translate("w_event", u"1h", None))
        self.pb_2h.setText(QCoreApplication.translate("w_event", u"2h", None))
        self.pb_4h.setText(QCoreApplication.translate("w_event", u"4h", None))
        self.pb_8h.setText(QCoreApplication.translate("w_event", u"8h", None))
#if QT_CONFIG(tooltip)
        self.l_icon.setToolTip(QCoreApplication.translate("w_event", u"<a target=\"_blank\" href=\"https://icons8.com/icon/A6tLwUMQ6zkN/calendar\">Calendar</a> icon by <a target=\"_blank\" href=\"https://icons8.com\">Icons8</a>", None))
#endif // QT_CONFIG(tooltip)
        self.l_icon.setText("")
        self.l_account.setText(QCoreApplication.translate("w_event", u"Account", None))
        self.l_all_day.setText(QCoreApplication.translate("w_event", u"All Day?", None))
        self.l_event_start.setText(QCoreApplication.translate("w_event", u"Event Start", None))
        self.l_event_end.setText(QCoreApplication.translate("w_event", u"Event End", None))
        self.l_event_link.setText(QCoreApplication.translate("w_event", u"Link to event in GCal", None))
        self.l_location_or_video_link.setText(QCoreApplication.translate("w_event", u"Location or Zoom", None))
        self.l_video_link.setText(QCoreApplication.translate("w_event", u"Video Link", None))
        self.pb_open_video_and_snooze.setText(QCoreApplication.translate("w_event", u"and Snooze for 5m", None))
        self.pb_open_video_and_dismiss.setText(QCoreApplication.translate("w_event", u"and Dismiss", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("w_event", u"Description", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("w_event", u"Raw Event", None))
        self.l_time_left.setText(QCoreApplication.translate("w_event", u"TextLabel", None))
        self.pb_open_video.setText(QCoreApplication.translate("w_event", u"Open Video", None))
        self.l_missing_video.setText(QCoreApplication.translate("w_event", u"There are multiple attendees but no video link", None))
        self.pb_hidden_button.setText(QCoreApplication.translate("w_event", u"HiddenButton", None))
    # retranslateUi

