from collections import OrderedDict
import datetime
import socket
import subprocess
import time

from ..core import DriverBase
from PIL import Image, ImageDraw, ImageFont
from Adafruit_SSD1306 import SSD1306_128_32, SSD1306_128_64



class Driver(DriverBase):
    def __init__(self, model64, rst=None):
        super().__init__()
        self._disp = SSD1306_128_64(rst) if model64 else SSD1306_128_32(rst)


    def run(self):
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
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # Load default font.
        font = ImageFont.load_default()

        # Retrieve values.
        timestr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            ssid = subprocess.check_output("/sbin/iwgetid -r", shell = True) \
                .decode("utf-8")
        except:
            ssid = "---"
        device_id = socket.gethostname()

        # Write text
        t, l = -2, 0
        draw.text((l, t + 0),  " "       + timestr,     font=font, fill=255)
        draw.text((l, t + 8),  "---------------------", font=font, fill=255)
        draw.text((l, t + 16), "SSID:  " + ssid,        font=font, fill=255)
        draw.text((l, t + 24), "DevID: " + device_id,   font=font, fill=255)

        # Display image.
        self._disp.image(image)
        self._disp.display()

        return [(self.sid(), int(time.time() * 1e9), None)]
