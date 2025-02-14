#!/bin/bash

# Wait for desktop environment to be ready (adjust sleep if needed)
sleep 20

# Activate virtual environment and run monitor
cd ~/Projects/grow-python-lgpio-fork/examples  # Adjust path to your project directory
source pimoroni/bin/activate  # Adjust if your venv is named differently
python examples/monitor.py 

chmod +x examples/start_monitor.sh 