from PIL import Image
import ST7735
import time

# Display dimensions
DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 80

# Initialise the display
display = ST7735.ST7735(
    port=0,          # SPI0
    cs=0,            # Chip Select (0 or 1 depending on wiring)
    dc=9,            # Data/Command pin
    backlight=12,    # Backlight pin
    rotation=270,    # Orientation of the display
    spi_speed_hz=8000000,  # SPI speed
    invert=False,    # Whether to invert colours
    bgr=False        # Test with True/False to see colour difference
)

# Begin the display
display.begin()

# Create a white image
image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(255, 255, 255))

# Display the image
display.display(image)

COLOR_WHITE = (255, 255, 255)
COLOR_BLUE = (31, 137, 251)
COLOR_GREEN = (99, 255, 1)
COLOR_YELLOW = (254, 219, 82)
COLOR_RED = (247, 0, 63)
COLOR_BLACK = (0, 0, 0)

COLORS = [
    ("Red", (247, 0, 63)),
    ("Green", (99, 255, 1)),
    ("Blue", (31, 137, 251)),
    ("Black", (0, 0, 0)),
    ("White", (255, 255, 255)),
    ("Yellow", (254, 219, 82))
]

for name, color in COLORS:
    print(f"Testing {name} color...")
    image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color)
    display.display(image)
    time.sleep(2)


# Keep the screen on
try:
    while True:
        pass
except KeyboardInterrupt:
    # Clean exit
    display.set_backlight(0)  # Turn off backlight on exit
    print("\nExiting...")

