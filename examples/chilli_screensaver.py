# This is version 2.0 of the code

from PIL import Image
import time
import logging
from threading import Event, Lock
import math

def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    logging.info("TEST TEST TEST - USING CHILLI_SCREENSAVER.PY")  # Very obvious log message
    
    # Make it move in a square pattern instead of bouncing
    try:
        chilli_icon = icons['chilli']
        width, height = display.width, display.height
        x, y = 0, 0
        
        # Define square movement pattern
        moves = [
            (2, 0),    # Move right
            (0, 2),    # Move down
            (-2, 0),   # Move left
            (0, -2),   # Move up
        ]
        current_move = 0
        steps = 0
        max_steps = 30  # Number of steps before changing direction
        
        while not stop_event.is_set():
            try:
                image = Image.new("RGB", (width, height), (0, 0, 0))
                image.paste(chilli_icon, (x, y), mask=chilli_icon)
                
                # Update position
                dx, dy = moves[current_move]
                x += dx
                y += dy
                
                steps += 1
                if steps >= max_steps:
                    steps = 0
                    current_move = (current_move + 1) % len(moves)
                
                # Keep within bounds
                x = max(0, min(x, width - chilli_icon.size[0]))
                y = max(0, min(y, height - chilli_icon.size[1]))
                
                with display_lock:
                    display.display(image)
                
                time.sleep(0.05)
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
    


