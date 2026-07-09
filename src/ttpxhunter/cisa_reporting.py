from __future__ import annotations

import csv
import html
import math
import os
from collections import Counter
from copy import deepcopy
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Sequence


def enhance_benchmark_payload(payload: dict[str, Any], top_n: int = 15) -> dict[str, Any]:
    payload["insights"] = build_benchmark_insights(payload, top_n=top_n)
    return payload


def build_benchmark_insights(payload: dict[str, Any], top_n: int = 15) -> dict[str, Any]:
    rows = payload.get("rows", [])
    names = payload.get("technique_names", {})

    expected_counts = [int(row["expected_count"]) for row in rows]
    predicted_counts = [int(row["predicted_count"]) for row in rows]
    sentence_counts = [int(row["sentence_count"]) for row in rows]

    return {
        "article_quality": {
            "exact_match_articles": sum(
                1 for row in rows if not row["missing"] and not row["extra"]
            ),
            "articles_with_no_expected": sum(1 for count in expected_counts if count == 0),
            "articles_with_no_predictions": sum(1 for count in predicted_counts if count == 0),
            "mean_expected_per_article": _round(_mean(expected_counts)),
            "median_expected_per_article": _round(_median(expected_counts)),
            "mean_predicted_per_article": _round(_mean(predicted_counts)),
            "median_predicted_per_article": _round(_median(predicted_counts)),
            "mean_sentences_per_article": _round(_mean(sentence_counts)),
            "median_sentences_per_article": _round(_median(sentence_counts)),
        },
        "top_missing": _top_terms(rows, "missing", names, top_n=top_n),
        "top_extra": _top_terms(rows, "extra", names, top_n=top_n),
        "top_matches": _top_terms(rows, "matches", names, top_n=top_n),
        "best_articles": _article_summaries(
            sorted(
                rows,
                key=lambda row: (
                    float(row["metrics"]["f1"]),
                    float(row["metrics"]["recall"]),
                    int(row["metrics"]["tp"]),
                ),
                reverse=True,
            )[:top_n]
        ),
        "worst_articles": _article_summaries(
            sorted(
                [row for row in rows if int(row["expected_count"]) > 0],
                key=lambda row: (
                    float(row["metrics"]["f1"]),
                    float(row["metrics"]["recall"]),
                    -int(row["metrics"]["fn"]),
                ),
            )[:top_n]
        ),
    }


