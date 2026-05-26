from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.router import router
from infrastructure.settings import load_settings

app = FastAPI(title="Newfan Priority Setup API", version="0.1.0")
settings = load_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


app.include_router(router)
