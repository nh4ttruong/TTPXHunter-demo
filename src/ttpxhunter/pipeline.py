from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Sequence

import nltk

from .paths import MODEL_ARTIFACTS_DIR
<<<<<<< HEAD
=======
from .preprocessing import PreprocessMode, SectionFilterMode, prepare_text
>>>>>>> feat/demo

if TYPE_CHECKING:
    import torch
    from transformers import RobertaForSequenceClassification, RobertaTokenizer

DEFAULT_MODEL_ID = "nanda-rani/TTPXHunter"
DEFAULT_THRESHOLD = 0.644
DEFAULT_LABEL_DICT = MODEL_ARTIFACTS_DIR / "label_dict.pkl"
DEFAULT_TTPID2NAME = MODEL_ARTIFACTS_DIR / "ttp_id_name.pkl"

OrderMode = Literal["first-seen", "sorted", "legacy-set"]


@dataclass(frozen=True)
class TTPResult:
    ttp_id: str
    name: str


<<<<<<< HEAD
=======
@dataclass(frozen=True)
class SentenceLabelPrediction:
    sentence: str
    label: str
    confidence: float


@dataclass(frozen=True)
class SentenceTTPPrediction:
    sentence: str
    label: str
    confidence: float
    ttp_id: str
    name: str


@dataclass(frozen=True)
class TTPEvidence:
    ttp_id: str
    name: str
    max_confidence: float
    support_sentence_count: int
    example_sentence: str


>>>>>>> feat/demo
def ensure_sentence_tokenizer() -> None:
    """Ensure NLTK sentence tokenizer data exists for old and new NLTK builds."""
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)

    try:
        nltk.sent_tokenize("A short sentence. Another one.")
    except LookupError as exc:
        if "punkt_tab" not in str(exc):
            raise
        nltk.download("punkt_tab", quiet=True)


def remove_consecutive_newlines(text: str) -> str:
    if not text:
        return text

    cleaned = [text[0]]
    for char in text[1:]:
        if char == "\n" and cleaned[-1] == "\n":
            continue
        cleaned.append(char)
    return "".join(cleaned)


<<<<<<< HEAD
def text_to_sentences(text: str) -> list[str]:
    ensure_sentence_tokenizer()

    cleaned = remove_consecutive_newlines(text)
=======
def text_to_sentences(
    text: str,
    preprocess: PreprocessMode = "none",
    section_filter: SectionFilterMode = "none",
) -> list[str]:
    ensure_sentence_tokenizer()

    cleaned = prepare_text(text, preprocess=preprocess, section_filter=section_filter)
    cleaned = remove_consecutive_newlines(cleaned)
>>>>>>> feat/demo
    cleaned = cleaned.replace("\t", " ").replace("\\'", "'")

    sentences: list[str] = []
    for sentence in nltk.sent_tokenize(cleaned):
        sentences.extend(line for line in sentence.split("\n") if line)
    return sentences


<<<<<<< HEAD
def report_to_sentences(report_path: str | Path) -> list[str]:
    return text_to_sentences(Path(report_path).read_text(encoding="utf-8"))
=======
def report_to_sentences(
    report_path: str | Path,
    preprocess: PreprocessMode = "none",
    section_filter: SectionFilterMode = "none",
) -> list[str]:
    return text_to_sentences(
        Path(report_path).read_text(encoding="utf-8"),
        preprocess=preprocess,
        section_filter=section_filter,
    )
>>>>>>> feat/demo


def resolve_device(device: str | None = None) -> torch.device:
    import torch

    if device:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model_and_tokenizer(
    model_id: str = DEFAULT_MODEL_ID,
    revision: str | None = None,
    device: str | torch.device | None = None,
) -> tuple[RobertaForSequenceClassification, RobertaTokenizer, torch.device]:
    from transformers import RobertaForSequenceClassification, RobertaTokenizer

    resolved_device = resolve_device(str(device) if device is not None else None)
    kwargs = {"revision": revision} if revision else {}

    model = RobertaForSequenceClassification.from_pretrained(model_id, **kwargs)
    tokenizer = RobertaTokenizer.from_pretrained(model_id, **kwargs)
    model.to(resolved_device)
    model.eval()
    return model, tokenizer, resolved_device


