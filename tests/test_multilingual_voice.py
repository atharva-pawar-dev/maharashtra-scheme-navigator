from __future__ import annotations

import io
import re
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.agents.interviewer import _parse_answer, QUESTION_SPECS
from scheme_navigator.agents.voice import Transcription
from scheme_navigator.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# --------------------------------------------------------------------------
# 1. Numeric and Lakh/Crore Normalisation Tests
# --------------------------------------------------------------------------

def test_devanagari_numeral_and_lakh_crore_conversions():
    # Phase 3 Required regression cases:
    # २५ → 25
    assert _parse_answer("age_years", "२५") == ("age_years", 25)
    # १,५०,००० → 150000
    assert _parse_answer("annual_family_income", "१,५०,०००") == ("annual_family_income", 150000)
    # २.५ लाख → 250000
    assert _parse_answer("annual_family_income", "२.५ लाख") == ("annual_family_income", 250000)
    # ३ करोड़ → 30000000
    assert _parse_answer("annual_family_income", "३ करोड़") == ("annual_family_income", 30000000)
    # 2.5 lakh → 250000
    assert _parse_answer("annual_family_income", "2.5 lakh") == ("annual_family_income", 250000)

    # Additional Indian numeral formatting cases
    assert _parse_answer("age_years", "६० वर्षे") == ("age_years", 60)
    assert _parse_answer("age_years", "18 completed years") == ("age_years", 18)
    assert _parse_answer("annual_family_income", "₹५०,०००") == ("annual_family_income", 50000)
    assert _parse_answer("annual_family_income", "10 crore") == ("annual_family_income", 100000000)
    assert _parse_answer("annual_family_income", "१० करोड") == ("annual_family_income", 100000000)


def test_multilingual_yes_no_and_gender_and_residence():
    # Marathi yes/no
    assert _parse_answer("bpl", "हो") == ("bpl", True)
    assert _parse_answer("bpl", "होय") == ("bpl", True)
    assert _parse_answer("bpl", "नाही") == ("bpl", False)

    # Hindi yes/no
    assert _parse_answer("bpl", "हाँ") == ("bpl", True)
    assert _parse_answer("bpl", "जी") == ("bpl", True)
    assert _parse_answer("bpl", "नहीं") == ("bpl", False)

    # English yes/no
    assert _parse_answer("bpl", "yes") == ("bpl", True)
    assert _parse_answer("bpl", "no") == ("bpl", False)

    # Gender parsing
    assert _parse_answer("gender", "महिला") == ("gender", "female")
    assert _parse_answer("gender", "स्त्री") == ("gender", "female")
    assert _parse_answer("gender", "पुरुष") == ("gender", "male")
    assert _parse_answer("gender", "औरत") == ("gender", "female")
    assert _parse_answer("gender", "इतर") == ("gender", "other")
    assert _parse_answer("gender", "सांगू इच्छित नाही") == ("gender", "prefer_not_to_say")
    assert _parse_answer("gender", "बताना नहीं चाहते") == ("gender", "prefer_not_to_say")

    # Residence
    assert _parse_answer("resident_state", "महाराष्ट्र") == ("resident_state", "maharashtra")
    assert _parse_answer("resident_state", "Maharashtra") == ("resident_state", "maharashtra")
    assert _parse_answer("resident_state", "Other state") == ("resident_state", "other state")


# --------------------------------------------------------------------------
# 2. Voice Endpoint Validation & Cloud Consent Tests
# --------------------------------------------------------------------------

def test_voice_transcribe_mime_validation(client):
    # Non-audio MIME type rejected with 415
    res = client.post(
        "/voice/transcribe?provider=whisper&language=en",
        files={"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")},
    )
    assert res.status_code == 415
    assert "upload an audio file" in res.json()["detail"].lower()

    # Plain text rejected with 415
    res_txt = client.post(
        "/voice/transcribe?provider=whisper&language=en",
        files={"file": ("hello.txt", b"Hello", "text/plain")},
    )
    assert res_txt.status_code == 415


def test_voice_transcribe_max_upload_size(client):
    # Payload over 15 MiB rejected with 413
    oversized = b"0" * (15 * 1024 * 1024 + 10)
    res = client.post(
        "/voice/transcribe?provider=whisper&language=en",
        files={"file": ("huge.wav", oversized, "audio/wav")},
    )
    assert res.status_code == 413
    assert "exceeds 15 mib" in res.json()["detail"].lower()


