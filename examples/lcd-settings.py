#!/usr/bin/env python3
import logging
import time
from PIL import Image, ImageDraw, ImageFont
import ST7735

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Display dimensions
DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 80

# Define colour sets
COLOURS = [
    ("White", (255, 255, 255)),
    ("Red", (255, 0, 0)),
    ("Green", (0, 255, 0)),
    ("Blue", (0, 0, 255)),
    ("Black", (0, 0, 0))
]

# Fonts for testing
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Adjust if needed
FONT_SIZE = 16

# Create display instance
def init_display(invert=False, spi_speed=8000000):
    """Initialise the display with given settings."""
    try:
        display = ST7735.ST7735(
            port=0,
            cs=0,
            dc=9,
            backlight=12,
            rotation=270,
            spi_speed_hz=spi_speed,
            invert=invert
        )
        display.begin()
        logging.info(f"Display initialised: invert={invert}, spi_speed={spi_speed}")
        return display
    except Exception as e:
        logging.error(f"Failed to initialise display: {e}")
        return None

def draw_test_pattern(display, colour, message):
    """Draw a test pattern with the specified colour and message."""
    image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), colour)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        logging.warning("Custom font not found, using default font")
        font = ImageFont.load_default()

    text = f"Testing: {message}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_x = (DISPLAY_WIDTH - text_width) // 2
    text_y = (DISPLAY_HEIGHT - text_height) // 2

    draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)
    display.display(image)
    time.sleep(2)


# Test different configurations
def run_tests():
    spi_speeds = [1000000, 4000000, 8000000, 16000000]
    invert_options = [False, True]
    
    for spi_speed in spi_speeds:
        for invert in invert_options:
            display = init_display(invert=invert, spi_speed=spi_speed)
            if not display:
                logging.error("Skipping tests due to display initialisation failure")
                continue

            logging.info(f"Running tests: invert={invert}, spi_speed={spi_speed}")
            for colour_name, colour_value in COLOURS:
                logging.info(f"Testing colour: {colour_name}")
                draw_test_pattern(display, colour_value, f"{colour_name} (SPI={spi_speed})")

            logging.info("Clearing display")
            display.display(Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0)))
            time.sleep(2)

if __name__ == "__main__":
    run_tests()
