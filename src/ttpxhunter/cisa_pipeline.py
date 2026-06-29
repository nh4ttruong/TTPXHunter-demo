from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal, Sequence

from .cisa_dataset import (
    CISAArticle,
    CISA_DEFAULT_JSON,
    CISA_ZENODO_DOI,
    CISA_ZENODO_RECORD_ID,
    SetMetrics,
    load_cisa_articles,
    metrics_for_sets,
    normalize_attack_ids,
    set_metrics_to_dict,
)
from .pipeline import (
    DEFAULT_LABEL_DICT,
    DEFAULT_MODEL_ID,
    DEFAULT_THRESHOLD,
    DEFAULT_TTPID2NAME,
    TTPResult,
    extract_ttp_from_sentences_with_model,
    load_label_space,
    load_pickle,
    load_model_and_tokenizer,
    text_to_sentences,
)

ExpectedMode = Literal["model-label-space", "all-base"]
TextField = Literal["clean", "raw"]


def run_cisa_benchmark(
    dataset_path: str | Path = CISA_DEFAULT_JSON,
    threshold: float = DEFAULT_THRESHOLD,
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
    model_id: str = DEFAULT_MODEL_ID,
    revision: str | None = None,
    device: str | None = None,
    order: str = "first-seen",
    batch_size: int = 16,
    limit: int | None = None,
    offset: int = 0,
    expected_mode: ExpectedMode = "model-label-space",
    text_field: TextField = "clean",
) -> dict[str, Any]:
    articles = load_cisa_articles(dataset_path)
    selected = articles[offset : offset + limit if limit is not None else None]
    label_space = load_label_space(label_dict_path)
    expected_label_space = label_space if expected_mode == "model-label-space" else None

    model, tokenizer, resolved_device = load_model_and_tokenizer(
        model_id=model_id,
        revision=revision,
        device=device,
    )

    rows: list[dict[str, Any]] = []
    for article in selected:
        text = article.raw_text if text_field == "raw" else article.clean_text
        sentences = text_to_sentences(text)
        predictions = extract_ttp_from_sentences_with_model(
            sentences=sentences,
            model=model,
            tokenizer=tokenizer,
            device=resolved_device,
            threshold=threshold,
            label_dict_path=label_dict_path,
            ttpid2name_path=ttpid2name_path,
            order=order,  # type: ignore[arg-type]
            batch_size=batch_size,
        )
        expected_ids = normalize_attack_ids(
            article.attack_ids,
            label_space=expected_label_space,
            collapse_subtechniques=True,
            drop_tactics=True,
        )
        row = build_evaluation_row(
            article=article,
            predictions=predictions,
            expected_ids=expected_ids,
            sentence_count=len(sentences),
        )
        rows.append(row)

    aggregate = aggregate_rows(rows)
    technique_names = build_technique_name_map(rows, ttpid2name_path)
    return {
        "dataset": {
            "record_id": CISA_ZENODO_RECORD_ID,
            "doi": CISA_ZENODO_DOI,
            "path": str(dataset_path),
            "total_articles": len(articles),
            "evaluated_articles": len(selected),
            "offset": offset,
            "limit": limit,
            "text_field": text_field,
            "expected_mode": expected_mode,
        },
        "model": {
            "model_id": model_id,
            "revision": revision,
            "threshold": threshold,
            "device": str(resolved_device),
            "batch_size": batch_size,
        },
        "aggregate": aggregate,
        "technique_names": technique_names,
        "rows": rows,
    }


def build_evaluation_row(
    article: CISAArticle,
    predictions: Sequence[TTPResult],
    expected_ids: Sequence[str],
    sentence_count: int,
) -> dict[str, Any]:
    predicted_ids = sorted({prediction.ttp_id for prediction in predictions})
    metrics = metrics_for_sets(predicted_ids, expected_ids)
    expected_set = set(expected_ids)
    predicted_set = set(predicted_ids)
    return {
        "index": article.index,
        "url": article.url,
        "sentence_count": sentence_count,
        "raw_attack_id_count": len(article.attack_ids),
        "expected_count": len(expected_ids),
        "predicted_count": len(predicted_ids),
        "metrics": set_metrics_to_dict(metrics),
        "matches": sorted(predicted_set & expected_set),
        "missing": sorted(expected_set - predicted_set),
        "extra": sorted(predicted_set - expected_set),
        "expected": list(expected_ids),
        "predicted": [asdict(prediction) for prediction in predictions],
    }


def aggregate_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    total_tp = sum(int(row["metrics"]["tp"]) for row in rows)
    total_fp = sum(int(row["metrics"]["fp"]) for row in rows)
    total_fn = sum(int(row["metrics"]["fn"]) for row in rows)
    micro_precision = _safe_ratio(total_tp, total_tp + total_fp)
    micro_recall = _safe_ratio(total_tp, total_tp + total_fn)
    micro_f1 = (
        0.0
        if micro_precision + micro_recall == 0
        else 2 * micro_precision * micro_recall / (micro_precision + micro_recall)
    )
    micro = SetMetrics(
        tp=total_tp,
        fp=total_fp,
        fn=total_fn,
        precision=micro_precision,
        recall=micro_recall,
        f1=micro_f1,
    )

    count = len(rows)
    macro_precision = _mean(float(row["metrics"]["precision"]) for row in rows)
    macro_recall = _mean(float(row["metrics"]["recall"]) for row in rows)
    macro_f1 = _mean(float(row["metrics"]["f1"]) for row in rows)

    return {
        "article_count": count,
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "micro": set_metrics_to_dict(micro),
        "macro": {
            "precision": round(macro_precision, 6),
            "recall": round(macro_recall, 6),
            "f1": round(macro_f1, 6),
        },
        "expected_count": sum(int(row["expected_count"]) for row in rows),
        "predicted_count": sum(int(row["predicted_count"]) for row in rows),
    }


def build_technique_name_map(
    rows: Sequence[dict[str, Any]],
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
) -> dict[str, str]:
    id_to_name = {str(key): str(value) for key, value in load_pickle(ttpid2name_path).items()}
    ids: set[str] = set()
    for row in rows:
        ids.update(str(item) for item in row["expected"])
        ids.update(str(item) for item in row["matches"])
        ids.update(str(item) for item in row["missing"])
        ids.update(str(item) for item in row["extra"])
    return {ttp_id: id_to_name[ttp_id] for ttp_id in sorted(ids) if ttp_id in id_to_name}


def _mean(values: Sequence[float] | Any) -> float:
    materialized = list(values)
    if not materialized:
        return 0.0
    return sum(materialized) / len(materialized)


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
