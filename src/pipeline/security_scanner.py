"""Security scanner for detecting sensitive information in markdown content.

Scans for API keys, passwords, credit card numbers, SSNs, email addresses,
phone numbers, and other PII/PHI. Any detection forces the note to
``visibility: private`` until manually validated.

This scanner runs automatically on every file entering the inbox.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# API keys and tokens
_API_KEY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Key", re.compile(r"(?i)aws_secret_access_key\s*[=:]\s*\S{20,}")),
    ("Anthropic API Key", re.compile(r"sk-ant-api\d{2}-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API Key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("GitHub PAT", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("Slack Token", re.compile(r"xox[bpors]-[A-Za-z0-9-]{10,}")),
    ("Stripe Key", re.compile(r"[sr]k_(live|test)_[A-Za-z0-9]{20,}")),
    (
        "Generic API Key",
        re.compile(r"(?i)(api[_-]?key|apikey|api[_-]?secret)\s*[=:]\s*['\"]?\S{16,}['\"]?"),
    ),
    (
        "Generic Token",
        re.compile(r"(?i)(access[_-]?token|auth[_-]?token|bearer)\s*[=:]\s*['\"]?\S{16,}['\"]?"),
    ),
    ("Generic Password", re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?\S{6,}['\"]?")),
    ("Private Key Header", re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("Telegram Bot Token", re.compile(r"\d{8,10}:[A-Za-z0-9_-]{35}")),
]

# Financial
_FINANCIAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Credit Card (Visa)", re.compile(r"\b4[0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b")),
    (
        "Credit Card (MC)",
        re.compile(r"\b5[1-5][0-9]{2}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b"),
    ),
    ("Credit Card (Amex)", re.compile(r"\b3[47][0-9]{2}[\s-]?[0-9]{6}[\s-]?[0-9]{5}\b")),
    ("Bank Account", re.compile(r"(?i)(account\s*#?|acct\s*#?)\s*:?\s*\d{8,17}")),
    ("Routing Number", re.compile(r"(?i)routing\s*#?\s*:?\s*\d{9}\b")),
]

# PII (Personally Identifiable Information)
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("SSN (no dashes)", re.compile(r"(?i)(?:ssn|social\s*security)\s*#?\s*:?\s*\d{9}\b")),
    ("Phone (US)", re.compile(r"\b(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")),
    ("Email Address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    ("IP Address (v4)", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")),
    ("Passport Number", re.compile(r"(?i)passport\s*#?\s*:?\s*[A-Z0-9]{6,9}\b")),
    ("Driver License", re.compile(r"(?i)(?:driver'?s?\s*license|DL)\s*#?\s*:?\s*[A-Z0-9]{5,15}\b")),
    (
        "Date of Birth",
        re.compile(
            r"(?i)(?:dob|date\s*of\s*birth|birthday)\s*:?\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}"
        ),
    ),
]

# PHI (Protected Health Information)
_PHI_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Medical Record #",
        re.compile(r"(?i)(?:medical\s*record|MRN|patient\s*id)\s*#?\s*:?\s*\S{5,}"),
    ),
    (
        "Health Insurance ID",
        re.compile(r"(?i)(?:insurance|policy)\s*(?:id|#|number)\s*:?\s*\S{5,}"),
    ),
    ("DEA Number", re.compile(r"\b[A-Z][A-Z9][0-9]{7}\b")),
]

# All patterns grouped by category
ALL_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    "api_key": _API_KEY_PATTERNS,
    "financial": _FINANCIAL_PATTERNS,
    "pii": _PII_PATTERNS,
    "phi": _PHI_PATTERNS,
}


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class SecurityFinding:
    """A single sensitive data detection."""

    category: str  # api_key | financial | pii | phi
    pattern_name: str  # e.g. "Credit Card (Visa)"
    line_number: int
    snippet: str  # redacted excerpt showing the match location
    confidence: str = "high"  # high | medium


@dataclass
class ScanResult:
    """Result of scanning a document for sensitive information."""

    findings: list[SecurityFinding] = field(default_factory=list)
    forced_private: bool = False
    summary: str = ""

    @property
    def has_findings(self) -> bool:
        """Return True if any sensitive data was detected."""
        return len(self.findings) > 0

    @property
    def high_severity_count(self) -> int:
        """Count of high-confidence findings."""
        return sum(1 for f in self.findings if f.confidence == "high")


# ---------------------------------------------------------------------------
# Ignore patterns (reduce false positives)
# ---------------------------------------------------------------------------

# Lines starting with these are likely code examples, not real secrets
_IGNORE_PREFIXES = (
    "# ",  # comments
    "// ",  # comments
    "-- ",  # comments
    "```",  # code fence
    "    ",  # indented code (4 spaces)
    "\t",  # indented code (tab)
)

# Content inside code blocks is less likely to be real secrets
_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)


def _is_in_code_block(content: str, match_start: int) -> bool:
    """Check if a match position falls inside a fenced code block."""
    for block in _CODE_BLOCK_RE.finditer(content):
        if block.start() <= match_start <= block.end():
            return True
    return False


def _redact_snippet(line: str, match_start: int, match_end: int) -> str:
    """Create a redacted snippet showing context around the match."""
    matched = line[match_start:match_end]
    if len(matched) <= 8:
        redacted = matched[:2] + "***" + matched[-1:]
    else:
        redacted = matched[:4] + "***" + matched[-4:]
    return line[:match_start] + redacted + line[match_end:]


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def scan_content(content: str) -> ScanResult:
    """Scan markdown content for sensitive information.

    Args:
        content: The markdown body text (without frontmatter).

    Returns:
        ScanResult with all findings. If any high-severity findings exist,
        ``forced_private`` is True.
    """
    findings: list[SecurityFinding] = []

    lines = content.split("\n")
    for line_num, line in enumerate(lines, start=1):
        # Skip obvious non-secret lines
        stripped = line.lstrip()
        if any(stripped.startswith(p) for p in _IGNORE_PREFIXES):
            continue

        for category, patterns in ALL_PATTERNS.items():
            for pattern_name, regex in patterns:
                for match in regex.finditer(line):
                    # Reduce false positives: skip matches inside code blocks
                    abs_pos = sum(len(ln) + 1 for ln in lines[: line_num - 1]) + match.start()
                    if _is_in_code_block(content, abs_pos):
                        continue

                    # Email in source_url or author fields is expected
                    if pattern_name == "Email Address" and line_num <= 3:
                        continue

                    snippet = _redact_snippet(line, match.start(), match.end())

                    # API keys and financial data are always high confidence
                    # PII patterns like phone/email can be medium
                    confidence = "high"
                    if pattern_name in ("Phone (US)", "Email Address", "IP Address (v4)"):
                        confidence = "medium"

                    findings.append(
                        SecurityFinding(
                            category=category,
                            pattern_name=pattern_name,
                            line_number=line_num,
                            snippet=snippet[:100],
                            confidence=confidence,
                        )
                    )

    forced_private = any(f.confidence == "high" for f in findings)

    # Build summary
    if not findings:
        summary = "No sensitive data detected."
    else:
        cats = set(f.category for f in findings)
        summary = (
            f"Found {len(findings)} potential sensitive item(s) "
            f"in categories: {', '.join(sorted(cats))}. "
        )
        if forced_private:
            summary += "Visibility forced to private until validated."

    if findings:
        logger.warning(
            "security_scan_findings",
            count=len(findings),
            high_severity=sum(1 for f in findings if f.confidence == "high"),
            categories=sorted(set(f.category for f in findings)),
            forced_private=forced_private,
        )

    return ScanResult(
        findings=findings,
        forced_private=forced_private,
        summary=summary,
    )
