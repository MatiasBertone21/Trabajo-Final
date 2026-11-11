"""
Aggregate JSONL telemetry from automation-playwright/reports/, compute statistical
metrics (median, p95, mean, stdev, pass rate, confidence score, DOM ground-truth hit rate),
generate CSV series for the Jenkins Plot plugin, append historical metrics, and render a
self-contained scientific HTML dashboard (`reports/dashboard.html`) with Base64 PNG charts
that complies with Jenkins CSP (zero JavaScript required).
"""
import csv
import html
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

CI_DIR = Path(__file__).resolve().parent
if str(CI_DIR) not in sys.path:
    sys.path.insert(0, str(CI_DIR))

from reporting import (
    FRONTENDS,
    HISTORY_CSV_FIELDNAMES,
    HISTORY_DIR,
    REPORTS_DIR,
    STRATEGIES,
    BaseHTMLReport,
    draw_scenario_bars_chart,
    draw_stacked_layers_chart,
    file_to_base64,
    load_jsonl_glob,
    summarize_cell_records,
)


def _export_csv_and_plot_series(
    summary_by_cell: Dict[Tuple[str, str], Dict[str, Any]],
    build_num: str,
    now_iso: str,
) -> Tuple[Path, Path]:
    """Write `summary_metrics.csv`, append to `metrics-history/history.csv`, and write Jenkins Plot CSVs."""
    summary_csv_path = REPORTS_DIR / "summary_metrics.csv"
    history_csv_path = HISTORY_DIR / "history.csv"

    with open(summary_csv_path, "w", newline="", encoding="utf-8") as sf:
        writer = csv.DictWriter(sf, fieldnames=HISTORY_CSV_FIELDNAMES)
        writer.writeheader()
        for key in sorted(summary_by_cell.keys()):
            writer.writerow({"build_number": build_num, "timestamp": now_iso, **summary_by_cell[key]})

    write_hist_header = not history_csv_path.exists()
    with open(history_csv_path, "a", newline="", encoding="utf-8") as hf:
        writer = csv.DictWriter(hf, fieldnames=HISTORY_CSV_FIELDNAMES)
        if write_hist_header:
            writer.writeheader()
        for key in sorted(summary_by_cell.keys()):
            writer.writerow({"build_number": build_num, "timestamp": now_iso, **summary_by_cell[key]})

    series_cols = [f"{s}-{f}" for s in STRATEGIES for f in FRONTENDS]
    for filename, metric_key in (
        ("plot_duration_ms.csv", "total_median_ms"),
        ("plot_step_ms.csv", "step_median_ms"),
        ("plot_pass_rate.csv", "pass_rate_pct"),
    ):
        with open(REPORTS_DIR / filename, "w", newline="", encoding="utf-8") as pf:
            w = csv.writer(pf)
            w.writerow(series_cols)
            w.writerow([summary_by_cell.get((s, f), {}).get(metric_key, 0.0) for s in STRATEGIES for f in FRONTENDS])

    return summary_csv_path, history_csv_path


