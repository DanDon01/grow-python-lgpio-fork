# This is version 2.0 of the code

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import time
import sys
import os
from threading import Event, Lock
import logging
import colorsys

def tint_image(image, color):
    """Tint the image with RGB color while maintaining its alpha channel."""
    # Split the image into bands
    r, g, b, a = image.split()
    
    # Create a new image with the tint color
    tinted = Image.merge('RGB', (
        r.point(lambda x: min(255, int(x * color[0]))),
        g.point(lambda x: min(255, int(x * color[1]))),
        b.point(lambda x: min(255, int(x * color[2])))
    ))
    
    # Add back the alpha channel
    tinted.putalpha(a)
    return tinted

def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    logging.info("Starting chilli animation from chilli_screensaver.py")
    try:
        chilli_icon = icons['chilli']
        width, height = display.width, display.height
        x, y = 0, 0  # Starting position
        dx, dy = 2, 2  # Movement speed and direction
        
        # Color transition variables
        color_index = 0
        colors = [
            (0.0, 2.0, 0.0),  # Green
            (2.0, 2.0, 0.0),  # Yellow
            (2.0, 0.0, 0.0),  # Red
        ]
        transition_steps = 30  # Number of steps between colors
        current_step = 0
        
        current_color = colors[0]
        next_color = colors[1]
        
        logging.info(f"Initial color: {current_color}")
        
        while not stop_event.is_set():
            try:
                # Create a new image for each frame
                image = Image.new("RGB", (width, height), (0, 0, 0))
                
                # Calculate current color in transition
                r = current_color[0] + (next_color[0] - current_color[0]) * current_step / transition_steps
                g = current_color[1] + (next_color[1] - current_color[1]) * current_step / transition_steps
                b = current_color[2] + (next_color[2] - current_color[2]) * current_step / transition_steps
                
                # Tint the chilli with current color
                tinted_chilli = tint_image(chilli_icon, (r, g, b))
                image.paste(tinted_chilli, (x, y), mask=tinted_chilli)
                
                # Update position
                x += dx
                y += dy
                
                # Bounce off edges
                if x <= 0 or x >= width - chilli_icon.size[0]:
                    dx = -dx
                if y <= 0 or y >= height - chilli_icon.size[1]:
                    dy = -dy
                
                # Update color transition
                current_step += 1
                if current_step >= transition_steps:
                    current_step = 0
                    color_index = (color_index + 1) % len(colors)
                    current_color = colors[color_index]
                    next_color = colors[(color_index + 1) % len(colors)]
                    logging.info(f"Color transition: {current_color} -> {next_color}")
                
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
    


