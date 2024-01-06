from PIL import Image, ImageFont, ImageDraw
from PyQt5 import QtGui

NO_REMINDERS_ICON = 'icons/icons8-calendar-ice-cream/icons8-calendar-96.png'
REMINDERS_EXIST_ICON = 'icons/icons8-calendar-kmg-design-outline-color/icons8-calendar-64.png'

def set_icon_with_number(app, number, sys_tray=None, show_number_in_icon = False):
    if (number == 0): # No reminders
        # Just show the icon for no reminders
        output = NO_REMINDERS_ICON

    else: # At least one reminder
        if (not show_number_in_icon):
            # Just show a reminders icon
            output = REMINDERS_EXIST_ICON

        else: # Show the number of reminders - generate that icon
            background = REMINDERS_EXIST_ICON
            output = 'icon-with-number.png'

            # Create a font object from a True-Type font file and specify the font size.
            fontobj = ImageFont.truetype('/Library/Fonts/Arial Unicode.ttf', 24)

            img = Image.open(background)
            draw = ImageDraw.Draw(img)

            # Write a text over the background image.
            # Parameters: location(x, y), text, textcolor(R, G, B), fontobject
            draw.text((0, 20), '{0:01d}'.format(number), (0, 0, 0), font=fontobj)
            img.save(output.format(number))

    icon = QtGui.QIcon(output)
    app.setWindowIcon(icon)

    if (sys_tray):
        sys_tray.setIcon(icon)
