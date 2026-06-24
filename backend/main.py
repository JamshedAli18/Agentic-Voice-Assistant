# backend/main.py

import uuid
import json
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from config import get_settings
from memory import get_memory, delete_memory
from agent import run_agent
from stt import transcribe_audio
from tts import synthesize_speech

settings = get_settings()

app = FastAPI(title="Voice AI Chatbot", version="1.0.0")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ──────────────────────────────────────────────────────────────────
class TextRequest(BaseModel):
    text: str
    session_id: str


class TTSRequest(BaseModel):
    text: str
    voice_id: str = None


class SessionResponse(BaseModel):
    session_id: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "message": "Voice AI Chatbot is running"}


@app.get("/session", response_model=SessionResponse)
async def create_session():
    """Generate a new session ID for the frontend."""
    return {"session_id": str(uuid.uuid4())}


@app.get("/voices")
async def get_voices():
    """Get available TTS voices."""
    voices = [{"name": name, "id": voice_id} for name, voice_id in settings.CARTESIA_VOICES.items()]
    return {"voices": voices}


@app.post("/voice")
async def voice_endpoint(
    audio: UploadFile = File(...),
    session_id: str = None,
    voice_id: str = None,
):
    """
    Main voice pipeline:
    1. Receive audio file from frontend
    2. Transcribe with Groq Whisper (STT)
    3. Run through LangGraph agent (LLM + tools)
    4. Convert response to speech with Cartesia (TTS)
    5. Return audio bytes + transcript info
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        # Step 1: Read audio bytes
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Step 2: STT — transcribe audio
        user_text = await transcribe_audio(
            audio_bytes,
            filename=audio.filename or "audio.webm"
        )
        if not user_text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        # Step 3: Get conversation memory
        memory = get_memory(session_id)
        history = memory.get_messages()

        # Step 4: Run agent
        ai_text = await run_agent(user_text, history)

        # Step 5: Update memory
        memory.add_user_message(user_text)
        memory.add_ai_message(ai_text)

        # Step 6: TTS — convert response to speech
        audio_response = await synthesize_speech(ai_text, voice_id=voice_id)

        # Return audio with transcript headers
        return Response(
            content=audio_response,
            media_type="audio/wav",
            headers={
                "X-User-Text": user_text,
                "X-AI-Text": ai_text,
                "X-Session-Id": session_id,
                "Access-Control-Expose-Headers": "X-User-Text, X-AI-Text, X-Session-Id",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_endpoint(request: TextRequest):
    """
    Text-only chat endpoint (no STT).
    Used by the frontend text input.
    """
    try:
        memory = get_memory(request.session_id)
        history = memory.get_messages()

        ai_text = await run_agent(request.text, history)

        memory.add_user_message(request.text)
        memory.add_ai_message(ai_text)

        return {
            "response": ai_text,
            "session_id": request.session_id,
            "history": memory.to_dict_list(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-stream")
async def chat_stream_endpoint(request: TextRequest):
    """
    Streaming chat endpoint.
    Returns response as Server-Sent Events for real-time streaming.
    """
    async def event_generator():
        try:
            memory = get_memory(request.session_id)
            history = memory.get_messages()

            # Add user message immediately
            memory.add_user_message(request.text)

            # Stream the AI response
            ai_text = ""
            async for chunk in stream_agent_response(request.text, history):
                ai_text += chunk
                # Send chunk as SSE
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # Add complete response to memory
            memory.add_ai_message(ai_text)
            
            # Send completion event
            yield f"data: {json.dumps({'done': True, 'response': ai_text})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def stream_agent_response(user_text: str, history: list):
    """
    Stream the agent response token by token.
    This is a helper that needs to work with your agent implementation.
    """
    # For now, call the regular agent and yield the response
    # In a real implementation, this would stream from the LLM
    ai_text = await run_agent(user_text, history)
    
    # Simulate streaming by yielding words/sentences
    words = ai_text.split()
    for i, word in enumerate(words):
        if i == 0:
            yield word
        else:
            yield " " + word
        # Add a small delay to simulate streaming
        await asyncio.sleep(0.01)


@app.post("/tts")
async def tts_endpoint(request: TTSRequest):
    """
    Convert text to speech.
    Used by frontend after text chat responses.
    Supports optional voice_id selection.
    """
    try:
        audio = await synthesize_speech(request.text, voice_id=request.voice_id)
        return Response(content=audio, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation memory for a session."""
    delete_memory(session_id)
    return {"status": "cleared", "session_id": session_id}