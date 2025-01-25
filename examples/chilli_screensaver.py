# This is version 2.0 of the code

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import time
import sys
import os
from threading import Event, Lock
import logging
import colorsys

def tint_image(image, hue):
    """Tint the image with a specific hue while maintaining its alpha channel."""
    # Convert hue to RGB (hue ranges from 0 to 1)
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    
    # Split the image into bands
    r, g, b, a = image.split()
    
    # Create a new image with the tint color, with stronger effect
    tinted = Image.merge('RGB', (
        r.point(lambda x: int(x * rgb[0] * 1.5)),  # Increase color intensity
        g.point(lambda x: int(x * rgb[1] * 1.5)),
        b.point(lambda x: int(x * rgb[2] * 1.5))
    ))
    
    # Add back the alpha channel
    tinted.putalpha(a)
    
    return tinted

def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    try:
        chilli_icon = icons['chilli']
        width, height = display.width, display.height
        x, y = 0, 0  # Starting position
        dx, dy = 2, 2  # Movement speed and direction
        
        # Color transition variables
        hue = 0.33  # Start with green (HSV: 120 degrees = 0.33)
        hue_step = 0.005  # Larger step for more noticeable transition
        
        while not stop_event.is_set():
            try:
                # Create a new image for each frame
                image = Image.new("RGB", (width, height), (0, 0, 0))
                
                # Tint the chilli with current hue
                # Map hue to color transitions: green -> yellow -> red
                current_hue = max(0.0, min(0.33, hue))  # Clamp between 0 (red) and 0.33 (green)
                tinted_chilli = tint_image(chilli_icon, current_hue)
                
                # Draw single chilli at current position
                image.paste(tinted_chilli, (x, y), mask=tinted_chilli)
                
                # Update position
                x += dx
                y += dy
                
                # Bounce off edges
                if x <= 0 or x >= width - chilli_icon.size[0]:
                    dx = -dx
                if y <= 0 or y >= height - chilli_icon.size[1]:
                    dy = -dy
                
                # Update hue (cycle through green -> yellow -> red)
                hue -= hue_step  # Decrease hue to go from green to red
                if hue < 0:  # Reset when we reach red
                    hue = 0.33  # Back to green
                
                # Display the image with lock
                with display_lock:
                    display.display(image)
                
                time.sleep(0.03)  # Animation speed
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
        spi_speed_hz=80000000
    )
    display.begin()
    draw_chilli_animation(display, icons, stop_event, display_lock)
    


