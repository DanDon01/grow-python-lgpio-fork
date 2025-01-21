from PIL import Image, ImageDraw
from grow.icons import ICONS

def draw_chilli_animation(display):
    """Animate chilli icons across the screen."""
    # Create a blank image for the display
    WIDTH = display.width
    HEIGHT = display.height
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    chilli_icon = ICONS["chilli"]  # Get the chilli icon from the library

    # Loop for the animation
    for x in range(0, WIDTH, 4):  # Move chilli icon left to right
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))  # Clear screen
        draw.bitmap((x, HEIGHT // 2 - 4), chilli_icon, fill=(255, 0, 0))
        display.display(img)  # Render image to the screen
        time.sleep(0.2)

    for x in range(WIDTH - 4, -4, -4):  # Move chilli icon right to left
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))  # Clear screen
        draw.bitmap((x, HEIGHT // 2 - 4), chilli_icon, fill=(255, 0, 0))
        display.display(img)  # Render image to the screen
        time.sleep(0.2)

    # Clear the display after animation
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))
    display.display(img)
