from datetime import date
import unittest

from scripts.rectification.contracts import normalize_rectification_request
from scripts.rectification.scoring_service import build_event_contribution_matrix, calculation_spec, sha256

EVENT_ID = "00000000-0000-4000-8000-000000000002"

def request():
    return {
        "birth_date": "1990-01-02", "start_time": "05:00", "end_time": "06:00",
        "lat": 25.033, "lon": 121.5654, "tz": 8,
        "events": [{"id": EVENT_ID, "domain": "career", "event_kind": "career_change", "date_start": "2020-01-01", "date_end": "2020-12-31", "precision": "year", "summary": "工作变动"}],
    }

class RectificationProvenanceTest(unittest.TestCase):
    def test_missing_and_explicit_null_remain_distinct(self):
        legacy = normalize_rectification_request(request(), today=date(2026, 7, 30))
        self.assertNotIn("birth_time_source", legacy)
        enriched_input = request()
        enriched_input["birth_time_source"] = None
        enriched_input["events"][0]["date_source"] = None
        enriched = normalize_rectification_request(enriched_input, today=date(2026, 7, 30))
        self.assertIn("birth_time_source", enriched)
        self.assertIsNone(enriched["birth_time_source"])
        self.assertIn("date_source", enriched["events"][0])

    def test_enriched_spec_hash_matches_typescript_fixture(self):
        value = request()
        value.update({"birth_time_source": "family_exact", "timezone_id": "Asia/Taipei", "timezone_source": "iana_historical", "local_time_status": "resolved"})
        normalized = normalize_rectification_request(value, today=date(2026, 7, 30))
        self.assertEqual(sha256(calculation_spec(normalized)), "fa4afe79228bedebd809c7b3c9d9d32a428f7066e3e1fd1813e44b317bd38e66")

    def test_event_provenance_is_not_forwarded_to_scoring_weights(self):
        value = request()
        value["events"][0].update({"date_source": "user_reported", "date_reliability": "medium"})
        normalized = normalize_rectification_request(value, today=date(2026, 7, 30))
        seen = []
        def provider(payload):
            seen.append(payload)
            return [{"time": "05:00", "score": 1, "evidence": [{"event_id": EVENT_ID, "domain": "career", "candidate_time": "05:00", "rule_ids": ["D10:test"], "points": 1}], "missing_layers": []}]
        build_event_contribution_matrix(normalized, provider)
        self.assertTrue(seen)
        self.assertTrue(all("date_source" not in payload["events"][0] for payload in seen))

if __name__ == "__main__":
    unittest.main()
