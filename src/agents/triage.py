import uuid
from ..utils import now_iso
from ..memory.memory_bank import save_incident


class TriageAgent:

    name = 'triage'

    def __init__(self):
        pass

    def classify(self, text):
        t = (text or '').lower()
        if any(w in t for w in ['fire', 'trapped', 'dead', 'collapsed', 'bleeding', 'tsunami', 'drowning', 'flooded']):
            return 'high'
        if any(w in t for w in ['injury', 'injured', 'hurt', 'help', 'evacuate', 'smoke']):
            return 'medium'
        return 'low'

    def receive(self, msg):
        if msg.get('kind') != 'report':
            return
        inc = msg['payload']
        severity = self.classify(inc.get('text'))
        inc['severity'] = severity
        inc['triage_ts'] = now_iso()
        save_incident(inc)
        out = {'id': str(uuid.uuid4()), 'timestamp': now_iso(), 'sender': self.name,
               'receiver': 'coordinator', 'kind': 'triage_result', 'payload': inc}
        print(f"Triage: incident {inc['id']} -> severity={severity}")
        # lazy import to avoid circular import at module-import time
        from .. import router
        router.route_message(out)
        return out
