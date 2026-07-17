from scripts.production_smoke import check


def test_health_route_declares_required_checks() -> None:
    source = open("frontend/src/app/api/health/route.ts", encoding="utf-8").read()

    for expected in (
        "supabasePublicConfig",
        "supabaseServiceRole",
        "modelProvider",
        "jyotishApi",
        "JYOTISH_API_BASE",
    ):
        assert expected in source


def test_production_smoke_accepts_health_degraded_status(monkeypatch) -> None:
    def fake_fetch(url: str, timeout: float) -> tuple[int, str, float]:
        if url.endswith("/api/health"):
            return 503, '{"status":"blocked","checks":{"web":{},"jyotishApi":{}}}', 0.01
        return 200, "Jyotisha", 0.01

    monkeypatch.setattr("scripts.production_smoke.fetch", fake_fetch)

    report = check("https://example.invalid", 1.0)

    assert report["ok"] is True
    assert report["checks"][1]["health_status"] == "blocked"
