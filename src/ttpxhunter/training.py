from __future__ import annotations

import csv
import json
import pickle
import random
from collections.abc import Callable
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from .paths import DATASETS_DIR, MODEL_ARTIFACTS_DIR
from .pipeline import DEFAULT_LABEL_DICT, DEFAULT_MODEL_ID, DEFAULT_TTPID2NAME, load_pickle, resolve_device

DEFAULT_MITRE_SENTENCE_DATASET = DATASETS_DIR / "mitre_attack" / "MITRE_ATT&CK_Dataset.csv"
DEFAULT_RETRAINED_MODEL_DIR = MODEL_ARTIFACTS_DIR / "retrained" / "ttpxhunter-mitre-continued"
ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class TrainingExample:
    sentence: str
    ttp_id: str
    label_id: int


def load_mitre_sentence_dataset(
    dataset_path: str | Path = DEFAULT_MITRE_SENTENCE_DATASET,
    label_dict_path: str | Path | None = DEFAULT_LABEL_DICT,
    limit_per_class: int | None = None,
) -> tuple[list[TrainingExample], dict[str, int], dict[str, str]]:
    rows = _read_training_rows(dataset_path)
    label_dict = _load_or_build_label_dict(rows, label_dict_path)
    name_map: dict[str, str] = {}
    examples: list[TrainingExample] = []
    counts: dict[str, int] = defaultdict(int)

    for row in rows:
        ttp_id = row["Technique ID"].strip()
        sentence = row["Sentences"].strip()
        if not ttp_id or not sentence or ttp_id not in label_dict:
            continue
        if limit_per_class is not None and counts[ttp_id] >= limit_per_class:
            continue
        counts[ttp_id] += 1
        name_map.setdefault(ttp_id, row["Technique Name"].strip())
        examples.append(
            TrainingExample(
                sentence=sentence,
                ttp_id=ttp_id,
                label_id=int(label_dict[ttp_id]),
            )
        )

    return examples, label_dict, name_map


def stratified_split(
    examples: Sequence[TrainingExample],
    validation_ratio: float = 0.2,
    seed: int = 13,
) -> tuple[list[TrainingExample], list[TrainingExample]]:
    rng = random.Random(seed)
    groups: dict[int, list[TrainingExample]] = defaultdict(list)
    for example in examples:
        groups[example.label_id].append(example)

    train: list[TrainingExample] = []
    validation: list[TrainingExample] = []
    for label_id in sorted(groups):
        group = list(groups[label_id])
        rng.shuffle(group)
        validation_count = int(round(len(group) * validation_ratio))
        if len(group) > 1:
            validation_count = max(1, min(validation_count, len(group) - 1))
        else:
            validation_count = 0
        validation.extend(group[:validation_count])
        train.extend(group[validation_count:])

    rng.shuffle(train)
    rng.shuffle(validation)
    return train, validation


