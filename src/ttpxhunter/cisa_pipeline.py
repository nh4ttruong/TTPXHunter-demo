from __future__ import annotations

from collections.abc import Callable
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
    TTPEvidence,
    TTPResult,
    aggregate_prediction_evidence,
    load_label_space,
    load_pickle,
    load_model_and_tokenizer,
    predict_ttp_for_sentences_with_model,
    text_to_sentences,
)
from .preprocessing import PreprocessMode, SectionFilterMode

ExpectedMode = Literal["model-label-space", "all-base"]
TextField = Literal["clean", "raw"]
ProgressCallback = Callable[[str], None]


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
    preprocess: PreprocessMode = "none",
    section_filter: SectionFilterMode = "none",
    top_k: int | None = None,
    include_evidence: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    cache = build_cisa_prediction_cache(
        dataset_path=dataset_path,
        label_dict_path=label_dict_path,
        ttpid2name_path=ttpid2name_path,
        model_id=model_id,
        revision=revision,
        device=device,
        batch_size=batch_size,
        limit=limit,
        offset=offset,
        expected_mode=expected_mode,
        text_field=text_field,
        preprocess=preprocess,
        section_filter=section_filter,
        progress_callback=progress_callback,
    )
    if progress_callback:
        progress_callback(
            f"evaluating threshold={threshold} top_k={_display_top_k(top_k)}"
        )
    return evaluate_cisa_prediction_cache(
        cache,
        threshold=threshold,
        order=order,
        top_k=top_k,
        include_evidence=include_evidence,
    )


def run_cisa_sweep(
    dataset_path: str | Path = CISA_DEFAULT_JSON,
    thresholds: Sequence[float] = (0.644, 0.70, 0.75, 0.80, 0.85, 0.90),
    top_ks: Sequence[int | None] = (None, 10, 15, 20, 25, 30),
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
    preprocess: PreprocessMode = "none",
    section_filter: SectionFilterMode = "none",
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    cache = build_cisa_prediction_cache(
        dataset_path=dataset_path,
        label_dict_path=label_dict_path,
        ttpid2name_path=ttpid2name_path,
        model_id=model_id,
        revision=revision,
        device=device,
        batch_size=batch_size,
        limit=limit,
        offset=offset,
        expected_mode=expected_mode,
        text_field=text_field,
        preprocess=preprocess,
        section_filter=section_filter,
        progress_callback=progress_callback,
    )

    sweep_rows: list[dict[str, Any]] = []
    for threshold in thresholds:
        for top_k in top_ks:
            if progress_callback:
                progress_callback(
                    f"sweep threshold={threshold} top_k={_display_top_k(top_k)}"
                )
            payload = evaluate_cisa_prediction_cache(
                cache,
                threshold=threshold,
                order=order,
                top_k=top_k,
                include_evidence=False,
            )
            aggregate = payload["aggregate"]
            micro = aggregate["micro"]
            sweep_rows.append(
                {
                    "threshold": threshold,
                    "top_k": top_k,
                    "article_count": aggregate["article_count"],
                    "expected_count": aggregate["expected_count"],
                    "predicted_count": aggregate["predicted_count"],
                    "tp": aggregate["tp"],
                    "fp": aggregate["fp"],
                    "fn": aggregate["fn"],
                    "micro_precision": micro["precision"],
                    "micro_recall": micro["recall"],
                    "micro_f1": micro["f1"],
                    "label_macro_f1": aggregate["label_macro"]["f1"],
                    "hamming_loss": aggregate["hamming_loss"],
                    "fp_rate": _safe_ratio(aggregate["fp"], aggregate["predicted_count"]),
                    "fn_rate": _safe_ratio(aggregate["fn"], aggregate["expected_count"]),
                }
            )

    return {
        "dataset": cache["dataset"],
        "model": {
            **cache["model"],
            "thresholds": list(thresholds),
            "top_ks": list(top_ks),
        },
        "sweep_rows": sweep_rows,
    }


def build_cisa_prediction_cache(
    dataset_path: str | Path = CISA_DEFAULT_JSON,
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
    model_id: str = DEFAULT_MODEL_ID,
    revision: str | None = None,
    device: str | None = None,
    batch_size: int = 16,
    limit: int | None = None,
    offset: int = 0,
    expected_mode: ExpectedMode = "model-label-space",
    text_field: TextField = "clean",
    preprocess: PreprocessMode = "none",
    section_filter: SectionFilterMode = "none",
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    articles = load_cisa_articles(dataset_path)
    selected = articles[offset : offset + limit if limit is not None else None]
    label_space = load_label_space(label_dict_path)
    expected_label_space = label_space if expected_mode == "model-label-space" else None

    if progress_callback:
        progress_callback(
            f"loading model={model_id} articles={len(selected)}/{len(articles)} "
            f"preprocess={preprocess} section_filter={section_filter}"
        )
    model, tokenizer, resolved_device = load_model_and_tokenizer(
        model_id=model_id,
        revision=revision,
        device=device,
    )
    if progress_callback:
        progress_callback(f"model loaded on device={resolved_device}")

    cached_rows: list[dict[str, Any]] = []
    total_selected = len(selected)
    for position, article in enumerate(selected, start=1):
        text = article.raw_text if text_field == "raw" else article.clean_text
        sentences = text_to_sentences(
            text,
            preprocess=preprocess,
            section_filter=section_filter,
        )
        if progress_callback:
            progress_callback(
                f"article {position}/{total_selected} index={article.index} "
                f"sentences={len(sentences)} start"
            )
        sentence_predictions = predict_ttp_for_sentences_with_model(
            sentences=sentences,
            model=model,
            tokenizer=tokenizer,
            device=resolved_device,
            label_dict_path=label_dict_path,
            ttpid2name_path=ttpid2name_path,
            batch_size=batch_size,
        )
        expected_ids = normalize_attack_ids(
            article.attack_ids,
            label_space=expected_label_space,
            collapse_subtechniques=True,
            drop_tactics=True,
        )
        if progress_callback:
            progress_callback(
                f"article {position}/{total_selected} index={article.index} "
                f"expected={len(expected_ids)} sentence_predictions={len(sentence_predictions)} done"
            )
        cached_rows.append(
            {
                "article": article,
                "sentence_count": len(sentences),
                "expected_ids": expected_ids,
                "sentence_predictions": sentence_predictions,
            }
        )

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
            "preprocess": preprocess,
            "section_filter": section_filter,
        },
        "model": {
            "model_id": model_id,
            "revision": revision,
            "device": str(resolved_device),
            "batch_size": batch_size,
        },
        "label_space": sorted(label_space),
        "label_dict_path": str(label_dict_path),
        "ttpid2name_path": str(ttpid2name_path),
        "rows": cached_rows,
    }


