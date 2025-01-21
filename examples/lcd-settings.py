import logging
import time
import sys
from PIL import Image, ImageDraw, ImageFont
import ST7735
import termios
import tty

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 80
FONT_SIZE = 14
ICON_PATH = "icons/veg-chilli.png"  # Change this to a valid icon path

def wait_for_space():
    """Wait for the user to press the space bar."""
    print("Press SPACE to continue or Q to quit...", end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == ' ':
                break
            elif ch.lower() == 'q':
                print("\nExiting.")
                sys.exit(0)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    print("\n")

def test_display(display, invert, bgr, spi_speed):
    """Test the display with given settings."""
    logging.info(f"Testing with invert={invert}, bgr={bgr}, spi_speed={spi_speed}")

    # Initialize display
    display = ST7735.ST7735(
        port=0,
        cs=0,  # Change to 1 if using CE1
        dc=9,
        backlight=12,
        rotation=270,
        spi_speed_hz=spi_speed,
        invert=invert,
        bgr=bgr
    )
    display.begin()

    # Create image
    image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Draw background
    draw.rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), fill=(0, 128, 128))

    # Load and draw icon
    try:
        icon = Image.open(ICON_PATH).convert("RGBA")
        image.paste(icon, (10, 10), mask=icon)
    except FileNotFoundError:
        logging.error(f"Icon not found at {ICON_PATH}")
        draw.text((10, 10), "Icon Missing", fill=(255, 0, 0))

    # Add text
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE)
    draw.text((10, 60), f"Invert={invert}, BGR={bgr}\nSPI={spi_speed // 1_000_000}MHz", font=font, fill=(255, 255, 255))

    # Display image
    display.display(image)

def main():
    settings = [
        (invert, bgr, spi_speed)
        for invert in [True, False]
        for bgr in [True, False]
        for spi_speed in [4000000, 10000000, 20000000, 40000000]
    ]

    logging.info("Starting display tests...")

    for invert, bgr, spi_speed in settings:
        print(f"Testing: invert={invert}, bgr={bgr}, spi_speed={spi_speed // 1_000_000}MHz")
        try:
            test_display(None, invert, bgr, spi_speed)
        except Exception as e:
            logging.error(f"Error testing settings invert={invert}, bgr={bgr}, spi_speed={spi_speed}: {e}")
        wait_for_space()

if __name__ == "__main__":
    main()
