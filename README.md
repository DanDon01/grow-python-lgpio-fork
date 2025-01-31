# 🌱 Plant Monitoring System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

A Raspberry Pi-based plant monitoring and automation system using lgpio for GPIO control, with a web interface for real-time monitoring and control.

## 🚀 Features

- Real-time sensor data monitoring (moisture, temperature)
- Automated pump control based on moisture levels
- Web interface with live charts and controls
- REST API for system control and data access
- Alarm system for critical moisture levels
- Built with lgpio for improved GPIO handling

## 📋 Prerequisites

- Raspberry Pi (tested on Pi 4)
- Python 3.9 or higher
- Virtual environment
- lgpio library installed

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/plant-monitoring-system.git
cd plant-monitoring-system
```
2. Create and activate virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Usage
1. Start the Flask server:
```bash
python flask_app.py
```
2. Access the web interface:
- Open http://localhost:5000 in your browser
- View real-time sensor data
- Control pumps manually
- Set moisture thresholds

## 🔧 Configuration
Edit config.json to set:
- Sensor pins
- Pump channels
- Moisture thresholds
- Sampling intervals

## 📊 API Endpoints

- GET /sensor_data - Retrieve current sensor readings
- POST /activate_pump/<channel_id> - Activate specific pump
- GET /alarms - Get alarm history
- POST /threshold/<channel_id> - Set moisture threshold

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🔍 Troubleshooting
Known Issues
SPI Chip-Select limitations with Kernel 5.4.51+
See TROUBLESHOOTING.md for more details

## 📞 Support
Create an issue for bugs/features
Check existing issues before creating new ones


## 🔍 Troubleshooting
## Kernel 5.4.51 SPI Chip-Select Issue Fix Has been used...

As of the recent Kernel 5.4.51, it's no longer possible to add_event_detect on an SPI Chip-Select pin while the SPI interface is enabled.

To replicate, use the following code snippet on a 5.4.51 Pi vs the previous kernel:

```python
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(8, GPIO.IN)

def test(pin):
    pass

GPIO.add_event_detect(8, edge=GPIO.RISING, callback=test)
```

It attempts to set up edge detection on SPI's default CE0 pin.

Run this without SPI enabled and it will work fine.

Run it with SPI enabled, and it will fail with "RuntimeError: Failed to add edge detection".

This has changed from previous behavior and is likely due to changes in the 5.x Linux kernel (the new mutually exclusive gpiochip instead of sysfs) and is likely intended behavior despite breaking some potential back-compatibility cases, including the use of CS0 to read a moisture channel on the Grow board.

The fix is simple enough. You must re-allocate the offending chip select channel to a different pin. There's a dtoverlay for this:

```plaintext
dtoverlay=spi0-cs,cs0_pin=14 # Re-assign CS0 from BCM 8 so that Grow can use it
```

This allocates CS0 to BCM14 (UART transmit) (currently unused by Grow) so that the above code will work in both cases.

This line should be added to the Grow installer to be placed in `/boot/Firmware/config.txt` and we should consider moving that pin in a future revision (groan).

The example `monitor.py` monitors the moisture level of your soil and sounds an alarm when it drops below a defined threshold.

It's configured using `settings.yml`. Your settings for monitoring will look something like this:

```yaml
channel1:
        warn_level: 0.2
channel2:
        warn_level: 0.2
channel3:
        warn_level: 0.2
general:
        alarm_enable: True
        alarm_interval: 1.0
```

`monitor.py` includes a main view showing the moisture status of each channel and the level beyond which the alarm will sound.

The controls from the main view are as follows:

* `A` - cycle through the main screen and each channel
* `B` - snooze the alarm
* `X` - configure global settings or the selected channel

The warning moisture level can be configured for each channel, along with the Wet and Dry points that store the frequency expected from the sensor when soil is fully wet/dry.

## Watering

If you've got pumps attached to Grow and want to automatically water your plants, you'll need some extra configuration options.

See [Channel Settings](#channel-settings) and [General Settings](#general-settings) for more information on what these do.

```yaml
channel1:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        wet_point: 0.7
        dry_point: 27.6
        auto_water: True
        watering_delay: 60
channel2:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        wet_point: 0.7
        dry_point: 27.6
        auto_water: True
        watering_delay: 60
channel3:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        wet_point: 0.7
        dry_point: 27.6
        auto_water: True
        watering_delay: 60
general:
        alarm_enable: True
        alarm_interval: 1.0
```

## Channel Settings

Grow has three channels which are separated into the sections `channel1`, `channel2` and `channel3`, each of these sections has the following configuration options:

* `water_level` - The level at which auto-watering should be triggered (soil saturation from 0.0 to 1.0)
* `warn_level` - The level at which the alarm should be triggered (soil saturation from 0.0 to 1.0)
* `pump_speed` - The speed at which the pump should be run (from 0.0 low speed to 1.0 full speed)
* `pump_time` - The time that the pump should run for (in seconds)
* `auto_water` - Whether to run the attached pump (True to auto-water, False for manual watering)
* `wet_point` - Value for the sensor in saturated soil (in Hz)
* `dry_point` - Value for the sensor in totally dry soil (in Hz)
* `watering_delay` - Delay between waterings (in seconds)

## General Settings

An additional `general` section can be used for global settings:

* `alarm_enable` - Whether to enable the alarm
* `alarm_interval` - The interval at which the alarm should beep (in seconds)
