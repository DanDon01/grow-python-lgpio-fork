# This is version 2.0 of the code

from PIL import Image, ImageEnhance
import time
import logging
from threading import Event, Lock
import math
import colorsys

def tint_image(image, hue):
    """Tint the image with a specific hue while maintaining its alpha channel."""
    # Convert hue to RGB (hue ranges from 0 to 1)
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    
    # Split the image into bands
    r, g, b, a = image.split()
    
    # Create a new image with the tint color
    tinted = Image.merge('RGB', (
        r.point(lambda x: int(x * rgb[0] * 2.0)),  # Multiply by 2 for stronger colors
        g.point(lambda x: int(x * rgb[1] * 2.0)),
        b.point(lambda x: int(x * rgb[2] * 2.0))
    ))
    
    # Add back the alpha channel
    tinted.putalpha(a)
    return tinted

def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    logging.info("TEST TEST TEST - USING CHILLI_SCREENSAVER.PY")
    try:
        chilli_icon = icons['chilli']
        width, height = display.width, display.height
        x, y = 0, 0  # Starting position
        dx, dy = 2, 2  # Movement speed and direction
        angle = 0  # Starting angle for rotation
        rotation_speed = 1  # Degrees per frame (slow rotation)
        
        # Color transition variables
        hue = 0.33  # Start with green (HSV: 120 degrees = 0.33)
        hue_step = 0.001  # Small step for smooth transition
        
        while not stop_event.is_set():
            try:
                # Create a new image for each frame
                image = Image.new("RGB", (width, height), (0, 0, 0))
                
                # Tint and rotate the chilli
                tinted_chilli = tint_image(chilli_icon, hue)
                rotated_chilli = tinted_chilli.rotate(angle, expand=True, resample=Image.BICUBIC)
                
                # Calculate position adjustment for rotated image
                rot_width, rot_height = rotated_chilli.size
                x_adjust = (rot_width - chilli_icon.size[0]) // 2
                y_adjust = (rot_height - chilli_icon.size[1]) // 2
                
                # Draw rotated and tinted chilli
                image.paste(rotated_chilli, (x - x_adjust, y - y_adjust), mask=rotated_chilli)
                
                # Update position (bouncing)
                x += dx
                y += dy
                
                # Bounce off edges
                if x <= x_adjust or x >= width - (chilli_icon.size[0] - x_adjust):
                    dx = -dx
                if y <= y_adjust or y >= height - (chilli_icon.size[1] - y_adjust):
                    dy = -dy
                
                # Update rotation
                angle = (angle + rotation_speed) % 360
                
                # Update color (green -> yellow -> red)
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
    


