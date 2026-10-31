import os
import sys

# Ensure the working directory is the python folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create data folder if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.server import run

def start_server(data_dir=None):
    if data_dir:
        os.environ["NSM_DATA_DIR"] = data_dir
    try:
        run(host="127.0.0.1", port=8081)
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"Server crashed: {e}")
        if data_dir:
            try:
                with open(os.path.join(data_dir, "crash.log"), "w") as f:
                    f.write(err_msg)
            except Exception:
                pass
