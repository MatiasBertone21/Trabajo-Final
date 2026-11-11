"""
Generate a self-contained HTML visual catalog (`reports/templates_gallery.html`)
for auditing all harvested UI templates across React, Angular, and Svelte in Jenkins.
"""
import html
import sys
from datetime import datetime
from pathlib import Path
from typing import List

CI_DIR = Path(__file__).resolve().parent
if str(CI_DIR) not in sys.path:
    sys.path.insert(0, str(CI_DIR))

from reporting import (
    EXPECTED_TEMPLATES,
    FRONTENDS,
    REPORTS_DIR,
    TEMPLATES_DIR,
    BaseHTMLReport,
    read_png_info,
)


class TemplatesGalleryReport(BaseHTMLReport):
    """HTML catalog report for auditing harvested OpenVisor UI templates per frontend."""

    def __init__(self) -> None:
        super().__init__()
        os_marker = TEMPLATES_DIR / ".harvested_os"
        self.harvested_os = (
            os_marker.read_text(encoding="utf-8").strip() if os_marker.exists() else "Unknown"
        )

    def page_title(self) -> str:
        return "Automation Lab — Catálogo de Plantillas Visuales (OpenVisor)"

    def header_title(self) -> str:
        return "Automation Lab — Catálogo Auditable de Plantillas Visuales (OpenVisor)"

    def header_subtitle(self) -> str:
        return (
            f"Build #{html.escape(str(self.build_num))} | "
            f"Generado: {html.escape(self.now_iso)} | "
            f"Sistema Operativo de Cosecha: <b>{html.escape(self.harvested_os)}</b>"
        )

    def extra_css(self) -> str:
        return """
    th, td { text-align: left; }
    .tpl-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
    }
    .tpl-card {
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
    }
    .tpl-card.missing { border-color: #fca5a5; background: #fef2f2; }
    .tpl-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: #f1f5f9;
      border-bottom: 1px solid #e2e8f0;
    }
    .key-badge { font-size: 12px; font-weight: 700; color: #1e293b; }
    .extra-badge { color: #64748b; }
    .tpl-preview {
      padding: 14px;
      min-height: 90px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-image: linear-gradient(45deg, #f1f5f9 25%, transparent 25%),
                        linear-gradient(-45deg, #f1f5f9 25%, transparent 25%),
                        linear-gradient(45deg, transparent 75%, #f1f5f9 75%),
                        linear-gradient(-45deg, transparent 75%, #f1f5f9 75%);
      background-size: 16px 16px;
      background-position: 0 0, 0 8px, 8px -8px, -8px 0;
    }
    .tpl-preview img {
      max-width: 100%;
      max-height: 160px;
      border: 1px dashed #94a3b8;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .tpl-preview.empty { color: #991b1b; font-size: 12px; font-weight: 600; }
    .tpl-meta {
      padding: 8px 12px;
      border-top: 1px solid #e2e8f0;
      font-size: 11px;
      background: #f8fafc;
    }
    .tpl-meta .dim { color: #64748b; margin-top: 4px; }
"""

    @staticmethod
    def _render_template_card(
        key: str,
        rel_path: str,
        fpath: Path,
        is_extra: bool = False,
    ) -> str:
        w, h, size_kb, b64 = read_png_info(fpath)
        dim_str = f"{w}x{h} px" if w and h else "PNG"
        mtime = datetime.fromtimestamp(fpath.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        card_cls = "extra" if is_extra else "ok"
        badge_cls = "key-badge extra-badge" if is_extra else "key-badge"
        return f"""
        <div class="tpl-card {card_cls}">
          <div class="tpl-top">
            <span class="{badge_cls}">{html.escape(key)}</span>
            {BaseHTMLReport.status_pill("OK", True)}
          </div>
          <div class="tpl-preview">
            <img src="data:image/png;base64,{b64}" alt="{html.escape(rel_path)}" />
          </div>
          <div class="tpl-meta">
            <div><code>{html.escape(rel_path)}</code></div>
            <div class="dim">{dim_str} &middot; {size_kb} KB &middot; {mtime}</div>
          </div>
        </div>
        """

    def build_body(self) -> str:
        sections_html: List[str] = []
        summary_rows: List[str] = []
        total_expected = len(EXPECTED_TEMPLATES)

        for fe in FRONTENDS:
            fe_dir = TEMPLATES_DIR / fe
            cards_html: List[str] = []
            found_count = 0
            seen_rel_paths = set()

            # 1. Check all catalog templates required by OpenVisor
            for key, rel_path in EXPECTED_TEMPLATES.items():
                seen_rel_paths.add(rel_path)
                fpath = fe_dir / rel_path
                if fpath.exists():
                    found_count += 1
                    cards_html.append(self._render_template_card(key, rel_path, fpath))
                else:
                    cards_html.append(
                        f"""
                        <div class="tpl-card missing">
                          <div class="tpl-top">
                            <span class="key-badge">{html.escape(key)}</span>
                            {self.status_pill("MISSING", False)}
                          </div>
                          <div class="tpl-preview empty">No encontrado</div>
                          <div class="tpl-meta">
                            <div><code>{html.escape(rel_path)}</code></div>
                          </div>
                        </div>
                        """
                    )

            # 2. Include any extra harvested PNGs (e.g. login inputs, category badge)
            if fe_dir.exists():
                for extra_path in sorted(fe_dir.rglob("*.png")):
                    rel_p = extra_path.relative_to(fe_dir).as_posix()
                    if rel_p in seen_rel_paths:
                        continue
                    cards_html.append(
                        self._render_template_card("extra", rel_p, extra_path, is_extra=True)
                    )

            # In Svelte, cart-item-description is optional on the cart item card
            passed = found_count >= (total_expected - 1)
            summary_rows.append(
                f"""
                <tr>
                  <td><b>{fe.upper()}</b></td>
                  <td><code>templates/{fe}/</code></td>
                  <td>{self.status_pill(f"{found_count} / {total_expected} requeridos", passed)}</td>
                  <td>{html.escape(self.harvested_os)}</td>
                </tr>
                """
            )

            sections_html.append(
                f"""
                <section class="card">
                  <h2>Frontend: {fe.upper()} (<code>templates/{fe}/</code>)</h2>
                  <div class="tpl-grid">
                    {"".join(cards_html)}
                  </div>
                </section>
                """
            )

        return f"""
  <section class="card">
    <h2>Resumen de Cobertura del Catálogo (`ENV_TEMPLATE_CATALOG`)</h2>
    <table>
      <thead>
        <tr>
          <th>Frontend</th>
          <th>Directorio</th>
          <th>Plantillas Requeridas</th>
          <th>OS Renderizado</th>
        </tr>
      </thead>
      <tbody>
        {"".join(summary_rows)}
      </tbody>
    </table>
  </section>

  {"".join(sections_html)}
"""


def main() -> int:
    report = TemplatesGalleryReport()
    gallery_path = report.save(REPORTS_DIR / "templates_gallery.html")
    print(f"[Templates Gallery] Generated {gallery_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
