from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence


def write_inference_markdown(payload: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_inference_markdown(payload), encoding="utf-8")
    return output_path


def build_inference_markdown(payload: dict[str, Any]) -> str:
    results = payload.get("results", [])
    lines = [
        "# TTPXHunter Inference Report",
        "",
        "## Run Configuration",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Report | `{payload.get('report', '-')}` |",
        f"| Model | `{payload.get('model_id', '-')}` |",
        f"| Revision | `{_display_revision(payload.get('revision'))}` |",
        f"| Threshold | {payload.get('threshold', '-')} |",
        f"| Order | `{payload.get('order', '-')}` |",
        f"| Preprocess | `{payload.get('preprocess', 'none')}` |",
        f"| Section filter | `{payload.get('section_filter', 'none')}` |",
        f"| Top-k | {_display_none(payload.get('top_k'))} |",
        f"| Extracted TTP count | {payload.get('count', len(results))} |",
        "",
    ]

    comparison = payload.get("comparison")
    if comparison:
        agreement = _agreement_metrics(comparison)
        lines.extend(
            [
                "## Notebook Agreement",
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Actual count | {comparison['actual_count']} |",
                f"| Notebook expected count | {comparison['expected_count']} |",
                f"| Set match | {_bool_text(comparison['set_match'])} |",
                f"| Order match | {_bool_text(comparison['order_match'])} |",
                f"| Agreement precision | {agreement['precision']:.6f} |",
                f"| Agreement recall | {agreement['recall']:.6f} |",
                f"| Agreement F1 | {agreement['f1']:.6f} |",
                "",
                "Agreement metrics compare this run with the saved notebook output. They are reproduction metrics, not independent model accuracy.",
                "",
                "### Differences",
                "",
                "| Type | Values |",
                "| --- | --- |",
                f"| Missing vs notebook | {_join_code(comparison.get('missing', []))} |",
                f"| Extra vs notebook | {_join_code(comparison.get('extra', []))} |",
                "",
            ]
        )

    lines.extend(
        [
            "## Extracted Techniques",
            "",
            _results_table(results),
            "",
        ]
    )
    return "\n".join(lines)


def _agreement_metrics(comparison: dict[str, Any]) -> dict[str, float]:
    missing = len(comparison.get("missing", []))
    extra = len(comparison.get("extra", []))
    actual_count = int(comparison.get("actual_count", 0))
    expected_count = int(comparison.get("expected_count", 0))
    tp = max(0, expected_count - missing)
    precision = _safe_ratio(tp, actual_count)
    recall = _safe_ratio(tp, expected_count)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1, "extra": float(extra)}


def _results_table(results: Sequence[dict[str, Any]]) -> str:
    lines = ["| Rank | Technique | Name |", "| ---: | --- | --- |"]
    if not results:
        lines.append("| - | - | - |")
        return "\n".join(lines)
    for rank, item in enumerate(results, start=1):
        lines.append(f"| {rank} | `{item['ttp_id']}` | {item['name']} |")
    return "\n".join(lines)


def _join_code(values: Sequence[Any]) -> str:
    if not values:
        return "-"
    return ", ".join(f"`{value}`" for value in values)


def _bool_text(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _display_revision(value: Any) -> str:
    if value is None:
        return "not pinned"
    return str(value)


def _display_none(value: Any) -> str:
    if value is None:
        return "none"
    return str(value)


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
