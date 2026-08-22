
import io
import logging
import os
 
import speech_recognition as sr
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
 
logger = logging.getLogger("ip_sakti_backend.voice")
 
router = APIRouter(prefix="/api/v1/voice", tags=["Voice Transcription"])
 
MAX_AUDIO_BYTES = 15 * 1024 * 1024  # 15MB safety cap
 
# Opt-in only. If set, a genuinely failed transcription (e.g. offline, no
# ffmpeg) returns a clearly-labeled stub instead of a hard error, so local
# dev/demo rehearsal isn't blocked by a broken mic setup. This must NEVER be
# the default — see why below.
DEV_FALLBACK_ENABLED = os.getenv("VOICE_DEV_FALLBACK", "false").lower() == "true"
 
 
class VoiceTranscribeResponse(BaseModel):
    status: str = "success"          # "success" | "stub" — see DEV_FALLBACK_ENABLED
    transcribed_text: str
    detected_language: str
 
 
@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en-IN")  # 'en-IN' for Indian English, 'hi-IN' for Hindi
):
    audio_bytes = await file.read()
 
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large (max 15MB)")
 
    # --- Convert whatever format the browser sent (webm/ogg/mp3/etc) to WAV.
    # speech_recognition.AudioFile can only read WAV/AIFF/FLAC directly, so
    # without this step, real browser-recorded audio ALWAYS fails to load —
    # which is why a silent fallback here is so dangerous: it was masking
    # a total functional failure, not an occasional edge case.
    try:
        sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
    except FileNotFoundError:
        # This is what pydub raises when ffmpeg isn't installed/on PATH.
        logger.error("ffmpeg not found — pydub cannot convert uploaded audio.")
        return _fail_or_stub(language, "ffmpeg is not installed or not on PATH on this server.")
    except CouldntDecodeError as exc:
        logger.warning("Could not decode uploaded audio: %s", exc)
        return _fail_or_stub(language, "Could not decode audio — unsupported or corrupt file.")
 
    wav_io = io.BytesIO()
    sound.export(wav_io, format="wav")
    wav_io.seek(0)
 
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError:
        # Genuinely unintelligible audio — this is a real, informative
        # result, not a system failure, so it stays a 400 rather than a stub.
        raise HTTPException(status_code=400, detail="Unable to recognize speech in audio file.")
    except sr.RequestError as exc:
        logger.warning("Speech recognition service unavailable: %s", exc)
        return _fail_or_stub(language, f"Speech recognition service unavailable: {exc}")
 
    return VoiceTranscribeResponse(
        status="success",
        transcribed_text=text,
        detected_language=language,
    )
 
 
def _fail_or_stub(language: str, reason: str) -> VoiceTranscribeResponse:
    """
    Default behavior: raise a real 503 so a broken voice pipeline is visible
    and gets fixed before demo day, instead of being invisibly replaced by
    fake "successful" transcriptions of unrelated content.
 
    Only if VOICE_DEV_FALLBACK=true is a stub returned instead — and even
    then it's clearly labeled status="stub" so callers/UI can distinguish
    it from a real result rather than displaying it as if the mic worked.
    """
    if DEV_FALLBACK_ENABLED:
        logger.warning("Returning DEV stub transcription due to: %s", reason)
        return VoiceTranscribeResponse(
            status="stub",
            transcribed_text="[DEV STUB] Nano-emulsion of Ashwagandha patentability",
            detected_language=language,
        )
    raise HTTPException(status_code=503, detail=f"Voice transcription failed: {reason}")
 
