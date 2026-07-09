import os
from pathlib import Path

import pytest

from ttpxhunter.pipeline import (
    compare_results,
    load_expected_results,
    process_text_file_for_attack_patterns,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_REPORT = ROOT / "examples" / "reports" / "SharpPanda_APT_Campaign_Expands_its_Arsenal_Targeting_G20_Nations.txt"
EXPECTED = ROOT / "tests" / "expected_sharppanda.json"


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("RUN_HF_INTEGRATION") != "1",
    reason="Set RUN_HF_INTEGRATION=1 to download and run the Hugging Face model.",
)
def test_sharppanda_reproduces_saved_notebook_ttp_set() -> None:
    actual = process_text_file_for_attack_patterns(SAMPLE_REPORT, order="first-seen")
    expected = load_expected_results(EXPECTED)
    comparison = compare_results(actual, expected)
    assert comparison["set_match"], comparison
    assert comparison["actual_count"] == 19
