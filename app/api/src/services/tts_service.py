import os
from collections.abc import Iterable
from elevenlabs.client import ElevenLabs

ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")


def synthesize_speech_bytes(text: str) -> bytes:
    if not text or not text.strip():
        raise ValueError("Text is required for TTS.")
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set.")

    client = ElevenLabs(api_key=api_key)
    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            model_id=ELEVENLABS_MODEL_ID,
            text=text.strip(),
            output_format="mp3_22050_32",
        )
    except Exception as e:
        raise RuntimeError(
            f"ElevenLabs TTS failed for voice_id = {ELEVENLABS_VOICE_ID}, "
            f"model_id={ELEVENLABS_MODEL_ID}: {e}"
        ) from e 

    if isinstance(audio_stream, (bytes, bytearray)):
        audio_bytes = bytes(audio_stream)
    elif isinstance(audio_stream, Iterable):
        audio_bytes = b"".join(
            chunk for chunk in audio_stream
            if isinstance(chunk, (bytes, bytearray))
        )
    else:
        raise RuntimeError("We have an unexpected ElevenLabs audio response type.")
    
    if not audio_bytes:
        raise RuntimeError("ElevenLabs did not return audio bytes.")
    
    return audio_bytes