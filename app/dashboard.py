"""Single-page dashboard served at GET /."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
INDEX_HTML_PATH = TEMPLATES_DIR / "index.html"


def get_dashboard_html() -> str:
    """Read and return the dashboard HTML template."""
    return INDEX_HTML_PATH.read_text(encoding="utf-8")


DASHBOARD_HTML = get_dashboard_html()
