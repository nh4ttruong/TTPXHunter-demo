# CISA TTPXHunter Benchmark Report

## Run Configuration

| Field | Value |
| --- | --- |
| Dataset | `datasets/cisa/CISA-crawl-rt-ttp-ct.json` |
| Zenodo record | `14659512` |
| DOI | `10.5281/zenodo.14659512` |
| Articles evaluated | 77 / 77 |
| Text field | `clean` |
| Expected mode | `model-label-space` |
| Preprocess | `paper-ioc` |
| Section filter | `none` |
| Model | `nanda-rani/TTPXHunter` |
| Revision | `not pinned` |
| Threshold | 0.644 |
| Top-k | none |
| Device | `cpu` |
| Batch size | 16 |

## Aggregate Metrics

| Metric | Value |
| --- | ---: |
| Expected labels | 1325 |
| Predicted labels | 2141 |
| True positives | 512 |
| False positives | 1629 |
| False negatives | 813 |
| Micro precision | 0.239141 |
| Micro recall | 0.386415 |
| Micro F1 | 0.295441 |
| Article macro precision | 0.207672 |
| Article macro recall | 0.341068 |
| Article macro F1 | 0.239309 |
| Label macro precision | 0.240045 |
| Label macro recall | 0.306792 |
| Label macro F1 | 0.218158 |
| Hamming loss | 0.164323 |

## Charts

### Metrics overview

![Metrics overview](charts_ioc/metrics_overview.svg)

### TP / FP / FN counts

![TP / FP / FN counts](charts_ioc/confusion_counts.svg)

### Most missed expected techniques

![Most missed expected techniques](charts_ioc/top_missing.svg)

### Most frequent extra predictions

![Most frequent extra predictions](charts_ioc/top_extra.svg)

### Article F1 distribution

![Article F1 distribution](charts_ioc/article_f1_distribution.svg)

## Article Quality

| Metric | Value |
| --- | ---: |
| Exact-match articles | 0 |
| Articles with no expected labels | 4 |
| Articles with no predictions | 0 |
| Mean expected labels/article | 17.208 |
| Median expected labels/article | 13.000 |
| Mean predicted labels/article | 27.805 |
| Median predicted labels/article | 25.000 |
| Mean sentences/article | 190.026 |
| Median sentences/article | 165.000 |

## Top Gaps

### Most Missed Expected Techniques

| Rank | Technique | Name | Count |
| ---: | --- | --- | ---: |
| 1 | `T1133` | External Remote Services | 29 |
| 2 | `T1078` | Valid Accounts | 22 |
| 3 | `T1566` | Phishing | 22 |
| 4 | `T1190` | Exploit Public-Facing Application | 22 |
| 5 | `T1003` | OS Credential Dumping | 19 |
| 6 | `T1110` | Brute Force | 18 |
| 7 | `T1055` | Process Injection | 16 |
| 8 | `T1105` | Ingress Tool Transfer | 16 |
| 9 | `T1555` | Credentials from Password Stores | 15 |
| 10 | `T1552` | Unsecured Credentials | 14 |
| 11 | `T1560` | Archive Collected Data | 14 |
| 12 | `T1486` | Data Encrypted for Impact | 13 |
| 13 | `T1046` | Network Service Discovery | 12 |
| 14 | `T1016` | System Network Configuration Discovery | 12 |
| 15 | `T1071` | Application Layer Protocol | 12 |

### Most Frequent Extra Predictions

| Rank | Technique | Name | Count |
| ---: | --- | --- | ---: |
| 1 | `T1587` | Develop Capabilities | 70 |
| 2 | `T1531` | Account Access Removal | 69 |
| 3 | `T1213` | Data from Information Repositories | 62 |
| 4 | `T1119` | Automated Collection | 56 |
| 5 | `T1482` | Domain Trust Discovery | 46 |
| 6 | `T1553` | Subvert Trust Controls | 46 |
| 7 | `T1498` | Network Denial of Service | 45 |
| 8 | `T1029` | Scheduled Transfer | 34 |
| 9 | `T1565` | Data Manipulation | 32 |
| 10 | `T1027` | Obfuscated Files or Information | 32 |
| 11 | `T1480` | Execution Guardrails | 31 |
| 12 | `T1528` | Steal Application Access Token | 30 |
| 13 | `T1049` | System Network Connections Discovery | 30 |
| 14 | `T1588` | Obtain Capabilities | 29 |
| 15 | `T1140` | Deobfuscate/Decode Files or Information | 29 |

### Most Frequent Matches

| Rank | Technique | Name | Count |
| ---: | --- | --- | ---: |
| 1 | `T1059` | Command and Scripting Interpreter | 30 |
| 2 | `T1190` | Exploit Public-Facing Application | 18 |
| 3 | `T1070` | Indicator Removal on Host | 17 |
| 4 | `T1083` | File and Directory Discovery | 16 |
| 5 | `T1027` | Obfuscated Files or Information | 15 |
| 6 | `T1078` | Valid Accounts | 15 |
| 7 | `T1090` | Proxy | 13 |
| 8 | `T1021` | Remote Services | 13 |
| 9 | `T1071` | Application Layer Protocol | 11 |
| 10 | `T1036` | Masquerading | 11 |
| 11 | `T1053` | Scheduled Task/Job | 11 |
| 12 | `T1018` | Remote System Discovery | 11 |
| 13 | `T1003` | OS Credential Dumping | 10 |
| 14 | `T1486` | Data Encrypted for Impact | 10 |
| 15 | `T1087` | Account Discovery | 9 |

