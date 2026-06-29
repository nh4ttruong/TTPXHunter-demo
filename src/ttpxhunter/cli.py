from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .cisa_dataset import (
    CISA_DEFAULT_JSON,
    download_cisa_dataset,
    load_cisa_articles,
    summarize_dataset,
)
from .cisa_pipeline import run_cisa_benchmark
from .cisa_reporting import (
    enhance_benchmark_payload,
    write_benchmark_charts,
    write_benchmark_markdown,
    write_benchmark_rows_csv,
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
    infer.add_argument("--compare", default=None, help="Expected JSON payload to compare against.")
    infer.add_argument("--output", default=None, help="Optional path to save the JSON payload.")
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
    benchmark.add_argument("--limit", type=int, default=None)
    benchmark.add_argument("--offset", type=int, default=0)
    benchmark.add_argument(
        "--expected-mode",
        choices=["model-label-space", "all-base"],
        default="model-label-space",
    )
    benchmark.add_argument("--text-field", choices=["clean", "raw"], default="clean")
    benchmark.add_argument("--output", default=None)
    benchmark.add_argument("--report-md", default=None)
    benchmark.add_argument("--rows-csv", default=None)
    benchmark.add_argument("--charts-dir", default=None)
    benchmark.add_argument("--top-n", type=int, default=15)
    benchmark.add_argument("--json", action="store_true")
    benchmark.set_defaults(handler=_run_cisa_benchmark)

    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def _add_inference_options(parser: argparse.ArgumentParser) -> None:
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
    )
    payload = results_to_payload(
        results,
        report=args.report,
        threshold=args.threshold,
        model_id=args.model_id,
        revision=args.revision,
        order=args.order,
    )

    if args.compare:
        expected = load_expected_results(args.compare)
        payload["comparison"] = compare_results(results, expected)

    if args.output:
        _write_json(payload, args.output)

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


def _write_json(payload: dict, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def _emit_cisa_payload(payload: dict, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
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


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
