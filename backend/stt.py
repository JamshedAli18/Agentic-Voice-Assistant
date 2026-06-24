# backend/stt.py

import io
from groq import AsyncGroq
from config import get_settings

settings = get_settings()

_client = AsyncGroq(api_key=settings.GROQ_API_KEY)


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribe audio bytes using Groq Whisper.
    Accepts any common audio format: webm, mp4, wav, mp3, ogg.
    Returns the transcribed text.
    """
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        transcription = await _client.audio.transcriptions.create(
            file=audio_file,
            model=settings.GROQ_WHISPER_MODEL,
            language="en",
            response_format="text",
        )

        # response_format="text" returns a plain string
        text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
        return text

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {str(e)}")