from datetime import datetime
def infer_timezone(lat: float, lon: float, dt: datetime) -> float:
    from domain_calculation_service import infer_timezone_offset

    return infer_timezone_offset(lat=lat, lon=lon, local_datetime=dt)
