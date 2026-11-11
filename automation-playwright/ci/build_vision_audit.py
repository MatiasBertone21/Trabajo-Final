"""
Sync telemetry from the current test execution (`reports/*/*/telemetry_*.jsonl`) into
`metrics-history/` (`history_tests.jsonl`, `history_steps.jsonl`, `history.csv`) and
render a dedicated OpenVisor Visual Audit HTML report (`reports/vision_audit.html`)
for the `run-e2e-tests` Jenkins job, grouped by executed test.
"""
import csv
import html
import json
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

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
    file_to_base64,
    load_jsonl_file,
    load_jsonl_glob,
    summarize_cell_records,
)


def _sync_to_history(
    current_tests: List[Dict[str, Any]],
    current_steps: List[Dict[str, Any]],
) -> Set[Tuple[str, str]]:
    """
    Append deduplicated test and step JSONL records from the current execution into
    `metrics-history/history_tests.jsonl`, `metrics-history/history_steps.jsonl`,
    and `metrics-history/history.csv` (text telemetry only, no image duplication).
    """
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    hist_tests_path = HISTORY_DIR / "history_tests.jsonl"
    hist_steps_path = HISTORY_DIR / "history_steps.jsonl"
    history_csv_path = HISTORY_DIR / "history.csv"

    hist_tests = load_jsonl_file(hist_tests_path)
    hist_steps = load_jsonl_file(hist_steps_path)

    seen_tests = {
        (r.get("run_id"), r.get("strategy"), r.get("frontend"), r.get("repeat_idx"))
        for r in hist_tests
    }
    seen_steps = {
        (r.get("run_id"), r.get("strategy"), r.get("frontend"), r.get("repeat_idx"), r.get("step_name"))
        for r in hist_steps
    }

    new_tests = []
    newly_added_cells: Set[Tuple[str, str]] = set()
    for r in current_tests:
        key = (r.get("run_id"), r.get("strategy"), r.get("frontend"), r.get("repeat_idx"))
        if key not in seen_tests:
            seen_tests.add(key)
            new_tests.append(r)
            newly_added_cells.add((str(r.get("strategy")), str(r.get("frontend"))))

    new_steps = []
    for r in current_steps:
        key = (r.get("run_id"), r.get("strategy"), r.get("frontend"), r.get("repeat_idx"), r.get("step_name"))
        if key not in seen_steps:
            seen_steps.add(key)
            new_steps.append(r)

    if new_tests:
        with open(hist_tests_path, "a", encoding="utf-8") as f:
            for r in new_tests:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if new_steps:
        with open(hist_steps_path, "a", encoding="utf-8") as f:
            for r in new_steps:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if newly_added_cells:
        now_iso = datetime.now().isoformat(timespec="seconds")
        build_num = os.getenv("BUILD_NUMBER", "local")
        write_header = not history_csv_path.exists()

        with open(history_csv_path, "a", newline="", encoding="utf-8") as hf:
            writer = csv.DictWriter(hf, fieldnames=HISTORY_CSV_FIELDNAMES)
            if write_header:
                writer.writeheader()
            for strat, fe in sorted(newly_added_cells):
                t_recs = [r for r in current_tests if r.get("strategy") == strat and r.get("frontend") == fe]
                s_recs = [r for r in current_steps if r.get("strategy") == strat and r.get("frontend") == fe]
                if not t_recs:
                    continue
                summary = summarize_cell_records(strat, fe, t_recs, s_recs)
                writer.writerow({"build_number": build_num, "timestamp": now_iso, **summary})

    return newly_added_cells


