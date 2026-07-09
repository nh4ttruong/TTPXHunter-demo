from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .cisa_dataset import (
    CISA_DEFAULT_JSON,
    download_cisa_dataset,
    load_cisa_articles,
    summarize_dataset,
)
from .cisa_pipeline import run_cisa_benchmark, run_cisa_sweep
from .cisa_reporting import (
    enhance_benchmark_payload,
    write_comparison_charts,
    write_comparison_markdown,
    write_benchmark_charts,
    write_benchmark_markdown,
    write_benchmark_rows_csv,
    write_sweep_markdown,
    write_sweep_rows_csv,
)

from .pipeline import (
    DEFAULT_LABEL_DICT,
    DEFAULT_MODEL_ID,
    DEFAULT_THRESHOLD,
    DEFAULT_TTPID2NAME,
    compare_results,
    load_expected_results,
    load_label_space,
    process_text_file_for_attack_patterns,
    results_to_payload,
)
from .reporting import write_inference_markdown
from .training import (
    DEFAULT_MITRE_SENTENCE_DATASET,
    DEFAULT_RETRAINED_MODEL_DIR,
    train_sentence_classifier,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run TTPXHunter reproduction inference and CISA benchmarks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    infer = subparsers.add_parser(
        "infer",
        help="Extract MITRE ATT&CK techniques from a threat report.",
    )
    infer.add_argument("report", help="Path to a finished cyber threat report text file.")
    _add_inference_options(infer)
    _add_text_processing_options(infer)
    infer.add_argument("--top-k", type=int, default=None)
    infer.add_argument("--compare", default=None, help="Expected JSON payload to compare against.")
    infer.add_argument("--output", default=None, help="Optional path to save the JSON payload.")
    infer.add_argument("--report-md", default=None, help="Optional path to save a Markdown report.")
    infer.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    infer.set_defaults(handler=_run_infer)

    cisa = subparsers.add_parser(
        "cisa",
        help="Download, inspect, and benchmark the CISA TTP Articles Data Set.",
    )
    cisa_subparsers = cisa.add_subparsers(dest="cisa_command", required=True)

    download = cisa_subparsers.add_parser("download", help="Download the CISA dataset.")
    download.add_argument("--out-dir", default=str(CISA_DEFAULT_JSON.parent))
    download.add_argument("--format", choices=["json", "csv", "both"], default="both")
    download.add_argument("--overwrite", action="store_true")
    download.add_argument("--json", action="store_true")
    download.set_defaults(handler=_run_cisa_download)

    describe = cisa_subparsers.add_parser("describe", help="Describe the CISA dataset.")
    describe.add_argument("dataset", nargs="?", default=str(CISA_DEFAULT_JSON))
    describe.add_argument("--label-dict", default=str(DEFAULT_LABEL_DICT))
    describe.add_argument("--json", action="store_true")
    describe.set_defaults(handler=_run_cisa_describe)

    benchmark = cisa_subparsers.add_parser(
        "benchmark",
        help="Run the TTPXHunter model against CISA articles.",
    )
    benchmark.add_argument("dataset", nargs="?", default=str(CISA_DEFAULT_JSON))
    _add_inference_options(benchmark)
    _add_text_processing_options(benchmark)
    benchmark.add_argument("--limit", type=int, default=None)
    benchmark.add_argument("--offset", type=int, default=0)
    benchmark.add_argument(
        "--expected-mode",
        choices=["model-label-space", "all-base"],
        default="model-label-space",
    )
    benchmark.add_argument("--text-field", choices=["clean", "raw"], default="clean")
    benchmark.add_argument("--top-k", type=int, default=None)
    benchmark.add_argument("--include-evidence", action="store_true")
    benchmark.add_argument("--output", default=None)
    benchmark.add_argument("--report-md", default=None)
    benchmark.add_argument("--rows-csv", default=None)
    benchmark.add_argument("--charts-dir", default=None)
    benchmark.add_argument("--top-n", type=int, default=15)
    _add_progress_options(benchmark)
    benchmark.add_argument("--json", action="store_true")
    benchmark.set_defaults(handler=_run_cisa_benchmark)

    sweep = cisa_subparsers.add_parser(
        "sweep",
        help="Run one CISA model pass and evaluate threshold/top-k calibration variants.",
    )
    sweep.add_argument("dataset", nargs="?", default=str(CISA_DEFAULT_JSON))
    _add_inference_options(sweep, include_threshold=False)
    _add_text_processing_options(sweep)
    sweep.add_argument("--limit", type=int, default=None)
    sweep.add_argument("--offset", type=int, default=0)
    sweep.add_argument(
        "--expected-mode",
        choices=["model-label-space", "all-base"],
        default="model-label-space",
    )
    sweep.add_argument("--text-field", choices=["clean", "raw"], default="clean")
    sweep.add_argument("--thresholds", default="0.644,0.70,0.75,0.80,0.85,0.90")
    sweep.add_argument("--top-k-values", default="none,10,15,20,25,30")
    sweep.add_argument("--output", default=None, help="Optional CSV path for sweep rows.")
    sweep.add_argument("--report-md", default=None)
    _add_progress_options(sweep)
    sweep.add_argument("--json", action="store_true")
    sweep.set_defaults(handler=_run_cisa_sweep)

    gap_report = cisa_subparsers.add_parser(
        "gap-report",
        help="Run baseline, IOC, and IOC+section-filter CISA variants and compare them.",
    )
    gap_report.add_argument("dataset", nargs="?", default=str(CISA_DEFAULT_JSON))
    _add_inference_options(gap_report)
    gap_report.add_argument("--limit", type=int, default=None)
    gap_report.add_argument("--offset", type=int, default=0)
    gap_report.add_argument(
        "--expected-mode",
        choices=["model-label-space", "all-base"],
        default="model-label-space",
    )
    gap_report.add_argument("--text-field", choices=["clean", "raw"], default="clean")
    gap_report.add_argument("--top-k", type=int, default=None)
    gap_report.add_argument("--output-md", default="results/cisa/cisa_gap_comparison.md")
    gap_report.add_argument(
        "--charts-dir",
        default=None,
        help="Directory for comparison SVG charts. Defaults beside --output-md.",
    )
    _add_progress_options(gap_report)
    gap_report.add_argument("--json", action="store_true")
    gap_report.set_defaults(handler=_run_cisa_gap_report)

    compare_models = cisa_subparsers.add_parser(
        "compare-models",
        help="Compare original and retrained models on baseline and filtered CISA variants.",
    )
    compare_models.add_argument("dataset", nargs="?", default=str(CISA_DEFAULT_JSON))
    _add_inference_options(compare_models)
    compare_models.add_argument("--limit", type=int, default=None)
    compare_models.add_argument("--offset", type=int, default=0)
    compare_models.add_argument(
        "--expected-mode",
        choices=["model-label-space", "all-base"],
        default="model-label-space",
    )
    compare_models.add_argument("--text-field", choices=["clean", "raw"], default="clean")
    compare_models.add_argument("--top-k", type=int, default=None)
    compare_models.add_argument("--retrained-model", default=str(DEFAULT_RETRAINED_MODEL_DIR))
    compare_models.add_argument(
        "--retrained-label-dict",
        default=str(DEFAULT_RETRAINED_MODEL_DIR / "label_dict.pkl"),
    )
    compare_models.add_argument(
        "--retrained-ttpid2name",
        default=str(DEFAULT_RETRAINED_MODEL_DIR / "ttp_id_name.pkl"),
    )
    compare_models.add_argument("--output-md", default="results/cisa/cisa_model_comparison.md")
    compare_models.add_argument(
        "--charts-dir",
        default=None,
        help="Directory for comparison SVG charts. Defaults beside --output-md.",
    )
    _add_progress_options(compare_models)
    compare_models.add_argument("--json", action="store_true")
    compare_models.set_defaults(handler=_run_cisa_compare_models)

    train = subparsers.add_parser("train", help="Experimental model training commands.")
    train_subparsers = train.add_subparsers(dest="train_command", required=True)
    sentence_classifier = train_subparsers.add_parser(
        "sentence-classifier",
        help="Continued fine-tune the TTPXHunter sentence classifier.",
    )
    sentence_classifier.add_argument("--dataset", default=str(DEFAULT_MITRE_SENTENCE_DATASET))
    sentence_classifier.add_argument("--base-model-id", default=DEFAULT_MODEL_ID)
    sentence_classifier.add_argument("--revision", default=None)
    sentence_classifier.add_argument("--device", default=None)
    sentence_classifier.add_argument("--output-dir", default=str(DEFAULT_RETRAINED_MODEL_DIR))
    sentence_classifier.add_argument("--label-dict", default=str(DEFAULT_LABEL_DICT))
    sentence_classifier.add_argument("--ttpid2name", default=str(DEFAULT_TTPID2NAME))
    sentence_classifier.add_argument("--epochs", type=int, default=3)
    sentence_classifier.add_argument("--batch-size", type=int, default=16)
    sentence_classifier.add_argument("--learning-rate", type=float, default=1e-5)
    sentence_classifier.add_argument("--max-length", type=int, default=256)
    sentence_classifier.add_argument("--validation-ratio", type=float, default=0.2)
    sentence_classifier.add_argument("--seed", type=int, default=13)
    sentence_classifier.add_argument("--limit-per-class", type=int, default=None)
    _add_progress_options(sentence_classifier)
    sentence_classifier.add_argument("--json", action="store_true")
    sentence_classifier.set_defaults(handler=_run_train_sentence_classifier)

    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def _add_inference_options(
    parser: argparse.ArgumentParser,
    include_threshold: bool = True,
) -> None:
    if include_threshold:
        parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--device", default=None, help="Torch device, e.g. cpu, cuda, or mps.")
    parser.add_argument("--label-dict", default=str(DEFAULT_LABEL_DICT))
    parser.add_argument("--ttpid2name", default=str(DEFAULT_TTPID2NAME))
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--order",
        choices=["first-seen", "sorted", "legacy-set"],
        default="first-seen",
        help="Unique TTP ordering. legacy-set mirrors the notebook's nondeterministic set conversion.",
    )


