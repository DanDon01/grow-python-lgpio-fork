import time
from PIL import Image, ImageDraw, ImageFont
import ST7735

DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 80

display = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=80000000,
    invert=False,  # Try toggling this
)
display.begin()

def show_colour(colour, name):
    image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), colour)
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), name, fill=(255, 255, 255) if colour != (255, 255, 255) else (0, 0, 0))
    display.display(image)
    time.sleep(2)

colours = [
    ((255, 0, 0), "Red"),
    ((0, 255, 0), "Green"),
    ((0, 0, 255), "Blue"),
    ((255, 255, 255), "White"),
    ((0, 0, 0), "Black"),
]

for colour, name in colours:
    show_colour(colour, name)
