import uuid
from ..tools.resource_db import find_nearby
from ..utils import now_iso


class ResourceAgent:
    name = 'resource'

    def __init__(self):
        pass

    def receive(self, msg):
        if msg.get('kind') != 'resource_request':
            return
        inc = msg['payload']['incident']
        lat, lon = inc.get('lat'), inc.get('lon')
        nearby = find_nearby(lat, lon)
        allocation = {}
        for r in nearby:
            allocation.setdefault(r['type'], []).append(r['id'])
        out = {'id': str(uuid.uuid4()), 'timestamp': now_iso(), 'sender': self.name, 'receiver': 'coordinator',
               'kind': 'resource_allocation', 'payload': {'incident_id': inc['id'], 'allocation': allocation}}
        print(f"Resource: proposed allocation for {inc['id']} -> {allocation}")
        # lazy import to avoid circular import at module-import time
        from .. import router
        router.route_message(out)
        return out
