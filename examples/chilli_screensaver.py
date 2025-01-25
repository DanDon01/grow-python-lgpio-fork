# This is version 2.0 of the code

from PIL import Image
import time
import logging
from threading import Event, Lock
import math

def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    logging.info("Starting chilli animation from chilli_screensaver.py")
    try:
        chilli_icon = icons['chilli']
        width, height = display.width, display.height
        x, y = 0, 0  # Starting position
        dx, dy = 2, 2  # Movement speed and direction
        angle = 0  # Starting angle for rotation
        rotation_speed = 5  # Increased speed for more noticeable rotation
        
        # Convert RGBA to RGB with white background for better rotation
        bg = Image.new('RGBA', chilli_icon.size, (255, 255, 255, 255))
        chilli_icon = Image.alpha_composite(bg, chilli_icon)
        
        logging.info(f"Chilli size: {chilli_icon.size}, Display size: {width}x{height}")
        
        while not stop_event.is_set():
            try:
                # Create a new image for each frame
                image = Image.new("RGB", (width, height), (0, 0, 0))
                
                # Rotate the chilli
                rotated_chilli = chilli_icon.rotate(angle, resample=Image.BILINEAR)
                logging.info(f"Rotation angle: {angle}")
                
                # Draw rotated chilli at current position
                image.paste(rotated_chilli, (x, y))
                
                # Update position
                x += dx
                y += dy
                
                # Update rotation
                angle += rotation_speed
                if angle >= 360:
                    angle = 0
                
                # Bounce off edges
                if x <= 0 or x >= width - rotated_chilli.size[0]:
                    dx = -dx
                if y <= 0 or y >= height - rotated_chilli.size[1]:
                    dy = -dy
                
                # Display the image with lock
                with display_lock:
                    display.display(image)
                
                time.sleep(0.05)  # Slightly slower for smoother rotation
            except Exception as e:
                logging.error(f"Error in animation loop: {e}")
                logging.error(f"Error details: {str(e)}")
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
    


