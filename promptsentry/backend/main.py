import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from middleware.gatekeeping import GatekeepingMiddleware
from routes.admin import router as admin_router
from routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # make sure request_logs table exists
    init_db()
    yield


app = FastAPI(title="PromptSentry", version="0.1.0", lifespan=lifespan)

# auth + rate limit
app.add_middleware(GatekeepingMiddleware)

# cors so the next.js dashboard can call /admin/logs from the browser
_cors_origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