def test_voice_transcribe_provider_and_language_validation(client):
    valid_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
    # Unsupported provider
    res_bad_prov = client.post(
        "/voice/transcribe?provider=unknown_provider&language=en",
        files={"file": ("speech.wav", valid_wav, "audio/wav")},
    )
    assert res_bad_prov.status_code == 400
    assert "provider must be" in res_bad_prov.json()["detail"].lower()

    # Unsupported language
    res_bad_lang = client.post(
        "/voice/transcribe?provider=whisper&language=fr",
        files={"file": ("speech.wav", valid_wav, "audio/wav")},
    )
    assert res_bad_lang.status_code == 400
    assert "language must be" in res_bad_lang.json()["detail"].lower()


def test_bhashini_cloud_consent_enforcement(client):
    valid_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
    # Bhashini requires explicit consent=true
    res_no_consent = client.post(
        "/voice/transcribe?provider=bhashini&language=mr&consent_to_cloud_processing=false",
        files={"file": ("speech.wav", valid_wav, "audio/wav")},
    )
    assert res_no_consent.status_code == 400
    assert "consent" in res_no_consent.json()["detail"].lower()

    # With consent=true and mocked Bhashini adapter
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = Transcription(
        text="माझे उत्पन्न दोन लाख रुपये आहे",
        language="mr",
        confidence=None,
        provider="bhashini",
    )
    with patch("scheme_navigator.api.main.get_transcriber", return_value=mock_transcriber):
        res_consent = client.post(
            "/voice/transcribe?provider=bhashini&language=mr&consent_to_cloud_processing=true",
            files={"file": ("speech.webm", b"\x1a\x45\xdf\xa3webm-bytes", "audio/webm")},
        )
        assert res_consent.status_code == 200
        data = res_consent.json()
        assert data["transcript"] == "माझे उत्पन्न दोन लाख रुपये आहे"
        assert data["provider"] == "bhashini"
        assert data["detected_language"] == "mr"
        assert data["profile_modified"] is False


