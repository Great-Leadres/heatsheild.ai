import sys
import os

# Allow Python to import your backend logic
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from main import app  # Imports your existing FastAPI app from backend/main.py