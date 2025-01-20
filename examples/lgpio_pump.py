import time
import lgpio as GPIO

# Verify pump GPIO pins are correct
PUMP_1_PIN = 17  # GPIO 17 (Pin 11) - Pump 1
PUMP_2_PIN = 27  # GPIO 27 (Pin 13) - Pump 2
PUMP_3_PIN = 22  # GPIO 22 (Pin 15) - Pump 3

class Pump:
    def __init__(self, channel, gpio_handle=None):
        """Create a new pump instance for a specific channel (1-3)."""
        self._gpio_pin = [PUMP_1_PIN, PUMP_2_PIN, PUMP_3_PIN][channel - 1]
        self._h = gpio_handle if gpio_handle is not None else GPIO.gpiochip_open(0)
        self._owns_handle = gpio_handle is None
        GPIO.gpio_claim_output(self._h, self._gpio_pin, 0)  # Initialize as off

    def dose(self, speed=1.0, duration=0.1, blocking=True):
        """Run pump at speed for duration seconds."""
        try:
            # Convert speed (0.0 to 1.0) to PWM
            pwm = min(max(int(speed * 255), 0), 255)  # Scale to 0-255
            GPIO.gpio_write(self._h, self._gpio_pin, 1)  # Turn on pump
            
            if blocking:
                time.sleep(duration)
                GPIO.gpio_write(self._h, self._gpio_pin, 0)  # Turn off pump
            else:
                def stop_pump():
                    time.sleep(duration)
                    GPIO.gpio_write(self._h, self._gpio_pin, 0)
                import threading
                threading.Thread(target=stop_pump, daemon=True).start()

        except Exception as e:
            print(f"Error during pump dose: {e}")
            GPIO.gpio_write(self._h, self._gpio_pin, 0)  # Ensure pump is off

    def __del__(self):
        """Clean up GPIO resources."""
        try:
            GPIO.gpio_write(self._h, self._gpio_pin, 0)  # Ensure pump is off
            if self._owns_handle:
                GPIO.gpiochip_close(self._h)
        except:
            pass
