import time
import lgpio as GPIO
import logging

# Update moisture sensor pins to match the correct pinout
MOISTURE_1_PIN = 23  # GPIO 23 (Pin 16) - Moisture 1
MOISTURE_2_PIN = 8   # GPIO 8  (Pin 24) - Moisture 2
MOISTURE_3_PIN = 25  # GPIO 25 (Pin 22) - Moisture 3
MOISTURE_INT_PIN = 4  # GPIO 4  (Pin 7)  - Moisture Int

# Track which pins are in use
_initialized_pins = set()

class Moisture:
    def __init__(self, channel, gpio_handle=None):
        """Create a new moisture sensor instance for a specific channel (1-3)."""
        self._gpio_pin = [MOISTURE_1_PIN, MOISTURE_2_PIN, MOISTURE_3_PIN][channel - 1]
        
        # Check if pin is already in use
        if self._gpio_pin in _initialized_pins:
            raise RuntimeError(f"GPIO {self._gpio_pin} already in use")
            
        self._history = []
        self._freq = 0.0
        self._last_value = 0
        self._last_change = None
        self._transitions = 0
        self._measure_start = None
        self._wet_point = 0.7
        self._dry_point = 26.7
        self._h = gpio_handle if gpio_handle is not None else GPIO.gpiochip_open(0)
        self._owns_handle = gpio_handle is None
        self.active = False
        self.channel = channel

        try:
            # Simple input setup without edge detection
            GPIO.gpio_claim_input(self._h, self._gpio_pin)
            self.active = True
            logging.debug(f"Moisture sensor {channel} initialized on GPIO {self._gpio_pin}")
            
            # Mark pin as in use
            _initialized_pins.add(self._gpio_pin)
            
        except Exception as e:
            logging.error(f"Could not initialize moisture sensor {channel}: {e}")
            self.active = False
            # Try to clean up if initialization failed
            try:
                GPIO.gpio_free(self._h, self._gpio_pin)
            except:
                pass

    def _measure_frequency(self):
        """Poll GPIO and measure frequency over a fixed time window"""
        if not self.active:
            return 0.0

        now = time.time()
        
        # Start new measurement window
        if self._measure_start is None:
            self._measure_start = now
            self._transitions = 0
            self._last_value = GPIO.gpio_read(self._h, self._gpio_pin)
            return self._freq  # Return last known frequency

        # Read current value
        value = GPIO.gpio_read(self._h, self._gpio_pin)
        
        # Count transitions
        if value != self._last_value:
            self._transitions += 1
            self._last_value = value

        # Calculate frequency after measurement window
        if now - self._measure_start >= 0.1:  # 100ms measurement window
            self._freq = self._transitions * 5  # Convert to Hz (transitions/0.1s * 10)
            self._measure_start = None  # Reset for next measurement
            
        return self._freq

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
        if not self.active:
            return 0.0
        
        freq = self._measure_frequency()
        self._history.append(self.saturation)
        if len(self._history) > 96:
            self._history.pop(0)
            
        return freq

    @property
    def saturation(self):
        """Return the current saturation as a float between 0.0 and 1.0."""
        # If not active, no data can be collected
        if not self.active:
            return 0.0

        moisture = self.moisture
        if moisture == 0:
            return 0.0
        zero = self._dry_point
        span = self._wet_point - self._dry_point
        moisture = (moisture - zero) / span
        return max(0.0, min(1.0, moisture))

    def __del__(self):
        """Clean up GPIO resources when this object is destroyed."""
        try:
            if self._gpio_pin in _initialized_pins:
                _initialized_pins.remove(self._gpio_pin)
            if self._owns_handle:
                GPIO.gpiochip_close(self._h)
            else:
                GPIO.gpio_free(self._h, self._gpio_pin)
        except:
            pass
