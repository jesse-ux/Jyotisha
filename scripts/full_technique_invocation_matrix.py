#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "references/oracle/full_technique_invocation_matrix_2026_07_22.json"

SCAN_ROOTS = {
    "skill": ["SKILL.md", "skills"],
    "api": ["mcp_server.py", "scripts/jyotish_api_server.py", "scripts"],
    "ui": ["jyotish-app"],
    "scripts": ["scripts"],
    "references": ["references"],
    "tests": ["tests"],
}

SKIP_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
}
MAX_SCAN_BYTES = 1_000_000


@dataclass(frozen=True)
class Technique:
    technique_id: str
    label: str
    domain: str
    aliases: tuple[str, ...]
    p_batch: str
    first_batch: bool = False


TECHNIQUES: tuple[Technique, ...] = (
    Technique("ul_arudha_upapada", "UL / Upapada Lagna", "arudha_rectification", ("UL", "Upapada", "upapada"), "P0", True),
    Technique("a7_arudha_relationship", "A7 Arudha", "arudha_rectification", ("A7", "arudha a7", "darapada"), "P0", True),
    Technique("a10_arudha_career", "A10 Arudha", "arudha_rectification", ("A10", "arudha a10", "rajyapada"), "P0", True),
    Technique("kp_exact_cusp", "KP exact cusp", "kp_precision_timing", ("KP cusp", "house cusp", "exact cusp", "cusp longitude"), "P0", True),
    Technique("kp_star_sub_sub", "KP star / sub / sub-sub", "kp_precision_timing", ("star lord", "sub lord", "sub-sub", "sub sub", "KP star"), "P0", True),
    Technique("kp_significator", "KP significator table", "kp_precision_timing", ("significator", "KP significator"), "P1", True),
    Technique("kp_ruling_planets", "KP ruling planets", "kp_precision_timing", ("ruling planets", "RP", "KP ruling"), "P1", True),
    Technique("shadbala", "Shadbala total", "strength", ("Shadbala", "Ṣaḍbala", "Sadbal"), "P0", True),
    Technique("shadbala_chesta", "Shadbala Chesta Bala", "strength", ("Chesta", "ceṣṭā", "mean-motion", "Seeghrochcha"), "P0", True),
    Technique("shadbala_sthana", "Shadbala Sthana Bala", "strength", ("Sthana", "Uccha", "Saptavargaja", "Ojayugma", "Kendradi", "Drekkana"), "P0", True),
    Technique("shadbala_dig", "Shadbala Dig Bala", "strength", ("Dig Bala", "Digbala"), "P1"),
    Technique("shadbala_drik", "Shadbala Drik Bala", "strength", ("Drik Bala", "aspect strength"), "P1"),
    Technique("shadbala_kala", "Shadbala Kala Bala", "strength", ("Kala Bala", "Natonnata", "Paksha", "Tribhaga", "Abda", "Masa", "Vara", "Hora"), "P1"),
    Technique("naisargika_bala", "Naisargika Bala", "strength", ("Naisargika", "natural strength"), "P1"),
    Technique("ashtakavarga_bav", "Ashtakavarga BAV", "ashtakavarga", ("BAV", "Bhinnashtakavarga", "Bhinnashtaka"), "P1"),
    Technique("ashtakavarga_sav", "Ashtakavarga SAV", "ashtakavarga", ("SAV", "Sarvashtakavarga", "Sarvashtaka"), "P1"),
    Technique("ashtakavarga_kakshya", "Ashtakavarga Kakshya", "ashtakavarga", ("Kakshya", "kakshya transit"), "P1"),
    Technique("muhurta", "Muhurta full scoring", "muhurta", ("Muhurta", "Electional", "择日"), "P0", True),
    Technique("tarabala", "Tarabala", "muhurta", ("Tarabala", "Tara Bala"), "P0", True),
    Technique("chandrabala", "Chandrabala", "muhurta", ("Chandrabala", "Chandra Bala"), "P0", True),
    Technique("rahu_kalam", "Rahu Kalam", "muhurta", ("Rahu Kalam", "Rahu Kala", "Rāhukāla"), "P0", True),
    Technique("yamaganda", "Yamaganda", "muhurta", ("Yamaganda", "Yama Gandam", "Yamakanda"), "P1"),
    Technique("gulika_kalam", "Gulika Kalam", "muhurta", ("Gulika Kalam", "Gulikai", "Mandi Kalam"), "P1"),
    Technique("abhijit_muhurta", "Abhijit Muhurta", "muhurta", ("Abhijit", "Abhijit Muhurta"), "P0", True),
    Technique("panchaka", "Panchaka", "muhurta", ("Panchaka",), "P1"),
    Technique("vyatipata_vaidhriti", "Vyatipata / Vaidhriti", "muhurta", ("Vyatipata", "Vaidhriti"), "P1"),
    Technique("sankranti_gate", "Sankranti gate", "muhurta", ("Sankranti", "Saṅkrānti"), "P1"),
    Technique("prashna", "Prashna chart", "horary", ("Prashna", "Horary", "question chart"), "P0", True),
    Technique("sphuta", "Sphuta set", "horary", ("Sphuta", "Trisphuta", "Catusphuta", "Panchasphuta"), "P0", True),
    Technique("gulika", "Gulika / Mandi", "horary", ("Gulika", "Mandi"), "P0", True),
    Technique("saham", "Saham lots", "horary_annual", ("Saham", "Sahams", "Arabic parts"), "P0", True),
    Technique("tajika", "Tajika / Varshaphala", "annual", ("Tajika", "Varshaphala", "annual chart"), "P0", True),
    Technique("muntha", "Muntha", "annual", ("Muntha",), "P1"),
    Technique("mudda_dasha", "Mudda Dasha", "annual", ("Mudda", "Mudda Dasha"), "P1"),
    Technique("vimshottari", "Vimshottari Dasha", "dasha", ("Vimshottari",), "P1"),
    Technique("narayana_dasha", "Narayana Dasha", "dasha", ("Narayana",), "P1"),
    Technique("chara_dasha", "Chara Dasha", "dasha", ("Chara Dasha",), "P2"),
    Technique("functional_benefic_malefic", "Functional Benefic / Malefic", "interpretation_gate", ("Functional Benefic", "Functional Malefic", "功能性吉凶"), "P0"),
    Technique("mevg", "MEVG / real-case calibration", "interpretation_gate", ("MEVG", "Real Case Calibration", "Global Web Evidence"), "P0"),
    Technique("birth_time_rectification", "Birth-time rectification", "rectification", ("birth-time rectification", "生时校正", "rectification"), "P0"),
    Technique("timing_holdout", "Timing negative holdout", "timing", ("holdout", "negative controls", "blind ranking", "负样本"), "P0"),
    Technique("d1_rasi", "D1 Rasi", "varga", ("D1", "Rasi", "Rāśi"), "P1"),
    Technique("d2_hora", "D2 Hora", "varga", ("D2", "Hora"), "P1"),
    Technique("d3_drekkana", "D3 Drekkana", "varga", ("D3", "Drekkana", "Decanate"), "P1"),
    Technique("d4_chaturthamsha", "D4 Chaturthamsha", "varga", ("D4", "Chaturthamsha"), "P1"),
    Technique("d7_saptamsha", "D7 Saptamsha", "varga", ("D7", "Saptamsha"), "P1"),
    Technique("d9_navamsa", "D9 Navamsa", "varga", ("D9", "Navamsa"), "P1"),
    Technique("d10_dasamsha", "D10 Dasamsha", "varga", ("D10", "Dasamsha"), "P1"),
    Technique("d12_dwadashamsha", "D12 Dwadashamsha", "varga", ("D12", "Dwadashamsha"), "P2"),
    Technique("d24_chaturvimshamsha", "D24 Chaturvimshamsha", "varga", ("D24", "Chaturvimshamsha", "Siddhamsa"), "P2"),
    Technique("d30_trimsamsha", "D30 Trimsamsha", "varga", ("D30", "Trimsamsha"), "P2"),
    Technique("d60_shashtiamsha", "D60 Shashtiamsha", "varga", ("D60", "Shashtiamsha"), "P1"),
    Technique("darakaraka", "Darakaraka", "relationship", ("Darakaraka", "DK"), "P1"),
    Technique("ashtakoota", "Ashtakoota matching", "relationship", ("Ashtakoota", "Koota", "Guna Milan"), "P1"),
    Technique("mangal_dosha", "Mangal Dosha", "relationship", ("Mangal Dosha", "Kuja Dosha"), "P1"),
    Technique("relationship_combinations", "Relationship rule-family combinations", "relationship", ("relationship combinations", "marriage combinations", "合盘"), "P1"),
    Technique("conception_adhana_niseka", "Adhana / Niseka conception chart", "conception", ("Adhana", "Niseka", "conception chart"), "P2"),
    Technique("argala", "Argala", "interpretation", ("Argala",), "P2"),
    Technique("yoga", "Yoga rules", "interpretation", ("Yoga", "Raja Yoga", "Dhana Yoga"), "P1"),
)