def test_whisper_local_transcription_mocked(client):
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = Transcription(
        text="२५",
        language="mr",
        confidence=0.92,
        provider="whisper-local",
    )
    with patch("scheme_navigator.api.main.get_transcriber", return_value=mock_transcriber):
        res = client.post(
            "/voice/transcribe?provider=whisper&language=mr&consent_to_cloud_processing=false",
            files={"file": ("speech.webm", b"\x1a\x45\xdf\xa3webm-bytes", "audio/webm")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["transcript"] == "२५"
        assert data["provider"] == "whisper-local"
        assert data["detected_language"] == "mr"
        assert data["confidence"] == 0.92
        assert data["profile_modified"] is False


# --------------------------------------------------------------------------
# 3. Two-Step Transcript Confirmation & Typed Fallback Invariant
# --------------------------------------------------------------------------

def test_transcription_does_not_mutate_interview_without_answer_submission(client):
    thread_id = "test-no-auto-submit-thread"
    start_res = client.post(
        "/interview/start",
        json={"thread_id": thread_id, "language": "mr", "profile": {}},
    )
    assert start_res.status_code == 200
    q1 = start_res.json()["question"]
    assert q1 is not None

    # Step 1: Citizen transcribes audio
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = Transcription(
        text="२५",
        language="mr",
        confidence=0.95,
        provider="whisper-local",
    )
    with patch("scheme_navigator.api.main.get_transcriber", return_value=mock_transcriber):
        voice_res = client.post(
            "/voice/transcribe?provider=whisper&language=mr",
            files={"file": ("voice.webm", b"\x1a\x45\xdf\xa3dummy-audio", "audio/webm")},
        )
        assert voice_res.status_code == 200
        assert voice_res.json()["profile_modified"] is False

    # Check interview state: it has NOT answered the question yet!
    state_res = client.get(f"/interview/{thread_id}")
    assert state_res.status_code == 200
    assert state_res.json()["complete"] is False
    assert state_res.json()["question"]["field"] == q1["field"]

    # Step 2: Citizen explicitly confirms and submits the transcribed answer
    ans_res = client.post(
        "/interview/answer",
        json={"thread_id": thread_id, "answer": voice_res.json()["transcript"], "language": "mr"},
    )
    assert ans_res.status_code == 200
    # Field has been filled and interview progressed!
    profile = ans_res.json()["profile"]
    assert profile is not None


def test_typed_answer_fallback_remains_functional(client):
    thread_id = "test-typed-fallback-thread"
    client.post(
        "/interview/start",
        json={"thread_id": thread_id, "language": "hi", "profile": {}},
    )
    # Citizen types directly in Hindi:
    ans_res = client.post(
        "/interview/answer",
        json={"thread_id": thread_id, "answer": "हाँ", "language": "hi"},
    )
    assert ans_res.status_code == 200
    assert ans_res.json()["profile"] is not None


# --------------------------------------------------------------------------
# 4. Multilingual Interview Questions & Choices
# --------------------------------------------------------------------------

def test_multilingual_question_specs_and_choices():
    for field, spec in QUESTION_SPECS.items():
        assert "labels" in spec
        assert "en" in spec["labels"]
        assert "mr" in spec["labels"]
        assert "hi" in spec["labels"]
        assert len(spec["labels"]["mr"]) > 3
        assert len(spec["labels"]["hi"]) > 3

        if spec["choices"]:
            assert "choice_labels" in spec
            assert "mr" in spec["choice_labels"]
            assert "hi" in spec["choice_labels"]


def test_interview_start_returns_localized_question_and_choices(client):
    # Marathi interview start
    res_mr = client.post(
        "/interview/start",
        json={"thread_id": "test-lang-mr", "language": "mr", "profile": {}},
    )
    assert res_mr.status_code == 200
    q_mr = res_mr.json()["question"]
    assert q_mr is not None
    # Verify Devanagari text in question
    assert re.search(r"[\u0900-\u097F]", q_mr["text"])

    # Hindi interview start
    res_hi = client.post(
        "/interview/start",
        json={"thread_id": "test-lang-hi", "language": "hi", "profile": {}},
    )
    assert res_hi.status_code == 200
    q_hi = res_hi.json()["question"]
    assert q_hi is not None
    assert re.search(r"[\u0900-\u097F]", q_hi["text"])


# --------------------------------------------------------------------------
# 5. UI Translation Dictionary Completeness & Strict Privacy Invariants
# --------------------------------------------------------------------------

def test_ui_translation_dictionary_completeness():
    from pathlib import Path
    portal_path = Path(__file__).resolve().parents[1] / "static" / "index.html"
    assert portal_path.is_file()
    html_content = portal_path.read_text(encoding="utf-8")

    # Extract TRANSLATIONS object definition
    assert "const TRANSLATIONS = {" in html_content
    # Check that all three languages are defined
    assert "en: {" in html_content
    assert "mr: {" in html_content
    assert "hi: {" in html_content

    # Check key markers across languages
    for lang in ["en", "mr", "hi"]:
        assert f"brand_name:" in html_content
        assert f"btn_confirm_submit:" in html_content
        assert f"btn_mic_label:" in html_content
        assert f"voice_transcribing:" in html_content
        assert f"consent_bhashini_label:" in html_content


def test_ui_contains_voice_recording_and_confirmation_elements():
    from pathlib import Path
    html_content = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")

    # Microphone button
    assert "btn-mic" in html_content
    # Recording bar and timer
    assert "voice-recording-bar" in html_content
    assert "recording-timer" in html_content
    assert "btn_stop_record" in html_content
    assert "btn_cancel_record" in html_content
    # Transcript review & confirmation area
    assert "transcript-confirmation-area" in html_content
    assert "transcript-edit-input" in html_content
    assert "btn-confirm-transcript" in html_content
    # Bhashini explicit consent
    assert "voice-bhashini-consent" in html_content
    # MediaRecorder feature detection
    assert "MediaRecorder.isTypeSupported" in html_content
    assert "navigator.mediaDevices.getUserMedia" in html_content


def test_no_sensitive_browser_storage_in_ui():
    from pathlib import Path
    html_content = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")

    # In saveSession(), verify strict allowlist only:
    # version, selectedSchemeId, threadId, language, interviewComplete, reviewId, financialYear
    snapshot_match = re.search(r"const snapshot = \{([^}]+)\};", html_content)
    assert snapshot_match is not None
    snapshot_code = snapshot_match.group(1)

    allowed_fields = {
        "version",
        "selectedSchemeId",
        "threadId",
        "language",
        "interviewComplete",
        "reviewId",
        "financialYear",
    }
    keys = {
        line.split(":")[0].strip()
        for line in snapshot_code.strip().splitlines()
        if ":" in line
    }
    assert keys == allowed_fields

    assert "audio" not in keys
    assert "transcript" not in keys
    assert "chunks" not in keys
    assert "blob" not in keys
    assert "profile" not in keys
