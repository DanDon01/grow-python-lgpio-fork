from PIL import Image, ImageDraw, ImageFont
import time
import sys
import os
from threading import Event, Lock

def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    chilli_icon = icons['chilli']
    width, height = display.width, display.height
    x, y = 0, 0
    dx, dy = 1, 1

    while not stop_event.is_set():
        with display_lock:
            image = Image.new("RGB", (width, height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            image.paste(chilli_icon, (x, y), chilli_icon)
            display.display(image)

        x += dx
        y += dy

        if x + chilli_icon.width >= width or x <= 0:
            dx = -dx
        if y + chilli_icon.height >= height or y <= 0:
            dy = -dy

        time.sleep(0.05)

if __name__ == "__main__":
    # This part will be executed when the script is run directly
    from monitor import load_icons, display_lock
    import ST7735

    stop_event = Event()
    icons = load_icons()
    display = ST7735.ST7735(
        port=0,
        cs=0,
        dc=9,
        backlight=12,
        rotation=270,
        spi_speed_hz=40000000,
      #  invert=True,
      #  bgr=True
    )
    display.begin()
    draw_chilli_animation(display, icons, stop_event, display_lock)


