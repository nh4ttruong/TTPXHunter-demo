# CISA Benchmark Workflow

## Purpose

This workflow uses the CISA TTP Articles Data Set as an external benchmark for
the TTPXHunter model.

In short:

```text
CISA advisory text
  -> TTPXHunter inference
  -> predicted MITRE ATT&CK techniques
  -> compare with CISA dataset labels
  -> precision / recall / F1 / missing / extra
```

So the CISA dataset is not used to validate itself. It provides:

- input text: CISA cybersecurity advisories;
- expected labels: ATT&CK IDs extracted from those advisories.

TTPXHunter provides:

- the model that predicts ATT&CK techniques from advisory text.

## Data Shape

The local files live in:

```text
datasets/cisa/
├── CISA-crawl-rt-ttp-ct.csv
└── CISA-crawl-rt-ttp-ct.json
```

Each article row has these fields:

| Field | Role |
| --- | --- |
| `RawText` | Crawled advisory text before stronger cleanup. |
| `CleanText` | Text used by default for model inference. |
| `TTP` | Expected ATT&CK IDs from the dataset. |
| `URL` | Source CISA advisory URL. |

The current dataset has 77 advisory rows.

## End-to-End Flow

### 1. Load Articles

The loader reads the JSON-lines or CSV file and turns every row into a
`CISAArticle`.

Relevant code:

```text
src/ttpxhunter/cisa_dataset.py
```

### 2. Choose Input Text

By default the benchmark uses `CleanText`.

```bash
--text-field clean
```

To test against the less-normalized crawl text:

```bash
--text-field raw
```

### 3. Parse Expected Labels

The `TTP` field is parsed into ATT&CK-like IDs.

Examples:

```text
T1059
T1071.002
TA0001
```

The raw labels may include tactics, base techniques, sub-techniques, and noisy
regex matches.

### 4. Normalize Labels

The current TTPXHunter model can emit base techniques only, such as `T1059`.

The default benchmark therefore normalizes CISA expected labels like this:

| Raw value | Default action |
| --- | --- |
| `TA0001` | Drop tactic. |
| `T1071.002` | Collapse to parent `T1071`. |
| `T1059` | Keep as base technique. |
| Invalid ATT&CK-like strings | Drop. |
| IDs outside model label space | Drop in `model-label-space` mode. |

Default expected-label mode:

```bash
--expected-mode model-label-space
```

Alternative:

```bash
--expected-mode all-base
```

`all-base` keeps every valid normalized base technique, including labels that
the current model cannot predict. This is stricter, but less fair for evaluating
this exact 193-class classifier.

### 5. Sentence Split

The selected article text is split into sentences with NLTK.

This mirrors the original TTPXHunter notebook behavior, but the productionized
pipeline batches sentences for faster inference.

Relevant code:

```text
src/ttpxhunter/pipeline.py
```

### 6. Run TTPXHunter Inference

For each article:

1. tokenize sentences with the Hugging Face tokenizer;
2. run `nanda-rani/TTPXHunter`;
3. keep predictions above the confidence threshold;
4. map `LABEL_n` back to ATT&CK IDs using `model_artifacts/label_dict.pkl`;
5. map IDs to names using `model_artifacts/ttp_id_name.pkl`;
6. deduplicate article-level predictions.

Default threshold:

```text
0.644
```

This value is preserved from the original notebook.

### 7. Compare Predicted vs Expected

For each article:

```text
matches = predicted ∩ expected
missing = expected - predicted
extra   = predicted - expected
```

Then the benchmark computes:

- true positives;
- false positives;
- false negatives;
- precision;
- recall;
- F1.

The report includes both micro and macro averages.

### 8. Export Results

The benchmark can write three main outputs:

| Artifact | Purpose |
| --- | --- |
| JSON | Complete machine-readable payload. |
| Markdown report | Human-readable benchmark report. |
| CSV rows | Flat per-article table for spreadsheet analysis. |

It can also generate SVG charts and embed them in the Markdown report.

## Commands

Describe the dataset:

```bash
python -m ttpxhunter cisa describe \
  datasets/cisa/CISA-crawl-rt-ttp-ct.json \
  --json
```

Run a quick smoke benchmark:

```bash
python -m ttpxhunter cisa benchmark \
  datasets/cisa/CISA-crawl-rt-ttp-ct.json \
  --limit 3 \
  --output results/cisa/cisa_benchmark_limit3.json \
  --report-md results/cisa/cisa_benchmark_limit3_report.md \
  --rows-csv results/cisa/cisa_benchmark_limit3_rows.csv \
  --charts-dir results/cisa/charts_limit3
```

Run the full benchmark:

```bash
python -m ttpxhunter cisa benchmark \
  datasets/cisa/CISA-crawl-rt-ttp-ct.json \
  --device mps \
  --batch-size 32 \
  --output results/cisa/cisa_benchmark_full.json \
  --report-md results/cisa/cisa_benchmark_full_report.md \
  --rows-csv results/cisa/cisa_benchmark_full_rows.csv \
  --charts-dir results/cisa/charts_full
```

## Current Full Benchmark Snapshot

Current saved configuration:

```text
text_field=clean
expected_mode=model-label-space
threshold=0.644
device=mps
batch_size=32
```

Current saved result:

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
```

## How To Read The Result

The current benchmark shows that TTPXHunter finds many relevant techniques, but
it over-predicts on long CISA advisories.

High false positives mean:

- the original threshold may be too permissive for CISA-style advisories;
- long advisories contain many general security descriptions that can trigger
  plausible but unsupported techniques;
- report-level evaluation is stricter than sentence-level extraction.

High false negatives mean:

- some expected CISA labels are not expressed in sentence forms the model
  recognizes;
- some CISA labels come from explicit ATT&CK tables rather than narrative
  evidence;
- sub-technique-to-parent normalization can still leave semantic mismatch.

## Key Files

```text
src/ttpxhunter/cisa_dataset.py      # load, parse, normalize CISA data
src/ttpxhunter/cisa_pipeline.py     # run model and compute metrics
src/ttpxhunter/cisa_reporting.py    # JSON insights, Markdown, CSV, SVG charts
src/ttpxhunter/cli.py               # unified CLI
results/cisa/                       # generated benchmark artifacts
```
