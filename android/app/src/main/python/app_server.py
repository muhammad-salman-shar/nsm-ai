import os
import sys

# Ensure the working directory is the python folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create data folder if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.server import run

def start_server():
    try:
        run(host="127.0.0.1", port=8081)
    except Exception as e:
        print(f"Server crashed: {e}")
