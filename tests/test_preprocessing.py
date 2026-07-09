from ttpxhunter.preprocessing import apply_section_filter, replace_iocs_with_base_names


def test_replace_iocs_with_base_names_matches_paper_patterns() -> None:
    text = (
        r"User admin@example.test connected to 10.0.0.8 and attacker-example.com. "
        r"The malware dropped C:\Users\Default\AppData\Roaming\payload.exe, "
        r"modified HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run, "
        r"and exploited CVE-2024-12345."
    )

    cleaned = replace_iocs_with_base_names(text)

    assert "email" in cleaned
    assert "ip address" in cleaned
    assert "domain" in cleaned
    assert "file path" in cleaned
    assert "registry" in cleaned
    assert "cve" in cleaned
    assert "admin@example.test" not in cleaned
    assert "10.0.0.8" not in cleaned
    assert "CVE-2024-12345" not in cleaned


def test_cisa_attack_narrative_filter_removes_non_attack_sections() -> None:
    text = """SUMMARY
Keep this summary.
TECHNICAL DETAILS
The actor used PowerShell for execution.
MITRE ATT&CK TECHNIQUES
T1059 Command and Scripting Interpreter
MITIGATIONS
Patch systems and train users.
RESOURCES
CISA: Some resource
DISCLAIMER
Do not keep this.
"""

    filtered = apply_section_filter(text, mode="cisa-attack-narrative")

    assert "Keep this summary" in filtered
    assert "The actor used PowerShell" in filtered
    assert "T1059 Command" not in filtered
    assert "Patch systems" not in filtered
    assert "Some resource" not in filtered
    assert "Do not keep this" not in filtered
