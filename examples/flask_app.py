from flask import Flask, jsonify, render_template, request
import logging
from examples.lgpio_moisture import Moisture
from examples.lgpio_pump import Pump

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize moisture sensors and pumps
sensors = [Moisture(_+1) for _ in range(3)]
pumps = [Pump(_+1) for _ in range(3)]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sensors', methods=['GET'])
def get_sensors():
    data = {
        "sensor1": sensors[0].moisture,
        "sensor2": sensors[1].moisture,
        "sensor3": sensors[2].moisture,
    }
    return jsonify(data)

@app.route('/logs', methods=['GET'])
def get_logs():
    with open('app.log', 'r') as log_file:
        logs = log_file.readlines()
    return jsonify(logs)

@app.route('/pump/<int:pump_id>', methods=['POST'])
def run_pump(pump_id):
    if 1 <= pump_id <= 3:
        pumps[pump_id - 1].run()
        return jsonify({"status": "success", "message": f"Pump {pump_id} activated"})
    else:
        return jsonify({"status": "error", "message": "Invalid pump ID"}), 400

if __name__ == '__main__':
    logging.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000)
