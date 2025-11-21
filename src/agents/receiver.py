# ...existing code...
from ..utils import now_iso
from ..memory.memory_bank import save_incident
from ..tools.geocode import geocode
from ..utils import save_json_field
import uuid


class ReceiverAgent:

    name = 'receiver'

    def __init__(self):
        pass

    def receive_report(self, reporter, text, place_text=None, lat=None, lon=None, raw=None, autopush=True):
        if (lat is None or lon is None) and place_text:
            lat, lon = geocode(place_text)
        inc = {
            'id': str(uuid.uuid4()),
            'created_at': now_iso(),
            'reporter': reporter,
            'text': text,
            'lat': lat,
            'lon': lon,
            'severity': None,
            'triage_ts': None,
            'raw_json': save_json_field(raw or {})
        }
        save_incident(inc)
        msg = {
            'id': str(uuid.uuid4()),
            'timestamp': now_iso(),
            'sender': self.name,
            'receiver': 'triage',
            'kind': 'report',
            'payload': inc
        }
        if autopush:
            # lazy import of router to avoid circular import at module load
            from .. import router
            print(f"Receiver: created incident {inc['id']}")
            router.route_message(msg)
        else:
            print(f"Receiver: incident {inc['id']} staged for manual routing")
        return msg

    def receive(self, msg):
        # adapter for router -> call receive_report when router routes to 'receiver'
        payload = msg.get('payload', {})
        reporter = payload.get('reporter') or payload.get(
            'sender') or 'unknown'
        text = payload.get('text') or ''
        lat = payload.get('lat')
        lon = payload.get('lon')
        place_text = payload.get('place_text')
        raw = payload.get('raw_json') or payload.get('raw')
        return self.receive_report(reporter, text, place_text=place_text, lat=lat, lon=lon, raw=raw)
# ...existing code...
