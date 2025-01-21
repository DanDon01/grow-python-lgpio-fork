from flask import Flask, jsonify, render_template, request
import json
import logging
from datetime import datetime
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_sensor_data():
    """Read sensor data from JSON file"""
    try:
        with open('sensor_data.json', 'r') as f:
            data = json.load(f)
            # Check if data is stale (older than 5 seconds)
            timestamp = datetime.fromisoformat(data['timestamp'])
            if (datetime.now() - timestamp).total_seconds() > 5:
                return {"error": "Sensor data is stale"}
            return data
    except FileNotFoundError:
        return {"error": "No sensor data available"}
    except Exception as e:
        logging.error(f"Error reading sensor data: {e}")
        return {"error": "Failed to read sensor data"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sensors', methods=['GET'])
def get_sensors():
    data = get_sensor_data()
    if 'error' in data:
        return jsonify({"error": data['error']})
    return jsonify(data['sensors'])

@app.route('/history', methods=['GET'])
def get_history():
    data = get_sensor_data()
    if 'error' in data:
        return jsonify({"error": data['error']})
    
    history = {}
    for channel, info in data['sensors'].items():
        history[channel] = info.get('history', [])
    return jsonify(history)

if __name__ == '__main__':
    logging.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000)
