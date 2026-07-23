from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from services.tts_service import synthesize_speech_bytes

router = APIRouter(prefix="/api", tags=["tts"])

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


@router.post("/tts")
def text_to_speech(payload: TTSRequest) -> Response:
    try:
        audio_bytes = synthesize_speech_bytes(payload.text)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="answer.mp3"'
            },
        )
    except Exception as e: 
        message = str(e)
        if "paid_plan_required" in message:
            raise HTTPException(
                status_code=400,
                detail="The selected voice is not available on the current ElevenLabs plan.",
            )
        if "ELEVENLABS_API_KEY" in message: 
            raise HTTPException(
                status_code=500,
                detail="The ElevenLabs API Key is not properly configured",
            )
        raise HTTPException(
            status_code=500,
            detail="Unable to generate audio right now.",
        )