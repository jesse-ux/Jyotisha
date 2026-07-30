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


if __name__ == "__main__":
    unittest.main()
