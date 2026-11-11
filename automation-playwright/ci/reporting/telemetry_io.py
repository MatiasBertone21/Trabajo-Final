"""
Shared statistical, JSONL/CSV I/O, per-run telemetry aggregation, and Base64 image helpers.
"""
import base64
import csv
import io
import json
import math
import statistics
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image


def percentile(sorted_vals: List[float], p: float) -> float:
    """Compute linear-interpolated percentile `p` (0..100) from a pre-sorted list."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def compute_stats(values: List[float]) -> Dict[str, float]:
    """Return median, p95, mean, stdev, min, and max for a list of numeric values."""
    if not values:
        return {"median": 0.0, "p95": 0.0, "mean": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0}
    s = sorted(values)
    return {
        "median": round(statistics.median(s), 2),
        "p95": round(percentile(s, 95), 2),
        "mean": round(statistics.mean(s), 2),
        "stdev": round(statistics.stdev(s), 2) if len(s) > 1 else 0.0,
        "min": round(s[0], 2),
        "max": round(s[-1], 2),
    }


def load_jsonl_file(path: Path) -> List[Dict[str, Any]]:
    """Read a JSON Lines file and return a list of parsed dictionary records."""
    records: List[Dict[str, Any]] = []
    if not path.exists():
        return records
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}")
    return records


def load_jsonl_glob(root: Path, pattern: str) -> List[Dict[str, Any]]:
    """Read and concatenate all JSON Lines files matching `pattern` under `root`."""
    records: List[Dict[str, Any]] = []
    for path in sorted(root.glob(pattern)):
        records.extend(load_jsonl_file(path))
    return records


def load_legacy_csv_history(csv_path: Path) -> List[Dict[str, Any]]:
    """Read rows from `metrics-history/history.csv` (handles UTF-8 with or without BOM)."""
    if not csv_path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                rows.append(r)
    except Exception as e:
        print(f"[WARN] Could not read {csv_path}: {e}")
    return rows


def img_to_base64(img: Image.Image) -> str:
    """Encode a Pillow Image instance as an optimized Base64 PNG string."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def file_to_base64(path: Path, max_width: int = 760) -> Optional[str]:
    """Load an image file, downscale if wider than `max_width`, and return Base64 PNG."""
    if not path.exists():
        return None
    try:
        with Image.open(path) as im:
            if im.width > max_width:
                ratio = max_width / float(im.width)
                new_h = int(im.height * ratio)
                im = im.resize((max_width, new_h), Image.Resampling.LANCZOS)
            return img_to_base64(im)
    except Exception:
        return None


