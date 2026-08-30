import os
import sys

# Ensure local module imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
api_dir = os.path.join(root_dir, "api")

for p in [current_dir, root_dir, api_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from api.index import (
    app,
    home,
    health,
    get_heatmap,
    get_analysis,
    get_risk,
    get_agent_decision
)