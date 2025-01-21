from PIL import Image, ImageDraw
import time

def draw_chilli_animation(display):
    """Animate chilli icons across the screen."""
    # Screen dimensions
    WIDTH = display.width
    HEIGHT = display.height

    # Create a blank image for the LCD
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load and resize the chilli icon
    chilli_icon = Image.open("icons/veg-chilli.png").resize((16, 16))

    # Animate the chilli across the screen
    for x in range(0, WIDTH, 4):  # Move from left to right
        img.paste((0, 0, 0), [0, 0, WIDTH, HEIGHT])  # Clear the screen
        img.paste(chilli_icon, (x, HEIGHT // 2 - 8))  # Paste the chilli icon
        display.display(img)
        time.sleep(0.1)

    for x in range(WIDTH - 16, -16, -4):  # Move from right to left
        img.paste((0, 0, 0), [0, 0, WIDTH, HEIGHT])  # Clear the screen
        img.paste(chilli_icon, (x, HEIGHT // 2 - 8))  # Paste the chilli icon
        display.display(img)
        time.sleep(0.1)

    # Clear the screen after the animation
    img.paste((0, 0, 0), [0, 0, WIDTH, HEIGHT])
    display.display(img)