def train_sentence_classifier(
    dataset_path: str | Path = DEFAULT_MITRE_SENTENCE_DATASET,
    base_model_id: str = DEFAULT_MODEL_ID,
    output_dir: str | Path = DEFAULT_RETRAINED_MODEL_DIR,
    label_dict_path: str | Path | None = DEFAULT_LABEL_DICT,
    ttpid2name_path: str | Path | None = DEFAULT_TTPID2NAME,
    revision: str | None = None,
    device: str | None = None,
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 1e-5,
    max_length: int = 256,
    validation_ratio: float = 0.2,
    seed: int = 13,
    limit_per_class: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    if progress_callback:
        progress_callback("loading training dependencies")
    import torch
    from torch.utils.data import DataLoader
    from transformers import RobertaForSequenceClassification, RobertaTokenizer

    if progress_callback:
        progress_callback(f"loading dataset={dataset_path}")
    examples, label_dict, dataset_name_map = load_mitre_sentence_dataset(
        dataset_path=dataset_path,
        label_dict_path=label_dict_path,
        limit_per_class=limit_per_class,
    )
    train_examples, validation_examples = stratified_split(
        examples,
        validation_ratio=validation_ratio,
        seed=seed,
    )
    if progress_callback:
        progress_callback(
            f"dataset ready examples={len(examples)} train={len(train_examples)} "
            f"validation={len(validation_examples)} labels={len(label_dict)}"
        )
    id_to_name = _load_name_map(ttpid2name_path, dataset_name_map)
    id2label = {int(index): f"LABEL_{int(index)}" for index in label_dict.values()}
    label2id = {label: index for index, label in id2label.items()}
    resolved_device = resolve_device(device)
    kwargs = {"revision": revision} if revision else {}

    if progress_callback:
        progress_callback(f"loading base model={base_model_id} device={resolved_device}")
    tokenizer = RobertaTokenizer.from_pretrained(base_model_id, **kwargs)
    model = RobertaForSequenceClassification.from_pretrained(
        base_model_id,
        num_labels=len(label_dict),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
        **kwargs,
    )
    model.to(resolved_device)

    def collate(batch: Sequence[TrainingExample]) -> dict[str, Any]:
        encoded = tokenizer(
            [example.sentence for example in batch],
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch.tensor(
            [example.label_id for example in batch],
            dtype=torch.long,
        )
        return {key: value.to(resolved_device) for key, value in encoded.items()}

    generator = torch.Generator()
    generator.manual_seed(seed)
    train_loader = DataLoader(
        train_examples,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate,
        generator=generator,
    )
    validation_loader = DataLoader(
        validation_examples,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    history: list[dict[str, Any]] = []
    for epoch in range(1, epochs + 1):
        if progress_callback:
            progress_callback(f"epoch {epoch}/{epochs} training start")
        model.train()
        total_loss = 0.0
        train_batches = 0
        for batch in train_loader:
            optimizer.zero_grad(set_to_none=True)
            outputs = model(**batch)
            outputs.loss.backward()
            optimizer.step()
            total_loss += float(outputs.loss.item())
            train_batches += 1

        validation_metrics = _evaluate_model(model, validation_loader)
        epoch_summary = {
            "epoch": epoch,
            "train_loss": round(total_loss / max(train_batches, 1), 6),
            **validation_metrics,
        }
        history.append(epoch_summary)
        if progress_callback:
            progress_callback(
                f"epoch {epoch}/{epochs} done train_loss={epoch_summary['train_loss']} "
                f"validation_loss={epoch_summary['validation_loss']} "
                f"validation_accuracy={epoch_summary['validation_accuracy']}"
            )

    output_path = Path(output_dir)
    if progress_callback:
        progress_callback(f"saving model to {output_path}")
    output_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    with (output_path / "label_dict.pkl").open("wb") as file:
        pickle.dump(label_dict, file)
    with (output_path / "ttp_id_name.pkl").open("wb") as file:
        pickle.dump(id_to_name, file)

    summary = {
        "dataset_path": str(dataset_path),
        "base_model_id": base_model_id,
        "revision": revision,
        "output_dir": str(output_path),
        "device": str(resolved_device),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "max_length": max_length,
        "validation_ratio": validation_ratio,
        "seed": seed,
        "limit_per_class": limit_per_class,
        "train_examples": len(train_examples),
        "validation_examples": len(validation_examples),
        "label_count": len(label_dict),
        "history": history,
    }
    (output_path / "training_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _read_training_rows(dataset_path: str | Path) -> list[dict[str, str]]:
    with Path(dataset_path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required = {"Technique ID", "Technique Name", "Sentences"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                "training dataset must contain columns: Technique ID, Technique Name, Sentences"
            )
        return list(reader)


def _load_or_build_label_dict(
    rows: Sequence[dict[str, str]],
    label_dict_path: str | Path | None,
) -> dict[str, int]:
    if label_dict_path is not None:
        return {str(key): int(value) for key, value in load_pickle(label_dict_path).items()}
    return {
        ttp_id: index
        for index, ttp_id in enumerate(sorted({row["Technique ID"].strip() for row in rows}))
        if ttp_id
    }


def _load_name_map(
    ttpid2name_path: str | Path | None,
    fallback: dict[str, str],
) -> dict[str, str]:
    if ttpid2name_path is None:
        return dict(fallback)
    try:
        return {str(key): str(value) for key, value in load_pickle(ttpid2name_path).items()}
    except FileNotFoundError:
        return dict(fallback)


def _evaluate_model(model: Any, validation_loader: Any) -> dict[str, float]:
    import torch

    model.eval()
    total_loss = 0.0
    batches = 0
    correct = 0
    total = 0
    with torch.inference_mode():
        for batch in validation_loader:
            outputs = model(**batch)
            total_loss += float(outputs.loss.item())
            batches += 1
            predictions = torch.argmax(outputs.logits, dim=1)
            correct += int((predictions == batch["labels"]).sum().item())
            total += int(batch["labels"].numel())
    return {
        "validation_loss": round(total_loss / max(batches, 1), 6),
        "validation_accuracy": round(correct / total, 6) if total else 0.0,
    }


def training_examples_to_dicts(examples: Sequence[TrainingExample]) -> list[dict[str, Any]]:
    return [asdict(example) for example in examples]
