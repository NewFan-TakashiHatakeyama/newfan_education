from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.router import router
from presentation.venture_router import router as venture_router
from infrastructure.db import begin_session_scope, end_session_scope
from infrastructure.settings import load_settings

app = FastAPI(title="Newfan Priority Setup API", version="0.1.0")
settings = load_settings()


class DbSessionScopeMiddleware:
    """リクエストごとにDBのSessionスコープを開き、終了時に必ず閉じる。

    素のASGIミドルウェアにしているのは、ここで設定した ContextVar を
    スレッドプールで動くエンドポイントへそのまま伝播させるため。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        token = begin_session_scope()
        try:
            await self.app(scope, receive, send)
        finally:
            end_session_scope(token)


app.add_middleware(DbSessionScopeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.web_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


app.include_router(router)
app.include_router(venture_router)
