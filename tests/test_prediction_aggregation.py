from ttpxhunter.cisa_pipeline import aggregate_rows
from ttpxhunter.pipeline import SentenceTTPPrediction, aggregate_prediction_evidence


def test_aggregate_prediction_evidence_supports_threshold_and_top_k() -> None:
    predictions = [
        SentenceTTPPrediction("one", "LABEL_1", 0.90, "T1001", "One"),
        SentenceTTPPrediction("two", "LABEL_2", 0.80, "T1002", "Two"),
        SentenceTTPPrediction("three", "LABEL_1", 0.70, "T1001", "One"),
        SentenceTTPPrediction("four", "LABEL_3", 0.95, "T1003", "Three"),
    ]

    evidence = aggregate_prediction_evidence(
        predictions,
        threshold=0.65,
        order="first-seen",
        top_k=2,
    )

    assert [item.ttp_id for item in evidence] == ["T1003", "T1001"]
    assert evidence[1].support_sentence_count == 2
    assert evidence[1].example_sentence == "one"


def test_aggregate_rows_adds_label_macro_and_hamming_loss() -> None:
    rows = [
        {
            "expected_count": 2,
            "predicted_count": 2,
            "metrics": {"tp": 1, "fp": 1, "fn": 1, "precision": 0.5, "recall": 0.5, "f1": 0.5},
            "expected": ["T1001", "T1002"],
            "predicted": [{"ttp_id": "T1001"}, {"ttp_id": "T1003"}],
        },
        {
            "expected_count": 1,
            "predicted_count": 0,
            "metrics": {"tp": 0, "fp": 0, "fn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0},
            "expected": ["T1002"],
            "predicted": [],
        },
    ]

    aggregate = aggregate_rows(rows, label_space=["T1001", "T1002", "T1003"])

    assert aggregate["tp"] == 1
    assert aggregate["fp"] == 1
    assert aggregate["fn"] == 2
    assert aggregate["hamming_loss"] == 0.5
    assert aggregate["label_macro"]["label_count"] == 3
    assert aggregate["article_macro"]["f1"] == 0.25
