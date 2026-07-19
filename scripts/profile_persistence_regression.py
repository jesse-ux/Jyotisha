#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request

def _request(method: str, url: str, payload: dict, cookie: str) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json", "cookie": cookie})
    with urllib.request.urlopen(req, timeout=20) as r:
        return {"status": r.status, "body": r.read(2000).decode("utf-8", "replace")}

def run() -> dict:
    base = os.getenv("JYOTISHA_PRODUCTION_BASE_URL")
    cookie = os.getenv("JYOTISHA_PRODUCTION_COOKIE")
    if not base or not cookie:
        return {"scope": "profile_persistence_regression", "status": "blocked", "reason": "missing_base_url_or_cookie"}
    payload = {"displayName": "E2E验证用户", "birth": {"year": 1997, "month": 1, "day": 1, "hour": 12, "minute": 0, "city": "北京", "lat": 39.9042, "lon": 116.4074, "tz": 8}}
    account = _request("PATCH", base.rstrip()+"/api/account", payload, cookie)
    return {"scope": "profile_persistence_regression", "status": "pass" if 200 <= account["status"] < 300 else "fail", "account": account}

if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
