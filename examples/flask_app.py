from flask import Flask, jsonify, render_template, request
import logging
from lgpio_moisture import Moisture
from lgpio_pump import Pump

app = Flask(__name__)
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sensors', methods=['GET'])
def get_sensors():
    data = {
        "sensor1": sensors[0].moisture if sensors[0] else "Error",
        "sensor2": sensors[1].moisture if sensors[1] else "Error",
        "sensor3": sensors[2].moisture if sensors[2] else "Error",
    }
    return jsonify(data)

@app.route('/logs', methods=['GET'])
def get_logs():
    with open('app.log', 'r') as log_file:
        logs = log_file.readlines()
    return jsonify(logs)

@app.route('/pump/<int:pump_id>', methods=['POST'])
def run_pump(pump_id):
    if 1 <= pump_id <= 3 and pumps[pump_id - 1]:
        pumps[pump_id - 1].run()
        return jsonify({"status": "success", "message": f"Pump {pump_id} activated"})
    else:
        return jsonify({"status": "error", "message": "Invalid pump ID or pump not initialized"}), 400

if __name__ == '__main__':
    logging.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000)
