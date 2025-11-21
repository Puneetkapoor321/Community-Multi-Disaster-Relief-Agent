# ...existing code...
# small in-memory resource DB. Replace with real source for production.
import math

resources = [
    {"id": "vol-1", "type": "volunteer", "lat": 20.5, "lon": 72.5, "available": True},
    {"id": "shel-1", "type": "shelter", "lat": 20.8, "lon": 72.7, "available": True},
    {"id": "med-1", "type": "medical_kit",
        "lat": 20.6, "lon": 72.6, "available": True},
]


def haversine_km(lat1, lon1, lat2, lon2):
    """Return great-circle distance between two points (kilometers)."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * \
        math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearby(lat, lon, radius_km=50, limit=5):
    """
    Find up to `limit` resources within `radius_km` kilometers of (lat, lon).
    Returns a list of resource dicts sorted by distance (closest first).
    """
    if lat is None or lon is None:
        return []

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return []

    scored = []
    for r in resources:
        try:
            rlat = float(r.get("lat"))
            rlon = float(r.get("lon"))
        except (TypeError, ValueError):
            continue
        d = haversine_km(lat, lon, rlat, rlon)
        if d <= radius_km:
            scored.append((d, r))

    scored.sort(key=lambda x: x[0])
    return [r for d, r in scored[:limit]]
# ...existing code...
