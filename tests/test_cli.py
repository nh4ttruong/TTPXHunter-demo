from ttpxhunter.cli import parse_args


def test_parse_infer_command() -> None:
<<<<<<< HEAD
    args = parse_args(["infer", "report.txt", "--batch-size", "4", "--json"])
=======
    args = parse_args(
        [
            "infer",
            "report.txt",
            "--batch-size",
            "4",
            "--report-md",
            "report.md",
            "--json",
        ]
    )
>>>>>>> feat/demo

    assert args.command == "infer"
    assert args.report == "report.txt"
    assert args.batch_size == 4
<<<<<<< HEAD
=======
    assert args.report_md == "report.md"
>>>>>>> feat/demo
    assert args.json is True


def test_parse_cisa_benchmark_command() -> None:
    args = parse_args(
        [
            "cisa",
            "benchmark",
            "dataset.json",
            "--limit",
            "3",
<<<<<<< HEAD
=======
            "--preprocess",
            "paper-ioc",
            "--section-filter",
            "cisa-attack-narrative",
            "--include-evidence",
            "--quiet",
>>>>>>> feat/demo
            "--rows-csv",
            "rows.csv",
        ]
    )

    assert args.command == "cisa"
    assert args.cisa_command == "benchmark"
    assert args.dataset == "dataset.json"
    assert args.limit == 3
<<<<<<< HEAD
    assert args.rows_csv == "rows.csv"
=======
    assert args.preprocess == "paper-ioc"
    assert args.section_filter == "cisa-attack-narrative"
    assert args.include_evidence is True
    assert args.quiet is True
    assert args.rows_csv == "rows.csv"


def test_parse_cisa_sweep_command() -> None:
    args = parse_args(
        [
            "cisa",
            "sweep",
            "dataset.json",
            "--thresholds",
            "0.7,0.8",
            "--top-k-values",
            "none,10",
            "--output",
            "sweep.csv",
            "--quiet",
        ]
    )

    assert args.command == "cisa"
    assert args.cisa_command == "sweep"
    assert args.thresholds == "0.7,0.8"
    assert args.top_k_values == "none,10"
    assert args.output == "sweep.csv"
    assert args.quiet is True


def test_parse_cisa_gap_report_command() -> None:
    args = parse_args(
        [
            "cisa",
            "gap-report",
            "dataset.json",
            "--output-md",
            "gap.md",
            "--charts-dir",
            "gap_charts",
        ]
    )

    assert args.command == "cisa"
    assert args.cisa_command == "gap-report"
    assert args.output_md == "gap.md"
    assert args.charts_dir == "gap_charts"


def test_parse_train_sentence_classifier_command() -> None:
    args = parse_args(
        [
            "train",
            "sentence-classifier",
            "--limit-per-class",
            "2",
            "--epochs",
            "1",
            "--quiet",
        ]
    )

    assert args.command == "train"
    assert args.train_command == "sentence-classifier"
    assert args.limit_per_class == 2
    assert args.epochs == 1
    assert args.quiet is True
>>>>>>> feat/demo
