"""
Flask web dashboard for the CommunityRelief "Clear Vibe" disaster agent.

Run locally with:
    python -m src.app
or
    flask --app src.app run
"""

from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request

from .agents.receiver import ReceiverAgent
from .agents.triage import TriageAgent
from .memory.memory_bank import list_incidents, save_incident
from .tools.resource_db import find_nearby
from .utils import now_iso

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
)

receiver_agent = ReceiverAgent()
triage_agent = TriageAgent()
PIPELINE_STEPS = [
    {"label": "Receiver", "description": "Normalize & geocode incoming report"},
    {"label": "Triage", "description": "Assess severity & urgency"},
    {"label": "Coordinator", "description": "Contextualize incident timeline"},
    {"label": "Resource", "description": "Allocate nearest responders"},
]
EVENT_FEED = deque(maxlen=60)


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_resources(raw_resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    allocation: Dict[str, List[Dict[str, Any]]] = {}
    for item in raw_resources:
        entry = {
            "id": item.get("id"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
        }
        allocation.setdefault(item.get("type", "misc"), []).append(entry)
    return allocation


def _record_event(incident: Dict[str, Any], allocation: Dict[str, List[Dict[str, Any]]], source: str) -> Dict[str, Any]:
    event = {
        "id": incident.get("id"),
        "reporter": incident.get("reporter"),
        "text": incident.get("text"),
        "severity": incident.get("severity"),
        "lat": incident.get("lat"),
        "lon": incident.get("lon"),
        "created_at": incident.get("created_at"),
        "triage_ts": incident.get("triage_ts"),
        "stage": "Resources ready" if allocation else "Triaged",
        "allocation": allocation,
        "source": source,
        "timeline": [
            {"label": "Receiver", "ts": incident.get("created_at")},
            {"label": "Triage", "ts": incident.get("triage_ts")},
            {"label": "Resource", "ts": now_iso() if allocation else None},
        ],
    }
    EVENT_FEED.appendleft(event)
    return event


def _bootstrap_feed() -> None:
    historical = list_incidents(limit=8)
    for inc in historical:
        allocation = _format_resources(
            find_nearby(inc.get("lat"), inc.get("lon"), radius_km=80, limit=3)
        )
        _record_event(inc, allocation, source="history")


def _process_incident(payload: Dict[str, Any], source: str = "web") -> Dict[str, Any]:
    reporter = payload.get("reporter") or "web_user"
    text = payload.get("text") or ""
    place_text = payload.get("place_text")
    lat = _safe_float(payload.get("lat"))
    lon = _safe_float(payload.get("lon"))
    msg = receiver_agent.receive_report(
        reporter,
        text,
        place_text=place_text,
        lat=lat,
        lon=lon,
        raw=payload,
        autopush=False,
    )
    incident = msg["payload"]
    severity = triage_agent.classify(incident.get("text"))
    incident["severity"] = severity
    incident["triage_ts"] = now_iso()
    save_incident(incident)
    allocation = _format_resources(
        find_nearby(incident.get("lat"), incident.get("lon"), radius_km=120, limit=5)
    )
    return _record_event(incident, allocation, source=source)


@app.get("/")
def dashboard():
    incidents = list_incidents(limit=12)
    events = list(EVENT_FEED)
    return render_template(
        "dashboard.html",
        pipeline=PIPELINE_STEPS,
        incidents=incidents,
        events=events,
    )


@app.post("/api/incidents")
def create_incident():
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data or not data.get("text"):
        return jsonify({"status": "error", "message": "Text field is required"}), 400
    event = _process_incident(data, source="web")
    return jsonify({"status": "ok", "event": event})


@app.get("/api/stream")
def stream_events():
    return jsonify({"events": list(EVENT_FEED)})


@app.get("/healthz")
def healthcheck():
    return jsonify({"status": "ok", "timestamp": now_iso()})


_bootstrap_feed()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
