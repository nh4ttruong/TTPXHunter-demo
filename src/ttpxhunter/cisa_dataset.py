from __future__ import annotations

import ast
import csv
import json
import re
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .paths import DATASETS_DIR

CISA_ZENODO_RECORD_ID = "14659512"
CISA_ZENODO_DOI = "10.5281/zenodo.14659512"
CISA_ZENODO_API_URL = f"https://zenodo.org/api/records/{CISA_ZENODO_RECORD_ID}"
CISA_JSON_NAME = "CISA-crawl-rt-ttp-ct.json"
CISA_CSV_NAME = "CISA-crawl-rt-ttp-ct.csv"
CISA_DEFAULT_DIR = DATASETS_DIR / "cisa"
CISA_DEFAULT_JSON = CISA_DEFAULT_DIR / CISA_JSON_NAME

ATTACK_ID_RE = re.compile(r"(?<![A-Z0-9])(?:TA\d{4}|T\d{4}(?:\.\d{3})?)(?![\d.])")
BASE_TECHNIQUE_RE = re.compile(r"^T\d{4}$")
SUBTECHNIQUE_RE = re.compile(r"^(T\d{4})\.\d{3}$")
TACTIC_RE = re.compile(r"^TA\d{4}$")


@dataclass(frozen=True)
class CISAArticle:
    index: int
    raw_text: str
    clean_text: str
    attack_ids: tuple[str, ...]
    url: str


@dataclass(frozen=True)
class SetMetrics:
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float


def download_cisa_dataset(
    out_dir: str | Path = CISA_DEFAULT_DIR,
    file_format: str = "both",
    overwrite: bool = False,
) -> list[Path]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(CISA_ZENODO_API_URL, timeout=60) as response:
        record = json.load(response)

    requested = {CISA_JSON_NAME, CISA_CSV_NAME}
    if file_format == "json":
        requested = {CISA_JSON_NAME}
    elif file_format == "csv":
        requested = {CISA_CSV_NAME}
    elif file_format != "both":
        raise ValueError("file_format must be one of: json, csv, both")

    downloaded: list[Path] = []
    files = {item["key"]: item["links"]["self"] for item in record["files"]}
    for name in sorted(requested):
        target = out_path / name
        if target.exists() and not overwrite:
            downloaded.append(target)
            continue
        urllib.request.urlretrieve(files[name], target)
        downloaded.append(target)
    return downloaded


def load_cisa_articles(path: str | Path = CISA_DEFAULT_JSON) -> list[CISAArticle]:
    dataset_path = Path(path)
    if dataset_path.suffix.lower() == ".csv":
        rows = _load_csv_rows(dataset_path)
    else:
        rows = _load_json_rows(dataset_path)

    articles: list[CISAArticle] = []
    for fallback_index, row in enumerate(rows):
        raw_index = row.get("", fallback_index)
        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            index = fallback_index

        articles.append(
            CISAArticle(
                index=index,
                raw_text=str(row.get("RawText", "")),
                clean_text=str(row.get("CleanText", "")),
                attack_ids=tuple(sorted(parse_ttp_field(row.get("TTP", "")))),
                url=str(row.get("URL", "")),
            )
        )
    return articles


def _load_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _load_json_rows(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").lstrip()
    if not text:
        return []
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def parse_ttp_field(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (set, list, tuple)):
        return {str(item) for item in value}

    text = str(value)
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return set(ATTACK_ID_RE.findall(text))

    if isinstance(parsed, (set, list, tuple)):
        return {str(item) for item in parsed}
    return set(ATTACK_ID_RE.findall(text))


def normalize_attack_ids(
    attack_ids: Iterable[str],
    label_space: set[str] | None = None,
    collapse_subtechniques: bool = True,
    drop_tactics: bool = True,
) -> list[str]:
    normalized: set[str] = set()
    for attack_id in attack_ids:
        value = str(attack_id).strip()
        if drop_tactics and TACTIC_RE.fullmatch(value):
            continue
        if BASE_TECHNIQUE_RE.fullmatch(value):
            technique_id = value
        else:
            subtechnique_match = SUBTECHNIQUE_RE.fullmatch(value)
            if subtechnique_match and collapse_subtechniques:
                technique_id = subtechnique_match.group(1)
            elif subtechnique_match:
                technique_id = value
            else:
                continue
        if label_space is not None and technique_id not in label_space:
            continue
        normalized.add(technique_id)
    return sorted(normalized)


def metrics_for_sets(predicted: Sequence[str], expected: Sequence[str]) -> SetMetrics:
    predicted_set = set(predicted)
    expected_set = set(expected)
    tp = len(predicted_set & expected_set)
    fp = len(predicted_set - expected_set)
    fn = len(expected_set - predicted_set)
    precision = _safe_ratio(tp, tp + fp, perfect_when_empty=(len(expected_set) == 0))
    recall = _safe_ratio(tp, tp + fn, perfect_when_empty=(len(predicted_set) == 0))
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return SetMetrics(tp=tp, fp=fp, fn=fn, precision=precision, recall=recall, f1=f1)


def summarize_dataset(
    articles: Sequence[CISAArticle],
    label_space: set[str] | None = None,
) -> dict[str, Any]:
    raw_counts = [len(article.attack_ids) for article in articles]
    base_counts = [
        len(normalize_attack_ids(article.attack_ids, label_space=None))
        for article in articles
    ]
    model_counts = [
        len(normalize_attack_ids(article.attack_ids, label_space=label_space))
        for article in articles
    ]
    return {
        "record_id": CISA_ZENODO_RECORD_ID,
        "doi": CISA_ZENODO_DOI,
        "article_count": len(articles),
        "raw_attack_id_count": sum(raw_counts),
        "base_technique_count": sum(base_counts),
        "model_label_space_technique_count": sum(model_counts) if label_space else None,
        "articles_with_no_raw_ttps": sum(1 for count in raw_counts if count == 0),
        "max_raw_ttps_per_article": max(raw_counts) if raw_counts else 0,
        "max_base_ttps_per_article": max(base_counts) if base_counts else 0,
    }


def set_metrics_to_dict(metrics: SetMetrics) -> dict[str, Any]:
    payload = asdict(metrics)
    payload["precision"] = round(metrics.precision, 6)
    payload["recall"] = round(metrics.recall, 6)
    payload["f1"] = round(metrics.f1, 6)
    return payload


def _safe_ratio(numerator: int, denominator: int, perfect_when_empty: bool = False) -> float:
    if denominator == 0:
        return 1.0 if perfect_when_empty else 0.0
    return numerator / denominator
