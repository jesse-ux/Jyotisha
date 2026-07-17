from pathlib import Path

from scripts.vedastro_official_source_contract import audit_source


def test_official_source_contract_resolves_zero_offset_semantics(tmp_path: Path) -> None:
    (tmp_path / "Library/Data").mkdir(parents=True)
    (tmp_path / "Library/Logic/Calculate").mkdir(parents=True)
    (tmp_path / "Library/Logic").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Library/Library.csproj").write_text("<Version>1.2.0</Version><PackageLicenseExpression>MIT</PackageLicenseExpression>")
    (tmp_path / "Library/Data/Time.cs").write_text('DateTimeOffset.ParseExact(stdDateTimeText, Time.DateTimeFormat, null); public const string DateTimeFormat = "HH:mm dd/MM/yyyy zzz";')
    (tmp_path / "Library/Logic/Tools.cs").write_text('var parsedTimezone = Tools.StringToTimezone(offsetStr); if (parsedTimezone == null || parsedTimezone == TimeSpan.Zero) offsetStr = await Calculate.GeoLocationToTimezone(geoLocation, parsedInputTime); DateTimeOffset.ParseExact(timezoneRaw, "zzz", CultureInfo.InvariantCulture).Offset;')
    (tmp_path / "Library/Logic/Calculate/Core.cs").write_text("public static List<PlanetLongitude> AllPlanetLongitude(Time time) { return PlanetNirayanaLongitude(Sun, time); }")

    report = audit_source(tmp_path)

    assert report["source_contract_status"] == "verified"
    assert report["timezone_contract"]["zero_offset"] == "auto_lookup_sentinel"
    assert report["timezone_contract"]["negative_offset"] == "literal_offset"
    assert report["longitude_contract"]["AllPlanetLongitude"] == "nirayana"
    assert report["deployment_identity_status"] == "blocked"
