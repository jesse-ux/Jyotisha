#!/usr/bin/env python3
"""Create Prashna input contract and numeric oracle candidate queue."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "references/oracle/prashna_input_contract_2026_07_20.json"
QUEUE = ROOT / "references/oracle/prashna_numeric_oracle_packet_queue_2026_07_20.json"

def h(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def build(date: str):
    contract = {
        "scope": "prashna_input_contract",
        "created_at": date,
        "status": "contract_ready",
        "claim_status": "ready_contract",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "required_fields": [
            {"field": "question_datetime_local", "format": "YYYY-MM-DDTHH:MM:SS", "boundary": "exact time question is received/accepted"},
            {"field": "location", "format": "lat/lon + place label", "boundary": "place of querent/astrologer must be explicit"},
            {"field": "timezone", "format": "IANA or UTC offset", "boundary": "no implicit local machine timezone"},
            {"field": "ayanamsa", "format": "named sidereal ayanamsa", "boundary": "default must be recorded, e.g. Lahiri"},
            {"field": "node_mode", "format": "mean|true", "boundary": "Rahu/Ketu mode must be frozen"},
        ],
        "optional_fields": ["question_text", "querent_id", "house_focus", "language"],
        "claim_boundary": "Input contract only; does not validate Prashna predictions or external numeric parity.",
    }
    rows = [
        {
            "source_id": "vedastro_prasna_marga_ch5_sphuta_example",
            "domain": "horary_annual_sensitive_points",
            "technique_family": "sphuta_trisphuta_family",
            "url": "https://vedastro.org/book/PrasnaMarga/Chapter5",
            "source_role": "public_numeric_candidate",
            "numeric_fields_present": True,
            "expected_values": {
                "sun": "4s 3° 8' 25\"",
                "moon": "3s 19° 36' 34\"",
                "lagna": "3s 27° 22'",
                "gulika": "3s 14° 10'",
                "rahu": "3s 8° 16'",
                "trisphuta": "11s 1° 8' 34\"",
                "chatusphuta": "2s 15° 18' 34\"",
                "panchasphuta": "5s 23° 34' 34\"",
            },
            "missing_for_oracle": ["complete_prashna_input", "ayanamsa", "node_mode", "timezone", "raw_capture_hash", "local_replay", "pyjhora_or_other_legal_replay"],
            "upgrade_status": "candidate_not_oracle",
            "candidate_hash": "",
            "claim_boundary": "Numeric Sphuta example exists, but full Prashna input/settings are incomplete; use as candidate only.",
        }
    ]
    for row in rows:
        row["candidate_hash"] = h(row)
    queue = {
        "scope": "prashna_numeric_oracle_packet_queue",
        "created_at": date,
        "status": "queue_ready",
        "claim_status": "open_queue",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "summary": {"candidate_count": len(rows), "numeric_candidate_count": sum(r["numeric_fields_present"] for r in rows), "oracle_ready_count": 0},
        "rows": rows,
        "boundary": "Queue only; no Prashna/Saham/Gulika/Sphuta claim is upgraded until complete input, raw/hash and local/external replay close.",
    }
    return {"contract": contract, "queue": queue}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--date", default="2026-07-20"); args=ap.parse_args()
    data=build(args.date)
    CONTRACT.write_text(json.dumps(data["contract"], ensure_ascii=False, indent=2, sort_keys=True)+"\n")
    QUEUE.write_text(json.dumps(data["queue"], ensure_ascii=False, indent=2, sort_keys=True)+"\n")
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
if __name__ == "__main__": main()
