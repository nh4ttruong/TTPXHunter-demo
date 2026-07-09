# TTPXHunter Inference Report

## Run Configuration

| Field | Value |
| --- | --- |
| Report | `examples/reports/SharpPanda_APT_Campaign_Expands_its_Arsenal_Targeting_G20_Nations.txt` |
| Model | `nanda-rani/TTPXHunter` |
| Revision | `not pinned` |
| Threshold | 0.644 |
| Order | `first-seen` |
| Preprocess | `none` |
| Section filter | `none` |
| Top-k | none |
| Extracted TTP count | 19 |

## Notebook Agreement

| Metric | Value |
| --- | ---: |
| Actual count | 19 |
| Notebook expected count | 19 |
| Set match | yes |
| Order match | no |
| Agreement precision | 1.000000 |
| Agreement recall | 1.000000 |
| Agreement F1 | 1.000000 |

Agreement metrics compare this run with the saved notebook output. They are reproduction metrics, not independent model accuracy.

### Differences

| Type | Values |
| --- | --- |
| Missing vs notebook | - |
| Extra vs notebook | - |

## Extracted Techniques

| Rank | Technique | Name |
| ---: | --- | --- |
| 1 | `T1568` | Dynamic Resolution |
| 2 | `T1005` | Data from Local System |
| 3 | `T1588` | Obtain Capabilities |
| 4 | `T1566` | Phishing |
| 5 | `T1105` | Ingress Tool Transfer |
| 6 | `T1027` | Obfuscated Files or Information |
| 7 | `T1203` | Exploitation for Client Execution |
| 8 | `T1218` | System Binary Proxy Execution |
| 9 | `T1140` | Deobfuscate/Decode Files or Information |
| 10 | `T1036` | Masquerading |
| 11 | `T1082` | System Information Discovery |
| 12 | `T1560` | Archive Collected Data |
| 13 | `T1041` | Exfiltration Over C2 Channel |
| 14 | `T1210` | Exploitation of Remote Services |
| 15 | `T1119` | Automated Collection |
| 16 | `T1531` | Account Access Removal |
| 17 | `T1480` | Execution Guardrails |
| 18 | `T1205` | Traffic Signaling |
| 19 | `T1587` | Develop Capabilities |
