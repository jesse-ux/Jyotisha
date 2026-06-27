from datetime import datetime
import logging

def infer_timezone(lat: float, lon: float, dt: datetime, default: float = 8.0) -> float:
    try:
        from timezonefinder import TimezoneFinder
        import pytz
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        if tz_name:
            offset_seconds = pytz.timezone(tz_name).localize(dt).utcoffset().total_seconds()
            offset = float(offset_seconds / 3600.0)
            logging.info(f"[Timezone Auth] Detected {tz_name} offset {offset} for {dt}")
            return offset
    except Exception as e:
        logging.warning(f"Timezone inference failed: {e}")
    return float(default)
