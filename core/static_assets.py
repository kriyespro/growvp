"""Load compiled static CSS for inlining (avoids HTML→CSS critical-path chain)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from django.conf import settings


@lru_cache(maxsize=1)
def get_app_css_text() -> str:
    """Return minified app.css contents (cached in-process)."""
    candidates = [
        Path(settings.BASE_DIR) / "static" / "css" / "app.css",
        Path(getattr(settings, "STATIC_ROOT", "") or "") / "css" / "app.css",
    ]
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return "/* app.css missing — run npm run build:css */\n"


def bust_app_css_cache() -> None:
    get_app_css_text.cache_clear()
