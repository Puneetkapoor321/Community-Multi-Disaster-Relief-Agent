# ...existing code...
from collections import deque
import uuid
from ..utils import now_iso
from ..memory.memory_bank import save_incident
# ...existing code...


class CoordinatorAgent:
    name = 'coordinator'

    def __init__(self):
        self.queue = deque()

    def receive(self, msg):

        kind = msg.get('kind')
        payload = msg.get('payload', {})
        # handle triage results: request resources if severity high/medium
        if kind == 'triage_result':
            inc = payload
            save_incident(inc)
            severity = inc.get('severity')
            if severity in ('high', 'medium'):
                # send resource_request to resource agent
                out = {
                    'id': str(uuid.uuid4()),
                    'timestamp': now_iso(),
                    'sender': self.name,
                    'receiver': 'resource',
                    'kind': 'resource_request',
                    'payload': {'incident': inc}
                }
                # lazy import to avoid circular import at module import time
                from .. import router
                router.route_message(out)
                return out
        # handle resource allocations or other messages as needed
        if kind == 'resource_allocation':
            save_incident(payload)
        return None
# ...existing code...