def predict_labels(
    sentences: Sequence[str],
    model: RobertaForSequenceClassification,
    tokenizer: RobertaTokenizer,
    device: torch.device,
    threshold: float = DEFAULT_THRESHOLD,
    batch_size: int = 16,
) -> list[str]:
<<<<<<< HEAD
    import torch

    predictions: list[str] = []
=======
    sentence_predictions = predict_sentence_labels(
        sentences=sentences,
        model=model,
        tokenizer=tokenizer,
        device=device,
        batch_size=batch_size,
    )
    return [
        prediction.label
        for prediction in sentence_predictions
        if prediction.confidence > threshold
    ]


def predict_sentence_labels(
    sentences: Sequence[str],
    model: RobertaForSequenceClassification,
    tokenizer: RobertaTokenizer,
    device: torch.device,
    batch_size: int = 16,
) -> list[SentenceLabelPrediction]:
    import torch

    predictions: list[SentenceLabelPrediction] = []
>>>>>>> feat/demo

    for start in range(0, len(sentences), batch_size):
        batch = list(sentences[start : start + batch_size])
        if not batch:
            continue

        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        ).to(device)

        with torch.inference_mode():
            outputs = model(**inputs)

        probabilities = torch.softmax(outputs.logits, dim=1)
        max_prob, predicted_class_indices = torch.max(probabilities, dim=1)

<<<<<<< HEAD
        for prob, class_idx in zip(max_prob, predicted_class_indices):
            if prob.item() > threshold:
                predictions.append(model.config.id2label[class_idx.item()])
=======
        for sentence, prob, class_idx in zip(batch, max_prob, predicted_class_indices):
            predictions.append(
                SentenceLabelPrediction(
                    sentence=sentence,
                    label=model.config.id2label[class_idx.item()],
                    confidence=float(prob.item()),
                )
            )
>>>>>>> feat/demo

    return predictions


def load_pickle(path: str | Path) -> Any:
    with Path(path).open("rb") as file:
        return pickle.load(file)


def predicted_labels_to_ttp_ids(
    predicted_labels: Sequence[str],
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    order: OrderMode = "first-seen",
) -> list[str]:
    label_dict = load_pickle(label_dict_path)
    inverted_label_dict = {int(value): str(key) for key, value in label_dict.items()}

    ttp_ids = []
    for label in predicted_labels:
        numeric_label = int(label.split("_", 1)[1])
        if numeric_label in inverted_label_dict:
            ttp_ids.append(inverted_label_dict[numeric_label])

    return unique_ttp_ids(ttp_ids, order=order)


<<<<<<< HEAD
=======
def sentence_labels_to_ttp_predictions(
    sentence_predictions: Sequence[SentenceLabelPrediction],
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
) -> list[SentenceTTPPrediction]:
    label_dict = load_pickle(label_dict_path)
    inverted_label_dict = {int(value): str(key) for key, value in label_dict.items()}
    id_to_name_map = load_pickle(ttpid2name_path)

    predictions: list[SentenceTTPPrediction] = []
    for prediction in sentence_predictions:
        numeric_label = int(prediction.label.split("_", 1)[1])
        ttp_id = inverted_label_dict.get(numeric_label)
        if ttp_id is None or ttp_id not in id_to_name_map:
            continue
        predictions.append(
            SentenceTTPPrediction(
                sentence=prediction.sentence,
                label=prediction.label,
                confidence=prediction.confidence,
                ttp_id=ttp_id,
                name=str(id_to_name_map[ttp_id]),
            )
        )
    return predictions


def aggregate_sentence_predictions(
    predictions: Sequence[SentenceTTPPrediction],
    threshold: float = DEFAULT_THRESHOLD,
    order: OrderMode = "first-seen",
    top_k: int | None = None,
) -> list[TTPResult]:
    evidence = aggregate_prediction_evidence(
        predictions=predictions,
        threshold=threshold,
        order=order,
        top_k=top_k,
    )
    return [TTPResult(ttp_id=item.ttp_id, name=item.name) for item in evidence]


