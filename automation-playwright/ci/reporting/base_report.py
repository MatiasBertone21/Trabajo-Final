"""
Abstract base class `BaseHTMLReport` implementing the Template Method pattern
for generating self-contained, Jenkins CSP-compliant HTML reports.
"""
import html
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

BASE_CSS = """
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      margin: 0;
      padding: 24px 32px;
    }
    header {
      background: #0f172a;
      color: #ffffff;
      padding: 20px 28px;
      border-radius: 12px;
      margin-bottom: 24px;
    }
    header h1 {
      margin: 0 0 6px 0;
      font-size: 22px;
    }
    header p {
      margin: 0;
      color: #cbd5e1;
      font-size: 13px;
    }
    .card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .card h2 {
      margin: 0 0 14px 0;
      font-size: 17px;
      color: #0f172a;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      padding: 9px 10px;
      text-align: right;
      border-bottom: 1px solid #e2e8f0;
    }
    th:nth-child(1), th:nth-child(2), td:nth-child(1), td:nth-child(2) {
      text-align: left;
    }
    th {
      background: #f1f5f9;
      color: #334155;
      font-weight: 600;
    }
    .strat-pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      color: #fff;
    }
    .strat-base { background: #2563eb; }
    .strat-getby { background: #10b981; }
    .strat-opencv { background: #f59e0b; }
    .strat-getby_full { background: #0d9488; }
    .strat-opencv_full { background: #e11d48; }
    .src-pill {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      background: #f1f5f9;
      color: #334155;
    }
    .status-pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
    }
    .status-pill.pass { background: #dcfce7; color: #166534; }
    .status-pill.fail { background: #fee2e2; color: #991b1b; }
    .charts-grid, .gallery-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
    }
    .chart-box img {
      max-width: 100%;
      height: auto;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
    }
    .gallery-card {
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      overflow: hidden;
      background: #f8fafc;
    }
    .gallery-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      padding: 10px 14px;
      background: #e2e8f0;
      font-size: 12.5px;
    }
    .gallery-card img {
      display: block;
      max-width: 100%;
      height: auto;
      margin: 0 auto;
    }
    .test-group-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 10px;
      margin-bottom: 16px;
    }
    .test-group-header h2 {
      margin: 0;
      border: none;
      padding: 0;
    }
    .test-time-badge {
      font-size: 12px;
      color: #334155;
      margin-left: 10px;
    }
    .muted {
      color: #64748b;
      font-size: 13px;
    }
"""


class BaseHTMLReport(ABC):
    """
    Base Template Method class for all CI HTML reports.
    Subclasses define `page_title`, `header_title`, `header_subtitle`, optional `extra_css`,
    and `build_body`, while `render_html` / `save` handle the document structure.
    """

    def __init__(self) -> None:
        self.build_num: str = os.getenv("BUILD_NUMBER", "local")
        self.now_iso: str = datetime.now().isoformat(timespec="seconds")

    @abstractmethod
    def page_title(self) -> str:
        """Return the HTML `<title>` string."""

    @abstractmethod
    def header_title(self) -> str:
        """Return the main `<header><h1>` heading."""

    @abstractmethod
    def header_subtitle(self) -> str:
        """Return the `<header><p>` metadata line (may contain safe HTML tags)."""

    def extra_css(self) -> str:
        """Return optional report-specific CSS rules."""
        return ""

    @abstractmethod
    def build_body(self) -> str:
        """Return the inner `<section class='card'>...</section>` blocks."""

    @staticmethod
    def strat_pill(strat: str) -> str:
        """Render a colored strategy pill (`base`, `getby`, `opencv`, `getby_full`, `opencv_full`)."""
        s_esc = html.escape(strat)
        return f'<span class="strat-pill strat-{s_esc}">{s_esc.upper()}</span>'

    @staticmethod
    def status_pill(text: str, passed: bool) -> str:
        """Render a green (`pass`) or red (`fail`) status pill."""
        cls = "pass" if passed else "fail"
        return f'<span class="status-pill {cls}">{html.escape(text)}</span>'

    def render_html(self) -> str:
        """Assemble the full HTML5 document using the Template Method hooks."""
        custom_css = self.extra_css()
        body_content = self.build_body()
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(self.page_title())}</title>
  <style>
{BASE_CSS}
{custom_css}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(self.header_title())}</h1>
    <p>{self.header_subtitle()}</p>
  </header>

{body_content}
</body>
</html>
"""

    def save(self, output_path: Path) -> Path:
        """Render the HTML report and write it to `output_path`."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_html(), encoding="utf-8")
        return output_path
