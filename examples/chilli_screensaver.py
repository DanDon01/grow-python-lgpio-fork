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
    # Convert hue to RGB with full saturation and value
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    
    # Create multipliers for stronger effect
    multiplier = 2.0  # Increase this for stronger colors
    r_mult = rgb[0] * multiplier
    g_mult = rgb[1] * multiplier
    b_mult = rgb[2] * multiplier
    
    # Split the image into bands
    r, g, b, a = image.split()
    
    # Create a new image with the tint color
    tinted = Image.merge('RGB', (
        r.point(lambda x: min(255, int(x * r_mult))),
        g.point(lambda x: min(255, int(x * g_mult))),
        b.point(lambda x: min(255, int(x * b_mult)))
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
        color_index = 0
        colors = [
            0.33,  # Green (HSV: 120 degrees)
            0.17,  # Yellow (HSV: 60 degrees)
            0.0    # Red (HSV: 0 degrees)
        ]
        color_step = 0.01  # Steps between colors
        current_hue = colors[0]
        
        while not stop_event.is_set():
            try:
                # Create a new image for each frame
                image = Image.new("RGB", (width, height), (0, 0, 0))
                
                # Tint the chilli with current color
                tinted_chilli = tint_image(chilli_icon, current_hue)
                image.paste(tinted_chilli, (x, y), mask=tinted_chilli)
                
                # Update position
                x += dx
                y += dy
                
                # Bounce off edges
                if x <= 0 or x >= width - chilli_icon.size[0]:
                    dx = -dx
                if y <= 0 or y >= height - chilli_icon.size[1]:
                    dy = -dy
                
                # Update color
                target_color = colors[color_index]
                if abs(current_hue - target_color) < color_step:
                    # Move to next color
                    color_index = (color_index + 1) % len(colors)
                    target_color = colors[color_index]
                
                # Move current_hue towards target_color
                if current_hue < target_color:
                    current_hue = min(target_color, current_hue + color_step)
                else:
                    current_hue = max(target_color, current_hue - color_step)
                
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
    