def aggregate_prediction_evidence(
    predictions: Sequence[SentenceTTPPrediction],
    threshold: float = DEFAULT_THRESHOLD,
    order: OrderMode = "first-seen",
    top_k: int | None = None,
) -> list[TTPEvidence]:
    filtered = [prediction for prediction in predictions if prediction.confidence > threshold]
    if order == "sorted":
        ttp_order = sorted({prediction.ttp_id for prediction in filtered})
    elif order == "legacy-set":
        ttp_order = list({prediction.ttp_id for prediction in filtered})
    else:
        seen: set[str] = set()
        ttp_order = []
        for prediction in filtered:
            if prediction.ttp_id not in seen:
                seen.add(prediction.ttp_id)
                ttp_order.append(prediction.ttp_id)

    evidence: list[TTPEvidence] = []
    for ttp_id in ttp_order:
        supports = [prediction for prediction in filtered if prediction.ttp_id == ttp_id]
        if not supports:
            continue
        strongest = max(supports, key=lambda prediction: prediction.confidence)
        evidence.append(
            TTPEvidence(
                ttp_id=ttp_id,
                name=strongest.name,
                max_confidence=round(strongest.confidence, 6),
                support_sentence_count=len(supports),
                example_sentence=strongest.sentence,
            )
        )

    if top_k is not None:
        evidence = sorted(
            evidence,
            key=lambda item: (
                item.max_confidence,
                item.support_sentence_count,
                item.ttp_id,
            ),
            reverse=True,
        )[:top_k]
    return evidence


>>>>>>> feat/demo
def unique_ttp_ids(ttp_ids: Sequence[str], order: OrderMode = "first-seen") -> list[str]:
    if order == "legacy-set":
        return list(set(ttp_ids))
    if order == "sorted":
        return sorted(set(ttp_ids))

    seen: set[str] = set()
    unique_ids: list[str] = []
    for ttp_id in ttp_ids:
        if ttp_id not in seen:
            seen.add(ttp_id)
            unique_ids.append(ttp_id)
    return unique_ids


def load_label_space(label_dict_path: str | Path = DEFAULT_LABEL_DICT) -> set[str]:
    return {str(ttp_id) for ttp_id in load_pickle(label_dict_path).keys()}


def translate_ttp_ids_to_names(
    ttp_ids: Sequence[str],
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
) -> list[TTPResult]:
    id_to_name_map = load_pickle(ttpid2name_path)
    return [
        TTPResult(ttp_id=ttp_id, name=str(id_to_name_map[ttp_id]))
        for ttp_id in ttp_ids
        if ttp_id in id_to_name_map
    ]


def extract_ttp_from_sentences(
    sentences: Sequence[str],
    threshold: float = DEFAULT_THRESHOLD,
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
    model_id: str = DEFAULT_MODEL_ID,
    revision: str | None = None,
    device: str | None = None,
    order: OrderMode = "first-seen",
    batch_size: int = 16,
<<<<<<< HEAD
=======
    top_k: int | None = None,
>>>>>>> feat/demo
) -> list[TTPResult]:
    model, tokenizer, resolved_device = load_model_and_tokenizer(
        model_id=model_id,
        revision=revision,
        device=device,
    )
    return extract_ttp_from_sentences_with_model(
        sentences=sentences,
        model=model,
        tokenizer=tokenizer,
        device=resolved_device,
        threshold=threshold,
        label_dict_path=label_dict_path,
        ttpid2name_path=ttpid2name_path,
        order=order,
        batch_size=batch_size,
<<<<<<< HEAD
=======
        top_k=top_k,
>>>>>>> feat/demo
    )


