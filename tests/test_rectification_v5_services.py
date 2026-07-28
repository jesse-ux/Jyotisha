from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from scripts.rectification.api_service import diagnostics, score_candidates
from scripts.rectification.contracts import normalize_rectification_request
from scripts.rectification.scoring_service import build_event_contribution_matrix, sample_event_dates, score_from_matrix
from scripts.jyotish_api_server import (
    API_COMMAND_MAP,
    TECHNIQUE_EXAMPLE_ENDPOINTS,
    BadRequest,
    JyotishAPIHandler,
)

EVENT_ID = "00000000-0000-4000-8000-000000000001"


def request(*, precision: str = "month", event_kind: str = "education_milestone", domain: str = "education"):
    return {
        "birth_date": "1997-08-08",
        "start_time": "05:13",
        "end_time": "05:15",
        "lat": 36.419,
        "lon": 114.213,
        "tz": 8,
        "events": [{
            "id": EVENT_ID,
            "domain": domain,
            "event_kind": event_kind,
            "date_start": "2016-09-01",
            "date_end": "2016-09-30",
            "precision": precision,
            "summary": "大学入学",
        }],
    }


class RectificationV5ServicesTest(unittest.TestCase):
    def test_shared_validator_rejects_family_and_non_self_health_scoring(self):
        with self.assertRaisesRegex(ValueError, "domain is not scoreable"):
            normalize_rectification_request(request(domain="family", event_kind="family_bereavement"), today=date(2026, 7, 28))
        with self.assertRaisesRegex(ValueError, "event_kind does not match domain"):
            normalize_rectification_request(request(domain="health_pressure", event_kind="family_health_event"), today=date(2026, 7, 28))
        normalized = normalize_rectification_request(request(domain="health_pressure", event_kind="self_health_event"), today=date(2026, 7, 28))
        self.assertEqual(normalized["events"][0]["event_kind"], "self_health_event")

    def test_date_sampling_preserves_declared_range_and_uses_bounded_samples(self):
        base = request()["events"][0]
        self.assertEqual(sample_event_dates({**base, "precision": "month"}), ["2016-09-01", "2016-09-15", "2016-09-30"])
        year = {**base, "precision": "year", "date_start": "2016-01-01", "date_end": "2016-12-31"}
        self.assertEqual(len(sample_event_dates(year)), 12)
        ranged = {**base, "precision": "range", "date_start": "2015-01-01", "date_end": "2016-12-31"}
        self.assertLessEqual(len(sample_event_dates(ranged)), 12)

    def test_contribution_matrix_and_leave_out_diagnostics_use_matrix_math(self):
        normalized = normalize_rectification_request(request(), today=date(2026, 7, 28))

        def rows(value):
            sampled = value["events"][0]["date"]
            shift = {"2016-09-01": 0, "2016-09-15": 1, "2016-09-30": 2}[sampled]
            return [{
                "time": candidate,
                "score": points + shift,
                "evidence": [{
                    "event_id": EVENT_ID,
                    "domain": "education",
                    "candidate_time": candidate,
                    "rule_ids": ["D24:test"],
                    "points": points + shift,
                }],
                "missing_layers": ["KP_cusps"],
            } for candidate, points in [("05:13", 9), ("05:14", 10), ("05:15", 8)]]

        built = build_event_contribution_matrix(normalized, row_provider=rows)
        scored = score_from_matrix(normalized, built)
        self.assertEqual(built["matrix"][EVENT_ID]["05:14"]["points"], 11)
        self.assertEqual(scored[1]["score"], 11)
        self.assertEqual(built["missing_layers"], ["KP_cusps"])

    def test_formal_score_and_diagnostics_endpoints_share_the_service_bundle(self):
        normalized = normalize_rectification_request(request(), today=date(2026, 7, 28))
        built = {
            "candidate_times": ["05:13", "05:14"],
            "matrix": {EVENT_ID: {
                "05:13": {"points": 10, "rule_ids": ["D24:a"], "technique_layers": ["D24"]},
                "05:14": {"points": 8, "rule_ids": ["D24:b"], "technique_layers": ["D24"]},
            }},
            "date_sensitivity": [{
                "event_id": EVENT_ID,
                "declared_date_range": {"start": "2016-09-01", "end": "2016-09-30", "precision": "month"},
                "sample_dates": ["2016-09-01", "2016-09-15", "2016-09-30"],
                "winner_retention_rate": 1,
                "score_variance": 1,
                "sample_winners": ["05:13", "05:13", "05:13"],
            }],
            "missing_layers": ["KP_cusps"],
            "static_contexts": [{"feature": {"time": "05:13"}}, {"feature": {"time": "05:14"}}],
        }
        feature = {
            "calculation_spec_hash": "0" * 64,
            "algorithm_version": "rectification-v5-matrix-scoring-1",
            "candidate_count": 2,
            "feature_hash": "1" * 64,
            "features": [{"time": "05:13"}, {"time": "05:14"}],
        }
        with patch("scripts.rectification.api_service.build_event_contribution_matrix", return_value=built), patch(
            "scripts.rectification.api_service.build_candidate_feature_snapshot", return_value=feature
        ):
            scored = score_candidates(normalized)
            diagnostic_result = diagnostics(normalized)
        self.assertFalse(scored["can_confirm_exact_minute"])
        self.assertIn("event_contribution_matrix", scored)
        self.assertEqual(diagnostic_result["diagnostics"]["leave_one_event_out_retention_rate"], 1)
        self.assertFalse(diagnostic_result["can_confirm_exact_minute"])

    def test_http_registry_exposes_all_v5_endpoints(self):
        expected = {
            "rectification-v5-candidate-features": "/api/rectification/v5/candidate-features",
            "rectification-v5-score": "/api/rectification/v5/score",
            "rectification-v5-diagnostics": "/api/rectification/v5/diagnostics",
        }
        for command, endpoint in expected.items():
            self.assertEqual(API_COMMAND_MAP[command], endpoint)
            self.assertIn(endpoint, TECHNIQUE_EXAMPLE_ENDPOINTS)

    def test_http_handler_enforces_subject_and_event_kind_boundaries(self):
        handler = object.__new__(JyotishAPIHandler)
        with self.assertRaisesRegex(BadRequest, "domain is not scoreable"):
            handler._rectification_v5_request(request(domain="family", event_kind="family_bereavement"))
        with self.assertRaisesRegex(BadRequest, "event_kind does not match domain"):
            handler._rectification_v5_request(request(domain="health_pressure", event_kind="family_health_event"))
        normalized = handler._rectification_v5_request(
            request(domain="health_pressure", event_kind="self_health_event")
        )
        self.assertEqual(normalized["events"][0]["event_kind"], "self_health_event")

    def test_v4_compatibility_and_v5_score_handlers_share_the_v5_service(self):
        handler = object.__new__(JyotishAPIHandler)
        result = {"result_id": "00000000-0000-4000-8000-000000000099", "can_confirm_exact_minute": False}
        with patch("scripts.rectification.api_service.score_candidates", return_value=result) as scorer:
            v5 = handler._compute_rectification_v5_score(request())
            v4 = handler._compute_active_rectification_events_v4(request())
        self.assertEqual(scorer.call_count, 2)
        self.assertEqual(v5["endpoint"], "rectification_v5_score")
        self.assertEqual(v4["endpoint"], "active_rectification_events_v4")
        self.assertEqual(v5["result_id"], v4["result_id"])
        self.assertFalse(v5["can_confirm_exact_minute"])
        self.assertFalse(v4["can_confirm_exact_minute"])


if __name__ == "__main__":
    unittest.main()
