from ttpxhunter.cli import parse_args


def test_parse_infer_command() -> None:
    args = parse_args(["infer", "report.txt", "--batch-size", "4", "--json"])

    assert args.command == "infer"
    assert args.report == "report.txt"
    assert args.batch_size == 4
    assert args.json is True


def test_parse_cisa_benchmark_command() -> None:
    args = parse_args(
        [
            "cisa",
            "benchmark",
            "dataset.json",
            "--limit",
            "3",
            "--rows-csv",
            "rows.csv",
        ]
    )

    assert args.command == "cisa"
    assert args.cisa_command == "benchmark"
    assert args.dataset == "dataset.json"
    assert args.limit == 3
    assert args.rows_csv == "rows.csv"