def extract_ttp_from_sentences_with_model(
    sentences: Sequence[str],
    model: RobertaForSequenceClassification,
    tokenizer: RobertaTokenizer,
    device: torch.device,
    threshold: float = DEFAULT_THRESHOLD,
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
    order: OrderMode = "first-seen",
    batch_size: int = 16,
<<<<<<< HEAD
) -> list[TTPResult]:
    predicted_labels = predict_labels(
=======
    top_k: int | None = None,
) -> list[TTPResult]:
    sentence_label_predictions = predict_sentence_labels(
>>>>>>> feat/demo
        sentences=sentences,
        model=model,
        tokenizer=tokenizer,
        device=device,
<<<<<<< HEAD
        threshold=threshold,
        batch_size=batch_size,
    )
    ttp_ids = predicted_labels_to_ttp_ids(
        predicted_labels=predicted_labels,
        label_dict_path=label_dict_path,
        order=order,
    )
    return translate_ttp_ids_to_names(ttp_ids, ttpid2name_path=ttpid2name_path)
=======
        batch_size=batch_size,
    )
    sentence_ttp_predictions = sentence_labels_to_ttp_predictions(
        sentence_predictions=sentence_label_predictions,
        label_dict_path=label_dict_path,
        ttpid2name_path=ttpid2name_path,
    )
    return aggregate_sentence_predictions(
        predictions=sentence_ttp_predictions,
        threshold=threshold,
        order=order,
        top_k=top_k,
    )


def predict_ttp_for_sentences_with_model(
    sentences: Sequence[str],
    model: RobertaForSequenceClassification,
    tokenizer: RobertaTokenizer,
    device: torch.device,
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
    batch_size: int = 16,
) -> list[SentenceTTPPrediction]:
    sentence_label_predictions = predict_sentence_labels(
        sentences=sentences,
        model=model,
        tokenizer=tokenizer,
        device=device,
        batch_size=batch_size,
    )
    return sentence_labels_to_ttp_predictions(
        sentence_predictions=sentence_label_predictions,
        label_dict_path=label_dict_path,
        ttpid2name_path=ttpid2name_path,
    )
>>>>>>> feat/demo


def process_text_file_for_attack_patterns(
    report_path: str | Path,
    threshold: float = DEFAULT_THRESHOLD,
    label_dict_path: str | Path = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path = DEFAULT_TTPID2NAME,
    model_id: str = DEFAULT_MODEL_ID,
    revision: str | None = None,
    device: str | None = None,
    order: OrderMode = "first-seen",
    batch_size: int = 16,
<<<<<<< HEAD
) -> list[TTPResult]:
    sentences = report_to_sentences(report_path)
=======
    preprocess: PreprocessMode = "none",
    section_filter: SectionFilterMode = "none",
    top_k: int | None = None,
) -> list[TTPResult]:
    sentences = report_to_sentences(
        report_path,
        preprocess=preprocess,
        section_filter=section_filter,
    )
>>>>>>> feat/demo
    return extract_ttp_from_sentences(
        sentences=sentences,
        threshold=threshold,
        label_dict_path=label_dict_path,
        ttpid2name_path=ttpid2name_path,
        model_id=model_id,
        revision=revision,
        device=device,
        order=order,
        batch_size=batch_size,
<<<<<<< HEAD
=======
        top_k=top_k,
>>>>>>> feat/demo
    )


def results_to_payload(
    results: Sequence[TTPResult],
    report: str | Path | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    model_id: str = DEFAULT_MODEL_ID,
    revision: str | None = None,
    order: OrderMode = "first-seen",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "threshold": threshold,
        "model_id": model_id,
        "revision": revision,
        "order": order,
        "count": len(results),
        "results": [asdict(result) for result in results],
    }
    if report is not None:
        payload["report"] = str(report)
    return payload


def load_expected_results(path: str | Path) -> list[TTPResult]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        TTPResult(ttp_id=str(item["ttp_id"]), name=str(item["name"]))
        for item in payload["results"]
    ]


def compare_results(
    actual: Sequence[TTPResult],
    expected: Sequence[TTPResult],
) -> dict[str, Any]:
    actual_ids = [result.ttp_id for result in actual]
    expected_ids = [result.ttp_id for result in expected]
    actual_set = set(actual_ids)
    expected_set = set(expected_ids)

    return {
        "actual_count": len(actual),
        "expected_count": len(expected),
        "set_match": actual_set == expected_set,
        "order_match": actual_ids == expected_ids,
        "missing": sorted(expected_set - actual_set),
        "extra": sorted(actual_set - expected_set),
    }