def _add_text_processing_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--preprocess", choices=["none", "paper-ioc"], default="none")
    parser.add_argument(
        "--section-filter",
        choices=["none", "cisa-attack-narrative"],
        default="none",
    )


def _add_progress_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress logs. Final summaries and requested outputs are still written.",
    )


def _run_infer(args: argparse.Namespace) -> None:
    results = process_text_file_for_attack_patterns(
        report_path=args.report,
        threshold=args.threshold,
        label_dict_path=args.label_dict,
        ttpid2name_path=args.ttpid2name,
        model_id=args.model_id,
        revision=args.revision,
        device=args.device,
        order=args.order,
        batch_size=args.batch_size,
        preprocess=args.preprocess,
        section_filter=args.section_filter,
        top_k=args.top_k,
    )
    payload = results_to_payload(
        results,
        report=args.report,
        threshold=args.threshold,
        model_id=args.model_id,
        revision=args.revision,
        order=args.order,
    )
    payload["preprocess"] = args.preprocess
    payload["section_filter"] = args.section_filter
    payload["top_k"] = args.top_k

    if args.compare:
        expected = load_expected_results(args.compare)
        payload["comparison"] = compare_results(results, expected)

    if args.output:
        _write_json(payload, args.output)
    if args.report_md:
        write_inference_markdown(payload, args.report_md)

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(len(results))
    for result in results:
        print(f"{result.ttp_id} - {result.name}")
    if "comparison" in payload:
        comparison = payload["comparison"]
        print(
            "comparison: "
            f"set_match={comparison['set_match']} "
            f"order_match={comparison['order_match']} "
            f"missing={comparison['missing']} "
            f"extra={comparison['extra']}"
        )


