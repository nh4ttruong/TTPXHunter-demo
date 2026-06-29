from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Sequence

import nltk

from .paths import MODEL_ARTIFACTS_DIR

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


def text_to_sentences(text: str) -> list[str]:
    ensure_sentence_tokenizer()

    cleaned = remove_consecutive_newlines(text)
    cleaned = cleaned.replace("\t", " ").replace("\\'", "'")

    sentences: list[str] = []
    for sentence in nltk.sent_tokenize(cleaned):
        sentences.extend(line for line in sentence.split("\n") if line)
    return sentences


def report_to_sentences(report_path: str | Path) -> list[str]:
    return text_to_sentences(Path(report_path).read_text(encoding="utf-8"))


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
    import torch

    predictions: list[str] = []

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

        for prob, class_idx in zip(max_prob, predicted_class_indices):
            if prob.item() > threshold:
                predictions.append(model.config.id2label[class_idx.item()])

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
) -> list[TTPResult]:
    predicted_labels = predict_labels(
        sentences=sentences,
        model=model,
        tokenizer=tokenizer,
        device=device,
        threshold=threshold,
        batch_size=batch_size,
    )
    ttp_ids = predicted_labels_to_ttp_ids(
        predicted_labels=predicted_labels,
        label_dict_path=label_dict_path,
        order=order,
    )
    return translate_ttp_ids_to_names(ttp_ids, ttpid2name_path=ttpid2name_path)


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
) -> list[TTPResult]:
    sentences = report_to_sentences(report_path)
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
