from ttpxhunter.cisa_reporting import (
    build_benchmark_markdown,
<<<<<<< HEAD
=======
    build_comparison_markdown,
>>>>>>> feat/demo
    enhance_benchmark_payload,
    write_benchmark_charts,
    write_benchmark_markdown,
    write_benchmark_rows_csv,
<<<<<<< HEAD
=======
    write_comparison_charts,
>>>>>>> feat/demo
)


def sample_payload() -> dict:
    return {
        "dataset": {
            "record_id": "14659512",
            "doi": "10.5281/zenodo.14659512",
            "path": "sample.json",
            "total_articles": 1,
            "evaluated_articles": 1,
            "text_field": "clean",
            "expected_mode": "model-label-space",
        },
        "model": {
            "model_id": "nanda-rani/TTPXHunter",
            "revision": None,
            "threshold": 0.644,
            "device": "cpu",
            "batch_size": 16,
        },
        "aggregate": {
            "article_count": 1,
            "tp": 1,
            "fp": 1,
            "fn": 1,
            "expected_count": 2,
            "predicted_count": 2,
            "micro": {
                "tp": 1,
                "fp": 1,
                "fn": 1,
                "precision": 0.5,
                "recall": 0.5,
                "f1": 0.5,
            },
            "macro": {"precision": 0.5, "recall": 0.5, "f1": 0.5},
        },
        "technique_names": {
            "T1005": "Data from Local System",
            "T1036": "Masquerading",
            "T1105": "Ingress Tool Transfer",
        },
        "rows": [
            {
                "index": 0,
                "url": "https://example.test/a",
                "sentence_count": 5,
                "raw_attack_id_count": 2,
                "expected_count": 2,
                "predicted_count": 2,
                "metrics": {
                    "tp": 1,
                    "fp": 1,
                    "fn": 1,
                    "precision": 0.5,
                    "recall": 0.5,
                    "f1": 0.5,
                },
                "matches": ["T1005"],
                "missing": ["T1105"],
                "extra": ["T1036"],
                "expected": ["T1005", "T1105"],
                "predicted": [
                    {"ttp_id": "T1005", "name": "Data from Local System"},
                    {"ttp_id": "T1036", "name": "Masquerading"},
                ],
            }
        ],
    }


def test_enhance_benchmark_payload_adds_actionable_insights() -> None:
    payload = enhance_benchmark_payload(sample_payload(), top_n=3)
    insights = payload["insights"]
    assert insights["article_quality"]["exact_match_articles"] == 0
    assert insights["top_missing"][0]["ttp_id"] == "T1105"
    assert insights["top_extra"][0]["name"] == "Masquerading"


def test_build_benchmark_markdown_contains_summary_and_top_terms() -> None:
    payload = enhance_benchmark_payload(sample_payload())
    payload["artifacts"] = {"chart_metrics": "charts/metrics_overview.svg"}
    markdown = build_benchmark_markdown(payload)
    assert "# CISA TTPXHunter Benchmark Report" in markdown
    assert "Micro F1" in markdown
    assert "Ingress Tool Transfer" in markdown
    assert "![Metrics overview](charts/metrics_overview.svg)" in markdown


def test_write_benchmark_rows_csv_creates_flat_article_table(tmp_path) -> None:
    path = tmp_path / "rows.csv"
    write_benchmark_rows_csv(enhance_benchmark_payload(sample_payload()), path)
    text = path.read_text(encoding="utf-8")
    assert "index,url,sentence_count" in text
    assert "T1005;T1036" in text


def test_write_benchmark_charts_creates_svg_files(tmp_path) -> None:
    payload = enhance_benchmark_payload(sample_payload())
    charts = write_benchmark_charts(payload, tmp_path / "charts")
    assert set(charts) == {
        "chart_metrics",
        "chart_confusion",
        "chart_top_missing",
        "chart_top_extra",
        "chart_f1_distribution",
    }
    for path in charts.values():
        text = path.read_text(encoding="utf-8")
        assert text.startswith("<svg")
        assert "</svg>" in text


def test_write_benchmark_markdown_uses_report_relative_chart_paths(tmp_path) -> None:
    payload = enhance_benchmark_payload(sample_payload())
    charts = write_benchmark_charts(payload, tmp_path / "reports" / "charts")
    payload["artifacts"] = {key: str(path) for key, path in charts.items()}
    report = tmp_path / "reports" / "report.md"
    write_benchmark_markdown(payload, report)
    markdown = report.read_text(encoding="utf-8")
    assert "![Metrics overview](charts/metrics_overview.svg)" in markdown
<<<<<<< HEAD
=======


def test_comparison_markdown_can_embed_gap_charts(tmp_path) -> None:
    items = [
        {"label": "baseline", "payload": enhance_benchmark_payload(sample_payload())},
        {"label": "paper-ioc", "payload": enhance_benchmark_payload(sample_payload())},
    ]
    charts = write_comparison_charts(items, tmp_path / "charts")
    assert set(charts) == {
        "chart_micro_metrics",
        "chart_error_counts",
        "chart_hamming_loss",
        "chart_label_volume",
    }
    for path in charts.values():
        text = path.read_text(encoding="utf-8")
        assert text.startswith("<svg")
        assert "</svg>" in text

    markdown = build_comparison_markdown(
        "CISA Gap Comparison",
        items,
        artifacts={"chart_micro_metrics": "charts/comparison_micro_metrics.svg"},
    )
    assert "## Charts" in markdown
    assert "![Micro precision / recall / F1](charts/comparison_micro_metrics.svg)" in markdown
>>>>>>> feat/demo
