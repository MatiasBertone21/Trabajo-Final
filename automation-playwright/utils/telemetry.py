"""
Lightweight JSONL telemetry collector for test-level and step-level benchmarks.
Stores records in memory during a test run and flushes to disk at session end.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PLAYWRIGHT_ROOT = Path(__file__).resolve().parent.parent


class TelemetryCollector:
    def __init__(self) -> None:
        self.run_id: str = os.getenv("TELEMETRY_RUN_ID") or datetime.now().strftime("%Y%m%d-%H%M%S")
        self.build_number: str = os.getenv("BUILD_NUMBER", "local")
        self.strategy: str = "unknown"
        self.frontend: str = "react"
        self.mutation: str = os.getenv("MUTATION_ID", "M0_CONTROL")
        self.repeat_idx: int = int(os.getenv("REPEAT_IDX", "1"))
        self.telemetry_dir: Optional[Path] = None

        self.test_records: List[Dict[str, Any]] = []
        self.step_records: List[Dict[str, Any]] = []
        self._phase_durations: Dict[str, Dict[str, float]] = {}

    def configure(
        self,
        strategy: str,
        frontend: str,
        mutation: Optional[str] = None,
        repeat_idx: Optional[int] = None,
        telemetry_dir: Optional[str] = None,
    ) -> None:
        self.strategy = strategy or self.strategy
        self.frontend = frontend or self.frontend
        if mutation:
            self.mutation = mutation
        if repeat_idx is not None:
            self.repeat_idx = repeat_idx
        if telemetry_dir:
            self.telemetry_dir = Path(telemetry_dir)
        else:
            self.telemetry_dir = PLAYWRIGHT_ROOT / "reports" / self.strategy / self.frontend

    def record_phase(self, nodeid: str, when: str, duration_s: float) -> None:
        phases = self._phase_durations.setdefault(
            nodeid, {"setup_ms": 0.0, "call_ms": 0.0, "teardown_ms": 0.0}
        )
        key = f"{when}_ms"
        if key in phases:
            phases[key] = round(duration_s * 1000.0, 2)

    def finalize_test(
        self,
        nodeid: str,
        test_name: str,
        strategy: str,
        frontend: str,
        outcome: str,
    ) -> Dict[str, Any]:
        phases = self._phase_durations.get(
            nodeid, {"setup_ms": 0.0, "call_ms": 0.0, "teardown_ms": 0.0}
        )
        total_ms = round(
            phases["setup_ms"] + phases["call_ms"] + phases["teardown_ms"], 2
        )
        # Aggregate step metrics recorded for this test
        matching_steps = [
            s for s in self.step_records
            if s.get("strategy") == strategy
            and s.get("frontend") == frontend
            and s.get("repeat_idx") == self.repeat_idx
        ]
        if not matching_steps:
            matching_steps = [
                s for s in self.step_records
                if s.get("strategy") == strategy and s.get("frontend") == frontend
            ]
        total_action_ms = sum(float(s.get("total_step_ms", 0.0)) for s in matching_steps)
        conf_vals = [float(s["confidence_score"]) for s in matching_steps if s.get("confidence_score") is not None]
        avg_confidence = round(sum(conf_vals) / len(conf_vals), 4) if conf_vals else None
        vision_calls = [s for s in matching_steps if str(s.get("layer_resolved", "")).startswith("vision")]
        screenshots_captured = sum(1 for s in vision_calls if not s.get("reused_screenshot", False))
        calls_template_only = sum(1 for s in vision_calls if s.get("enable_ocr") is False)
        calls_with_ocr = sum(1 for s in vision_calls if s.get("enable_ocr") is True)
        visual_assertions = sum(int(s.get("visual_assertions_count", 0)) for s in matching_steps)

        record = {
            "run_id": self.run_id,
            "build_number": self.build_number,
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "frontend": frontend,
            "mutation": self.mutation,
            "repeat_idx": self.repeat_idx,
            "test_id": nodeid,
            "test_name": test_name,
            "outcome": outcome,
            "setup_ms": phases["setup_ms"],
            "call_ms": phases["call_ms"],
            "teardown_ms": phases["teardown_ms"],
            "total_ms": total_ms,
            "action_step_ms": round(total_action_ms, 2),
            "confidence_score": avg_confidence,
            "steps_count": len(matching_steps),
            "vision_api_calls_count": len(vision_calls),
            "screenshots_captured_count": screenshots_captured,
            "calls_template_only": calls_template_only,
            "calls_with_ocr": calls_with_ocr,
            "visual_assertions_count": visual_assertions,
        }
        self.test_records.append(record)
        return record

    def record_step(
        self,
        step_name: str,
        strategy: str,
        frontend: str,
        layer_resolved: str,
        total_step_ms: float,
        capture_ms: float = 0.0,
        network_ms: float = 0.0,
        server_timings_ms: Optional[Dict[str, float]] = None,
        candidates_count: int = 1,
        confidence_score: Optional[float] = None,
        center_point: Optional[Dict[str, int]] = None,
        dom_ground_truth_hit: Optional[bool] = None,
        success: bool = True,
        enable_ocr: Optional[bool] = None,
        reused_screenshot: bool = False,
        visual_assertions_count: int = 0,
        audit_image: Optional[str] = None,
    ) -> Dict[str, Any]:
        srv = server_timings_ms or {}
        if enable_ocr is None and layer_resolved.startswith("vision"):
            enable_ocr = "ocr" in layer_resolved
        record = {
            "run_id": self.run_id,
            "build_number": self.build_number,
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "frontend": frontend,
            "mutation": self.mutation,
            "repeat_idx": self.repeat_idx,
            "step_name": step_name,
            "layer_resolved": layer_resolved,
            "enable_ocr": enable_ocr,
            "reused_screenshot": reused_screenshot,
            "visual_assertions_count": visual_assertions_count,
            "audit_image": audit_image,
            "total_step_ms": round(total_step_ms, 2),
            "capture_ms": round(capture_ms, 2),
            "network_ms": round(network_ms, 2),
            "server_decode_ms": round(float(srv.get("decode_ms", 0.0)), 2),
            "server_preprocess_ms": round(float(srv.get("preprocess_ms", 0.0)), 2),
            "server_template_ms": round(float(srv.get("template_ms", 0.0)), 2),
            "server_contour_ms": round(float(srv.get("contour_ms", 0.0)), 2),
            "server_ocr_ms": round(float(srv.get("ocr_ms", 0.0)), 2),
            "server_ranking_ms": round(float(srv.get("ranking_ms", 0.0)), 2),
            "server_total_ms": round(float(srv.get("total_server_ms", 0.0)), 2),
            "candidates_count": candidates_count,
            "confidence_score": round(float(confidence_score), 4) if confidence_score is not None else None,
            "center_point": center_point,
            "dom_ground_truth_hit": dom_ground_truth_hit,
            "success": success,
        }
        self.step_records.append(record)
        return record

    def flush(self, target_dir: Optional[Path] = None) -> None:
        out_dir = target_dir or self.telemetry_dir
        if out_dir is None:
            out_dir = PLAYWRIGHT_ROOT / "reports" / self.strategy / self.frontend
        out_dir.mkdir(parents=True, exist_ok=True)

        if self.test_records:
            tests_file = out_dir / "telemetry_tests.jsonl"
            with open(tests_file, "a", encoding="utf-8") as f:
                for rec in self.test_records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        if self.step_records:
            steps_file = out_dir / "telemetry_steps.jsonl"
            with open(steps_file, "a", encoding="utf-8") as f:
                for rec in self.step_records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")


telemetry = TelemetryCollector()

