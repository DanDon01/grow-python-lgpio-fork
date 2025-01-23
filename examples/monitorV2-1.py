import time
import lgpio as GPIO
import logging
from PIL import Image, ImageDraw, ImageFont
import ST7735

# Update moisture sensor pins to match the correct pinout
MOISTURE_1_PIN = 23  # GPIO 23 (Pin 16) - Moisture 1
MOISTURE_2_PIN = 8   # GPIO 8  (Pin 24) - Moisture 2
MOISTURE_3_PIN = 25  # GPIO 25 (Pin 22) - Moisture 3

# Button pins and labels
BUTTONS = [5, 6, 16, 24]  # GPIO pins for buttons A, B, X, Y
LABELS = ["A", "B", "X", "Y"]

# LCD display setup
DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 80
display = ST7735.ST7735(
    port=0,          # SPI0
    cs=0,            # CE1 => GPIO 7 => Pin 26
    dc=9,            # GPIO 9  => Pin 21 (Data/Command)
    backlight=12,    # GPIO 12 => Pin 32
    rotation=270,    # Rotate display 270 degrees
    spi_speed_hz=80000000,
    bgr=False,
    invert=False
)
display.begin()

# Font for the display
font = ImageFont.truetype("fonts/Roboto-Medium.ttf", 14)

# Global variables for sensor data
sensor_data = {
    'channel1': {'moisture': 0, 'saturation': 0, 'enabled': True},
    'channel2': {'moisture': 0, 'saturation': 0, 'enabled': True},
    'channel3': {'moisture': 0, 'saturation': 0, 'enabled': True},
}

class Moisture:
    def __init__(self, channel, gpio_handle):
        """Create a new moisture sensor instance for a specific channel (1-3)."""
        self._gpio_pin = [MOISTURE_1_PIN, MOISTURE_2_PIN, MOISTURE_3_PIN][channel - 1]
        self._history = []
        self._freq = 0.0
        self._last_edge = None
        self._wet_point = 0.7
        self._dry_point = 26.7
        self._h = gpio_handle
        self.active = True
        
        logging.info(f"Initializing Moisture sensor {channel} on GPIO {self._gpio_pin}")

        # Configure GPIO - with error handling and cleanup
        try:
            # First try to free the GPIO in case it's already claimed
            try:
                logging.info(f"Attempting to free GPIO {self._gpio_pin}")
                GPIO.gpio_free(self._h, self._gpio_pin)
            except Exception as e:
                logging.warning(f"Could not free GPIO {self._gpio_pin}: {e}")

            time.sleep(0.1)  # Give system time to release the pin

            # Now claim it as input
            logging.info(f"Claiming GPIO {self._gpio_pin} as input")
            GPIO.gpio_claim_input(self._h, self._gpio_pin)
            
            # Set up edge detection
            try:
                logging.info(f"Setting up edge detection on GPIO {self._gpio_pin}")
                GPIO.gpio_claim_alert(self._h, self._gpio_pin, GPIO.RISING_EDGE)
                GPIO.callback(self._h, self._gpio_pin, GPIO.RISING_EDGE, self._event_handler)
                logging.info(f"Successfully registered callbacks for pin {self._gpio_pin}")
            except Exception as e:
                logging.error(f"Failed to register callbacks for pin {self._gpio_pin}: {e}")
                self.active = False
                
        except Exception as e:
            logging.error(f"Failed to initialize GPIO {self._gpio_pin}: {e}")
            self.active = False
            raise

    def _event_handler(self, chip, gpio, level, timestamp):
        """Handle the GPIO edge event and calculate frequency."""
        current_time = time.time() * 1000000  # Convert to microseconds
        logging.debug(f"Edge detected on GPIO {gpio} at {timestamp}")  # Changed to debug level

        if self._last_edge is not None:
            delta = current_time - self._last_edge
            if delta > 0:
                self._freq = 1000000.0 / delta  # Convert from microseconds to Hz
                self._history.append(self.saturation)
                if len(self._history) > 96:  # Maintain 96 samples
                    self._history.pop(0)
        
        self._last_edge = current_time

    @property
    def moisture(self):
        """Return the current moisture frequency in Hz."""
        if self._last_edge is None or (time.time() * 1000000 - self._last_edge) > 1000000:  # 1 second timeout
            self._freq = 0
        return self._freq

    @property
    def saturation(self):
        """Return the current saturation as float 0.0 to 1.0."""
        moisture = self.moisture
        if moisture == 0:
            return 0.0
        zero = self._dry_point
        span = self._wet_point - self._dry_point
        moisture = (moisture - zero) / span
        return max(0.0, min(1.0, moisture))

