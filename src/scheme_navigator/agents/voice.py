from __future__ import annotations

import base64
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import httpx

from scheme_navigator.core.config import settings
from scheme_navigator.domain.models import Language

MAX_AUDIO_BYTES = 15 * 1024 * 1024
SUPPORTED_AUDIO_TYPES = {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/ogg", "audio/flac"}


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str
    confidence: float | None
    provider: Literal["whisper-local", "bhashini"]


class AudioTranscriber(Protocol):
    def transcribe(self, audio_bytes: bytes, filename: str, language: str = "auto") -> Transcription: ...


class LocalWhisperTranscriber:
    """Local Whisper adapter. Install faster-whisper and cache/download the model before offline use."""

    def __init__(self, model_size: str | None = None):
        self.model_size = model_size or settings.whisper_model_size
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Local Whisper is not installed; install the `voice` extra.") from exc
        # CPU/int8 avoids requiring CUDA. Model weights should be pre-cached for fully offline operation.
        self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8", local_files_only=True)

    def transcribe(self, audio_bytes: bytes, filename: str, language: str = "auto") -> Transcription:
        _validate_audio(audio_bytes)
        suffix = Path(filename).suffix[:10] or ".audio"
        path_name = None
        try:
            with tempfile.NamedTemporaryFile(prefix="scheme-nav-audio-", suffix=suffix, delete=False) as fp:
                fp.write(audio_bytes)
                path_name = fp.name
            segments, info = self.model.transcribe(
                path_name,
                language=None if language == "auto" else language,
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            segments = list(segments)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if not text:
                raise ValueError("No speech could be transcribed")
            probs = [max(0.0, min(1.0, 1.0 - float(segment.no_speech_prob))) for segment in segments]
            confidence = sum(probs) / len(probs) if probs else None
            detected = getattr(info, "language", None) or (language if language != "auto" else "en")
            return Transcription(text, detected, confidence, "whisper-local")
        finally:
            if path_name:
                try:
                    os.unlink(path_name)
                except OSError:
                    pass


class BhashiniASRTranscriber:
    """Bhashini ULCA ASR adapter. Credentials and pipeline ID must be provisioned by the project owner."""

    def __init__(self):
        self.user_id = settings.bhashini_user_id
        self.api_key = settings.bhashini_ulca_api_key
        self.pipeline_id = settings.bhashini_pipeline_id
        if not (self.user_id and self.api_key and self.pipeline_id):
            raise RuntimeError("Set BHASHINI_USER_ID, BHASHINI_ULCA_API_KEY and BHASHINI_PIPELINE_ID first.")
        self._pipeline_config: dict | None = None

    def _get_pipeline_config(self) -> dict:
        if self._pipeline_config is not None:
            return self._pipeline_config
        payload = {
            "pipelineTasks": [{"taskType": "asr"}],
            "pipelineRequestConfig": {"pipelineId": self.pipeline_id},
        }
        response = httpx.post(
            settings.bhashini_config_url,
            json=payload,
            headers={"userID": self.user_id, "ulcaApiKey": self.api_key},
            timeout=25,
        )
        response.raise_for_status()
        self._pipeline_config = response.json()
        return self._pipeline_config

    def transcribe(self, audio_bytes: bytes, filename: str, language: str = "en") -> Transcription:
        _validate_audio(audio_bytes)
        if language not in {Language.EN.value, Language.MR.value, Language.HI.value}:
            raise ValueError("Bhashini ASR requires language=en, mr, or hi")
        config_data = self._get_pipeline_config()
        task_configs = config_data.get("pipelineResponseConfig", [])
        asr_task = next((task for task in task_configs if task.get("taskType") == "asr"), None)
        endpoint = config_data.get("pipelineInferenceAPIEndPoint", {})
        callback_url = endpoint.get("callbackUrl")
        auth = endpoint.get("inferenceApiKey", {})
        service_config = None
        if asr_task:
            service_config = next(
                (item for item in (asr_task.get("config") or []) if item.get("language", {}).get("sourceLanguage") == language),
                None,
            )
        if not (callback_url and auth.get("name") and auth.get("value") and service_config):
            raise RuntimeError("Bhashini pipeline config has no ASR service for the requested language.")
        audio_format = Path(filename).suffix.lower().lstrip(".") or "wav"
        if audio_format == "mp3":
            audio_format = "mp3"
        if audio_format not in {"wav", "mp3", "flac", "ogg", "webm", "m4a"}:
            raise ValueError("Unsupported audio file extension; convert to WAV/MP3/FLAC first")
        sampling_rate = 16000 if audio_format == "wav" else None
        task_config = {
            "taskType": "asr",
            "config": {
                "language": {"sourceLanguage": language},
                "serviceId": service_config.get("serviceId"),
                "audioFormat": audio_format,
            },
        }
        if sampling_rate:
            task_config["config"]["samplingRate"] = sampling_rate
        payload = {
            "pipelineTasks": [task_config],
            "inputData": {"audio": [{"audioContent": base64.b64encode(audio_bytes).decode("ascii")}], "input": [{"source": None}]},
        }
        response = httpx.post(callback_url, json=payload, headers={auth["name"]: auth["value"]}, timeout=90)
        response.raise_for_status()
        data = response.json()
        pipeline_response = data.get("pipelineResponse", [])
        outputs = pipeline_response[0].get("output", []) if pipeline_response else []
        text = outputs[0].get("source", "").strip() if outputs else ""
        if not text:
            raise ValueError("Bhashini returned no transcription text")
        return Transcription(text, language, None, "bhashini")


def _validate_audio(audio_bytes: bytes) -> None:
    if not audio_bytes:
        raise ValueError("Audio file is empty")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValueError("Audio file exceeds 15 MiB")


def get_transcriber(provider: str) -> AudioTranscriber:
    if provider == "whisper":
        return LocalWhisperTranscriber()
    if provider == "bhashini":
        return BhashiniASRTranscriber()
    raise ValueError("provider must be 'whisper' or 'bhashini'")
