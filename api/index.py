import sys
import os

# Add root directory and backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.abspath(os.path.join(root_dir, "backend"))

for path in [root_dir, backend_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from backend.main import app
except ImportError:
    from main import app