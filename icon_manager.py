from PIL import Image, ImageFont, ImageDraw
from PyQt5 import QtGui
import subprocess

from AppKit import NSApplication, NSApplicationActivationPolicyRegular

import AppKit
import time

NO_REMINDERS_ICON = 'icons8-gray-bell-64.png'
REMINDERS_EXIST_ICON = 'icons8-yellow-bell-64.png'

class icon_manager():
    def __init__(self, app): 
        self.app = app

        self.set_icon_no_events()

    def set_icon(self, icon_file):
        icon = QtGui.QIcon(icon_file)
        self.app.setWindowIcon(icon)

    
    def set_icon_no_events(self):
        # Show a gray bell
        self.set_icon('icons8-gray-bell-64.png')

    def set_icon_with_events(self, num_of_events_with_notifications, num_of_events_with_no_nofitications):
        if (num_of_events_with_notifications > 0):
            # Show a red bell
            background = 'icons8-red-bell-64.png'

        elif (num_of_events_with_no_nofitications > 0):
            # Show a yellow bell
            background = 'icons8-yellow-bell-64.png'

        else:
            # No events to show
            self.set_icon_no_events()

            return

        number_of_events = num_of_events_with_notifications + num_of_events_with_no_nofitications

        output = 'icon-with-number.png'

        # Create a font object from a True-Type font file and specify the font size.
        fontobj = ImageFont.truetype('/Library/Fonts/Arial Unicode.ttf', 24)

        img = Image.open(background)
        draw = ImageDraw.Draw(img)

        # Write a text over the background image.
        # Parameters: location(x, y), text, textcolor(R, G, B), fontobject
        draw.text((0, 20), '{0:01d}'.format(number_of_events), (0, 0, 0), font=fontobj)
        img.save(output.format(number_of_events))

        self.set_icon(output)

    def continuous_dock_icon_bounce(self):     
        try:            
            # Setup NSApplication properly
            app = NSApplication.sharedApplication()
            app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
            app.activateIgnoringOtherApps_(True)
                      
            time.sleep(0.7)
            
            # Use NSCriticalRequest for continuous bouncing
            attention_request_id = app.requestUserAttention_(AppKit.NSCriticalRequest)
            
            if attention_request_id < 0:
                print("❌ Continuous bouncing failed!")
                print(f"Continuous bounce NSCriticalRequest result: {attention_request_id}")
            
        except Exception as e:
            print(f"Continuous bounce setup failed: {e}")


