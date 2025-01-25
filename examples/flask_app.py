from flask import Flask, jsonify
from flask_cors import CORS  # If needed for cross-origin requests
import json

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

@app.route('/sensor_data')
def get_sensor_data():
    try:
        with open('sensor_data.json', 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)