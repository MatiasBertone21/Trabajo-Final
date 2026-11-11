"""
Reusable Pillow chart builders for CI statistical and historical dashboards.
Generates crisp Base64-encoded PNG charts with zero external JS dependencies.
"""
import statistics
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from .constants import (
    FRONTENDS,
    FULL_FLOW_STEPS,
    LAYER_COLORS,
    STRATEGIES,
    STRATEGY_COLORS,
)
from .telemetry_io import img_to_base64


def _load_font(size: int = 12, bold: bool = False) -> Any:
    """Load a TrueType font supporting UTF-8 accents (Windows/Linux), falling back to Pillow default."""
    candidates = (
        [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_y_grid_and_axes(
    draw: ImageDraw.ImageDraw,
    font: Any,
    left: int,
    right: int,
    top: int,
    plot_h: int,
    width: int,
    max_val: float,
    steps: int = 5,
) -> None:
    """Draw horizontal reference grid lines, Y-axis tick labels, and X/Y axes."""
    for i in range(steps + 1):
        y = top + plot_h - int((i / steps) * plot_h)
        v = (i / steps) * max_val
        draw.line([(left, y), (width - right, y)], fill=(226, 232, 240), width=1)
        draw.text((14, y - 7), f"{v:.0f}", fill=(100, 116, 139), font=font)

    draw.line([(left, top), (left, top + plot_h)], fill=(148, 163, 184), width=2)
    draw.line([(left, top + plot_h), (width - right, top + plot_h)], fill=(148, 163, 184), width=2)


def draw_scenario_bars_chart(
    title: str,
    subtitle: Optional[str],
    strategies_subset: List[str],
    summary_by_cell: Dict[Tuple[str, str], Dict[str, Any]],
    metric_key: str = "total_median_ms",
    p95_key: Optional[str] = "total_p95_ms",
    show_overhead_ratio: bool = False,
) -> str:
    """
    Render a grouped vertical bar chart (Frontends on X-axis, `strategies_subset` as bars)
    with optional P95 whisker caps and DOM-vs-Vision overhead ratio annotations.
    """
    W, H = 880, 425 if subtitle else 405
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = _load_font(13, bold=True)
    font_sub = _load_font(11, bold=False)
    font = _load_font(11, bold=False)
    font_bold = _load_font(11, bold=True)

    left, right = 78, 40
    top = 80 if subtitle else 64
    bottom = 65
    plot_w = W - left - right
    plot_h = H - top - bottom

    draw.text((left, 12), title, fill=(15, 23, 42), font=font_title)
    if subtitle:
        draw.text((left, 31), subtitle, fill=(100, 116, 139), font=font_sub)

    # Dedicated legend row below subtitle so it never collides with long titles
    legend_y = 52 if subtitle else 38
    lx = left
    for s in strategies_subset:
        c = STRATEGY_COLORS[s]
        draw.rectangle([lx, legend_y, lx + 12, legend_y + 12], fill=c)
        draw.text((lx + 16, legend_y - 1), s.upper(), fill=(30, 41, 59), font=font_bold)
        lx += 120

    draw.text((14, top - 18), "ms", fill=(100, 116, 139), font=font)

    vals = [
        float(summary_by_cell.get((s, f), {}).get(p95_key or metric_key, 0.0))
        for s in strategies_subset
        for f in FRONTENDS
    ] + [
        float(summary_by_cell.get((s, f), {}).get(metric_key, 0.0))
        for s in strategies_subset
        for f in FRONTENDS
    ]
    max_val = max(vals + [10.0]) * (1.22 if p95_key else 1.18)

    _draw_y_grid_and_axes(draw, font, left, right, top, plot_h, W, max_val)

    group_w = plot_w / len(FRONTENDS)
    bar_w = 54 if len(strategies_subset) <= 3 else 34
    gap = 14 if len(strategies_subset) <= 3 else 8

    for f_idx, fe in enumerate(FRONTENDS):
        group_center = left + (f_idx + 0.5) * group_w
        total_bars_w = len(strategies_subset) * bar_w + (len(strategies_subset) - 1) * gap
        start_x = group_center - total_bars_w / 2

        for s_idx, strat in enumerate(strategies_subset):
            cell = summary_by_cell.get((strat, fe), {})
            val = float(cell.get(metric_key, 0.0))
            p95_val = float(cell.get(p95_key, val)) if p95_key else val

            bh = int((val / max_val) * plot_h) if max_val > 0 else 0
            x0 = int(start_x + s_idx * (bar_w + gap))
            y0 = top + plot_h - bh
            x1 = x0 + bar_w
            y1 = top + plot_h

            color = STRATEGY_COLORS[strat]
            draw.rectangle([x0, y0, x1, y1], fill=color, outline=(30, 41, 59))

            if p95_key and p95_val > val * 1.03 and max_val > 0:
                yp95 = top + plot_h - int((p95_val / max_val) * plot_h)
                cx = (x0 + x1) // 2
                draw.line([(cx, yp95), (cx, y0)], fill=(15, 23, 42), width=2)
                draw.line([(cx - 6, yp95), (cx + 6, yp95)], fill=(15, 23, 42), width=2)

            if val > 0:
                label_y = max(top + 2, y0 - 15)
                draw.text((x0 + 4, label_y), f"{val:.0f}", fill=(15, 23, 42), font=font)

        if show_overhead_ratio and len(strategies_subset) == 2:
            v_dom = float(summary_by_cell.get((strategies_subset[0], fe), {}).get(metric_key, 0.0))
            v_vis = float(summary_by_cell.get((strategies_subset[1], fe), {}).get(metric_key, 0.0))
            if v_dom > 0 and v_vis > 0:
                ratio = v_vis / v_dom
                draw.text(
                    (int(group_center - 42), top + plot_h + 32),
                    f"Overhead: {ratio:.1f}x",
                    fill=(190, 18, 60),
                    font=font_bold,
                )

        draw.text((int(group_center - 24), top + plot_h + 14), fe.upper(), fill=(15, 23, 42), font=font_bold)

    return img_to_base64(img)


def draw_step_profile_chart(all_steps: List[Dict[str, Any]]) -> str:
    """
    Chart 3: Step-by-step latency profile across the 7 sub-steps of the Full E2E flow,
    contrasting `getby_full` (DOM) vs `opencv_full` (highlighting OCR=False vs OCR=True).
    """
    W, H = 880, 430
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = _load_font(13, bold=True)
    font_sub = _load_font(11, bold=False)
    font = _load_font(11, bold=False)
    font_bold = _load_font(11, bold=True)

    left, right, top, bottom = 78, 40, 80, 75
    plot_w = W - left - right
    plot_h = H - top - bottom

    draw.text(
        (left, 12),
        "Gráfico 3: Perfil de Latencia Paso a Paso (getby_full vs opencv_full) y Selección Adaptativa de OCR",
        fill=(15, 23, 42),
        font=font_title,
    )
    draw.text(
        (left, 31),
        "Mediana por paso en los 3 frontends (ms) — Azul: Vision OCR=False (TM_CCOEFF_NORMED) | Rojo: Vision OCR=True (EasyOCR)",
        fill=(100, 116, 139),
        font=font_sub,
    )

    legend_items = [
        ("GETBY_FULL (DOM)", (13, 148, 136)),
        ("OPENCV_FULL (OCR=False)", (37, 99, 235)),
        ("OPENCV_FULL (OCR=True)", (225, 29, 72)),
    ]
    lx = left
    for lname, lcol in legend_items:
        draw.rectangle([lx, 52, lx + 12, 64], fill=lcol)
        draw.text((lx + 16, 51), lname, fill=(30, 41, 59), font=font_bold)
        lx += 225

    step_stats: List[Tuple[str, float, float, bool]] = []
    for step_id, short_label in FULL_FLOW_STEPS:
        dom_vals = [
            float(r.get("total_step_ms", 0.0))
            for r in all_steps
            if r.get("strategy") == "getby_full" and r.get("step_name") == step_id
        ]
        vis_recs = [
            r for r in all_steps
            if r.get("strategy") == "opencv_full" and r.get("step_name") == step_id
        ]
        vis_vals = [float(r.get("total_step_ms", 0.0)) for r in vis_recs]
        uses_ocr = any(bool(r.get("enable_ocr")) and float(r.get("server_ocr_ms", 0.0)) > 0 for r in vis_recs)
        d_med = statistics.median(dom_vals) if dom_vals else 0.0
        v_med = statistics.median(vis_vals) if vis_vals else 0.0
        step_stats.append((short_label, d_med, v_med, uses_ocr))

    max_val = max([max(d, v) for _, d, v, _ in step_stats] + [10.0]) * 1.22
    _draw_y_grid_and_axes(draw, font, left, right, top, plot_h, W, max_val)

    group_w = plot_w / len(FULL_FLOW_STEPS)
    bar_w = 28
    gap = 6

    for idx, (short_label, d_med, v_med, uses_ocr) in enumerate(step_stats):
        g_center = left + (idx + 0.5) * group_w
        x_dom = int(g_center - bar_w - gap // 2)
        x_vis = int(g_center + gap // 2)

        bh_d = int((d_med / max_val) * plot_h) if max_val > 0 else 0
        y0_d = top + plot_h - bh_d
        draw.rectangle([x_dom, y0_d, x_dom + bar_w, top + plot_h], fill=(13, 148, 136), outline=(30, 41, 59))
        if d_med > 0:
            draw.text((x_dom, max(top + 2, y0_d - 14)), f"{d_med:.0f}", fill=(13, 148, 136), font=font)

        v_col = (225, 29, 72) if uses_ocr else (37, 99, 235)
        bh_v = int((v_med / max_val) * plot_h) if max_val > 0 else 0
        y0_v = top + plot_h - bh_v
        draw.rectangle([x_vis, y0_v, x_vis + bar_w, top + plot_h], fill=v_col, outline=(30, 41, 59))
        if v_med > 0:
            draw.text((x_vis, max(top + 2, y0_v - 14)), f"{v_med:.0f}", fill=v_col, font=font)

        ocr_tag = "OCR=On" if uses_ocr else "OCR=Off"
        draw.text((int(g_center - 44), top + plot_h + 12), short_label, fill=(15, 23, 42), font=font)
        draw.text((int(g_center - 24), top + plot_h + 28), f"[{ocr_tag}]", fill=v_col, font=font_bold)

    return img_to_base64(img)


def draw_stacked_layers_chart(
    summary_by_cell: Dict[Tuple[str, str], Dict[str, Any]],
    title: str = "Gráfico 4: Desglose Apilado de Latencia por Capa del Pipeline de Percepción v1 (ms acumulados por corrida)",
) -> str:
    """Stacked horizontal bar chart breaking down action step latency by perception layer (v1)."""
    rows: List[Tuple[str, Dict[str, float]]] = []
    for fe in FRONTENDS:
        for strat in STRATEGIES:
            cell = summary_by_cell.get((strat, fe))
            if not cell or cell.get("runs", 0) == 0:
                continue
            label = f"{strat.upper()} @ {fe.capitalize()}"
            if strat in ("base", "getby", "getby_full"):
                parts = {
                    "DOM (CSS / get_by)": float(cell.get("step_median_ms", 0.0)),
                    "Viewport Capture": 0.0,
                    "Network + Decode": 0.0,
                    "Template Matching (TM_CCOEFF_NORMED)": 0.0,
                    "EasyOCR + Ranking": 0.0,
                }
            else:
                parts = {
                    "DOM (CSS / get_by)": 0.0,
                    "Viewport Capture": float(cell.get("capture_ms", 0.0)),
                    "Network + Decode": float(cell.get("network_ms", 0.0)) + float(cell.get("decode_preprocess_ms", 0.0)),
                    "Template Matching (TM_CCOEFF_NORMED)": float(cell.get("template_ms", 0.0)),
                    "EasyOCR + Ranking": float(cell.get("ocr_ranking_ms", 0.0)),
                }
            rows.append((label, parts))

    W = 880
    row_h = 34
    top, bottom, left, right = 86, 40, 185, 95
    H = max(240, top + bottom + len(rows) * row_h)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = _load_font(13, bold=True)
    font = _load_font(11, bold=False)
    font_bold = _load_font(11, bold=True)

    draw.text((20, 12), title, fill=(15, 23, 42), font=font_title)

    lx = 20
    ly = 38
    for lname, lcol in LAYER_COLORS.items():
        if lx > W - 240:
            lx = 20
            ly += 20
        draw.rectangle([lx, ly, lx + 12, ly + 12], fill=lcol)
        draw.text((lx + 16, ly - 1), lname, fill=(51, 65, 85), font=font)
        lx += 245 if "TM_CCOEFF" in lname else 155

    plot_w = W - left - right
    totals = [sum(p.values()) for _, p in rows]
    max_total = max(totals + [10.0]) * 1.15

    for idx, (label, parts) in enumerate(rows):
        y_center = top + idx * row_h + row_h // 2
        y0 = y_center - 10
        y1 = y_center + 10
        draw.text((18, y_center - 7), label, fill=(15, 23, 42), font=font_bold)

        cur_x = left
        for lname, lcol in LAYER_COLORS.items():
            val = parts.get(lname, 0.0)
            if val <= 0:
                continue
            seg_w = max(2, int((val / max_total) * plot_w))
            draw.rectangle([cur_x, y0, cur_x + seg_w, y1], fill=lcol)
            cur_x += seg_w

        total_ms = sum(parts.values())
        draw.text((cur_x + 8, y_center - 7), f"{total_ms:.1f} ms", fill=(15, 23, 42), font=font)

    return img_to_base64(img)


def draw_historical_trend_chart(csv_history: List[Dict[str, Any]]) -> str:
    """Chart 5: Multi-series trend chart of E2E latency across recent builds in `metrics-history/history.csv`."""
    W, H = 880, 400
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = _load_font(13, bold=True)
    font_sub = _load_font(11, bold=False)
    font = _load_font(11, bold=False)
    font_bold = _load_font(11, bold=True)

    left, right, top, bottom = 78, 40, 82, 60
    plot_w = W - left - right
    plot_h = H - top - bottom

    draw.text(
        (left, 12),
        "Gráfico 5: Evolución Histórica del Tiempo Total E2E a través de los Últimos Builds (Mediana en ms)",
        fill=(15, 23, 42),
        font=font_title,
    )
    draw.text(
        (left, 31),
        "Promedio de los 3 frontends por cada Build registrado en metrics-history/history.csv",
        fill=(100, 116, 139),
        font=font_sub,
    )

    # Dedicated row for strategy legend (y=52) so it never overlaps the title
    lx = left
    for s in STRATEGIES:
        c = STRATEGY_COLORS[s]
        draw.rectangle([lx, 52, lx + 12, 64], fill=c)
        draw.text((lx + 16, 51), s.upper(), fill=(30, 41, 59), font=font_bold)
        lx += 130

    builds_order: List[str] = []
    by_build_strat: Dict[Tuple[str, str], List[float]] = {}
    for r in csv_history:
        b = str(r.get("build_number") or r.get("\ufeffbuild_number") or "local").strip()
        if b == "local":
            continue
        s = str(r.get("strategy", "")).strip()
        if s not in STRATEGIES:
            continue
        try:
            val = float(r.get("total_median_ms", 0.0))
        except ValueError:
            continue
        if val <= 0:
            continue
        if b not in builds_order:
            builds_order.append(b)
        by_build_strat.setdefault((b, s), []).append(val)

    builds_order = builds_order[-10:]
    all_vals = [statistics.mean(v) for (b, _), v in by_build_strat.items() if b in builds_order and v]
    max_val = max(all_vals + [100.0]) * 1.18

    _draw_y_grid_and_axes(draw, font, left, right, top, plot_h, W, max_val)

    if not builds_order:
        draw.text((left + 40, top + plot_h // 2), "Sin historial suficiente aún.", fill=(100, 116, 139), font=font)
        return img_to_base64(img)

    n_b = len(builds_order)
    x_positions = [
        left + int((idx / max(1, n_b - 1)) * (plot_w - 40)) + 20 if n_b > 1 else left + plot_w // 2
        for idx in range(n_b)
    ]

    for idx, b in enumerate(builds_order):
        draw.text((x_positions[idx] - 14, top + plot_h + 14), f"#{b}", fill=(15, 23, 42), font=font_bold)

    for strat in STRATEGIES:
        pts: List[Tuple[int, int]] = []
        color = STRATEGY_COLORS[strat]
        for idx, b in enumerate(builds_order):
            vals = by_build_strat.get((b, strat))
            if not vals:
                continue
            avg_v = statistics.mean(vals)
            px = x_positions[idx]
            py = top + plot_h - int((avg_v / max_val) * plot_h)
            pts.append((px, py))

        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=color, width=3)
        for px, py in pts:
            draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=color, outline=(255, 255, 255))

    return img_to_base64(img)
