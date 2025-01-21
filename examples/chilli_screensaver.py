from PIL import Image, ImageDraw, ImageFont
import time
from monitor import display_lock  # Import the display_lock from monitor.py

def draw_chilli_animation(display, icons, stop_event):
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