def _run_cisa_download(args: argparse.Namespace) -> None:
    paths = download_cisa_dataset(
        out_dir=args.out_dir,
        file_format=args.format,
        overwrite=args.overwrite,
    )
    _emit_cisa_payload({"files": [str(path) for path in paths]}, as_json=args.json)


def _run_cisa_describe(args: argparse.Namespace) -> None:
    articles = load_cisa_articles(args.dataset)
    payload = summarize_dataset(articles, label_space=load_label_space(args.label_dict))
    _emit_cisa_payload(payload, as_json=args.json)


def _run_cisa_benchmark(args: argparse.Namespace) -> None:
    progress_callback = _progress_callback(args.quiet)
    payload = run_cisa_benchmark(
        dataset_path=args.dataset,
        threshold=args.threshold,
        label_dict_path=args.label_dict,
        ttpid2name_path=args.ttpid2name,
        model_id=args.model_id,
        revision=args.revision,
        device=args.device,
        order=args.order,
        batch_size=args.batch_size,
        limit=args.limit,
        offset=args.offset,
        expected_mode=args.expected_mode,
        text_field=args.text_field,
        preprocess=args.preprocess,
        section_filter=args.section_filter,
        top_k=args.top_k,
        include_evidence=args.include_evidence,
        progress_callback=progress_callback,
    )
    payload = enhance_benchmark_payload(payload, top_n=args.top_n)
    payload["artifacts"] = {}
    if args.output:
        payload["artifacts"]["json"] = args.output
    if args.report_md:
        payload["artifacts"]["markdown_report"] = args.report_md
    if args.rows_csv:
        payload["artifacts"]["rows_csv"] = args.rows_csv
    if args.charts_dir:
        chart_paths = write_benchmark_charts(payload, args.charts_dir)
        for label, path in chart_paths.items():
            payload["artifacts"][label] = str(path)

    if args.output:
        _write_json(payload, args.output)
    if args.report_md:
        write_benchmark_markdown(payload, args.report_md)
    if args.rows_csv:
        write_benchmark_rows_csv(payload, args.rows_csv)
    _emit_cisa_payload(payload, as_json=args.json)


