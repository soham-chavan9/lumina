"""Rule-based detector for HIPAA Safe Harbor identifiers (45 CFR 164.514(b)(2)).

Runs locally on extracted text with no model or network calls, so PHI never
leaves the process. It covers the identifiers that show up in text documents:
names, addresses, dates, ages over 89, phone/fax numbers, emails, SSNs, record,
plan, account, licence, vehicle and device numbers, URLs and IP addresses.

Safe Harbor covers identifiers of the individual and their relatives, employers
and household members, not the treating organisation, so letterhead and
provider contact lines (an address under a facility name, anything with an NPI)
are skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CATEGORY_LABELS = {
    "name": "Names",
    "address": "Street addresses",
    "dob": "Dates of birth",
    "date": "Dates related to the individual",
    "age_over_89": "Ages over 89",
    "phone": "Telephone numbers",
    "fax": "Fax numbers",
    "email": "Email addresses",
    "ssn": "Social Security numbers",
    "mrn": "Medical record numbers",
    "health_plan_id": "Health plan beneficiary numbers",
    "account": "Account numbers",
    "license": "Certificate / licence numbers",
    "vehicle": "Vehicle identifiers",
    "device": "Device identifiers / serial numbers",
    "url": "Web URLs",
    "ip": "IP addresses",
    "other_id": "Other unique identifying numbers",
}

# Identifiers that point at a specific person. Dates, phones, emails and
# addresses alone also appear in policies (effective dates, privacy-office
# contacts), so they don't mark a document as a patient record on their own.
PATIENT_RECORD_CATEGORIES = frozenset(
    {"name", "dob", "age_over_89", "ssn", "mrn", "health_plan_id", "account", "license", "vehicle", "device"}
)


@dataclass(frozen=True)
class PhiHit:
    category: str
    value: str
    start: int


_NAME = r"[A-Z][a-zA-Z'’\-]+(?:\s[A-Z][a-zA-Z'’\-]+){1,3}"
_NAME_VALUE = re.compile(rf"^{_NAME}$")
_NAME_LABELS = re.compile(
    r"^(patient|patient name|full name|name|name\s*/\s*relation|insured|insured name|subscriber|"
    r"subscriber name|member name|policyholder|guarantor|responsible party|emergency contact|next of kin)$",
    re.IGNORECASE,
)

# Label line -> category of the value on the next line (or after a colon).
_ID_LABELS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(ssn|social security( number| no\.?)?|patient ssn)$", re.I), "ssn"),
    (re.compile(r"^(mrn|medical record( #| number| no\.?)?)$", re.I), "mrn"),
    (
        re.compile(
            r"^(member id|insured id|subscriber id|beneficiary (id|#|number)|health plan id|"
            r"policy( #| number| no\.?)|group( #| number| no\.?)?)$",
            re.I,
        ),
        "health_plan_id",
    ),
    (re.compile(r"^((billing |patient )?account( #| number| no\.?)?|acct #?)$", re.I), "account"),
    (
        re.compile(
            r"^(driver'?s licen[cs]e( #| number| no\.?)?|licen[cs]e( #| number| no\.?)|"
            r"certificate( #| number| no\.?)?)$",
            re.I,
        ),
        "license",
    ),
    (re.compile(r"^((vehicle )?(licen[cs]e )?plate\b.*|vin)$", re.I), "vehicle"),
    (re.compile(r"^((device )?serial( #| number| no\.?)?)$", re.I), "device"),
    (re.compile(r"^(accession( #| number| no\.?)?)$", re.I), "other_id"),
]

_MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
_STREET_SUFFIX = (
    r"(?:St|Street|Rd|Road|Ave|Avenue|Blvd|Boulevard|Ln|Lane|Dr|Drive|Way|Ct|Court|Pl|Place|Plaza|"
    r"Ter|Terrace|Pkwy|Parkway|Hwy|Highway|Cir|Circle|Sq|Square)"
)

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("phone", re.compile(r"\(\d{3}\)\s*\d{3}[-.\s]\d{4}\b|\b\d{3}[-.]\d{3}[-.]\d{4}\b")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("url", re.compile(r"\bhttps?://[^\s<>\"')]+|\bwww\.[^\s<>\"')]+")),
    ("ip", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")),
    ("mrn", re.compile(r"\bMRN[-#:]?\s?\d{5,}\b")),
    ("account", re.compile(r"\bACCT[-#]?\d{5,}\b")),
    ("device", re.compile(r"\b(?:SN|S/N)[-:#]?\s?[A-Z0-9-]*\d[A-Z0-9-]*\b")),
    ("other_id", re.compile(r"\bACC-\d[\d-]{4,}\b")),
    ("date", re.compile(r"\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/(?:\d{4}|\d{2})\b")),
    ("date", re.compile(r"\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b")),
    ("date", re.compile(rf"\b{_MONTH}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b")),
    ("date", re.compile(rf"\b\d{{1,2}}\s+{_MONTH}\.?\s+\d{{4}}\b")),
    (
        "age_over_89",
        re.compile(
            r"\b(?:9\d|1[01]\d)[\s-]*(?:years?|yrs?)[\s-]*old\b|\b(?:9\d|1[01]\d)\s*y/?o\b|"
            r"\baged?\s+(?:9\d|1[01]\d)\b",
            re.I,
        ),
    ),
    (
        "address",
        re.compile(
            # Street part stays on one line ([ \t], not \s) so "2026\nAttending\nDr." isn't an address.
            rf"\b\d{{1,6}}[ \t]+(?:[A-Z][a-z]+\.?[ \t]){{1,4}}{_STREET_SUFFIX}\b\.?"
            rf"(?:,?\s*(?:Apt|Suite|Ste|Unit|#)\.?\s*[\w-]+)?"
            rf"(?:,\s*[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*,\s*[A-Z]{{2}}\s+\d{{5}}(?:-\d{{4}})?)?"
        ),
    ),
    ("address", re.compile(r"\bP\.?\s?O\.?\s+Box\s+\d+\b", re.I)),
    # Names in running text.
    ("name", re.compile(rf"\bRe:\s*({_NAME})")),
    ("name", re.compile(rf"\bpatient,\s+({_NAME})")),
    (
        "name",
        re.compile(
            r"\b(?:daughter|son|wife|husband|spouse|partner|mother|father|sister|brother|guardian|"
            rf"caregiver|neighbou?r|grandmother|grandfather|aunt|uncle),?\s+({_NAME})"
        ),
    ),
    ("name", re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Mx)\.?\s+([A-Z][a-zA-Z'’\-]+(?:\s[A-Z][a-zA-Z'’\-]+)?)")),
]

_ORG_NAME = re.compile(
    r"\b(center|centre|hospital|institute|clinic|medical|health system|healthcare|associates|practice|"
    r"laborator(y|ies)|pharmacy|university)\b",
    re.I,
)
_PROVIDER_LINE = re.compile(r"\b(NPI|tax id|EIN)\b", re.I)
_CONTACT_CATEGORIES = {"phone", "fax", "address", "email", "url"}
_SPECIFIC_OVER_GENERIC = {"dob": "date", "fax": "phone"}


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().rstrip(".,;:")


def _strip_parenthetical(value: str) -> str:
    return _clean(re.sub(r"\(.*?\)", "", value))


def _lines(text: str) -> list[tuple[int, str]]:
    out, pos = [], 0
    for line in text.splitlines(keepends=True):
        out.append((pos, line.rstrip("\r\n")))
        pos += len(line)
    return out


def _org_spans(lines: list[tuple[int, str]]) -> list[tuple[int, int]]:
    """Letterhead/provider contact lines: right under an organisation name, or naming an NPI/tax ID."""
    spans, prev = [], ""
    for start, line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        under_org = bool(_ORG_NAME.search(prev)) and not re.search(r"\d", prev)
        if under_org or _PROVIDER_LINE.search(stripped):
            spans.append((start, start + len(line)))
        prev = stripped
    return spans


def _label_hits(lines: list[tuple[int, str]]) -> list[PhiHit]:
    hits: list[PhiHit] = []
    rows = [(s, line.strip()) for s, line in lines if line.strip()]
    for i, (row_start, label_line) in enumerate(rows):
        label, inline = label_line, ""
        if ":" in label_line and "://" not in label_line:  # "SSN: 123-45-6789"
            label, inline = (part.strip() for part in label_line.split(":", 1))
        label = re.sub(r"\s*\(.*?\)\s*", " ", label).strip()
        if inline:
            value, value_start = inline, row_start + label_line.index(inline)
        elif i + 1 < len(rows):
            value_start, value = rows[i + 1]
        else:
            continue

        if _NAME_LABELS.match(label):
            name = _strip_parenthetical(value)
            if _NAME_VALUE.match(name):
                hits.append(PhiHit("name", name, value_start))
            continue
        for pattern, category in _ID_LABELS:
            if pattern.match(label):
                token = _strip_parenthetical(value).split(" ")[0] if value else ""
                if len(token) >= 4 and re.search(r"\d", token):
                    hits.append(PhiHit(category, token, value_start))
                break
    return hits


def _pattern_hits(text: str) -> list[PhiHit]:
    hits: list[PhiHit] = []
    for category, pattern in _PATTERNS:
        group = 1 if pattern.groups else 0
        for match in pattern.finditer(text):
            value, start = _clean(match.group(group)), match.start(group)
            if not value:
                continue
            before = text[max(0, start - 40):start].lower()
            found = category
            if category == "phone" and "fax" in before[-20:]:
                found = "fax"
            elif category == "date" and ("dob" in before or "birth" in before):
                found = "dob"
            hits.append(PhiHit(found, value, start))
    return hits


def detect_phi(text: str) -> list[PhiHit]:
    """Return Safe Harbor identifiers found in text, one hit per (category, value)."""
    if not text:
        return []
    lines = _lines(text)
    org = _org_spans(lines)

    def in_org(pos: int) -> bool:
        return any(a <= pos < b for a, b in org)

    candidates = _label_hits(lines) + _pattern_hits(text)
    # Letterhead/provider contact values are not the patient's; drop them everywhere.
    org_values = {h.value for h in candidates if h.category in _CONTACT_CATEGORIES and in_org(h.start)}
    kept = [h for h in candidates if h.value not in org_values and not (h.category in _CONTACT_CATEGORIES and in_org(h.start))]

    # One hit per (category, value); a value seen as dob/fax is not also listed as date/phone.
    specific = {(generic, h.value) for h in kept for cat, generic in _SPECIFIC_OVER_GENERIC.items() if h.category == cat}
    seen: set[tuple[str, str]] = set()
    result: list[PhiHit] = []
    for hit in sorted(kept, key=lambda h: h.start):
        key = (hit.category, hit.value)
        if key in seen or key in specific:
            continue
        seen.add(key)
        result.append(hit)
    return result


def looks_like_patient_record(hits: list[PhiHit]) -> bool:
    return any(h.category in PATIENT_RECORD_CATEGORIES for h in hits)


def mask(value: str) -> str:
    """Partially mask a detected value for display: first and last two characters, at most 8 dots."""
    if len(value) <= 4:
        return "•" * len(value)
    return value[:2] + "•" * min(len(value) - 4, 8) + value[-2:]
