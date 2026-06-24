# backend/tts.py

from cartesia import AsyncCartesia
from config import get_settings

settings = get_settings()


async def synthesize_speech(text: str, voice_id: str = None) -> bytes:
    """
    Convert text to speech using Cartesia.
    Returns raw audio bytes in WAV format (playable in browser).
    
    Args:
        text: The text to convert to speech
        voice_id: Optional voice ID. If not provided, uses the default from settings.
    """
    client = AsyncCartesia(api_key=settings.CARTESIA_API_KEY)
    
    # Use provided voice_id or fall back to default
    selected_voice_id = voice_id or settings.CARTESIA_VOICE_ID

    response = await client.tts.generate(
        model_id=settings.CARTESIA_MODEL_ID,
        transcript=text,
        voice={
            "mode": "id",
            "id": selected_voice_id,
        },
        output_format={
            "container": "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 44100,
        },
    )

    audio = await response.read()
    await client.close()
    return audio