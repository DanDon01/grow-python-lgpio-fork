import time
from examples.lgpio_moisture import Moisture
import statistics
import yaml
import os

def get_stable_reading(sensor, samples=10, delay=1):
    """Get a stable reading by averaging multiple samples."""
    readings = []
    print("Taking readings", end="")
    for _ in range(samples):
        readings.append(sensor.moisture)
        print(".", end="", flush=True)
        time.sleep(delay)
    print("\n")
    
    # Remove any zero readings and calculate average
    valid_readings = [r for r in readings if r > 0]
    if not valid_readings:
        return 0
    
    avg = statistics.mean(valid_readings)
    std = statistics.stdev(valid_readings) if len(valid_readings) > 1 else 0
    
    print(f"Average: {avg:.2f} Hz")
    print(f"Standard Deviation: {std:.2f} Hz")
    return avg

def calibrate_channel(channel):
    """Calibrate a single channel."""
    print(f"\n=== Calibrating Channel {channel} ===")
    sensor = Moisture(channel)
    
    # Wait for sensor to initialize
    time.sleep(2)
    
    input(f"\nEnsure sensor {channel} is completely DRY, then press Enter...")
    dry_reading = get_stable_reading(sensor)
    
    input(f"\nNow place sensor {channel} in WET soil or water, then press Enter...")
    wet_reading = get_stable_reading(sensor)
    
    return {
        'dry': dry_reading,
        'wet': wet_reading
    }

def update_settings(calibration_data):
    """Update settings.yml with new calibration values."""
    settings_path = 'examples/settings.yml'
    
    # Read existing settings
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = yaml.safe_load(f)
    else:
        settings = {}
    
    # Update calibration values
    for channel, data in calibration_data.items():
        channel_key = f'channel{channel}'
        if channel_key not in settings:
            settings[channel_key] = {}
        
        settings[channel_key]['dry_point'] = round(data['dry'], 1)
        settings[channel_key]['wet_point'] = round(data['wet'], 1)
    
    # Save updated settings
    with open(settings_path, 'w') as f:
        yaml.dump(settings, f, default_flow_style=False)

def main():
    print("=== Moisture Sensor Calibration Tool ===")
    print("\nThis tool will help you calibrate your moisture sensors.")
    print("You'll need:")
    print("1. A dry environment for dry calibration")
    print("2. Water or very wet soil for wet calibration")
    
    calibration_data = {}
    
    try:
        # Ask which channels to calibrate
        channels = input("\nEnter channel numbers to calibrate (1 2 3) or press Enter for all: ").strip()
        channels = [1, 2, 3] if not channels else [int(c) for c in channels.split()]
        
        for channel in channels:
            if channel not in [1, 2, 3]:
                print(f"Invalid channel {channel}, skipping...")
                continue
                
            calibration_data[channel] = calibrate_channel(channel)
        
        # Show results
        print("\n=== Calibration Results ===")
        for channel, data in calibration_data.items():
            print(f"\nChannel {channel}:")
            print(f"Dry point: {data['dry']:.1f} Hz")
            print(f"Wet point: {data['wet']:.1f} Hz")
        
        # Confirm before saving
        if input("\nSave these values to settings.yml? (y/n): ").lower() == 'y':
            update_settings(calibration_data)
            print("Settings updated successfully!")
        else:
            print("Calibration values not saved.")
            
    except KeyboardInterrupt:
        print("\nCalibration cancelled.")
    except Exception as e:
        print(f"\nError during calibration: {e}")
    finally:
        print("\nCalibration complete.")

if __name__ == "__main__":
    main() 