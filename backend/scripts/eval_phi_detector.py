"""Score the PHI detector against an answer key of synthetic test documents.

Usage (from the repo root):
    PYTHONPATH=. python backend/scripts/eval_phi_detector.py [fixtures_dir]

Recall = answer-key identifiers found. "Extra" detections are listed for review:
the key is not exhaustive (e.g. it omits some relatives and signature dates).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.phi_detector import detect_phi, looks_like_patient_record

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "phi"


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


def key_values(entry: dict) -> list[str]:
    values: list[str] = []
    for value in entry.values():
        values.extend(value if isinstance(value, list) else [value])
    return values


def matches(detected: str, expected: str) -> bool:
    d, e = _norm(detected), _norm(expected)
    return d == e or (len(d) >= 4 and d in e) or (len(e) >= 4 and e in d)


def score_file(pdf: Path, entry: dict) -> dict:
    hits = detect_phi(extract_text_from_pdf(str(pdf)))
    expected = key_values(entry)
    found = [e for e in expected if any(matches(h.value, e) for h in hits)]
    extras = [h for h in hits if not any(matches(h.value, e) for e in expected)]
    return {
        "file": pdf.name,
        "expected": len(expected),
        "found": len(found),
        "missed": [e for e in expected if e not in found],
        "detections": len(hits),
        "extras": [(h.category, h.value) for h in extras],
        "patient_record": looks_like_patient_record(hits),
    }


def main(directory: Path) -> int:
    key = json.loads((directory / "phi_answer_key.json").read_text())
    total_expected = total_found = 0
    print(f"{'file':32} {'recall':>9} {'detections':>11}  patient record")
    for name, entry in key.items():
        row = score_file(directory / name, entry)
        total_expected += row["expected"]
        total_found += row["found"]
        recall = f"{row['found']}/{row['expected']}" if row["expected"] else "n/a"
        print(f"{row['file']:32} {recall:>9} {row['detections']:>11}  {row['patient_record']}")
        for missed in row["missed"]:
            print(f"    MISSED  {missed}")
        for category, value in row["extras"]:
            print(f"    extra   {category:15} {value}")
    print(f"\nOverall recall: {total_found}/{total_expected}")
    return 0 if total_found == total_expected else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR))