def _run_cisa_sweep(args: argparse.Namespace) -> None:
    progress_callback = _progress_callback(args.quiet)
    payload = run_cisa_sweep(
        dataset_path=args.dataset,
        thresholds=_parse_float_list(args.thresholds),
        top_ks=_parse_top_k_list(args.top_k_values),
        label_dict_path=args.label_dict,
        ttpid2name_path=args.ttpid2name,
        model_id=args.model_id,
        revision=args.revision,
        device=args.device,
        order=args.order,
        batch_size=args.batch_size,
        limit=args.limit,
        offset=args.offset,
        expected_mode=args.expected_mode,
        text_field=args.text_field,
        preprocess=args.preprocess,
        section_filter=args.section_filter,
        progress_callback=progress_callback,
    )
    payload["artifacts"] = {}
    if args.output:
        write_sweep_rows_csv(payload, args.output)
        payload["artifacts"]["sweep_csv"] = args.output
    if args.report_md:
        write_sweep_markdown(payload, args.report_md)
        payload["artifacts"]["markdown_report"] = args.report_md
    _emit_cisa_payload(payload, as_json=args.json)


def _run_cisa_gap_report(args: argparse.Namespace) -> None:
    progress_callback = _progress_callback(args.quiet)
    variants = [
        ("baseline", "none", "none"),
        ("paper-ioc", "paper-ioc", "none"),
        ("paper-ioc + CISA section filter", "paper-ioc", "cisa-attack-narrative"),
    ]
    items = []
    for label, preprocess, section_filter in variants:
        if progress_callback:
            progress_callback(f"gap-report variant={label} start")
        payload = run_cisa_benchmark(
            dataset_path=args.dataset,
            threshold=args.threshold,
            label_dict_path=args.label_dict,
            ttpid2name_path=args.ttpid2name,
            model_id=args.model_id,
            revision=args.revision,
            device=args.device,
            order=args.order,
            batch_size=args.batch_size,
            limit=args.limit,
            offset=args.offset,
            expected_mode=args.expected_mode,
            text_field=args.text_field,
            preprocess=preprocess,  # type: ignore[arg-type]
            section_filter=section_filter,  # type: ignore[arg-type]
            top_k=args.top_k,
            progress_callback=progress_callback,
        )
        items.append({"label": label, "payload": payload})
        if progress_callback:
            progress_callback(f"gap-report variant={label} done")
    chart_artifacts = _write_comparison_chart_artifacts(items, args.output_md, args.charts_dir)
    write_comparison_markdown(
        "CISA Gap Comparison",
        items,
        args.output_md,
        artifacts=chart_artifacts,
    )
    result = {
        "items": items,
        "artifacts": {"markdown_report": args.output_md, **chart_artifacts},
    }
    _emit_cisa_payload(result, as_json=args.json)


