"""시연용 역할 로그인 API다. 실제 인증 기능은 제공하지 않는다."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_db


router = APIRouter(prefix='/api', tags=['auth'])


class LoginIn(BaseModel):
    login_id: str
    password: str


@router.post('/login')
def login(payload: LoginIn, conn: sqlite3.Connection = Depends(get_db)):
    """시드 계정의 역할과 기본 사용자 정보를 돌려준다."""
    row = conn.execute(
        'SELECT id, role, name, team FROM users WHERE login_id = ? AND password = ?',
        (payload.login_id, payload.password),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail='아이디 또는 비밀번호가 올바르지 않아요')
    return {'user_id': row['id'], 'role': row['role'], 'name': row['name'], 'team': row['team']}
