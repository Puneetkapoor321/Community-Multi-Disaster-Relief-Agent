# ...existing code...
import json
import sqlite3
from ..utils import get_conn, now_iso

# Initialize DB tables (run once on import)


def _ensure_tables():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS incidents(
      id TEXT PRIMARY KEY,
      created_at TEXT,
      reporter TEXT,
      text TEXT,
      lat REAL,
      lon REAL,
      severity TEXT,
      triage_ts TEXT,
      raw_json TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS seen_items(
      item_hash TEXT PRIMARY KEY,
      seen_at TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS geocode_cache(
      place_text TEXT PRIMARY KEY,
      lat REAL,
      lon REAL,
      cached_at TEXT
    )
    """)
    conn.commit()


_ensure_tables()


def _serialize_raw(raw):
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    try:
        return json.dumps(raw, ensure_ascii=False)
    except Exception:
        return json.dumps(str(raw))


def save_incident(inc):
    """
    Save or replace an incident row. Ensures raw_json is serialized before binding.
    Expects inc to be a dict; will tolerate missing fields.
    """
    conn = get_conn()
    c = conn.cursor()
    raw_str = _serialize_raw(inc.get('raw_json'))
    c.execute(
        '''REPLACE INTO incidents(id, created_at, reporter, text, lat, lon, severity, triage_ts, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            inc.get('id'),
            inc.get('created_at') or now_iso(),
            inc.get('reporter'),
            inc.get('text'),
            inc.get('lat'),
            inc.get('lon'),
            inc.get('severity'),
            inc.get('triage_ts'),
            raw_str,
        ),
    )
    conn.commit()
    return inc


def mark_seen(item_hash):
    conn = get_conn()
    c = conn.cursor()
    c.execute('REPLACE INTO seen_items (item_hash, seen_at) VALUES (?, ?)',
              (item_hash, now_iso()))
    conn.commit()


def is_seen(item_hash):
    conn = get_conn()
    c = conn.cursor()
    r = c.execute('SELECT 1 FROM seen_items WHERE item_hash=?',
                  (item_hash,)).fetchone()
    return r is not None


def cache_geocode(place_text, lat, lon):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'REPLACE INTO geocode_cache (place_text, lat, lon, cached_at) VALUES (?, ?, ?, ?)',
        (place_text, lat, lon, now_iso()),
    )
    conn.commit()


def get_cached_geocode(place_text):
    """
    Return (lat, lon) tuple if cached, otherwise None.
    Handles rows returned as tuples or sqlite3.Row/mapping.
    """
    conn = get_conn()
    c = conn.cursor()
    r = c.execute(
        'SELECT lat, lon FROM geocode_cache WHERE place_text=?', (place_text,)).fetchone()
    if not r:
        return None
    # r may be a sqlite3.Row (mapping) or a tuple
    try:
        # try mapping access first
        return (r['lat'], r['lon'])
    except Exception:
        try:
            return (r[0], r[1])
        except Exception:
            return None


def list_incidents(limit=25):
    """
    Return the most recent incidents ordered by triage timestamp (or created_at).
    """
    conn = get_conn()
    conn.row_factory = sqlite3.Row if hasattr(sqlite3, "Row") else None
    c = conn.cursor()
    rows = c.execute(
        """
        SELECT id, created_at, reporter, text, lat, lon, severity, triage_ts, raw_json
        FROM incidents
        ORDER BY COALESCE(triage_ts, created_at) DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    def _row_to_dict(row):
        if isinstance(row, dict):
            payload = dict(row)
        else:
            try:
                payload = {k: row[k] for k in row.keys()}
            except Exception:
                payload = {
                    "id": row[0],
                    "created_at": row[1],
                    "reporter": row[2],
                    "text": row[3],
                    "lat": row[4],
                    "lon": row[5],
                    "severity": row[6],
                    "triage_ts": row[7],
                    "raw_json": row[8],
                }
        raw_value = payload.get("raw_json")
        if raw_value:
            try:
                payload["raw_json"] = json.loads(raw_value)
            except Exception:
                payload["raw_json"] = raw_value
        return payload

    return [_row_to_dict(r) for r in rows]


# ...existing code...
 # filepath: c:\VS Language