def write_benchmark_rows_csv(payload: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "index",
        "url",
        "sentence_count",
        "raw_attack_id_count",
        "expected_count",
        "predicted_count",
        "tp",
        "fp",
        "fn",
        "precision",
        "recall",
        "f1",
        "matches",
        "missing",
        "extra",
        "expected",
        "predicted_ids",
        "predicted_names",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload.get("rows", []):
            predicted_ids = [item["ttp_id"] for item in row["predicted"]]
            predicted_names = [item["name"] for item in row["predicted"]]
            writer.writerow(
                {
                    "index": row["index"],
                    "url": row["url"],
                    "sentence_count": row["sentence_count"],
                    "raw_attack_id_count": row["raw_attack_id_count"],
                    "expected_count": row["expected_count"],
                    "predicted_count": row["predicted_count"],
                    "tp": row["metrics"]["tp"],
                    "fp": row["metrics"]["fp"],
                    "fn": row["metrics"]["fn"],
                    "precision": row["metrics"]["precision"],
                    "recall": row["metrics"]["recall"],
                    "f1": row["metrics"]["f1"],
                    "matches": _join(row["matches"]),
                    "missing": _join(row["missing"]),
                    "extra": _join(row["extra"]),
                    "expected": _join(row["expected"]),
                    "predicted_ids": _join(predicted_ids),
                    "predicted_names": _join(predicted_names),
                }
            )
    return output_path


<<<<<<< HEAD
=======
def write_sweep_rows_csv(payload: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "threshold",
        "top_k",
        "article_count",
        "expected_count",
        "predicted_count",
        "tp",
        "fp",
        "fn",
        "micro_precision",
        "micro_recall",
        "micro_f1",
        "label_macro_f1",
        "hamming_loss",
        "fp_rate",
        "fn_rate",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload.get("sweep_rows", []):
            writer.writerow(row)
    return output_path


>>>>>>> feat/demo
def write_benchmark_markdown(payload: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_payload = _payload_with_markdown_relative_paths(payload, output_path.parent)
    output_path.write_text(build_benchmark_markdown(render_payload), encoding="utf-8")
    return output_path


<<<<<<< HEAD
=======
def write_sweep_markdown(payload: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_sweep_markdown(payload), encoding="utf-8")
    return output_path


def write_comparison_markdown(
    title: str,
    items: Sequence[dict[str, Any]],
    path: str | Path,
    artifacts: dict[str, str] | None = None,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_comparison_markdown(title, items, artifacts=artifacts),
        encoding="utf-8",
    )
    return output_path


def write_comparison_charts(
    items: Sequence[dict[str, Any]],
    charts_dir: str | Path,
) -> dict[str, Path]:
    output_dir = Path(charts_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    charts = {
        "chart_micro_metrics": output_dir / "comparison_micro_metrics.svg",
        "chart_error_counts": output_dir / "comparison_error_counts.svg",
        "chart_hamming_loss": output_dir / "comparison_hamming_loss.svg",
        "chart_label_volume": output_dir / "comparison_label_volume.svg",
    }
    charts["chart_micro_metrics"].write_text(
        _comparison_micro_metrics_svg(items),
        encoding="utf-8",
    )
    charts["chart_error_counts"].write_text(
        _comparison_error_counts_svg(items),
        encoding="utf-8",
    )
    charts["chart_hamming_loss"].write_text(
        _comparison_hamming_loss_svg(items),
        encoding="utf-8",
    )
    charts["chart_label_volume"].write_text(
        _comparison_label_volume_svg(items),
        encoding="utf-8",
    )
    return charts


>>>>>>> feat/demo
def write_benchmark_charts(payload: dict[str, Any], charts_dir: str | Path) -> dict[str, Path]:
    output_dir = Path(charts_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    charts = {
        "chart_metrics": output_dir / "metrics_overview.svg",
        "chart_confusion": output_dir / "confusion_counts.svg",
        "chart_top_missing": output_dir / "top_missing.svg",
        "chart_top_extra": output_dir / "top_extra.svg",
        "chart_f1_distribution": output_dir / "article_f1_distribution.svg",
    }
    charts["chart_metrics"].write_text(_metrics_svg(payload), encoding="utf-8")
    charts["chart_confusion"].write_text(_confusion_svg(payload), encoding="utf-8")
    charts["chart_top_missing"].write_text(
        _terms_bar_svg("Most Missed Expected Techniques", payload["insights"]["top_missing"]),
        encoding="utf-8",
    )
    charts["chart_top_extra"].write_text(
        _terms_bar_svg("Most Frequent Extra Predictions", payload["insights"]["top_extra"]),
        encoding="utf-8",
    )
    charts["chart_f1_distribution"].write_text(_f1_distribution_svg(payload), encoding="utf-8")
    return charts


def build_benchmark_markdown(payload: dict[str, Any]) -> str:
    if "insights" not in payload:
        payload = enhance_benchmark_payload(payload)

    dataset = payload["dataset"]
    model = payload["model"]
    aggregate = payload["aggregate"]
    micro = aggregate["micro"]
<<<<<<< HEAD
    macro = aggregate["macro"]
=======
    article_macro = aggregate.get("article_macro", aggregate["macro"])
    label_macro = aggregate.get("label_macro", {})
>>>>>>> feat/demo
    insights = payload["insights"]
    quality = insights["article_quality"]

    lines = [
        "# CISA TTPXHunter Benchmark Report",
        "",
        "## Run Configuration",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Dataset | `{dataset['path']}` |",
        f"| Zenodo record | `{dataset['record_id']}` |",
        f"| DOI | `{dataset['doi']}` |",
        f"| Articles evaluated | {dataset['evaluated_articles']} / {dataset['total_articles']} |",
        f"| Text field | `{dataset['text_field']}` |",
        f"| Expected mode | `{dataset['expected_mode']}` |",
<<<<<<< HEAD
        f"| Model | `{model['model_id']}` |",
        f"| Revision | `{_display(model['revision'])}` |",
        f"| Threshold | {model['threshold']} |",
=======
        f"| Preprocess | `{dataset.get('preprocess', 'none')}` |",
        f"| Section filter | `{dataset.get('section_filter', 'none')}` |",
        f"| Model | `{model['model_id']}` |",
        f"| Revision | `{_display(model['revision'])}` |",
        f"| Threshold | {model['threshold']} |",
        f"| Top-k | {_display_none(model.get('top_k'))} |",
>>>>>>> feat/demo
        f"| Device | `{model['device']}` |",
        f"| Batch size | {model['batch_size']} |",
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Expected labels | {aggregate['expected_count']} |",
        f"| Predicted labels | {aggregate['predicted_count']} |",
        f"| True positives | {aggregate['tp']} |",
        f"| False positives | {aggregate['fp']} |",
        f"| False negatives | {aggregate['fn']} |",
        f"| Micro precision | {micro['precision']:.6f} |",
        f"| Micro recall | {micro['recall']:.6f} |",
        f"| Micro F1 | {micro['f1']:.6f} |",
<<<<<<< HEAD
        f"| Macro precision | {macro['precision']:.6f} |",
        f"| Macro recall | {macro['recall']:.6f} |",
        f"| Macro F1 | {macro['f1']:.6f} |",
=======
        f"| Article macro precision | {article_macro['precision']:.6f} |",
        f"| Article macro recall | {article_macro['recall']:.6f} |",
        f"| Article macro F1 | {article_macro['f1']:.6f} |",
        f"| Label macro precision | {label_macro.get('precision', 0.0):.6f} |",
        f"| Label macro recall | {label_macro.get('recall', 0.0):.6f} |",
        f"| Label macro F1 | {label_macro.get('f1', 0.0):.6f} |",
        f"| Hamming loss | {aggregate.get('hamming_loss', 0.0):.6f} |",
>>>>>>> feat/demo
        "",
        "## Charts",
        "",
        _charts_markdown(payload.get("artifacts", {})),
        "",
        "## Article Quality",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Exact-match articles | {quality['exact_match_articles']} |",
        f"| Articles with no expected labels | {quality['articles_with_no_expected']} |",
        f"| Articles with no predictions | {quality['articles_with_no_predictions']} |",
        f"| Mean expected labels/article | {quality['mean_expected_per_article']:.3f} |",
        f"| Median expected labels/article | {quality['median_expected_per_article']:.3f} |",
        f"| Mean predicted labels/article | {quality['mean_predicted_per_article']:.3f} |",
        f"| Median predicted labels/article | {quality['median_predicted_per_article']:.3f} |",
        f"| Mean sentences/article | {quality['mean_sentences_per_article']:.3f} |",
        f"| Median sentences/article | {quality['median_sentences_per_article']:.3f} |",
        "",
        "## Top Gaps",
        "",
        "### Most Missed Expected Techniques",
        "",
        _terms_table(insights["top_missing"]),
        "",
        "### Most Frequent Extra Predictions",
        "",
        _terms_table(insights["top_extra"]),
        "",
        "### Most Frequent Matches",
        "",
        _terms_table(insights["top_matches"]),
        "",
        "## Article-Level Extremes",
        "",
        "### Best Articles",
        "",
        _articles_table(insights["best_articles"]),
        "",
        "### Worst Articles",
        "",
        _articles_table(insights["worst_articles"]),
        "",
        "## Output Artifacts",
        "",
        _artifacts_table(payload.get("artifacts", {})),
        "",
        "## Interpretation Notes",
        "",
        "- The default benchmark compares base MITRE ATT&CK techniques only.",
        "- CISA tactics are dropped, sub-techniques are collapsed to parent techniques, and invalid regex matches are ignored.",
        "- `expected_mode=model-label-space` filters expected labels to techniques the TTPXHunter classifier can emit.",
        "- High false positives indicate the threshold may need tuning for CISA advisories, which are longer and more operational than the SharpPanda sample.",
        "",
    ]
    return "\n".join(lines)


<<<<<<< HEAD
=======
def build_sweep_markdown(payload: dict[str, Any]) -> str:
    dataset = payload["dataset"]
    model = payload["model"]
    rows = sorted(
        payload.get("sweep_rows", []),
        key=lambda row: (
            float(row["micro_f1"]),
            float(row["micro_precision"]),
            -float(row["hamming_loss"]),
        ),
        reverse=True,
    )
    lines = [
        "# CISA Threshold / Top-k Sweep",
        "",
        "## Run Configuration",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Dataset | `{dataset['path']}` |",
        f"| Articles evaluated | {dataset['evaluated_articles']} / {dataset['total_articles']} |",
        f"| Text field | `{dataset['text_field']}` |",
        f"| Expected mode | `{dataset['expected_mode']}` |",
        f"| Preprocess | `{dataset.get('preprocess', 'none')}` |",
        f"| Section filter | `{dataset.get('section_filter', 'none')}` |",
        f"| Model | `{model['model_id']}` |",
        f"| Revision | `{_display(model.get('revision'))}` |",
        f"| Device | `{model['device']}` |",
        f"| Batch size | {model['batch_size']} |",
        "",
        "## Best Configurations",
        "",
        _sweep_table(rows[:20]),
        "",
    ]
    return "\n".join(lines)


def build_comparison_markdown(
    title: str,
    items: Sequence[dict[str, Any]],
    artifacts: dict[str, str] | None = None,
) -> str:
    lines = [
        f"# {title}",
        "",
        "| Variant | Preprocess | Section filter | Model | Threshold | Top-k | Micro P | Micro R | Micro F1 | Label Macro F1 | Hamming Loss | Predicted | FP | FN |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in items:
        payload = item["payload"]
        dataset = payload["dataset"]
        model = payload["model"]
        aggregate = payload["aggregate"]
        micro = aggregate["micro"]
        lines.append(
            f"| {item['label']} | `{dataset.get('preprocess', 'none')}` | "
            f"`{dataset.get('section_filter', 'none')}` | `{model['model_id']}` | "
            f"{model['threshold']} | {_display_none(model.get('top_k'))} | "
            f"{micro['precision']:.6f} | {micro['recall']:.6f} | {micro['f1']:.6f} | "
            f"{aggregate.get('label_macro', {}).get('f1', 0.0):.6f} | "
            f"{aggregate.get('hamming_loss', 0.0):.6f} | "
            f"{aggregate['predicted_count']} | {aggregate['fp']} | {aggregate['fn']} |"
        )
    if artifacts:
        lines.extend(
            [
                "",
                "## Charts",
                "",
                _comparison_charts_markdown(artifacts),
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- CISA is used as an external robustness benchmark, not as the original paper benchmark.",
            "- Improvements should be read as preprocessing, filtering, calibration, or retraining effects under domain shift.",
            "- High false positives are expected when long advisory text contains non-attacker behavior because the classifier is closed-world.",
            "",
        ]
    )
    return "\n".join(lines)


>>>>>>> feat/demo
def _top_terms(
    rows: Sequence[dict[str, Any]],
    key: str,
    names: dict[str, str],
    top_n: int,
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(str(item) for item in row[key])
    return [
        {"ttp_id": ttp_id, "name": names.get(ttp_id, ""), "count": count}
        for ttp_id, count in counter.most_common(top_n)
    ]


def _article_summaries(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "index": row["index"],
            "url": row["url"],
            "expected_count": row["expected_count"],
            "predicted_count": row["predicted_count"],
            "tp": row["metrics"]["tp"],
            "fp": row["metrics"]["fp"],
            "fn": row["metrics"]["fn"],
            "precision": row["metrics"]["precision"],
            "recall": row["metrics"]["recall"],
            "f1": row["metrics"]["f1"],
        }
        for row in rows
    ]


def _terms_table(items: Sequence[dict[str, Any]]) -> str:
    lines = ["| Rank | Technique | Name | Count |", "| ---: | --- | --- | ---: |"]
    if not items:
        lines.append("| - | - | - | 0 |")
        return "\n".join(lines)
    for rank, item in enumerate(items, start=1):
        lines.append(
            f"| {rank} | `{item['ttp_id']}` | {item.get('name', '')} | {item['count']} |"
        )
    return "\n".join(lines)


def _articles_table(items: Sequence[dict[str, Any]]) -> str:
    lines = [
        "| Rank | Index | F1 | Precision | Recall | TP | FP | FN | Expected | Predicted | URL |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not items:
        lines.append("| - | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |")
        return "\n".join(lines)
    for rank, item in enumerate(items, start=1):
        url = item["url"]
        lines.append(
            f"| {rank} | {item['index']} | {item['f1']:.6f} | "
            f"{item['precision']:.6f} | {item['recall']:.6f} | "
            f"{item['tp']} | {item['fp']} | {item['fn']} | "
            f"{item['expected_count']} | {item['predicted_count']} | [open]({url}) |"
        )
    return "\n".join(lines)


def _artifacts_table(artifacts: dict[str, str]) -> str:
    lines = ["| Artifact | Path |", "| --- | --- |"]
    if not artifacts:
        lines.append("| - | - |")
        return "\n".join(lines)
    for label, path in artifacts.items():
        lines.append(f"| {label} | `{path}` |")
    return "\n".join(lines)


<<<<<<< HEAD
=======
def _sweep_table(items: Sequence[dict[str, Any]]) -> str:
    lines = [
        "| Rank | Threshold | Top-k | Micro P | Micro R | Micro F1 | Label Macro F1 | Hamming Loss | Predicted | FP | FN |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not items:
        lines.append("| - | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |")
        return "\n".join(lines)
    for rank, item in enumerate(items, start=1):
        lines.append(
            f"| {rank} | {item['threshold']} | {_display_none(item['top_k'])} | "
            f"{item['micro_precision']:.6f} | {item['micro_recall']:.6f} | "
            f"{item['micro_f1']:.6f} | {item['label_macro_f1']:.6f} | "
            f"{item['hamming_loss']:.6f} | {item['predicted_count']} | "
            f"{item['fp']} | {item['fn']} |"
        )
    return "\n".join(lines)


>>>>>>> feat/demo
def _charts_markdown(artifacts: dict[str, str]) -> str:
    chart_keys = [
        ("chart_metrics", "Metrics overview"),
        ("chart_confusion", "TP / FP / FN counts"),
        ("chart_top_missing", "Most missed expected techniques"),
        ("chart_top_extra", "Most frequent extra predictions"),
        ("chart_f1_distribution", "Article F1 distribution"),
    ]
    lines: list[str] = []
    for key, title in chart_keys:
        path = artifacts.get(key)
        if path:
            lines.extend([f"### {title}", "", f"![{title}]({path})", ""])
    if not lines:
        return "Charts were not generated for this run."
    return "\n".join(lines).rstrip()


<<<<<<< HEAD
=======
def _comparison_charts_markdown(artifacts: dict[str, str]) -> str:
    chart_keys = [
        ("chart_micro_metrics", "Micro precision / recall / F1"),
        ("chart_error_counts", "False positives / false negatives"),
        ("chart_hamming_loss", "Hamming loss"),
        ("chart_label_volume", "Expected / predicted labels"),
    ]
    lines: list[str] = []
    for key, title in chart_keys:
        path = artifacts.get(key)
        if path:
            lines.extend([f"### {title}", "", f"![{title}]({path})", ""])
    if not lines:
        return "Charts were not generated for this run."
    return "\n".join(lines).rstrip()


>>>>>>> feat/demo
def _payload_with_markdown_relative_paths(
    payload: dict[str, Any],
    report_dir: Path,
) -> dict[str, Any]:
    render_payload = deepcopy(payload)
    artifacts = render_payload.get("artifacts", {})
    for key in list(artifacts):
        if key.startswith("chart_"):
            artifacts[key] = os.path.relpath(Path(artifacts[key]), report_dir)
    return render_payload


def _metrics_svg(payload: dict[str, Any]) -> str:
    micro = payload["aggregate"]["micro"]
<<<<<<< HEAD
    macro = payload["aggregate"]["macro"]
=======
    article_macro = payload["aggregate"].get("article_macro", payload["aggregate"]["macro"])
    label_macro = payload["aggregate"].get("label_macro", {})
>>>>>>> feat/demo
    items = [
        ("Micro P", float(micro["precision"]), "#2f6f9f"),
        ("Micro R", float(micro["recall"]), "#4c956c"),
        ("Micro F1", float(micro["f1"]), "#d17a22"),
<<<<<<< HEAD
        ("Macro P", float(macro["precision"]), "#6f5aa7"),
        ("Macro R", float(macro["recall"]), "#2a9d8f"),
        ("Macro F1", float(macro["f1"]), "#c44536"),
=======
        ("Article F1", float(article_macro["f1"]), "#6f5aa7"),
        ("Label F1", float(label_macro.get("f1", 0.0)), "#c44536"),
>>>>>>> feat/demo
    ]
    return _vertical_bar_svg("Precision / Recall / F1", items, max_value=1.0, value_suffix="")


def _confusion_svg(payload: dict[str, Any]) -> str:
    aggregate = payload["aggregate"]
    items = [
        ("TP", int(aggregate["tp"]), "#4c956c"),
        ("FP", int(aggregate["fp"]), "#c44536"),
        ("FN", int(aggregate["fn"]), "#d17a22"),
    ]
    max_value = max((value for _, value, _ in items), default=1)
    return _vertical_bar_svg("Label-Level Counts", items, max_value=max_value, value_suffix="")


def _terms_bar_svg(title: str, items: Sequence[dict[str, Any]], limit: int = 12) -> str:
    top_items = list(items[:limit])
    rows = [
        (
            str(item["ttp_id"]),
            f"{item['ttp_id']} - {item.get('name', '')}".strip(" -"),
            int(item["count"]),
        )
        for item in top_items
    ]
    return _horizontal_bar_svg(title, rows)


def _f1_distribution_svg(payload: dict[str, Any]) -> str:
    rows = payload.get("rows", [])
    bins = [0 for _ in range(10)]
    for row in rows:
        value = float(row["metrics"]["f1"])
        index = min(9, max(0, int(math.floor(value * 10))))
        bins[index] += 1
    items = [
        (f"{i / 10:.1f}-{(i + 1) / 10:.1f}", count, "#2f6f9f")
        for i, count in enumerate(bins)
    ]
    return _vertical_bar_svg("Article F1 Distribution", items, max_value=max(bins) or 1, value_suffix="")


<<<<<<< HEAD
=======
def _comparison_micro_metrics_svg(items: Sequence[dict[str, Any]]) -> str:
    rows: list[tuple[str, float, float, float]] = []
    for item in items:
        micro = item["payload"]["aggregate"]["micro"]
        rows.append(
            (
                str(item["label"]),
                float(micro["precision"]),
                float(micro["recall"]),
                float(micro["f1"]),
            )
        )
    return _grouped_bar_svg(
        "Micro Metrics by Variant",
        rows,
        series=("Precision", "Recall", "F1"),
        colors=("#2f6f9f", "#4c956c", "#d17a22"),
        max_value=1.0,
    )


def _comparison_error_counts_svg(items: Sequence[dict[str, Any]]) -> str:
    rows: list[tuple[str, float, float]] = []
    for item in items:
        aggregate = item["payload"]["aggregate"]
        rows.append((str(item["label"]), float(aggregate["fp"]), float(aggregate["fn"])))
    max_value = max((value for row in rows for value in row[1:]), default=1)
    return _grouped_bar_svg(
        "False Positive / False Negative Counts",
        rows,
        series=("FP", "FN"),
        colors=("#c44536", "#d17a22"),
        max_value=max_value,
    )


def _comparison_hamming_loss_svg(items: Sequence[dict[str, Any]]) -> str:
    chart_items = [
        (
            _short_variant_label(str(item["label"])),
            float(item["payload"]["aggregate"].get("hamming_loss", 0.0)),
            "#6f5aa7",
        )
        for item in items
    ]
    max_value = max((value for _, value, _ in chart_items), default=1.0)
    return _vertical_bar_svg("Hamming Loss by Variant", chart_items, max_value=max(max_value, 1e-9), value_suffix="")


def _comparison_label_volume_svg(items: Sequence[dict[str, Any]]) -> str:
    rows: list[tuple[str, float, float]] = []
    for item in items:
        aggregate = item["payload"]["aggregate"]
        rows.append(
            (
                str(item["label"]),
                float(aggregate["expected_count"]),
                float(aggregate["predicted_count"]),
            )
        )
    max_value = max((value for row in rows for value in row[1:]), default=1)
    return _grouped_bar_svg(
        "Expected / Predicted Label Volume",
        rows,
        series=("Expected", "Predicted"),
        colors=("#4c956c", "#2f6f9f"),
        max_value=max_value,
    )


>>>>>>> feat/demo
def _vertical_bar_svg(
    title: str,
    items: Sequence[tuple[str, float, str]],
    max_value: float,
    value_suffix: str,
) -> str:
    width = 900
    height = 420
    margin_left = 70
    margin_right = 40
    margin_top = 70
    margin_bottom = 95
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom
    bar_gap = 18
    bar_width = (chart_width - bar_gap * (len(items) - 1)) / max(len(items), 1)
    safe_max = max(max_value, 1e-9)

    parts = [_svg_header(width, height, title)]
    parts.extend(_chart_grid(width, height, margin_left, margin_top, chart_width, chart_height))
    for idx, (label, value, color) in enumerate(items):
        bar_height = chart_height * (float(value) / safe_max)
        x = margin_left + idx * (bar_width + bar_gap)
        y = margin_top + chart_height - bar_height
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" '
            f'height="{bar_height:.2f}" rx="4" fill="{color}" />'
        )
        value_text = f"{value:.3f}{value_suffix}" if safe_max <= 1.0 else f"{int(value)}"
        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" '
            f'text-anchor="middle" class="value">{_escape(value_text)}</text>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{height - 48}" '
            f'text-anchor="middle" class="label">{_escape(label)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


<<<<<<< HEAD
=======
def _grouped_bar_svg(
    title: str,
    rows: Sequence[tuple[Any, ...]],
    series: Sequence[str],
    colors: Sequence[str],
    max_value: float,
) -> str:
    width = 1050
    height = 470
    margin_left = 80
    margin_right = 36
    margin_top = 82
    margin_bottom = 140
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom
    group_gap = 34
    group_width = (chart_width - group_gap * max(len(rows) - 1, 0)) / max(len(rows), 1)
    bar_gap = 5
    bar_width = (group_width - bar_gap * max(len(series) - 1, 0)) / max(len(series), 1)
    safe_max = max(max_value, 1e-9)

    parts = [_svg_header(width, height, title)]
    parts.extend(_chart_grid(width, height, margin_left, margin_top, chart_width, chart_height))
    for row_index, row in enumerate(rows):
        label = str(row[0])
        values = [float(value) for value in row[1:]]
        group_x = margin_left + row_index * (group_width + group_gap)
        for series_index, value in enumerate(values):
            bar_height = chart_height * (value / safe_max)
            x = group_x + series_index * (bar_width + bar_gap)
            y = margin_top + chart_height - bar_height
            color = colors[series_index % len(colors)]
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" '
                f'height="{bar_height:.2f}" rx="4" fill="{color}" />'
            )
            value_text = f"{value:.3f}" if safe_max <= 1.0 else f"{int(value)}"
            parts.append(
                f'<text x="{x + bar_width / 2:.2f}" y="{y - 7:.2f}" '
                f'text-anchor="middle" class="value">{_escape(value_text)}</text>'
            )
        parts.append(
            f'<text x="{group_x + group_width / 2:.2f}" y="{height - 76}" '
            f'text-anchor="middle" class="label">{_escape(_short_variant_label(label))}</text>'
        )
    legend_x = margin_left
    for index, name in enumerate(series):
        x = legend_x + index * 145
        parts.append(f'<rect x="{x}" y="50" width="14" height="14" rx="3" fill="{colors[index % len(colors)]}" />')
        parts.append(f'<text x="{x + 20}" y="62" class="label">{_escape(name)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


>>>>>>> feat/demo
def _horizontal_bar_svg(title: str, rows: Sequence[tuple[str, str, int]]) -> str:
    width = 1000
    row_height = 42
    margin_left = 250
    margin_right = 110
    margin_top = 72
    margin_bottom = 36
    height = margin_top + margin_bottom + max(1, len(rows)) * row_height
    chart_width = width - margin_left - margin_right
    max_value = max((value for _, _, value in rows), default=1)

    parts = [_svg_header(width, height, title)]
    for idx, (ttp_id, label, value) in enumerate(rows):
        y = margin_top + idx * row_height
        bar_width = chart_width * value / max_value
        parts.append(
            f'<text x="24" y="{y + 25}" class="label">{_escape(_truncate(label, 36))}</text>'
        )
        parts.append(
            f'<rect x="{margin_left}" y="{y + 7}" width="{bar_width:.2f}" '
            f'height="24" rx="4" fill="#2f6f9f" />'
        )
        parts.append(
            f'<text x="{margin_left + bar_width + 10:.2f}" y="{y + 25}" '
            f'class="value">{_escape(str(value))}</text>'
        )
        parts.append(
            f'<title>{_escape(ttp_id)} count {value}</title>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_header(width: int, height: int, title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">
<style>
  .title {{ font: 700 24px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #1f2933; }}
  .label {{ font: 500 13px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #334e68; }}
  .value {{ font: 700 13px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #102a43; }}
  .grid {{ stroke: #d9e2ec; stroke-width: 1; }}
  .axis {{ stroke: #9fb3c8; stroke-width: 1.2; }}
</style>
<rect width="100%" height="100%" fill="#ffffff" />
<text x="24" y="38" class="title">{_escape(title)}</text>'''


def _chart_grid(
    width: int,
    height: int,
    margin_left: int,
    margin_top: int,
    chart_width: int,
    chart_height: int,
) -> list[str]:
    parts = []
    for i in range(5):
        y = margin_top + chart_height * i / 4
        parts.append(
            f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + chart_width}" '
            f'y2="{y:.2f}" class="grid" />'
        )
    parts.append(
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" '
        f'y2="{margin_top + chart_height}" class="axis" />'
    )
    parts.append(
        f'<line x1="{margin_left}" y1="{margin_top + chart_height}" '
        f'x2="{width - 40}" y2="{margin_top + chart_height}" class="axis" />'
    )
    return parts


def _join(values: Iterable[Any]) -> str:
    return ";".join(str(value) for value in values)


def _display(value: Any) -> str:
    if value is None:
        return "not pinned"
    return str(value)


<<<<<<< HEAD
=======
def _display_none(value: Any) -> str:
    if value is None:
        return "none"
    return str(value)


>>>>>>> feat/demo
def _mean(values: Sequence[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _median(values: Sequence[int]) -> float:
    if not values:
        return 0.0
    return float(median(values))


def _round(value: float) -> float:
    return round(value, 6)


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "..."
<<<<<<< HEAD
=======


def _short_variant_label(value: str) -> str:
    replacements = {
        "paper-ioc + CISA section filter": "ioc+filter",
        "original paper-ioc + CISA section filter": "orig ioc+filter",
        "retrained paper-ioc + CISA section filter": "retrain ioc+filter",
        "original baseline": "orig base",
        "retrained baseline": "retrain base",
    }
    return replacements.get(value, _truncate(value, 18))
>>>>>>> feat/demo
