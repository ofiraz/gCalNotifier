from PIL import Image, ImageFont, ImageDraw
from PyQt5 import QtGui

def set_icon_with_number(app, number, sys_tray=None):
    background = 'icons8-calendar-64.png'
    output = 'icon-with-number.png'

    if (number > 0):
        # Create a font object from a True-Type font file and specify the font size.
        fontobj = ImageFont.truetype('/Library/Fonts/Arial Unicode.ttf', 24)

        img = Image.open(background)
        draw = ImageDraw.Draw(img)

        # Write a text over the background image.
        # Parameters: location(x, y), text, textcolor(R, G, B), fontobject
    #    draw.text((0, 0), '{0:04d}'.format(i), (255, 0, 0), font=fontobj)
        draw.text((35, 32), '{0:01d}'.format(number), (0, 255, 255), font=fontobj)
        img.save(output.format(number))
    else:
        output = background

    icon = QtGui.QIcon(output)
    app.setWindowIcon(icon)

    if (sys_tray):
        sys_tray.setIcon(icon)
