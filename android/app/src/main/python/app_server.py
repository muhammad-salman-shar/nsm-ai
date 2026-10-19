import os
import sys

# Add the current directory to path so src can be imported
sys.path.insert(0, os.path.dirname(__file__))

from src.server import run

def start_server():
    # We bind to 127.0.0.1 because it runs inside the phone itself
    run(host="127.0.0.1", port=8081)
