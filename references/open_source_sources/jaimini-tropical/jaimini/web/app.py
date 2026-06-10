"""FastAPI web application for Jaimini Tropical Astrology Engine."""

import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from jaimini.chart.chart import Chart
from jaimini.panchanga.panchanga import calc_panchanga
from jaimini.engine.time_utils import parse_dms, parse_timezone, local_to_utc
from jaimini.engine.ephemeris import get_all_planets

# --- App Setup ---
if getattr(sys, 'frozen', False):
    _BASE = Path(sys._MEIPASS) / "jaimini" / "web"
else:
    _BASE = Path(__file__).parent

app = FastAPI(title="Jaimini Tropical Astrology Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")

_INDEX_HTML = (_BASE / "templates" / "index.html").read_text(encoding="utf-8")


# --- Helpers ---

def _parse_dt(date_str, time_str):
    """Parse flexible date/time strings into a datetime."""
    date_str = str(date_str).replace("/", "-")
    if time_str.count(":") == 1:
        time_str += ":00"
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=_INDEX_HTML)


@app.post("/api/chart")
async def api_chart(data: dict):
    try:
        dt = _parse_dt(data["date"], data["time"])
        tz = parse_timezone(data.get("tz", "+8"))

        lat = parse_dms(str(data["lat"])) if isinstance(data["lat"], str) else float(data["lat"])
        lon = parse_dms(str(data["lon"])) if isinstance(data["lon"], str) else float(data["lon"])

        chart = Chart(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second,
            lat, lon, tz,
            name=data.get("name", ""),
            house_system=data.get("house_system", "W"),
        )

        return JSONResponse({"success": True, "data": chart.to_dict()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@app.get("/api/panchanga/{year}/{month}/{day}/{hour}/{minute}/{tz}/{lat}/{lon}")
async def api_panchanga(
    year: int, month: int, day: int,
    hour: int, minute: int,
    tz: str, lat: float, lon: float,
):
    try:
        tz_offset = parse_timezone(tz)
        utc_dt = local_to_utc(year, month, day, hour, minute, 0, tz_offset)

        planets = get_all_planets(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour, utc_dt.minute, utc_dt.second,
        )

        weekday = datetime(year, month, day, hour, minute).weekday()

        panchanga = calc_panchanga(planets["Su"]["lon"], planets["Mo"]["lon"], weekday)
        return JSONResponse({"success": True, "data": panchanga})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


# --- Runner ---

def run():
    import uvicorn
    print("Jaimini Tropical Astrology Engine — Web Server")
    print("Launch: http://127.0.0.1:8000")
    uvicorn.run("jaimini.web.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    run()
