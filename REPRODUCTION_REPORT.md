# TTPXHunter Reproduction Report

## Scope

Original source:

`../TTPXHunter-Actionable-Threat-Intelligence-Extraction-as-TTPs-from-Finished-Cyber-Threat-Reports`

Rebuilt source:

`../ttpxhunter`

The goal was to reproduce the original notebook inference path for the
SharpPanda sample report.

## Original Pipeline

The original `TTPXHunter.ipynb` notebook does the following:

1. Imports `transformers`, `torch`, `pickle`, `os`, and `nltk`.
2. Downloads NLTK `punkt`.
3. Loads `RobertaForSequenceClassification` and `RobertaTokenizer` from
   `nanda-rani/TTPXHunter`.
4. Reads the SharpPanda report text file.
5. Collapses consecutive newlines, replaces tabs, sentence-tokenizes text, and
   splits sentences again by newline.
6. Runs one sentence at a time through the model with `max_length=256`.
7. Keeps predictions whose max softmax probability is greater than `0.644`.
8. Maps `LABEL_n` values back to MITRE ATT&CK IDs using `label_dict.pkl`.
9. Maps MITRE ATT&CK IDs to names using `ttp_id_name.pkl`.

The saved notebook output contains 19 TTPs.

## Rebuilt Source

The rebuilt folder adds:

- `src/ttpxhunter/pipeline.py`: reusable pipeline functions.
- `src/ttpxhunter/cli.py`: unified command-line runner for report inference and CISA operations.
- `src/ttpxhunter/paths.py`: centralized project path constants.
- `src/ttpxhunter/cisa_dataset.py`: CISA dataset download/load/normalization helpers.
- `src/ttpxhunter/cisa_pipeline.py`: batch benchmark pipeline for CISA articles.
- `src/ttpxhunter/cisa_reporting.py`: benchmark insight, report, CSV, and SVG chart writers.
- `docs/CISA_BENCHMARK_WORKFLOW.md`: explanation of the CISA-as-benchmark workflow.
- `tests/expected_sharppanda.json`: saved notebook baseline.
- `tests/test_pipeline.py`: fast offline tests.
- `tests/test_cisa_dataset.py`: CISA parsing, normalization, and metric tests.
- `tests/test_cli.py`: unified CLI parser tests.
- `tests/test_integration_sharppanda.py`: Hugging Face model reproduction test.
- `requirements.txt`: runtime/test dependencies.
- `requirements-lock.txt`: exact dependency versions used for this run.
- `results/sharppanda.json`: generated CLI reproduction output.
- `results/cisa/cisa_benchmark_full.json`: full CISA benchmark output.
- `results/cisa/cisa_benchmark_full_report.md`: readable CISA benchmark report.
- `results/cisa/cisa_benchmark_full_rows.csv`: flat per-article CISA metrics.
- `results/cisa/charts_full/*.svg`: SVG charts embedded in the CISA benchmark report.

The artifacts and sample data were copied from the original repo:

- `model_artifacts/label_dict.pkl`
- `model_artifacts/ttp_id_name.pkl`
- `examples/reports/SharpPanda_APT_Campaign_Expands_its_Arsenal_Targeting_G20_Nations.txt`
- `datasets/mitre_attack/MITRE_ATT&CK_Dataset.csv`

## Test Results

Fast tests:

```text
18 passed, 1 skipped in 0.49s
```

Full integration test:

```text
1 passed, 2 warnings in 97.72s
```

CLI reproduction:

```text
actual_count=19
expected_count=19
set_match=True
order_match=False
missing=[]
extra=[]
```

## CISA Dataset Pipeline

The CISA TTP Articles Data Set from Zenodo record `14659512` was added as a
batch benchmark source. The dataset contains 77 CISA advisories with `RawText`,
`TTP`, `CleanText`, and `URL` fields.

Dataset description after loading:

```text
article_count=77
raw_attack_id_count=1940
base_technique_count=1412
model_label_space_technique_count=1325
articles_with_no_raw_ttps=3
max_raw_ttps_per_article=158
max_base_ttps_per_article=103
```

Full benchmark configuration:

```text
dataset=datasets/cisa/CISA-crawl-rt-ttp-ct.json
text_field=clean
expected_mode=model-label-space
device=mps
batch_size=32
threshold=0.644
```

Full benchmark result:

```text
articles=77
expected=1325
predicted=2112
tp=516
fp=1596
fn=809
micro_precision=0.244318
micro_recall=0.389434
micro_f1=0.300262
macro_precision=0.210597
macro_recall=0.342080
macro_f1=0.242000
```

The improved CISA output now includes:

- A richer JSON payload with `technique_names`, `insights`, and generated
  artifact paths.
- Top missed expected techniques, top extra predictions, and top matches.
- Article-quality summary with exact-match count, no-expected count,
  no-prediction count, mean/median label counts, and mean/median sentence
  counts.
- Best and worst articles by F1 score.
- A Markdown report and a flat CSV for spreadsheet analysis.
- SVG charts for metrics, TP/FP/FN counts, top missing techniques, top extra
  predictions, and article-level F1 distribution.

CISA ground truth normalization is necessary because the dataset's regex can
produce tactics (`TA####`), sub-techniques (`T####.###`), and occasional invalid
matches such as five-digit technique-like IDs. Since the TTPXHunter model used
here predicts only base techniques in its 193-label space, the default CISA
benchmark drops tactics, collapses sub-techniques to parent `T####` IDs, removes
invalid IDs, and filters expected labels to the model label space.

## Comparison

The rebuilt source reproduces the original saved notebook at the meaningful
output level: same count and same set of 19 MITRE ATT&CK TTP IDs/names.

The printed order differs. This is expected because the notebook uses
`list(set(ttp_list))`, and Python set iteration order is not a stable
reproducibility target across processes or hash seeds. The rebuilt CLI therefore
defaults to deterministic `first-seen` order while retaining `--order
legacy-set` for notebook-code parity.

## Reproducibility Risks

- The original notebook does not pin package versions.
- The Hugging Face model revision is not pinned.
- The notebook downloads NLTK data at runtime.
- The original code has no tests or CLI.
- Pickle artifacts require compatible Python dependencies, including `numpy`.

## Verdict

Reproduction succeeded for the SharpPanda sample report. The rebuilt source is
more reproducible than the notebook because it has a clean CLI, explicit
dependencies, unit tests, a full model integration test, a saved expected
baseline, and deterministic default output ordering.
