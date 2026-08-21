from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.api.routes import simulator as simulator_router
from app.api.routes import risk as risk_router
from app.api.routes import evaluation as evaluation_router

settings = get_settings()
configure_logging()

app = FastAPI(
    title="KhaataPulse",
    description="AI Revenue Recovery Policy Engine — Backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend (Phase 5+)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulator_router.router)
app.include_router(risk_router.router)
app.include_router(evaluation_router.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
