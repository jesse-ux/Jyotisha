import json
import subprocess
from pathlib import Path

from scripts.answer_quality_audit import audit_answer


ROOT = Path(__file__).resolve().parents[1]


def test_answer_quality_audit_blocks_absolute_claims() -> None:
    result = audit_answer("你一定发生婚姻，并且保证发财。")
    assert result["status"] == "fail"
    assert "一定发生" in result["forbidden_hits"]


def test_answer_quality_audit_requires_timing_health_case_and_method_boundaries() -> None:
    assert audit_answer("什么时候结婚？今年几月。")["timing_boundary_missing"] is True
    assert audit_answer("健康看这里。")["health_boundary_missing"] is True
    assert audit_answer("相似案例说明这个预测正确。")["case_boundary_missing"] is True
    assert audit_answer("Shadbala 和 Ashtakavarga 结果不同。")["method_boundary_missing"] is True


def test_answer_quality_audit_passes_when_boundaries_are_present(tmp_path: Path) -> None:
    rows = [
        {
            "answer": "应期只能给候选窗口，claim_status=exploratory_unvalidated；健康为非医疗表达；相似案例只是参考，不是证明；Shadbala 是流派/方法差异。"
        }
    ]
    path = tmp_path / "answers.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    data = json.loads(subprocess.check_output(["python3", "scripts/answer_quality_audit.py", str(path)], cwd=ROOT, text=True))
    assert data["scope"] == "answer_quality_audit"
    assert data["status"] == "pass"
    assert data["answer_count"] == 1
