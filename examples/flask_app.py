from flask import Flask, jsonify, request
from flask_cors import CORS  # If needed for cross-origin requests
import json

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

# Global variable to store channel references
channels = None

def init_channels(channel_list):
    """Initialize channels for the Flask app to access"""
    global channels
    channels = channel_list

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

@app.route('/activate_pump/<int:channel_id>', methods=['POST'])
def activate_pump(channel_id):
    """Activate pump for specified channel"""
    if not channels or channel_id < 1 or channel_id > len(channels):
        return jsonify({'error': 'Invalid channel ID'}), 400
    
    channel = channels[channel_id - 1]
    if not channel or not channel.pump:
        return jsonify({'error': 'Pump not available'}), 400
    
    try:
        # Get duration from request, default to channel's pump_time if not specified
        duration = request.json.get('duration', channel.pump_time)
        speed = request.json.get('speed', channel.pump_speed) / 100.0  # Convert percentage to 0-1 range
        
        # Use dose() method instead of run()
        channel.pump.dose(speed=speed, duration=duration, blocking=False)
        
        return jsonify({
            'success': True,
            'message': f'Pump {channel_id} activated for {duration} seconds at speed {speed*100}%'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)