def _run_cisa_compare_models(args: argparse.Namespace) -> None:
    progress_callback = _progress_callback(args.quiet)
    retrained_model = Path(args.retrained_model)
    if not retrained_model.exists():
        raise FileNotFoundError(
            f"retrained model does not exist: {retrained_model}. "
            "Run `ttpxhunter train sentence-classifier` first."
        )

    variants = [
        (
            "original baseline",
            args.model_id,
            args.label_dict,
            args.ttpid2name,
            "none",
            "none",
        ),
        (
            "original paper-ioc + CISA section filter",
            args.model_id,
            args.label_dict,
            args.ttpid2name,
            "paper-ioc",
            "cisa-attack-narrative",
        ),
        (
            "retrained baseline",
            str(retrained_model),
            args.retrained_label_dict,
            args.retrained_ttpid2name,
            "none",
            "none",
        ),
        (
            "retrained paper-ioc + CISA section filter",
            str(retrained_model),
            args.retrained_label_dict,
            args.retrained_ttpid2name,
            "paper-ioc",
            "cisa-attack-narrative",
        ),
    ]
    items = []
    for label, model_id, label_dict, ttpid2name, preprocess, section_filter in variants:
        if progress_callback:
            progress_callback(f"compare-models variant={label} start")
        payload = run_cisa_benchmark(
            dataset_path=args.dataset,
            threshold=args.threshold,
            label_dict_path=label_dict,
            ttpid2name_path=ttpid2name,
            model_id=model_id,
            revision=args.revision if model_id == args.model_id else None,
            device=args.device,
            order=args.order,
            batch_size=args.batch_size,
            limit=args.limit,
            offset=args.offset,
            expected_mode=args.expected_mode,
            text_field=args.text_field,
            preprocess=preprocess,  # type: ignore[arg-type]
            section_filter=section_filter,  # type: ignore[arg-type]
            top_k=args.top_k,
            progress_callback=progress_callback,
        )
        items.append({"label": label, "payload": payload})
        if progress_callback:
            progress_callback(f"compare-models variant={label} done")
    chart_artifacts = _write_comparison_chart_artifacts(items, args.output_md, args.charts_dir)
    write_comparison_markdown(
        "CISA Model Comparison",
        items,
        args.output_md,
        artifacts=chart_artifacts,
    )
    result = {
        "items": items,
        "artifacts": {"markdown_report": args.output_md, **chart_artifacts},
    }
    _emit_cisa_payload(result, as_json=args.json)


def _run_train_sentence_classifier(args: argparse.Namespace) -> None:
    progress_callback = _progress_callback(args.quiet)
    summary = train_sentence_classifier(
        dataset_path=args.dataset,
        base_model_id=args.base_model_id,
        output_dir=args.output_dir,
        label_dict_path=args.label_dict,
        ttpid2name_path=args.ttpid2name,
        revision=args.revision,
        device=args.device,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
        validation_ratio=args.validation_ratio,
        seed=args.seed,
        limit_per_class=args.limit_per_class,
        progress_callback=progress_callback,
    )
    if args.json:
        print(json.dumps(summary, indent=2))
        return
    print("Training complete")
    print(f"  Output: {summary['output_dir']}")
    print(f"  Train examples: {summary['train_examples']}")
    print(f"  Validation examples: {summary['validation_examples']}")
    if summary["history"]:
        last = summary["history"][-1]
        print(
            f"  Last epoch: train_loss={last['train_loss']} "
            f"validation_loss={last['validation_loss']} "
            f"validation_accuracy={last['validation_accuracy']}"
        )


