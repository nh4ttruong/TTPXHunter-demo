from __future__ import annotations

import re
from typing import Literal

PreprocessMode = Literal["none", "paper-ioc"]
SectionFilterMode = Literal["none", "cisa-attack-narrative"]

REGISTRY_RE = re.compile(
    r"\b(?:HKEY_LOCAL_MACHINE|HKEY_CURRENT_USER|HKEY_CLASSES_ROOT|"
    r"HKEY_USERS|HKEY_CURRENT_CONFIG)\\(?:[^\s\\]+\\)*[^\s\\]+",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)
WINDOWS_PATH_RE = re.compile(r"\b[a-zA-Z]:\\(?:[^\s\\]+\\)*[^\s\\]+\b")
FILE_NAME_RE = re.compile(
    r"\b[a-zA-Z0-9_.-]+\."
    r"(?:exe|dll|sys|bat|cmd|ps1|vbs|js|jse|jar|docx?|xlsx?|pptx?|pdf|zip|rar|7z|"
    r"txt|dat|bin|tmp|lnk|msi|scr|hta|iso|elf|so|dylib|sh|py|php|aspx?|jsp)\b",
    re.IGNORECASE,
)
DOMAIN_RE = re.compile(
    r"\b(?:[a-zA-Z0-9-]+\.)+"
    r"(?:com|net|org|io|co|gov|edu|mil|info|biz|ru|cn|uk|de|jp|fr|au|us|vn|ir|"
    r"br|in|nl|pl|kr|ca|eu|es|it|xyz|top|site|online|tech|dev)\b",
    re.IGNORECASE,
)

BLOCKED_SECTION_PREFIXES = (
    "INDICATORS OF COMPROMISE",
    "INDICATOR OF COMPROMISE",
    "IOCS",
    "MITRE ATT&CK",
    "MITRE ATTACK",
    "MITIGATIONS",
    "MITIGATION",
    "DETECTION",
    "VALIDATE SECURITY CONTROLS",
    "RESOURCES",
    "REFERENCES",
    "DISCLAIMER",
    "VERSION HISTORY",
    "APPENDIX",
    "ADDITIONAL RESOURCES",
)
ALLOWED_SECTION_PREFIXES = (
    "SUMMARY",
    "TECHNICAL DETAILS",
    "OVERVIEW",
    "THREAT ACTOR ACTIVITY",
    "OBSERVED TTPS",
    "RECONNAISSANCE",
    "RESOURCE DEVELOPMENT",
    "INITIAL ACCESS",
    "EXECUTION",
    "PERSISTENCE",
    "PRIVILEGE ESCALATION",
    "DEFENSE EVASION",
    "CREDENTIAL ACCESS",
    "DISCOVERY",
    "LATERAL MOVEMENT",
    "COLLECTION",
    "COMMAND AND CONTROL",
    "EXFILTRATION",
    "IMPACT",
)
BOILERPLATE_LINE_PATTERNS = (
    re.compile(r"^Actions to take today to mitigate\b", re.IGNORECASE),
    re.compile(r"^Download the PDF version\b", re.IGNORECASE),
    re.compile(r"^For a downloadable copy\b", re.IGNORECASE),
    re.compile(r"^\((?:PDF|XML|JSON),\s+[\d.]+\s+[KM]B$", re.IGNORECASE),
    re.compile(r"^AA\d{2}-\d{3}[A-Z]?\s+STIX\s+(?:XML|JSON)$", re.IGNORECASE),
    re.compile(r"^Figure\s+\d+:", re.IGNORECASE),
)


def preprocess_text(text: str, mode: PreprocessMode = "none") -> str:
    if mode == "none":
        return text
    if mode == "paper-ioc":
        return replace_iocs_with_base_names(text)
    raise ValueError("preprocess mode must be one of: none, paper-ioc")


def replace_iocs_with_base_names(text: str) -> str:
    replacements = [
        (REGISTRY_RE, "registry"),
        (EMAIL_RE, "email"),
        (CVE_RE, "cve"),
        (IP_RE, "ip address"),
        (WINDOWS_PATH_RE, "file path"),
        (FILE_NAME_RE, "file name"),
        (DOMAIN_RE, "domain"),
    ]
    cleaned = text
    for pattern, replacement in replacements:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def apply_section_filter(
    text: str,
    mode: SectionFilterMode = "none",
) -> str:
    if mode == "none":
        return text
    if mode != "cisa-attack-narrative":
        raise ValueError("section filter must be one of: none, cisa-attack-narrative")

    kept_lines: list[str] = []
    skipping_blocked_section = False
    for original_line in text.splitlines():
        line = original_line.strip()
        if not line:
            if kept_lines and kept_lines[-1] != "":
                kept_lines.append("")
            continue
        if _is_boilerplate_line(line):
            continue

        heading_key = _heading_key(line)
        if _starts_with_any(heading_key, BLOCKED_SECTION_PREFIXES):
            skipping_blocked_section = True
            continue
        if _starts_with_any(heading_key, ALLOWED_SECTION_PREFIXES):
            skipping_blocked_section = False

        if skipping_blocked_section:
            continue
        kept_lines.append(original_line)

    return "\n".join(_trim_blank_edges(kept_lines))


def prepare_text(
    text: str,
    preprocess: PreprocessMode = "none",
    section_filter: SectionFilterMode = "none",
) -> str:
    filtered = apply_section_filter(text, mode=section_filter)
    return preprocess_text(filtered, mode=preprocess)


def _is_boilerplate_line(line: str) -> bool:
    return any(pattern.search(line) for pattern in BOILERPLATE_LINE_PATTERNS)


def _heading_key(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip().rstrip(":")).upper()


def _starts_with_any(value: str, prefixes: tuple[str, ...]) -> bool:
    return any(value.startswith(prefix) for prefix in prefixes)


def _trim_blank_edges(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and lines[start] == "":
        start += 1
    while end > start and lines[end - 1] == "":
        end -= 1
    return lines[start:end]
