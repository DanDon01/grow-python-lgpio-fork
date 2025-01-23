from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from lgpio_moisture import Moisture
from lgpio_pump import Pump
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
logging.basicConfig(level=logging.INFO)

# Initialize moisture sensors and pumps
sensors = []
for i in range(3):
    try:
        sensor = Moisture(i + 1)
        sensors.append(sensor)
        logging.info(f"Moisture sensor {i + 1} initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Moisture sensor {i + 1}: {e}")
        sensors.append(None)

pumps = []
for i in range(3):
    try:
        pump = Pump(i + 1)
        pumps.append(pump)
        logging.info(f"Pump {i + 1} initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Pump {i + 1}: {e}")
        pumps.append(None)

# Simulated last watered times and ambient light
last_watered = [datetime.now(timezone.utc) for _ in range(3)]
ambient_light = 500  # Example value, replace with actual sensor reading if available

@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    plants = []
    for i in range(3):
        moisture = sensors[i].moisture if sensors[i] else 0
        plants.append({
            "id": i + 1,
            "name": f"Plant {i + 1}",
            "soilMoisture": moisture,
            "lastWatered": last_watered[i].isoformat()
        })
    
    data = {
        "plants": plants,
        "ambientLight": ambient_light  # Add actual ambient light sensor reading here if available
    }
    return jsonify(data)

@app.route('/water-plant/<int:plant_id>', methods=['POST'])
def water_plant(plant_id):
    if 1 <= plant_id <= 3 and pumps[plant_id - 1]:
        pumps[plant_id - 1].run()
        last_watered[plant_id - 1] = datetime.now(timezone.utc)
        return jsonify({"success": True, "message": f"Watered plant {plant_id}"})
    else:
        return jsonify({"success": False, "message": "Invalid plant ID or pump not initialized"}), 400

@app.route('/logs', methods=['GET'])
def get_logs():
    with open('app.log', 'r') as log_file:
        logs = log_file.readlines()
    return jsonify(logs)

if __name__ == '__main__':
    logging.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000)