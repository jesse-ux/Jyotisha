from __future__ import annotations

import unittest

from scripts.rectification.diagnostics_service import run_diagnostics


def row(time: str, score: float) -> dict:
    return {"time": time, "score": score, "evidence": [], "missing_layers": []}


def diagnostics(rows: list[dict]) -> dict:
    return run_diagnostics({"events": []}, rows, {"date_sensitivity": [], "matrix": {}})


class RectificationDiagnosticsClustersTest(unittest.TestCase):
    def test_primary_cluster_joins_adjacent_minutes_across_midnight(self):
        result = diagnostics([
            row("23:59", 100),
            row("12:00", 98),
            row("00:00", 99),
        ])

        self.assertEqual(result["neighbor_support_minutes"], 2)
        self.assertEqual(result["candidate_splits"][0]["left_cluster"], {
            "start": "23:59",
            "end": "00:00",
        })
        self.assertEqual(result["candidate_splits"][0]["right_cluster"], {
            "start": "12:00",
            "end": "12:00",
        })

    def test_primary_cluster_keeps_ordinary_daytime_gaps_separate(self):
        result = diagnostics([
            row("05:13", 100),
            row("05:14", 99),
            row("05:16", 98),
        ])

        self.assertEqual(result["neighbor_support_minutes"], 2)
        self.assertEqual(result["candidate_splits"][0]["left_cluster"], {
            "start": "05:13",
            "end": "05:14",
        })
        self.assertEqual(result["candidate_splits"][0]["right_cluster"], {
            "start": "05:16",
            "end": "05:16",
        })

    def test_candidate_split_reports_actual_candidate_deltas_not_global_activation(self):
        stable_event = "00000000-0000-4000-8000-000000000001"
        separating_event = "00000000-0000-4000-8000-000000000002"
        rows = [
            {
                "time": "05:13", "score": 100, "missing_layers": [],
                "evidence": [
                    {"event_id": stable_event, "domain": "relationship", "candidate_time": "05:13", "rule_ids": ["D9:a"], "points": 50},
                    {"event_id": separating_event, "domain": "education", "candidate_time": "05:13", "rule_ids": ["D24:a"], "points": 50},
                ],
            },
            {
                "time": "05:14", "score": 90, "missing_layers": [],
                "evidence": [
                    {"event_id": stable_event, "domain": "relationship", "candidate_time": "05:14", "rule_ids": ["D9:b"], "points": 50},
                    {"event_id": separating_event, "domain": "education", "candidate_time": "05:14", "rule_ids": ["D24:b"], "points": 40},
                ],
            },
        ]
        built = {
            "date_sensitivity": [],
            "static_contexts": [
                {"feature": {
                    "time": "05:13",
                    "varga_ascendants": {"D9": 1, "D24": 2},
                    "arudha_signs": {},
                    "fingerprints": {"ashtakavarga": "same", "shadbala": "same"},
                }},
                {"feature": {
                    "time": "05:14",
                    "varga_ascendants": {"D9": 1, "D24": 3},
                    "arudha_signs": {},
                    "fingerprints": {"ashtakavarga": "same", "shadbala": "same"},
                }},
            ],
            "matrix": {
                stable_event: {
                    "05:13": {"points": 50, "technique_layers": ["D9", "D24"]},
                    "05:14": {"points": 50, "technique_layers": ["D9", "D24"]},
                },
                separating_event: {
                    "05:13": {"points": 50, "technique_layers": ["D9", "D24"]},
                    "05:14": {"points": 40, "technique_layers": ["D9", "D24"]},
                },
            },
        }
        result = run_diagnostics({"events": [{"id": stable_event, "domain": "relationship"}, {"id": separating_event, "domain": "education"}]}, rows, built)
        self.assertEqual(result["candidate_splits"][0]["technique_layers"], ["D24"])
        self.assertEqual(result["candidate_splits"][0]["event_ids"], [separating_event])


if __name__ == "__main__":
    unittest.main()