def read_png_info(path: Path) -> Tuple[Optional[int], Optional[int], float, str]:
    """Return (width, height, size_kb, base64_str) for a PNG file by inspecting its IHDR header."""
    raw = path.read_bytes()
    size_kb = round(len(raw) / 1024.0, 1)
    b64 = base64.b64encode(raw).decode("ascii")
    w, h = None, None
    if len(raw) >= 24 and raw[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", raw[16:24])
    return w, h, size_kb, b64


def aggregate_per_run_layers(
    t_recs: List[Dict[str, Any]],
    s_recs: List[Dict[str, Any]],
) -> Dict[str, List[float]]:
    """
    Group step records by `(run_id, repeat_idx)` and sum each perception layer's latency
    across all steps of a run before taking cross-run medians. This ensures multi-step
    flows (`opencv_full` / `getby_full`) with mixed `OCR=True` and `OCR=False` steps
    reflect the true cumulative perception cost per test execution.
    """
    run_keys = {(r.get("run_id"), r.get("repeat_idx")) for r in t_recs}
    per_run_step_ms: List[float] = []
    per_run_cap_ms: List[float] = []
    per_run_net_ms: List[float] = []
    per_run_dec_ms: List[float] = []
    per_run_tpl_ms: List[float] = []
    per_run_ocr_ms: List[float] = []

    for rk in run_keys:
        r_steps = [s for s in s_recs if (s.get("run_id"), s.get("repeat_idx")) == rk]
        if r_steps:
            per_run_step_ms.append(sum(float(s.get("total_step_ms", 0.0)) for s in r_steps))
            per_run_cap_ms.append(sum(float(s.get("capture_ms", 0.0)) for s in r_steps))
            per_run_net_ms.append(sum(float(s.get("network_ms", 0.0)) for s in r_steps))
            per_run_dec_ms.append(
                sum(float(s.get("server_decode_ms", 0.0)) + float(s.get("server_preprocess_ms", 0.0)) for s in r_steps)
            )
            per_run_tpl_ms.append(sum(float(s.get("server_template_ms", 0.0)) for s in r_steps))
            per_run_ocr_ms.append(
                sum(float(s.get("server_ocr_ms", 0.0)) + float(s.get("server_ranking_ms", 0.0)) for s in r_steps)
            )

    if not per_run_step_ms:
        per_run_step_ms = [float(r.get("action_step_ms", 0.0)) for r in t_recs]

    return {
        "step_ms": per_run_step_ms,
        "capture_ms": per_run_cap_ms,
        "network_ms": per_run_net_ms,
        "decode_preprocess_ms": per_run_dec_ms,
        "template_ms": per_run_tpl_ms,
        "ocr_ranking_ms": per_run_ocr_ms,
    }


def summarize_cell_records(
    strat: str,
    fe: str,
    t_recs: List[Dict[str, Any]],
    s_recs: List[Dict[str, Any]],
    extra_total_times: Optional[List[float]] = None,
    extra_call_times: Optional[List[float]] = None,
    runs_override: Optional[int] = None,
    passed_override: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute standardized statistical summary dictionary for a `(strategy, frontend)` cell."""
    total_times = (extra_total_times or []) + [float(r.get("total_ms", 0.0)) for r in t_recs]
    call_times = (extra_call_times or []) + [float(r.get("call_ms", 0.0)) for r in t_recs]
    layers = aggregate_per_run_layers(t_recs, s_recs)

    runs_cnt = runs_override if runs_override is not None else len(t_recs)
    passed_cnt = passed_override if passed_override is not None else sum(
        1 for r in t_recs if r.get("outcome") == "passed"
    )
    pass_rate = round((passed_cnt / max(1, runs_cnt)) * 100.0, 1)

    confs = [float(r["confidence_score"]) for r in s_recs if r.get("confidence_score") is not None]
    hits = [bool(r["dom_ground_truth_hit"]) for r in s_recs if r.get("dom_ground_truth_hit") is not None]

    t_stats = compute_stats(total_times)
    c_stats = compute_stats(call_times)
    s_stats = compute_stats(layers["step_ms"])

    return {
        "strategy": strat,
        "frontend": fe,
        "runs": runs_cnt,
        "passed": passed_cnt,
        "pass_rate_pct": pass_rate,
        "total_median_ms": t_stats["median"],
        "total_p95_ms": t_stats["p95"],
        "total_mean_ms": t_stats["mean"],
        "total_stdev_ms": t_stats["stdev"],
        "call_median_ms": c_stats["median"],
        "step_median_ms": s_stats["median"],
        "step_p95_ms": s_stats["p95"],
        "capture_ms": round(statistics.median(layers["capture_ms"]), 2) if layers["capture_ms"] else 0.0,
        "network_ms": round(statistics.median(layers["network_ms"]), 2) if layers["network_ms"] else 0.0,
        "decode_preprocess_ms": (
            round(statistics.median(layers["decode_preprocess_ms"]), 2) if layers["decode_preprocess_ms"] else 0.0
        ),
        "template_ms": round(statistics.median(layers["template_ms"]), 2) if layers["template_ms"] else 0.0,
        "ocr_ranking_ms": round(statistics.median(layers["ocr_ranking_ms"]), 2) if layers["ocr_ranking_ms"] else 0.0,
        "mean_confidence": round(statistics.mean(confs), 4) if confs else 1.0,
        "dom_hit_rate_pct": round((sum(1 for h in hits if h) / len(hits)) * 100.0, 1) if hits else 100.0,
    }
