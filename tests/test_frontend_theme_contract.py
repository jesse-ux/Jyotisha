from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "frontend" / "src" / "app" / "globals.css"


def selector_rule(css: str, selector: str) -> str:
    start = css.index(f"{selector} {{")
    end = css.index("}", start)
    return css[start:end]


def test_lightweight_warm_palette_contract() -> None:
    css = CSS.read_text(encoding="utf-8")

    for token in (
        "--color-canvas: #fbfaf7;",
        "--color-canvas-soft: #f3f2ee;",
        "--color-canvas-muted: #ebe9e3;",
        "--color-ink: #1d1d1f;",
        "--color-ink-secondary: #676762;",
        "--color-ink-tertiary: #8a8983;",
        "--color-action: #85432f;",
        "--color-action-soft: #f4e8e2;",
        "--color-border: #d8d6cf;",
        "--color-border-strong: #b8b5ad;",
    ):
        assert token in css

    assert "--color-sidebar: rgba(235, 233, 227, .86);" in css
    assert "backdrop-filter: saturate(130%) blur(20px);" in css

    for selector in (
        ".sidebar",
        ".starter-list button:first-child",
        ".account-summary",
        ".auth-story",
        ".admin-table-wrap",
    ):
        assert "var(--color-surface-dark)" not in selector_rule(css, selector)
