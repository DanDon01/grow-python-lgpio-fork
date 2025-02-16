from flask import Flask, jsonify, request
from flask_cors import CORS  # If needed for cross-origin requests
import json
import lgpio as GPIO
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

# Global variable to store channel references
channels = None
gpio_handle = None  # Add this

def init_channels(channel_list, handle):  # Modify to accept GPIO handle
    """Initialize channels and GPIO handle for the Flask app to access"""
    global channels, gpio_handle  # Add gpio_handle
    channels = channel_list
    gpio_handle = handle  # Store the handle

@app.route('/')
def home():
    return "Flask server is running!"

@app.route('/sensor_data')
def get_sensor_data():
    try:
        with open('sensor_data.json', 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/activate_pump/<int:channel>', methods=['POST'])
def activate_pump(channel):
    if channel < 1 or channel > 3:
        return "Invalid channel", 400

    data = request.get_json()
    logging.info(f"Received pump activation request: {data}")
    
    duration = float(data.get('duration', 0.2))
    speed = min(max(float(data.get('speed', 100)), 0), 100) / 100
    
    # Get the channel object
    channel_obj = channels[channel - 1]
    
    # Activate the pump
    if channel_obj.pump:
        channel_obj.pump.dose(speed=speed, duration=duration)
        logging.info(f"Pump activated for channel {channel}")
    
    return "OK"

@app.route('/api/light/<state>', methods=['POST'])
def control_light(state):
    """Control USB grow light state"""
    try:
        # Use the global gpio_handle instead of looking in globals()
        if not gpio_handle:
            return jsonify({'error': 'GPIO not initialized'}), 500
            
        # Set up GPIO 26 as output if not already
        try:
            GPIO.gpio_claim_output(gpio_handle, 26)
        except:
            pass  # Already claimed
            
        # Convert state string to boolean
        turn_on = state.lower() == 'on'
        
        # Write to GPIO
        GPIO.gpio_write(gpio_handle, 26, 1 if turn_on else 0)
        
        return jsonify({
            'success': True,
            'state': 'on' if turn_on else 'off'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/light', methods=['GET'])
def get_light_state():
    """Get current state of USB grow light"""
    try:
        if not gpio_handle:
            return jsonify({'error': 'GPIO not initialized'}), 500
            
        # Read current state
        state = GPIO.gpio_read(gpio_handle, 26)
        
        return jsonify({
            'state': 'on' if state == 1 else 'off'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)