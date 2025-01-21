from PIL import Image, ImageDraw
import time

def draw_chilli_animation(display, icons, stop_event):
    """Animate chilli icons across the screen until stop_event is set."""
    WIDTH = display.width
    HEIGHT = display.height

    img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
    chilli_icon = icons['chilli']

    while not stop_event.is_set():  # Loop until stop_event is set
        for x in range(0, WIDTH, 4):
            if stop_event.is_set():
                break
            img.paste((0, 0, 0), [0, 0, WIDTH, HEIGHT])
            img.paste(chilli_icon, (x, HEIGHT // 2 - 8), chilli_icon)
            display.display(img)
            time.sleep(0.1)

        for x in range(WIDTH - 16, -16, -4):
            if stop_event.is_set():
                break
            img.paste((0, 0, 0), [0, 0, WIDTH, HEIGHT])
            img.paste(chilli_icon, (x, HEIGHT // 2 - 8), chilli_icon)
            display.display(img)
            time.sleep(0.1)

    # Clear the screen when the screensaver stops
    img.paste((0, 0, 0), [0, 0, WIDTH, HEIGHT])
    display.display(img)
    logging.info("Screensaver stopped and display cleared.")