def _write_json(payload: dict, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def _emit_cisa_payload(payload: dict, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
        return

    if "sweep_rows" in payload:
        rows = sorted(payload["sweep_rows"], key=lambda row: row["micro_f1"], reverse=True)
        print("CISA threshold/top-k sweep")
        for row in rows[:10]:
            print(
                f"  threshold={row['threshold']} top_k={row['top_k']} "
                f"micro_f1={row['micro_f1']:.6f} "
                f"precision={row['micro_precision']:.6f} recall={row['micro_recall']:.6f} "
                f"hamming_loss={row['hamming_loss']:.6f}"
            )
        artifacts = payload.get("artifacts", {})
        if artifacts:
            print("  Wrote:")
            for label, path in artifacts.items():
                print(f"    {label}: {path}")
        return

    if "items" in payload:
        print("CISA comparison")
        for item in payload["items"]:
            aggregate = item["payload"]["aggregate"]
            micro = aggregate["micro"]
            print(
                f"  {item['label']}: micro_f1={micro['f1']:.6f} "
                f"precision={micro['precision']:.6f} recall={micro['recall']:.6f} "
                f"hamming_loss={aggregate.get('hamming_loss', 0.0):.6f}"
            )
        artifacts = payload.get("artifacts", {})
        if artifacts:
            print("  Wrote:")
            for label, path in artifacts.items():
                print(f"    {label}: {path}")
        return

    if "aggregate" in payload:
        dataset = payload["dataset"]
        model = payload["model"]
        aggregate = payload["aggregate"]
        micro = aggregate["micro"]
        macro = aggregate["macro"]
        insights = payload.get("insights", {})
        quality = insights.get("article_quality", {})
        print("CISA TTPXHunter benchmark")
        print(
            f"  Dataset: {dataset['evaluated_articles']}/{dataset['total_articles']} articles, "
            f"text={dataset['text_field']}, expected={dataset['expected_mode']}"
        )
        print(
            f"  Model: {model['model_id']} threshold={model['threshold']} "
            f"device={model['device']} batch_size={model['batch_size']}"
        )
        print(
            f"  Labels: expected={aggregate['expected_count']} "
            f"predicted={aggregate['predicted_count']} "
            f"tp={aggregate['tp']} fp={aggregate['fp']} fn={aggregate['fn']}"
        )
        print(
            f"  Micro: precision={micro['precision']:.6f} "
            f"recall={micro['recall']:.6f} f1={micro['f1']:.6f}"
        )
        print(
            f"  Macro: precision={macro['precision']:.6f} "
            f"recall={macro['recall']:.6f} f1={macro['f1']:.6f}"
        )
        label_macro = aggregate.get("label_macro")
        if label_macro:
            print(
                f"  Label macro: precision={label_macro['precision']:.6f} "
                f"recall={label_macro['recall']:.6f} f1={label_macro['f1']:.6f}"
            )
        if "hamming_loss" in aggregate:
            print(f"  Hamming loss: {aggregate['hamming_loss']:.6f}")
        if quality:
            print(
                f"  Articles: exact={quality['exact_match_articles']} "
                f"no_expected={quality['articles_with_no_expected']} "
                f"no_predictions={quality['articles_with_no_predictions']}"
            )
        for label, key in [
            ("Top missing", "top_missing"),
            ("Top extra", "top_extra"),
            ("Top matches", "top_matches"),
        ]:
            items = insights.get(key, [])[:5]
            if items:
                compact = ", ".join(
                    f"{item['ttp_id']}({item['count']})" for item in items
                )
                print(f"  {label}: {compact}")
        artifacts = payload.get("artifacts", {})
        if artifacts:
            print("  Wrote:")
            for label, path in artifacts.items():
                print(f"    {label}: {path}")
        return

    for key, value in payload.items():
        print(f"{key}: {value}")


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _parse_top_k_list(value: str) -> list[int | None]:
    parsed: list[int | None] = []
    for item in value.split(","):
        token = item.strip().lower()
        if not token:
            continue
        if token in {"none", "null", "-"}:
            parsed.append(None)
        else:
            parsed.append(int(token))
    return parsed


def _write_comparison_chart_artifacts(
    items: Sequence[dict],
    output_md: str,
    charts_dir: str | None,
) -> dict[str, str]:
    report_path = Path(output_md)
    resolved_charts_dir = (
        Path(charts_dir)
        if charts_dir is not None
        else report_path.with_suffix("").parent / f"{report_path.stem}_charts"
    )
    chart_paths = write_comparison_charts(items, resolved_charts_dir)
    return {
        key: _relative_path_for_markdown(path, report_path.parent)
        for key, path in chart_paths.items()
    }


def _relative_path_for_markdown(path: Path, report_dir: Path) -> str:
    try:
        return str(path.relative_to(report_dir))
    except ValueError:
        return str(path)


def _progress_callback(quiet: bool):
    if quiet:
        return None

    def emit(message: str) -> None:
        print(f"[progress] {message}", file=sys.stderr, flush=True)

    return emit


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
