# This is version 2.0 of the code

from PIL import Image, ImageDraw, ImageFont
import time
import sys
import os
from threading import Event, Lock
import logging

def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    try:
        chilli_icon = icons['chilli']
        width, height = display.width, display.height
        x, y = 0, 0  # Starting position
        dx, dy = 2, 2  # Movement speed and direction

        while not stop_event.is_set():
            try:
                # Create a new image for each frame
                image = Image.new("RGB", (width, height), (0, 0, 0))
                
                # Draw single chilli at current position
                image.paste(chilli_icon, (x, y), mask=chilli_icon)
                
                # Update position
                x += dx
                y += dy
                
                # Bounce off edges
                if x <= 0 or x >= width - chilli_icon.size[0]:
                    dx = -dx
                if y <= 0 or y >= height - chilli_icon.size[1]:
                    dy = -dy
                
                # Display the image with lock
                with display_lock:
                    display.display(image)
                
                time.sleep(0.03)  # Faster animation
            except Exception as e:
                logging.error(f"Error in animation loop: {e}")
                time.sleep(0.1)
    except Exception as e:
        logging.error(f"Error in screensaver animation: {e}")
    finally:
        logging.info("Screensaver animation stopped")

def cleanup_display(display):
    display.invert(False)  # Restore inversion setting
    display.bgr(False)     # Restore color order        

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
        spi_speed_hz=80000000,
      #  invert=False,
      #  bgr=True
    )
    display.begin()
    draw_chilli_animation(display, icons, stop_event, display_lock)
    


