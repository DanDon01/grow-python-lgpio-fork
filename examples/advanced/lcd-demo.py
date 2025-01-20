#!/usr/bin/env python3

import logging

import ST7735
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info(
    """lcd.py - Hello, World! example on the 0.96" LCD.

Press Ctrl+C to exit!

"""
)

# Width and height to calculate text position.
WIDTH = 160
HEIGHT = 80

def test_display_pins():
    """Cycle through a few pins to see which one works correctly."""
    pins = [0, 1]  # CE0 and CE1
    for pin in pins:
        try:
            logging.info(f"Testing pin {pin}...")
            disp = ST7735.ST7735(
                port=0, cs=pin, dc=9, backlight=12, rotation=270, spi_speed_hz=10000000
            )
            disp.begin()
            img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            font_size = 25
            font = ImageFont.truetype(UserFont, font_size)
            text_colour = (255, 255, 255)
            back_colour = (0, 170, 170)
            message = f"Pin {pin} works!"
            bbox = draw.textbbox((0, 0), message, font)
            size_x, size_y = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (WIDTH - size_x) / 2
            y = (HEIGHT / 2) - (size_y / 2)
            draw.rectangle((0, 0, 160, 80), back_colour)
            draw.text((x, y), message, font=font, fill=text_colour)
            disp.display(img)
            logging.info(f"Pin {pin} works!")
            return pin
        except Exception as e:
            logging.error(f"Pin {pin} failed: {e}")
    return None

# Create LCD class instance.
disp = ST7735.ST7735(
    port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=10000000
)

# Initialize display.
try:
    disp.begin()
except Exception as e:
    logging.error(f"Failed to initialize display: {e}")
    working_pin = test_display_pins()
    if working_pin is not None:
        logging.info(f"Using working pin {working_pin}")
        disp = ST7735.ST7735(
            port=0, cs=working_pin, dc=9, backlight=12, rotation=270, spi_speed_hz=10000000
        )
        disp.begin()
    else:
        logging.error("No working pin found. Exiting.")
        exit(1)

# Width and height to calculate text position.
WIDTH = disp.width
HEIGHT = disp.height

# New canvas to draw on.
img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)

# Text settings.
font_size = 25
font = ImageFont.truetype(UserFont, font_size)
text_colour = (255, 255, 255)
back_colour = (0, 170, 170)

message = "Hello, World!"
bbox = draw.textbbox((0, 0), message, font)
size_x, size_y = bbox[2] - bbox[0], bbox[3] - bbox[1]

# Calculate text position
x = (WIDTH - size_x) / 2
y = (HEIGHT / 2) - (size_y / 2)

# Draw background rectangle and write text.
draw.rectangle((0, 0, 160, 80), back_colour)
draw.text((x, y), message, font=font, fill=text_colour)
disp.display(img)

# Keep running.
try:
    while True:
        pass

# Turn off backlight on control-c
except KeyboardInterrupt:
    disp.set_backlight(0)
