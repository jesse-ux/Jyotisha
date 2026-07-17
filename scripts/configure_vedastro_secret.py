"""Configure VedAstro local secret without echoing it.

Run manually from a trusted terminal. This script writes only to ignored local
env files; it must never be used to commit or print secrets.
"""

from __future__ import annotations

import getpass
from pathlib import Path


DEFAULT_ENV = Path(".env.local")
DEFAULT_ENDPOINT = "https://api.vedastro.org/api"


def update_env_text(text: str, updates: dict[str, str]) -> str:
    lines = text.splitlines()
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output.append(line)
            continue
        key, _value = line.split("=", 1)
        key = key.strip()
        if key in updates:
            output.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in updates.items():
        if key not in seen:
            output.append(f"{key}={value}")
    return "\n".join(output).rstrip() + "\n"


def write_env(path: Path, updates: dict[str, str]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(update_env_text(existing, updates), encoding="utf-8")


def main() -> int:
    key = getpass.getpass("VedAstro API key (hidden): ").strip()
    if not key:
        print("No key entered; nothing changed.")
        return 1
    endpoint = input(f"VedAstro endpoint [{DEFAULT_ENDPOINT}]: ").strip() or DEFAULT_ENDPOINT
    write_env(
        DEFAULT_ENV,
        {
            "VEDASTRO_API_KEY": key,
            "VEDASTRO_API_ENDPOINT": endpoint,
            "VEDASTRO_ENABLE_NETWORK": "1",
            "VEDASTRO_TIMEOUT_SECONDS": "20",
        },
    )
    print(f"Updated {DEFAULT_ENV}; secret value was not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