## Article-Level Extremes

### Best Articles

| Rank | Index | F1 | Precision | Recall | TP | FP | FN | Expected | Predicted | URL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 69 | 0.682353 | 0.865672 | 0.563107 | 58 | 9 | 45 | 103 | 67 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-336a) |
| 2 | 53 | 0.518519 | 0.567568 | 0.477273 | 21 | 16 | 23 | 44 | 37 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-055a) |
| 3 | 22 | 0.500000 | 0.409091 | 0.642857 | 18 | 26 | 10 | 28 | 44 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-201a) |
| 4 | 14 | 0.480000 | 0.387097 | 0.631579 | 12 | 19 | 7 | 19 | 31 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-319a) |
| 5 | 71 | 0.478873 | 0.361702 | 0.708333 | 17 | 30 | 7 | 24 | 47 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-301a) |
| 6 | 67 | 0.472727 | 0.333333 | 0.812500 | 13 | 26 | 3 | 16 | 39 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-048a) |
| 7 | 9 | 0.461538 | 0.375000 | 0.600000 | 6 | 10 | 4 | 10 | 16 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-341a) |
| 8 | 3 | 0.452174 | 0.412698 | 0.500000 | 26 | 37 | 26 | 52 | 63 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a) |
| 9 | 33 | 0.450000 | 0.461538 | 0.439024 | 18 | 21 | 23 | 41 | 39 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-059a) |
| 10 | 28 | 0.444444 | 0.400000 | 0.500000 | 20 | 30 | 20 | 40 | 50 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-129a) |
| 11 | 27 | 0.444444 | 0.400000 | 0.500000 | 14 | 21 | 14 | 28 | 35 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-136a) |
| 12 | 10 | 0.431373 | 0.333333 | 0.611111 | 11 | 22 | 7 | 18 | 33 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-339a) |
| 13 | 19 | 0.430769 | 0.424242 | 0.437500 | 14 | 19 | 18 | 32 | 33 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-250a) |
| 14 | 0 | 0.428571 | 0.428571 | 0.428571 | 15 | 20 | 20 | 35 | 35 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-060a) |
| 15 | 48 | 0.416667 | 0.285714 | 0.769231 | 10 | 25 | 3 | 13 | 35 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-138b) |

### Worst Articles

| Rank | Index | F1 | Precision | Recall | TP | FP | FN | Expected | Predicted | URL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 72 | 0.000000 | 0.000000 | 0.000000 | 0 | 19 | 5 | 5 | 19 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-296a) |
| 2 | 64 | 0.000000 | 0.000000 | 0.000000 | 0 | 22 | 4 | 4 | 22 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-148a) |
| 3 | 29 | 0.000000 | 0.000000 | 0.000000 | 0 | 24 | 3 | 3 | 24 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-108) |
| 4 | 60 | 0.000000 | 0.000000 | 0.000000 | 0 | 20 | 2 | 2 | 20 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-287a) |
| 5 | 68 | 0.000000 | 0.000000 | 0.000000 | 0 | 28 | 2 | 2 | 28 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-008a) |
| 6 | 11 | 0.000000 | 0.000000 | 0.000000 | 0 | 12 | 1 | 1 | 12 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-335a) |
| 7 | 12 | 0.047619 | 0.026316 | 0.250000 | 1 | 37 | 3 | 4 | 38 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-325a) |
| 8 | 43 | 0.083333 | 0.055556 | 0.166667 | 1 | 17 | 5 | 6 | 18 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-223a) |
| 9 | 57 | 0.108108 | 0.086957 | 0.142857 | 2 | 21 | 12 | 14 | 23 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-011a) |
| 10 | 51 | 0.109091 | 0.142857 | 0.088235 | 3 | 18 | 31 | 34 | 21 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-083a) |
| 11 | 34 | 0.117647 | 0.074074 | 0.285714 | 2 | 25 | 5 | 7 | 27 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-040a) |
| 12 | 62 | 0.125000 | 0.166667 | 0.100000 | 2 | 10 | 18 | 20 | 12 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-200a) |
| 13 | 47 | 0.129032 | 0.095238 | 0.200000 | 2 | 19 | 8 | 10 | 21 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-152a) |
| 14 | 63 | 0.133333 | 0.210526 | 0.097561 | 4 | 15 | 37 | 41 | 19 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-200b) |
| 15 | 15 | 0.133333 | 0.083333 | 0.333333 | 2 | 22 | 4 | 6 | 24 | [open](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-284a) |

## Output Artifacts

| Artifact | Path |
| --- | --- |
| json | `results/cisa/cisa_benchmark_full_ioc.json` |
| markdown_report | `results/cisa/cisa_benchmark_full_ioc_report.md` |
| rows_csv | `results/cisa/cisa_benchmark_full_ioc_rows.csv` |
| chart_metrics | `charts_ioc/metrics_overview.svg` |
| chart_confusion | `charts_ioc/confusion_counts.svg` |
| chart_top_missing | `charts_ioc/top_missing.svg` |
| chart_top_extra | `charts_ioc/top_extra.svg` |
| chart_f1_distribution | `charts_ioc/article_f1_distribution.svg` |

## Interpretation Notes

- The default benchmark compares base MITRE ATT&CK techniques only.
- CISA tactics are dropped, sub-techniques are collapsed to parent techniques, and invalid regex matches are ignored.
- `expected_mode=model-label-space` filters expected labels to techniques the TTPXHunter classifier can emit.
- High false positives indicate the threshold may need tuning for CISA advisories, which are longer and more operational than the SharpPanda sample.
