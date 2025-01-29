import time
import lgpio as GPIO
from examples.lgpio_moisture import Moisture
import statistics
import yaml
import os
import logging

def get_stable_reading(sensor, samples=10, delay=1):
    """Get a stable reading by averaging multiple samples."""
    readings = []
    print("Taking readings", end="")
    for _ in range(samples):
        if sensor.active:  # Only take readings if sensor is active
            reading = sensor.moisture
            if reading > 0:  # Only add non-zero readings
                readings.append(reading)
        print(".", end="", flush=True)
        time.sleep(delay)
    print("\n")
    
    if not readings:
        print("No valid readings obtained!")
        return 0
    
    avg = statistics.mean(readings)
    std = statistics.stdev(readings) if len(readings) > 1 else 0
    
    print(f"Average: {avg:.2f} Hz")
    print(f"Standard Deviation: {std:.2f} Hz")
    return avg

def calibrate_channel(channel, gpio_handle):
    """Calibrate a single channel."""
    print(f"\n=== Calibrating Channel {channel} ===")
    
    try:
        # Initialize sensor with delay
        sensor = Moisture(channel, gpio_handle=gpio_handle)
        time.sleep(0.5)  # Give sensor time to initialize
        
        if not sensor.active:
            print(f"Failed to initialize sensor {channel}")
            return None
        
        input(f"\nEnsure sensor {channel} is completely DRY, then press Enter...")
        dry_reading = get_stable_reading(sensor)
        
        if dry_reading == 0:
            print(f"Could not get valid dry readings for channel {channel}")
            return None
            
        input(f"\nNow place sensor {channel} in WET soil or water, then press Enter...")
        wet_reading = get_stable_reading(sensor)
        
        if wet_reading == 0:
            print(f"Could not get valid wet readings for channel {channel}")
            return None
            
        return {
            'dry': dry_reading,
            'wet': wet_reading
        }
        
    except Exception as e:
        print(f"Error calibrating channel {channel}: {e}")
        return None

def update_settings(calibration_data):
    """Update settings.yml with new calibration values."""
    settings_path = 'examples/settings.yml'
    
    # Read existing settings
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = yaml.safe_load(f) or {}
    else:
        settings = {}
    
    # Update calibration values
    for channel, data in calibration_data.items():
        if data is None:
            continue
            
        channel_key = f'channel{channel}'
        if channel_key not in settings:
            settings[channel_key] = {}
        
        settings[channel_key]['dry_point'] = round(data['dry'], 1)
        settings[channel_key]['wet_point'] = round(data['wet'], 1)
    
    # Save updated settings
    with open(settings_path, 'w') as f:
        yaml.dump(settings, f, default_flow_style=False)

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("=== Moisture Sensor Calibration Tool ===")
    print("\nThis tool will help you calibrate your moisture sensors.")
    print("You'll need:")
    print("1. A dry environment for dry calibration")
    print("2. Water or very wet soil for wet calibration")
    
    calibration_data = {}
    h = None
    
    try:
        # Initialize GPIO with delay
        time.sleep(0.1)
        h = GPIO.gpiochip_open(0)
        time.sleep(0.1)
        
        logging.info("GPIO initialized successfully")
        
        # Ask which channels to calibrate
        channels = input("\nEnter channel numbers to calibrate (1 2 3) or press Enter for all: ").strip()
        channels = [1, 2, 3] if not channels else [int(c) for c in channels.split()]
        
        for channel in channels:
            if channel not in [1, 2, 3]:
                print(f"Invalid channel {channel}, skipping...")
                continue
            
            result = calibrate_channel(channel, h)
            if result:
                calibration_data[channel] = result
        
        # Show results
        print("\n=== Calibration Results ===")
        for channel, data in calibration_data.items():
            if data:
                print(f"\nChannel {channel}:")
                print(f"Dry point: {data['dry']:.1f} Hz")
                print(f"Wet point: {data['wet']:.1f} Hz")
        
        # Confirm before saving
        if calibration_data and input("\nSave these values to settings.yml? (y/n): ").lower() == 'y':
            update_settings(calibration_data)
            print("Settings updated successfully!")
        else:
            print("No calibration values to save or save cancelled.")
            
    except KeyboardInterrupt:
        print("\nCalibration cancelled.")
    except Exception as e:
        logging.error(f"Error during calibration: {e}")
    finally:
        # Clean up GPIO
        if h is not None:
            try:
                time.sleep(0.1)
                GPIO.gpiochip_close(h)
                logging.info("GPIO cleanup completed")
            except Exception as e:
                logging.error(f"Error during GPIO cleanup: {e}")
        print("\nCalibration complete.")

if __name__ == "__main__":
    main() 