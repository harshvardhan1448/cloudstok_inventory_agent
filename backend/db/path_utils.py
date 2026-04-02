from __future__ import annotations

from pathlib import Path


def find_data_path(*parts: str) -> Path:
    """Return a path under the project data directory, regardless of cwd or container layout."""
    search_roots = [Path(__file__).resolve().parent, Path.cwd(), *Path(__file__).resolve().parents]
    for root in search_roots:
        candidate = root / "data"
        if candidate.exists():
            return candidate.joinpath(*parts)
    return Path.cwd().joinpath("data", *parts)