def _iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for rel in paths:
        base = ROOT / rel
        if not base.exists():
            continue
        if base.is_file():
            files.append(base)
            continue
        for path in base.rglob("*"):
            if path.is_file() and not (set(path.parts) & SKIP_PARTS):
                if path.suffix.lower() in {".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".md", ".txt"}:
                    files.append(path)
    return sorted(set(files))


def _read_layer(files: list[Path]) -> tuple[list[tuple[str, str]], list[str]]:
    indexed: list[tuple[str, str]] = []
    skipped: list[str] = []
    for path in files:
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                skipped.append(str(path.relative_to(ROOT)))
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        indexed.append((str(path.relative_to(ROOT)), text))
    return indexed, skipped


def _count_hits(indexed_files: list[tuple[str, str]], aliases: tuple[str, ...]) -> tuple[int, list[str]]:
    patterns = []
    for alias in aliases:
        escaped = re.escape(alias.lower())
        if re.fullmatch(r"[a-z0-9]+", alias.lower()) and len(alias) <= 4:
            patterns.append(re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"))
        else:
            patterns.append(re.compile(escaped))
    hit_files: list[str] = []
    total = 0
    for rel, text in indexed_files:
        count = sum(len(pattern.findall(text)) for pattern in patterns)
        if count:
            total += count
            hit_files.append(rel)
    return total, hit_files[:12]


def _state_from_hits(count: int, layer: str) -> str:
    if count <= 0:
        return "missing"
    if layer in {"references", "tests"}:
        return "present"
    if count <= 2:
        return "thin"
    return "present"


def _claim_status(tech: Technique, layer_states: dict[str, str]) -> str:
    refs = layer_states["references"] != "missing"
    code = layer_states["scripts"] != "missing" or layer_states["api"] != "missing"
    ui = layer_states["ui"] != "missing"
    tests = layer_states["tests"] != "missing"
    if tech.technique_id in {
        "kp_exact_cusp",
        "kp_star_sub_sub",
        "timing_holdout",
        "saham",
        "tajika",
        "gulika",
        "sphuta",
        "prashna",
    }:
        return "blocked_or_observation_only"
    if tech.technique_id in {"shadbala_chesta", "shadbala_sthana", "muhurta"}:
        return "component_partial"
    if refs and code and tests and ui:
        return "invoked_with_boundary"
    if refs and (code or tests):
        return "evidence_present_not_fully_invoked"
    if refs:
        return "reference_only"
    return "gap_candidate"


def _missing_integration(layer_states: dict[str, str]) -> list[str]:
    missing = []
    for key in ("skill", "api", "ui", "scripts", "tests"):
        if layer_states[key] == "missing":
            missing.append(key)
    return missing


def _priority_score(tech: Technique, layer_states: dict[str, str], claim_status: str) -> int:
    score = {"P0": 300, "P1": 200, "P2": 100}[tech.p_batch]
    if tech.first_batch:
        score += 80
    if layer_states["references"] != "missing":
        score += 40
    if layer_states["scripts"] != "missing" or layer_states["tests"] != "missing":
        score += 25
    if layer_states["api"] == "missing":
        score += 12
    if layer_states["ui"] == "missing":
        score += 10
    if claim_status in {"blocked_or_observation_only", "component_partial", "evidence_present_not_fully_invoked"}:
        score += 20
    return score


def build_matrix() -> dict:
    files_by_layer = {layer: _iter_files(paths) for layer, paths in SCAN_ROOTS.items()}
    indexed_by_layer = {}
    skipped_by_layer = {}
    for layer, files in files_by_layer.items():
        indexed_by_layer[layer], skipped_by_layer[layer] = _read_layer(files)
    rows = []
    for tech in TECHNIQUES:
        layer_hits = {}
        layer_samples = {}
        layer_states = {}
        for layer, indexed_files in indexed_by_layer.items():
            count, samples = _count_hits(indexed_files, tech.aliases)
            layer_hits[layer] = count
            layer_samples[layer] = samples
            layer_states[layer] = _state_from_hits(count, layer)
        claim_status = _claim_status(tech, layer_states)
        missing = _missing_integration(layer_states)
        has_material = layer_states["references"] != "missing" or layer_states["tests"] != "missing" or layer_states["scripts"] != "missing"
        uninvoked = has_material and ("api" in missing or "ui" in missing or "skill" in missing)
        rows.append(
            {
                "technique_id": tech.technique_id,
                "label": tech.label,
                "domain": tech.domain,
                "priority_batch": tech.p_batch,
                "first_batch_requested": tech.first_batch,
                "layer_states": layer_states,
                "hit_counts": layer_hits,
                "sample_files": layer_samples,
                "has_material": has_material,
                "has_material_but_not_fully_invoked": uninvoked,
                "missing_integration": missing,
                "claim_status": claim_status,
                "commercial_sync_policy": "sync_observation_or_boundary_contract_only"
                if claim_status in {"blocked_or_observation_only", "component_partial"}
                else "sync_when_invocation_and_claim_gate_are_explicit",
                "claim_boundary": _claim_boundary(tech, claim_status),
                "priority_score": _priority_score(tech, layer_states, claim_status),
            }
        )
    top50 = sorted(
        [row for row in rows if row["has_material_but_not_fully_invoked"]],
        key=lambda row: (-row["priority_score"], row["technique_id"]),
    )[:50]
    first_batch_ids = {
        "ul_arudha_upapada",
        "a7_arudha_relationship",
        "a10_arudha_career",
        "kp_exact_cusp",
        "kp_star_sub_sub",
        "kp_significator",
        "kp_ruling_planets",
        "shadbala_chesta",
        "shadbala_sthana",
        "muhurta",
        "tarabala",
        "chandrabala",
        "rahu_kalam",
        "abhijit_muhurta",
        "prashna",
        "sphuta",
        "gulika",
        "saham",
        "tajika",
    }
    migration_batches = {
        "P0_first_batch_requested": [
            row for row in rows if row["technique_id"] in first_batch_ids and row["priority_batch"] == "P0"
        ],
        "P1_first_batch_requested": [
            row for row in rows if row["technique_id"] in first_batch_ids and row["priority_batch"] == "P1"
        ],
        "P2_deferred": [row for row in rows if row["priority_batch"] == "P2"],
    }
    return {
        "scope": "full_technique_invocation_matrix",
        "created_at": "2026-07-22",
        "claim_status": "planning_and_invocation_audit",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "boundary": "Automated static invocation scan across skill/API/UI/scripts/references/tests. Hit presence is not numeric oracle closure or predictive validation.",
        "scan_roots": SCAN_ROOTS,
        "scan_limits": {
            "max_file_bytes": MAX_SCAN_BYTES,
            "skipped_large_files_by_layer": skipped_by_layer,
        },
        "summary": {
            "technique_count": len(rows),
            "first_batch_count": sum(1 for row in rows if row["first_batch_requested"]),
            "material_but_not_fully_invoked_count": sum(1 for row in rows if row["has_material_but_not_fully_invoked"]),
            "top50_count": len(top50),
            "p0_count": sum(1 for row in rows if row["priority_batch"] == "P0"),
            "p1_count": sum(1 for row in rows if row["priority_batch"] == "P1"),
            "p2_count": sum(1 for row in rows if row["priority_batch"] == "P2"),
        },
        "first_batch_execution_queue": [
            row for row in rows if row["first_batch_requested"] and row["priority_batch"] in {"P0", "P1"}
        ],
        "migration_batches": migration_batches,
        "top50_material_not_invoked": top50,
        "rows": rows,
        "content_hash": "",
    }


def _claim_boundary(tech: Technique, claim_status: str) -> str:
    if tech.technique_id.startswith("kp_"):
        return "KP runtime/probes may be displayed as observation; exact cusp/star-sub-sub needs public numeric worked example before verified timing use."
    if tech.technique_id.startswith("shadbala"):
        return "Shadbala must show component-level unit/formula/method-variant status; no absolute Virupa truth upgrade until component arbitration closes."
    if tech.domain == "muhurta":
        return "Muhurta factors may be shown as observations/scoring inputs; no final election verdict until worked examples validate the scoring matrix."
    if tech.technique_id in {"prashna", "sphuta", "gulika", "saham", "tajika"}:
        return "Horary/annual numeric packets require public input contract plus expected numeric fields; otherwise observation/queue only."
    if tech.technique_id == "timing_holdout":
        return "Exact month/day and rectification claims require frozen positive/negative labels and blind ranking."
    if claim_status == "reference_only":
        return "Reference exists but runtime invocation is not proven."
    return "Use only with explicit source, settings, and claim boundary."


def main() -> None:
    packet = build_matrix()
    without_hash = dict(packet)
    without_hash["content_hash"] = ""
    digest = hashlib.sha256(json.dumps(without_hash, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    packet["content_hash"] = digest
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUTPUT.relative_to(ROOT)), "sha256": digest, "summary": packet["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
