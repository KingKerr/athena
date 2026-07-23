from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from athena_api.ask import router as ask_router
from athena_api.health import router as health_router
from athena_api.tts import router as tts_router
from config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

origins = [
    "https://frontend-gentle-wildflower-1355.fly.dev",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(health_router)
app.include_router(tts_router)
app.include_router(ask_router)