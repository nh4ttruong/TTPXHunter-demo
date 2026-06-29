from pathlib import Path

from ttpxhunter.pipeline import (
    compare_results,
    load_expected_results,
    predicted_labels_to_ttp_ids,
    remove_consecutive_newlines,
    report_to_sentences,
    translate_ttp_ids_to_names,
    unique_ttp_ids,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_REPORT = ROOT / "examples" / "reports" / "SharpPanda_APT_Campaign_Expands_its_Arsenal_Targeting_G20_Nations.txt"
EXPECTED = ROOT / "tests" / "expected_sharppanda.json"


def test_remove_consecutive_newlines_keeps_single_newline_boundaries() -> None:
    assert remove_consecutive_newlines("a\n\n\nb\n\nc") == "a\nb\nc"
    assert remove_consecutive_newlines("") == ""


def test_unique_ttp_ids_first_seen_is_deterministic() -> None:
    assert unique_ttp_ids(["T1005", "T1005", "T1036", "T1005"]) == ["T1005", "T1036"]
    assert unique_ttp_ids(["T1036", "T1005"], order="sorted") == ["T1005", "T1036"]


def test_artifact_mapping_can_translate_saved_notebook_ids() -> None:
    expected = load_expected_results(EXPECTED)
    translated = translate_ttp_ids_to_names([result.ttp_id for result in expected])
    assert translated == expected


def test_label_pickle_maps_roberta_label_ids_to_ttp_ids() -> None:
    assert predicted_labels_to_ttp_ids(["LABEL_0", "LABEL_0", "LABEL_1"]) == [
        "T1543",
        "T1562",
    ]


def test_sample_report_sentence_split_is_stable_enough_for_reproduction() -> None:
    sentences = report_to_sentences(SAMPLE_REPORT)
    assert len(sentences) == 66
    assert any("SharpPanda" in sentence for sentence in sentences)


def test_compare_results_accepts_same_set_even_when_order_changes() -> None:
    expected = load_expected_results(EXPECTED)
    actual = list(reversed(expected))
    comparison = compare_results(actual, expected)
    assert comparison["set_match"] is True
    assert comparison["order_match"] is False
    assert comparison["missing"] == []
    assert comparison["extra"] == []
