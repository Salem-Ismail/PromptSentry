from contextlib import asynccontextmanager

from fastapi import FastAPI

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

app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
