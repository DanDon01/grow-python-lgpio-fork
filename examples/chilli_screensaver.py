from grow.lcd import LCD
from grow.icons import ICONS
import time

def draw_chilli_animation():
    """Animate chilli icons across the screen."""
    lcd = LCD()  # Initialize the LCD
    chilli_icon = ICONS['chilli']  # Use the chilli icon from the library

    lcd.clear()  # Clear the display
    for x in range(0, lcd.WIDTH, 4):  # Move chilli icon across the screen
        lcd.clear()
        lcd.image(chilli_icon, x, lcd.HEIGHT // 2 - 4)  # Centered vertically
        lcd.show()
        time.sleep(0.2)  # Delay for animation

    for x in range(lcd.WIDTH - 4, -4, -4):  # Reverse direction
        lcd.clear()
        lcd.image(chilli_icon, x, lcd.HEIGHT // 2 - 4)
        lcd.show()
        time.sleep(0.2)

    lcd.clear()
    lcd.show()
