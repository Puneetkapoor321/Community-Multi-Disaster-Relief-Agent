# ...existing code...
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import os
import sys

# Support running this module directly (for quick tests) as well as importing
# it as part of the `src` package. When run directly, relative imports fail,
# so add a fallback that puts the `src` directory on `sys.path` and imports
# the memory module by absolute name.
try:
    from ..memory.memory_bank import cache_geocode, get_cached_geocode
except Exception:
    THIS_DIR = os.path.dirname(__file__)
    SRC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    from memory.memory_bank import cache_geocode, get_cached_geocode

_geolocator = Nominatim(user_agent='communityrelief_demo_puneet', timeout=10)
_last_ts = 0.0
MIN_INTERVAL = 1.0


def geocode_stub(place_text):
    # simple deterministic stub for offline/demo
    h = abs(hash(place_text)) % 1000
    lat = 20 + (h % 50) * 0.1
    lon = 72 + ((h // 50) % 50) * 0.1
    return lat, lon


def geocode(place_text, fallback=True, retries=2):
    """
    Geocode a place_text using Nominatim with simple rate limiting,
    caching and an optional deterministic stub fallback.
    Returns (lat, lon) or (None, None).
    """
    global _last_ts

    if not place_text:
        return (None, None)

    # return cached result if available
    cached = get_cached_geocode(place_text)
    if cached:
        return cached

    # enforce minimum interval between requests
    now = time.time()
    elapsed = now - _last_ts
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    attempt = 0
    while attempt <= retries:
        try:
            attempt += 1
            loc = _geolocator.geocode(place_text)
            _last_ts = time.time()
            if loc:
                cache_geocode(place_text, loc.latitude, loc.longitude)
                return loc.latitude, loc.longitude
            # if no loc returned, break and consider fallback
            break
        except (GeocoderTimedOut, GeocoderServiceError):
            # transient error: retry with backoff
            if attempt > retries:
                break
            time.sleep(1.5 * attempt)
        except Exception:
            # unknown error: do not retry
            break

    # fallback to deterministic stub if allowed
    if fallback:
        lat, lon = geocode_stub(place_text)
        cache_geocode(place_text, lat, lon)
        return lat, lon

    return (None, None)
# ...existing code...
