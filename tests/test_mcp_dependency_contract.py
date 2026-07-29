import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_REQUIREMENT = "mcp>=1.0,<2"


def test_mcp_dependency_stays_on_compatible_major_version() -> None:
    requirements = {
        line.strip()
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert MCP_REQUIREMENT in requirements
    assert MCP_REQUIREMENT in project["project"]["optional-dependencies"]["api"]