class VisionAuditReport(BaseHTMLReport):
    """HTML report for OpenVisor visual detections and test execution summary in `run-e2e-tests`."""

    def __init__(
        self,
        current_tests: List[Dict[str, Any]],
        current_steps: List[Dict[str, Any]],
    ) -> None:
        super().__init__()
        self.current_tests = current_tests
        self.current_steps = current_steps

    def page_title(self) -> str:
        return "Automation Lab — Reporte de Ejecución y Auditoría Visual OpenVisor"

    def header_title(self) -> str:
        return "Automation Lab — Auditoría Visual de Detecciones OpenVisor (Ejecución de Tests)"

    def header_subtitle(self) -> str:
        return (
            f"Build #{html.escape(str(self.build_num))} | "
            f"Generado: {html.escape(self.now_iso)} | "
            f"Telemetría sincronizada en <code>metrics-history/</code>"
        )

    def extra_css(self) -> str:
        return """
    th:nth-child(3), td:nth-child(3) { text-align: left; }
"""

    def _build_summary_rows(self) -> str:
        run_rows_html: List[str] = []
        for strat in STRATEGIES:
            for fe in FRONTENDS:
                t_recs = [r for r in self.current_tests if r.get("strategy") == strat and r.get("frontend") == fe]
                if not t_recs:
                    continue
                s_recs = [r for r in self.current_steps if r.get("strategy") == strat and r.get("frontend") == fe]
                passed = sum(1 for r in t_recs if r.get("outcome") == "passed")
                pass_rate = round((passed / len(t_recs)) * 100.0, 1)
                med_total = statistics.median([float(r.get("total_ms", 0.0)) for r in t_recs])
                med_action = statistics.median([float(r.get("action_step_ms", 0.0)) for r in t_recs])
                confs = [float(r["confidence_score"]) for r in s_recs if r.get("confidence_score") is not None]
                mean_conf = statistics.mean(confs) if confs else 1.0
                test_name = str(t_recs[-1].get("test_id", "")).split("::")[0] or "tests/test_products.py"

                run_rows_html.append(
                    f"""
                    <tr>
                      <td>{self.strat_pill(strat)}</td>
                      <td><b>{fe.capitalize()}</b></td>
                      <td style="text-align:left"><code>{html.escape(test_name)}</code></td>
                      <td>{len(t_recs)}</td>
                      <td>{self.status_pill(f"{pass_rate:.0f}% ({passed}/{len(t_recs)})", pass_rate == 100.0)}</td>
                      <td><b>{med_total:.1f} ms</b></td>
                      <td>{med_action:.1f} ms</td>
                      <td>{len(s_recs) // max(1, len(t_recs))}</td>
                      <td>{mean_conf:.3f}</td>
                    </tr>
                    """
                )

        return (
            "\n".join(run_rows_html)
            if run_rows_html
            else '<tr><td colspan="9">No se encontraron ejecuciones en esta corrida.</td></tr>'
        )

    def _build_visual_sections(self) -> str:
        test_sections_html: List[str] = []
        for v_strat in ("opencv", "opencv_full"):
            for fe in FRONTENDS:
                audit_dir = REPORTS_DIR / v_strat / fe / "vision_audit"
                if not audit_dir.exists():
                    continue
                annotated_files = sorted(audit_dir.glob("*_annotated.png"))
                if not annotated_files:
                    continue

                t_recs = [r for r in self.current_tests if r.get("strategy") == v_strat and r.get("frontend") == fe]
                s_recs = [r for r in self.current_steps if r.get("strategy") == v_strat and r.get("frontend") == fe]

                test_file = "tests/test_full_vision_flow.py" if v_strat == "opencv_full" else "tests/test_products.py"
                passed = sum(1 for r in t_recs if r.get("outcome") == "passed")
                total_runs = len(t_recs) or 1
                is_pass = passed == total_runs
                status_txt = f"PASSED ({passed}/{total_runs})" if is_pass else f"FAILED ({passed}/{total_runs})"
                total_ms = statistics.median([float(r.get("total_ms", 0.0)) for r in t_recs]) if t_recs else 0.0

                cards_in_test_html: List[str] = []
                for img_path in annotated_files:
                    b64_img = file_to_base64(img_path, max_width=760)
                    if not b64_img:
                        continue

                    matching_step = next(
                        (
                            s for s in s_recs
                            if s.get("audit_image")
                            and Path(str(s["audit_image"]).replace("\\", "/")).name == img_path.name
                        ),
                        None,
                    )
                    if matching_step is None and v_strat == "opencv" and s_recs:
                        matching_step = s_recs[-1]

                    if matching_step:
                        step_label = str(matching_step.get("step_name", img_path.stem))
                        step_ms = float(matching_step.get("total_step_ms", 0.0))
                        tpl_ms = float(matching_step.get("server_template_ms", 0.0))
                        ocr_ms = float(matching_step.get("server_ocr_ms", 0.0))
                        conf = float(matching_step.get("confidence_score") or 0.0)
                        ocr_mode = (
                            "OCR=True (TM_CCOEFF + EasyOCR)"
                            if matching_step.get("enable_ocr")
                            else "OCR=False (TM_CCOEFF_NORMED)"
                        )
                        cp = matching_step.get("center_point")
                        click_str = (
                            f"Click: ({cp['x']}, {cp['y']})"
                            if isinstance(cp, dict) and "x" in cp
                            else "Aserción Visual"
                        )
                        meta_line = (
                            f"Paso: <code>{html.escape(step_label)}</code> | Modo: <b>{ocr_mode}</b> | "
                            f"{click_str} | Confianza: <b>{conf:.3f}</b> | "
                            f"Total Paso: <b>{step_ms:.1f} ms</b> (Template: {tpl_ms:.1f} ms, OCR: {ocr_ms:.1f} ms)"
                        )
                    else:
                        meta_line = f"Archivo: <code>{html.escape(img_path.name)}</code>"

                    cards_in_test_html.append(
                        f"""
                        <div class="gallery-card">
                          <div class="gallery-header">
                            <strong>{self.strat_pill(v_strat)} @ {html.escape(fe.upper())}</strong>
                            <span>{meta_line}</span>
                          </div>
                          <img src="data:image/png;base64,{b64_img}" alt="{html.escape(v_strat)} {html.escape(fe)} {html.escape(img_path.name)}" />
                        </div>
                        """
                    )

                test_sections_html.append(
                    f"""
                    <section class="card">
                      <div class="test-group-header">
                        <h2>
                          {self.strat_pill(v_strat)}
                          Frontend: {html.escape(fe.upper())} &mdash; <code>{html.escape(test_file)}</code>
                        </h2>
                        <div>
                          {self.status_pill(status_txt, is_pass)}
                          <span class="test-time-badge">Tiempo Total E2E: <b>{total_ms:.1f} ms</b> &middot; Capturas Auditadas: <b>{len(cards_in_test_html)}</b></span>
                        </div>
                      </div>
                      <div class="gallery-grid">
                        {"".join(cards_in_test_html)}
                      </div>
                    </section>
                    """
                )

        if test_sections_html:
            return "\n".join(test_sections_html)
        return """
        <section class="card">
          <h2>Auditoría Visual de Detecciones OpenVisor</h2>
          <p class="muted">En esta corrida solo se ejecutaron estrategias basadas en DOM (<code>base</code> / <code>getby</code> / <code>getby_full</code>). Sus métricas ya fueron sincronizadas en <code>metrics-history/</code>.</p>
        </section>
        """

    def build_body(self) -> str:
        rows_str = self._build_summary_rows()
        sections_str = self._build_visual_sections()
        return f"""
  <section class="card">
    <h2>1. Resumen de Pruebas Ejecutadas en este Build</h2>
    <table>
      <thead>
        <tr>
          <th>Estrategia</th>
          <th>Frontend</th>
          <th>Archivo de Test</th>
          <th>Corridas (N)</th>
          <th>Resultado</th>
          <th>Tiempo Total E2E</th>
          <th>Tiempo Acciones</th>
          <th>Pasos / Corrida</th>
          <th>Confianza Media</th>
        </tr>
      </thead>
      <tbody>
        {rows_str}
      </tbody>
    </table>
  </section>

  {sections_str}
"""


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    current_tests = load_jsonl_glob(REPORTS_DIR, "*/*/telemetry_tests.jsonl")
    current_steps = load_jsonl_glob(REPORTS_DIR, "*/*/telemetry_steps.jsonl")

    _sync_to_history(current_tests, current_steps)

    report = VisionAuditReport(current_tests, current_steps)
    audit_report_path = report.save(REPORTS_DIR / "vision_audit.html")
    print(f"[Vision Audit] Generated {audit_report_path} and synced telemetry to {HISTORY_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
