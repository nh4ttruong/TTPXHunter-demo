from ttpxhunter.reporting import build_inference_markdown


def test_build_inference_markdown_includes_notebook_agreement_metrics() -> None:
    payload = {
        "report": "report.txt",
        "model_id": "nanda-rani/TTPXHunter",
        "revision": None,
        "threshold": 0.644,
        "order": "first-seen",
        "count": 2,
        "results": [
            {"ttp_id": "T1001", "name": "One"},
            {"ttp_id": "T1002", "name": "Two"},
        ],
        "comparison": {
            "actual_count": 2,
            "expected_count": 2,
            "set_match": True,
            "order_match": False,
            "missing": [],
            "extra": [],
        },
    }

    markdown = build_inference_markdown(payload)

    assert "# TTPXHunter Inference Report" in markdown
    assert "Agreement F1" in markdown
    assert "reproduction metrics, not independent model accuracy" in markdown
    assert "`T1001`" in markdown