def handle_button(chip, gpio, level, timestamp):
    """Handle button presses."""
    index = BUTTONS.index(gpio)
    label = LABELS[index]
    logging.info(f"Button {label} pressed")

    # Example button actions
    if label == "A":
        logging.info("Button A: Toggle Channel 1")
        sensor_data['channel1']['enabled'] = not sensor_data['channel1']['enabled']
    elif label == "B":
        logging.info("Button B: Toggle Channel 2")
        sensor_data['channel2']['enabled'] = not sensor_data['channel2']['enabled']
    elif label == "X":
        logging.info("Button X: Toggle Channel 3")
        sensor_data['channel3']['enabled'] = not sensor_data['channel3']['enabled']
    elif label == "Y":
        logging.info("Button Y: Reset all channels")
        for channel in sensor_data.values():
            channel['enabled'] = True

def setup_buttons(gpio_handle):
    """Set up button handlers."""
    for pin in BUTTONS:
        try:
            GPIO.gpio_claim_input(gpio_handle, pin, GPIO.SET_PULL_UP)
            GPIO.gpio_claim_alert(gpio_handle, pin, GPIO.FALLING_EDGE, GPIO.SET_PULL_UP)
            GPIO.callback(gpio_handle, pin, GPIO.FALLING_EDGE, handle_button)
            logging.info(f"Button {pin} initialized successfully")
        except Exception as e:
            logging.warning(f"Failed to initialize button {pin}: {e}")

def update_display():
    """Update the LCD display with sensor data."""
    while True:
        # Create a blank image with a black background
        image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw sensor data on the display
        draw.text((10, 10), f"Ch1: {sensor_data['channel1']['moisture']:.2f} Hz", font=font, fill=(255, 255, 255))
        draw.text((10, 30), f"Ch2: {sensor_data['channel2']['moisture']:.2f} Hz", font=font, fill=(255, 255, 255))
        draw.text((10, 50), f"Ch3: {sensor_data['channel3']['moisture']:.2f} Hz", font=font, fill=(255, 255, 255))

        # Display the image
        display.display(image)
        time.sleep(1.0)

def main():
    # Initialize GPIO handle
    gpio_handle = GPIO.gpiochip_open(0)

    # Initialize moisture sensors
    m1 = Moisture(1, gpio_handle)
    m2 = Moisture(2, gpio_handle)
    m3 = Moisture(3, gpio_handle)

    # Set up button handlers
    setup_buttons(gpio_handle)

    # Start a thread to update the display
    display_thread = Thread(target=update_display)
    display_thread.daemon = True
    display_thread.start()

    # Main loop to update sensor data
    try:
        while True:
            sensor_data['channel1']['moisture'] = m1.moisture
            sensor_data['channel1']['saturation'] = m1.saturation * 100

            sensor_data['channel2']['moisture'] = m2.moisture
            sensor_data['channel2']['saturation'] = m2.saturation * 100

            sensor_data['channel3']['moisture'] = m3.moisture
            sensor_data['channel3']['saturation'] = m3.saturation * 100

            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        GPIO.gpiochip_close(gpio_handle)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()