from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

MODEL_ARTIFACTS_DIR = PROJECT_ROOT / "model_artifacts"
DATASETS_DIR = PROJECT_ROOT / "datasets"
EXAMPLES_DIR = PROJECT_ROOT / "examples"
RESULTS_DIR = PROJECT_ROOT / "results"
