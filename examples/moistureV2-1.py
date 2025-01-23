import time
import lgpio as GPIO
import logging
from flask import Flask, jsonify
from threading import Thread

# Update moisture sensor pins to match the correct pinout
MOISTURE_1_PIN = 23  # GPIO 23 (Pin 16) - Moisture 1
MOISTURE_2_PIN = 8   # GPIO 8  (Pin 24) - Moisture 2
MOISTURE_3_PIN = 25  # GPIO 25 (Pin 22) - Moisture 3
MOISTURE_INT_PIN = 4  # GPIO 4  (Pin 7)  - Moisture Int

# Button pins and labels
BUTTONS = [5, 6, 16, 24]  # GPIO pins for buttons A, B, X, Y
LABELS = ["A", "B", "X", "Y"]

# Flask app setup
app = Flask(__name__)

# Global variables for sensor data
sensor_data = {
    'timestamp': None,
    'sensors': {
        'channel1': {'moisture': 0, 'saturation': 0, 'alarm': False, 'enabled': True, 'history': []},
        'channel2': {'moisture': 0, 'saturation': 0, 'alarm': False, 'enabled': True, 'history': []},
        'channel3': {'moisture': 0, 'saturation': 0, 'alarm': False, 'enabled': True, 'history': []},
    }
}

class Moisture:
    def __init__(self, channel, gpio_handle=None):
        """Create a new moisture sensor instance for a specific channel (1-3)."""
        self._gpio_pin = [MOISTURE_1_PIN, MOISTURE_2_PIN, MOISTURE_3_PIN][channel - 1]
        self._history = []
        self._freq = 0.0
        self._last_edge = None
        self._wet_point = 0.7
        self._dry_point = 26.7
        self._h = gpio_handle if gpio_handle is not None else GPIO.gpiochip_open(0)
        self._owns_handle = gpio_handle is None
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

    def set_wet_point(self, freq):
        """Set the frequency for 100% saturation."""
        self._wet_point = freq

    def set_dry_point(self, freq):
        """Set the frequency for 0% saturation."""
        self._dry_point = freq

    @property
    def history(self):
        """Return history of saturation readings."""
        return self._history

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

    def __del__(self):
        """Clean up GPIO resources."""
        try:
            if self._owns_handle:
                GPIO.gpiochip_close(self._h)
        except:
            pass

def handle_button(chip, gpio, level, timestamp):
    """Handle button presses."""
    index = BUTTONS.index(gpio)
    label = LABELS[index]
    logging.info(f"Button {label} pressed")

    # Example button actions
    if label == "A":
        logging.info("Button A: Toggle Channel 1")
        sensor_data['sensors']['channel1']['enabled'] = not sensor_data['sensors']['channel1']['enabled']
    elif label == "B":
        logging.info("Button B: Toggle Channel 2")
        sensor_data['sensors']['channel2']['enabled'] = not sensor_data['sensors']['channel2']['enabled']
    elif label == "X":
        logging.info("Button X: Toggle Channel 3")
        sensor_data['sensors']['channel3']['enabled'] = not sensor_data['sensors']['channel3']['enabled']
    elif label == "Y":
        logging.info("Button Y: Reset all channels")
        for channel in sensor_data['sensors'].values():
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

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    """Flask endpoint to return sensor data."""
    return jsonify(sensor_data)

def update_sensor_data(m1, m2, m3):
    """Update global sensor data with current readings."""
    while True:
        sensor_data['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        sensor_data['sensors']['channel1']['moisture'] = m1.moisture
        sensor_data['sensors']['channel1']['saturation'] = m1.saturation * 100
        sensor_data['sensors']['channel1']['history'] = m1.history

        sensor_data['sensors']['channel2']['moisture'] = m2.moisture
        sensor_data['sensors']['channel2']['saturation'] = m2.saturation * 100
        sensor_data['sensors']['channel2']['history'] = m2.history

        sensor_data['sensors']['channel3']['moisture'] = m3.moisture
        sensor_data['sensors']['channel3']['saturation'] = m3.saturation * 100
        sensor_data['sensors']['channel3']['history'] = m3.history

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

    # Start a thread to update sensor data
    sensor_thread = Thread(target=update_sensor_data, args=(m1, m2, m3))
    sensor_thread.daemon = True
    sensor_thread.start()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()