def evaluate_cisa_prediction_cache(
    cache: dict[str, Any],
    threshold: float = DEFAULT_THRESHOLD,
    order: str = "first-seen",
    top_k: int | None = None,
    include_evidence: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for cached in cache["rows"]:
        evidence = aggregate_prediction_evidence(
            predictions=cached["sentence_predictions"],
            threshold=threshold,
            order=order,  # type: ignore[arg-type]
            top_k=top_k,
        )
        predictions = [
            TTPResult(ttp_id=item.ttp_id, name=item.name)
            for item in evidence
        ]
        rows.append(
            build_evaluation_row(
                article=cached["article"],
                predictions=predictions,
                expected_ids=cached["expected_ids"],
                sentence_count=cached["sentence_count"],
                evidence=evidence if include_evidence else None,
            )
        )

    aggregate = aggregate_rows(rows, label_space=cache["label_space"])
    technique_names = build_technique_name_map(rows, cache["ttpid2name_path"])
    return {
        "dataset": cache["dataset"],
        "model": {
            **cache["model"],
            "threshold": threshold,
            "top_k": top_k,
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
    evidence: Sequence[TTPEvidence] | None = None,
) -> dict[str, Any]:
    predicted_ids = sorted({prediction.ttp_id for prediction in predictions})
    metrics = metrics_for_sets(predicted_ids, expected_ids)
    expected_set = set(expected_ids)
    predicted_set = set(predicted_ids)
    row = {
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
    if evidence is not None:
        row["evidence"] = [asdict(item) for item in evidence]
    return row


def aggregate_rows(
    rows: Sequence[dict[str, Any]],
    label_space: Sequence[str] | None = None,
) -> dict[str, Any]:
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

    article_macro_precision = _mean(float(row["metrics"]["precision"]) for row in rows)
    article_macro_recall = _mean(float(row["metrics"]["recall"]) for row in rows)
    article_macro_f1 = _mean(float(row["metrics"]["f1"]) for row in rows)
    article_macro = {
        "precision": round(article_macro_precision, 6),
        "recall": round(article_macro_recall, 6),
        "f1": round(article_macro_f1, 6),
    }

    resolved_label_space = list(label_space or _labels_from_rows(rows))
    label_macro = _label_macro(rows, resolved_label_space)
    article_count = len(rows)
    label_space_size = len(resolved_label_space)

    return {
        "article_count": article_count,
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "micro": set_metrics_to_dict(micro),
        "macro": article_macro,
        "article_macro": article_macro,
        "label_macro": label_macro,
        "hamming_loss": round(
            _safe_ratio(total_fp + total_fn, article_count * label_space_size),
            6,
        ),
        "label_space_size": label_space_size,
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


def _label_macro(rows: Sequence[dict[str, Any]], label_space: Sequence[str]) -> dict[str, Any]:
    per_label: list[SetMetrics] = []
    for label in label_space:
        tp = fp = fn = 0
        for row in rows:
            expected = set(row["expected"])
            predicted = {item["ttp_id"] for item in row["predicted"]}
            if label in expected and label in predicted:
                tp += 1
            elif label not in expected and label in predicted:
                fp += 1
            elif label in expected and label not in predicted:
                fn += 1
        precision = _safe_ratio(tp, tp + fp)
        recall = _safe_ratio(tp, tp + fn)
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        per_label.append(SetMetrics(tp=tp, fp=fp, fn=fn, precision=precision, recall=recall, f1=f1))

    return {
        "precision": round(_mean(metric.precision for metric in per_label), 6),
        "recall": round(_mean(metric.recall for metric in per_label), 6),
        "f1": round(_mean(metric.f1 for metric in per_label), 6),
        "label_count": len(label_space),
    }


def _labels_from_rows(rows: Sequence[dict[str, Any]]) -> list[str]:
    labels: set[str] = set()
    for row in rows:
        labels.update(str(item) for item in row["expected"])
        labels.update(str(item["ttp_id"]) for item in row["predicted"])
    return sorted(labels)


def _mean(values: Sequence[float] | Any) -> float:
    materialized = list(values)
    if not materialized:
        return 0.0
    return sum(materialized) / len(materialized)


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _display_top_k(top_k: int | None) -> str:
    if top_k is None:
        return "none"
    return str(top_k)