class SingleRunBenchmarkReport(BaseHTMLReport):
    """Single-run benchmark HTML report for the legacy `benchmark` Jenkins job."""

    def __init__(self, summary_by_cell: Dict[Tuple[str, str], Dict[str, Any]]) -> None:
        super().__init__()
        self.summary_by_cell = summary_by_cell

    def page_title(self) -> str:
        return "Automation Lab — Dashboard Comparativo de Estrategias"

    def header_title(self) -> str:
        return "Automation Lab — Dashboard Comparativo de Estrategias de Localización UI"

    def header_subtitle(self) -> str:
        return (
            f"Build #{html.escape(str(self.build_num))} | "
            f"Generado: {html.escape(self.now_iso)} | "
            f"Ejecución 100% Serial Controlada"
        )

    def build_body(self) -> str:
        chart_total_b64 = draw_scenario_bars_chart(
            "Tiempo Total E2E por Estrategia y Frontend — Mediana (ms)",
            None,
            STRATEGIES,
            self.summary_by_cell,
            metric_key="total_median_ms",
            p95_key=None,
        )
        chart_step_b64 = draw_scenario_bars_chart(
            "Latencia de Acciones UI por Estrategia y Frontend — Mediana (ms)",
            None,
            STRATEGIES,
            self.summary_by_cell,
            metric_key="step_median_ms",
            p95_key=None,
        )
        chart_layers_b64 = draw_stacked_layers_chart(
            self.summary_by_cell,
            title="Desglose de Latencia por Capa de Percepción (ms acumulados por corrida)",
        )

        table_rows_html: List[str] = []
        for strat in STRATEGIES:
            for fe in FRONTENDS:
                cell = self.summary_by_cell.get((strat, fe))
                if not cell:
                    continue
                is_pass = cell["pass_rate_pct"] == 100.0
                status_txt = f"{cell['pass_rate_pct']:.1f}% ({cell['passed']}/{cell['runs']})"
                table_rows_html.append(
                    f"""
                    <tr>
                      <td>{self.strat_pill(strat)}</td>
                      <td><b>{fe.capitalize()}</b></td>
                      <td>{cell['runs']}</td>
                      <td>{self.status_pill(status_txt, is_pass)}</td>
                      <td><b>{cell['total_median_ms']:.1f}</b></td>
                      <td>{cell['total_p95_ms']:.1f}</td>
                      <td>{cell['total_stdev_ms']:.1f}</td>
                      <td><b>{cell['step_median_ms']:.1f}</b></td>
                      <td>{cell['capture_ms']:.1f}</td>
                      <td>{cell['template_ms']:.1f}</td>
                      <td>{cell['ocr_ranking_ms']:.1f}</td>
                      <td>{cell['mean_confidence']:.3f}</td>
                      <td>{cell['dom_hit_rate_pct']:.0f}%</td>
                    </tr>
                    """
                )

        gallery_items_html: List[str] = []
        for v_strat in ("opencv", "opencv_full"):
            for fe in FRONTENDS:
                audit_dir = REPORTS_DIR / v_strat / fe / "vision_audit"
                if not audit_dir.exists():
                    continue
                for img_path in sorted(audit_dir.glob("*_annotated.png")):
                    b64_img = file_to_base64(img_path, max_width=760)
                    if not b64_img:
                        continue
                    cell_info = self.summary_by_cell.get((v_strat, fe), {})
                    conf = cell_info.get("mean_confidence", 0.0)
                    step_ms = cell_info.get("step_median_ms", 0.0)
                    hit_pct = cell_info.get("dom_hit_rate_pct", 100.0)
                    gallery_items_html.append(
                        f"""
                        <div class="gallery-card">
                          <div class="gallery-header">
                            <strong>{self.strat_pill(v_strat)} @ {html.escape(fe.upper())}</strong>
                            <span>Archivo: <code>{html.escape(img_path.name)}</code> | Confianza: <b>{conf:.3f}</b> | Paso: <b>{step_ms:.1f} ms</b> | DOM Hit: <b>{hit_pct:.0f}%</b></span>
                          </div>
                          <img src="data:image/png;base64,{b64_img}" alt="{html.escape(v_strat)} {html.escape(fe)} annotated bbox" />
                        </div>
                        """
                    )

        rows_str = (
            "\n".join(table_rows_html)
            if table_rows_html
            else '<tr><td colspan="13">No se encontraron registros de telemetría en esta corrida.</td></tr>'
        )
        gallery_str = (
            "\n".join(gallery_items_html)
            if gallery_items_html
            else '<p class="muted">No se ejecutaron pruebas con la estrategia <code>opencv</code> en este build.</p>'
        )

        return f"""
  <section class="card">
    <h2>1. Tabla Resumen Experimental (Tiempos en ms, Confianza y Precisión Geométrica)</h2>
    <table>
      <thead>
        <tr>
          <th>Estrategia</th>
          <th>Frontend</th>
          <th>N</th>
          <th>Tasa Éxito</th>
          <th>Total Mediana (ms)</th>
          <th>Total p95 (ms)</th>
          <th>Total DE (ms)</th>
          <th>Paso add_to_cart (ms)</th>
          <th>Captura (ms)</th>
          <th>Template (ms)</th>
          <th>OCR+Rank (ms)</th>
          <th>Confianza</th>
          <th>DOM Hit</th>
        </tr>
      </thead>
      <tbody>
        {rows_str}
      </tbody>
    </table>
  </section>

  <section class="card">
    <h2>2. Comparativa de Tiempos de Ejecución y Desglose por Capa de Percepción</h2>
    <div class="charts-grid">
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_total_b64}" alt="Tiempo Total E2E" />
      </div>
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_step_b64}" alt="Tiempo Paso add_to_cart" />
      </div>
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_layers_b64}" alt="Desglose de Latencia por Capa" />
      </div>
    </div>
  </section>

  <section class="card">
    <h2>3. Auditoría Visual de Detecciones OpenVisor (BBoxes + Center Point + DOM Ground Truth)</h2>
    <div class="gallery-grid">
      {gallery_str}
    </div>
  </section>
"""


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    test_records = load_jsonl_glob(REPORTS_DIR, "*/*/telemetry_tests.jsonl")
    step_records = load_jsonl_glob(REPORTS_DIR, "*/*/telemetry_steps.jsonl")

    summary_by_cell: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for strat in STRATEGIES:
        for fe in FRONTENDS:
            t_recs = [r for r in test_records if r.get("strategy") == strat and r.get("frontend") == fe]
            if not t_recs:
                continue
            s_recs = [r for r in step_records if r.get("strategy") == strat and r.get("frontend") == fe]
            summary_by_cell[(strat, fe)] = summarize_cell_records(strat, fe, t_recs, s_recs)

    report = SingleRunBenchmarkReport(summary_by_cell)
    summary_csv_path, history_csv_path = _export_csv_and_plot_series(
        summary_by_cell, report.build_num, report.now_iso
    )
    dashboard_path = report.save(REPORTS_DIR / "dashboard.html")

    print(f"[Dashboard] Generated {dashboard_path}")
    print(f"[Dashboard] Generated {summary_csv_path} and updated {history_csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
