"""PHI detector scored against synthetic test records (backend/tests/fixtures/phi)."""

import glob
import json
from pathlib import Path

import pytest

from backend.scripts.eval_phi_detector import DEFAULT_DIR, score_file
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.phi_detector import detect_phi, looks_like_patient_record, mask

KEY = json.loads((DEFAULT_DIR / "phi_answer_key.json").read_text())
POLICY_PDFS = sorted(glob.glob(str(Path(__file__).resolve().parents[1] / "data" / "testing_pdfs" / "*.pdf")))


def _hits(name: str):
    return detect_phi(extract_text_from_pdf(str(DEFAULT_DIR / name)))


@pytest.mark.parametrize("name", [n for n, entry in KEY.items() if entry])
def test_every_answer_key_identifier_is_found(name):
    row = score_file(DEFAULT_DIR / name, KEY[name])
    assert row["missed"] == []
    assert row["patient_record"] is True


def test_deidentified_control_has_no_detections():
    assert _hits("06_deidentified_control.pdf") == []


@pytest.mark.parametrize("name", list(KEY))
def test_letterhead_and_providers_are_not_flagged(name):
    values = {h.value for h in _hits(name)}
    assert "(555) 010-2000" not in values  # facility phone in every letterhead
    assert not any("Test Plaza" in v or "Example Blvd" in v for v in values)
    assert not any("Marsh" in v or "Achebe" in v for v in values)  # treating providers


def test_relatives_beyond_the_answer_key_are_found():
    values = {(h.category, h.value) for h in _hits("01_patient_intake_form.pdf")}
    assert ("name", "Luis Delgado") in values  # spouse listed as emergency contact


@pytest.mark.parametrize("path", POLICY_PDFS)
def test_policy_documents_are_not_patient_records(path):
    assert looks_like_patient_record(detect_phi(extract_text_from_pdf(path))) is False


@pytest.mark.parametrize(
    "text, category, value",
    [
        ("SSN: 123-45-6789", "ssn", "123-45-6789"),
        ("Results phoned to (555)\n012-4527 today", "phone", "(555) 012-4527"),
        ("Referral faxed to (555) 011-4814.", "fax", "(555) 011-4814"),
        ("DOB 07/21/2003", "dob", "07/21/2003"),
        ("A 92-year-old woman presented", "age_over_89", "92-year-old"),
        ("Her son, Marcus Lee, drove her in.", "name", "Marcus Lee"),
    ],
)
def test_detects_identifiers_in_text(text, category, value):
    assert (category, value) in {(h.category, h.value) for h in detect_phi(text)}


def test_safe_harbor_allowed_values_are_not_flagged():
    text = "Age band 60-69. Region: 3-digit ZIP 027. Encounter year 2026. CPT 99214."
    assert detect_phi(text) == []


def test_mask_hides_the_middle():
    assert mask("941-38-3286") == "94•••••••86"
    assert mask("abc") == "•••"
    assert mask("8945 Maple Ridge Rd, Fairhaven, MA 02719") == "89••••••••19"  # length not revealed
