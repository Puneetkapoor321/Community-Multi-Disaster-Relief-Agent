# ...existing code...
import os
import sys
import uuid

# Allow running `python src/run_demo.py` by configuring package context.
if __package__ is None or __package__ == "":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    __package__ = "src"

from .agents.triage import TriageAgent
from .tools.resource_db import find_nearby
from .memory.memory_bank import save_incident
from .utils import now_iso


def main():
    # build a synthetic incident (as ReceiverAgent would)
    inc = {
        'id': str(uuid.uuid4()),
        'created_at': now_iso(),
        'reporter': 'demo_user',
        'text': 'There is a large fire and people trapped at Demo Street',
        'lat': 20.6,
        'lon': 72.6,
        'severity': None,
        'triage_ts': None,
        'raw_json': {}
    }

    # triage
    tri = TriageAgent()
    sev = tri.classify(inc['text'])
    inc['severity'] = sev
    inc['triage_ts'] = now_iso()
    save_incident(inc)
    print(f"Demo: incident {inc['id']} classified as {sev}")

    # resources (if needed)
    if sev in ('high', 'medium'):
        nearby = find_nearby(inc['lat'], inc['lon'], radius_km=50, limit=5)
        allocation = {}
        for r in nearby:
            allocation.setdefault(r['type'], []).append(r['id'])
        print(f"Demo: proposed allocation -> {allocation}")
    else:
        print("Demo: no allocation required for low severity")


if __name__ == '__main__':
    main()
# ...existing code...
