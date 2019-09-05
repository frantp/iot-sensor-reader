from sensors.base.base_sensor import BaseReader
import datetime
from collections import OrderedDict
import board
import busio
from Adafruit_SSD1306 import SSD1306_128_32, SSD1306_128_64
from PIL import Image, ImageDraw, ImageFont
import subprocess
import socket


class Reader(BaseReader):
    def __init__(self, model64, rst=None):
        super().__init__()
        self._disp = SSD1306_128_64(rst) if model64 else SSD1306_128_32(rst)

    def read(self):
        # Initialize library.
        self._disp.begin()
        
        # Clear display.
        self._disp.clear()
        self._disp.display()
        
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        width = self._disp.width
        height = self._disp.height
        image = Image.new('1', (width, height))
        
        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)
        
        # Draw a black filled box to clear the image.
        draw.rectangle((0,0,width,height), outline=0, fill=0)

        # First define some constants to allow easy resizing of shapes.
    	padding = -2
    	top = padding
    	bottom = height-padding
        x = 0

        # Load default font.
        font = ImageFont.load_default()

        # Retrieve values.
        timestr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            ssid = subprocess.check_output("/sbin/iwgetid -r", shell = True)
                .decode("utf-8")
        except:
            ssid = "---"
        device_id = socket.gethostname()

        # Write text
        draw.text((x, top + 0),               timestr,   font=font, fill=255)
        draw.text((x, top + 16), "SSID:   " + ssid,      font=font, fill=255)
        draw.text((x, top + 24), "DevID:  " + device_id, font=font, fill=255)

        # Display image.
        self._disp.image(image)
        self._disp.display()

        return None, None
