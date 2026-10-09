"""안전반장 mock API 애플리케이션을 만든다."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routers import auth, eval as eval_router, evidence, misc, tasks, transcription


ROOT = Path(__file__).resolve().parents[1]


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    """DB·업로드 경로를 주입할 수 있는 FastAPI 앱을 만든다."""
    app = FastAPI(title='안전반장 API (mock)')
    app.state.db_path = db_path or os.getenv('BANJANG_DB') or str(ROOT / 'data' / 'banjang.db')
    app.state.upload_dir = upload_dir or os.getenv('BANJANG_UPLOADS') or str(ROOT / 'data' / 'uploads')
    Path(app.state.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db(app.state.db_path)
    app.add_middleware(
        CORSMiddleware, allow_origins=['*'], allow_credentials=False,
        allow_methods=['*'], allow_headers=['*'],
    )

    @app.get('/api/health')
    def health():
        return {'ok': True}

    app.include_router(tasks.router)
    app.include_router(evidence.router)
    app.include_router(transcription.router)
    app.include_router(misc.router)
    app.include_router(auth.router)
    app.include_router(eval_router.router)
    app.mount('/api/uploads', StaticFiles(directory=app.state.upload_dir), name='uploads')
    dist = ROOT / 'web' / 'dist'
    if dist.exists():
        app.mount('/', StaticFiles(directory=dist, html=True), name='web')
    return app


app = create_app()
