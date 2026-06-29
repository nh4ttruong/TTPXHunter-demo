import json

from ttpxhunter.cisa_dataset import (
    load_cisa_articles,
    metrics_for_sets,
    normalize_attack_ids,
    parse_ttp_field,
    summarize_dataset,
)


def test_parse_ttp_field_handles_python_set_string() -> None:
    parsed = parse_ttp_field("{'T1083', 'T1071.002', 'TA0010', 'T20200'}")
    assert parsed == {"T1083", "T1071.002", "TA0010", "T20200"}


def test_normalize_attack_ids_drops_tactics_bad_ids_and_collapses_subtechniques() -> None:
    normalized = normalize_attack_ids(
        ["T1083", "T1071.002", "TA0010", "T20200", "T15880"],
        label_space={"T1083", "T1071"},
    )
    assert normalized == ["T1071", "T1083"]


def test_metrics_for_sets_reports_precision_recall_f1() -> None:
    metrics = metrics_for_sets(predicted=["T1005", "T1036"], expected=["T1005", "T1105"])
    assert metrics.tp == 1
    assert metrics.fp == 1
    assert metrics.fn == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5


def test_load_cisa_articles_supports_json_lines(tmp_path) -> None:
    path = tmp_path / "sample.json"
    rows = [
        {
            "RawText": "raw",
            "CleanText": "clean",
            "TTP": "{'T1083', 'T1071.002', 'TA0010'}",
            "URL": "https://example.test/a",
        }
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    articles = load_cisa_articles(path)

    assert len(articles) == 1
    assert articles[0].index == 0
    assert articles[0].clean_text == "clean"
    assert articles[0].attack_ids == ("T1071.002", "T1083", "TA0010")


def test_summarize_dataset_counts_model_label_space(tmp_path) -> None:
    path = tmp_path / "sample.json"
    path.write_text(
        json.dumps(
            {
                "RawText": "raw",
                "CleanText": "clean",
                "TTP": "{'T1083', 'T1071.002', 'TA0010'}",
                "URL": "https://example.test/a",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    summary = summarize_dataset(load_cisa_articles(path), label_space={"T1083"})
    assert summary["article_count"] == 1
    assert summary["raw_attack_id_count"] == 3
    assert summary["base_technique_count"] == 2
    assert summary["model_label_space_technique_count"] == 1
