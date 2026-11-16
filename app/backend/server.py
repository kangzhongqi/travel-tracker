"""travel-tracker 学习中心后端：注册/登录(JWT) + 用户数据云同步(SQLite)"""
import hashlib
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data")
os.makedirs(DB_PATH, exist_ok=True)
DB_FILE = os.path.join(DB_PATH, "app.db")
SECRET_FILE = os.path.join(DB_PATH, "secret.key")

if not os.path.exists(SECRET_FILE):
    with open(SECRET_FILE, "wb") as f:
        f.write(secrets.token_bytes(32))
with open(SECRET_FILE, "rb") as f:
    JWT_SECRET = f.read()

JWT_ALG = "HS256"
JWT_DAYS = 7
PBKDF2_ITERS = 600_000
ALLOWED_KEYS = {"finance", "spanish"}

app = FastAPI(title="travel-tracker 学习中心 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


def db():
    con = sqlite3.connect(DB_FILE)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.row_factory = sqlite3.Row
    return con


with db() as con:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pass_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_data(
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            mod_key TEXT NOT NULL,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, mod_key)
        );
        """
    )


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERS
    ).hex()


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=64)


class LoginIn(BaseModel):
    username: str
    password: str


class DataIn(BaseModel):
    payload: dict


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(security)) -> sqlite3.Row:
    if cred is None:
        raise HTTPException(401, "未登录")
    try:
        payload = jwt.decode(cred.credentials, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "无效令牌")
    with db() as con:
        row = con.execute("SELECT id, username FROM users WHERE id=?", (payload["sub"],)).fetchone()
    if row is None:
        raise HTTPException(401, "用户不存在")
    return row


@app.post("/api/auth/register")
def register(body: RegisterIn):
    salt = secrets.token_hex(16)
    with db() as con:
        try:
            cur = con.execute(
                "INSERT INTO users(username, pass_hash, salt, created_at) VALUES(?,?,?,?)",
                (body.username, hash_password(body.password, salt), salt, now_iso()),
            )
            con.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(400, "用户名已被占用")
        uid = cur.lastrowid
    token = jwt.encode(
        {"sub": str(uid), "exp": time.time() + JWT_DAYS * 86400, "iat": time.time()},
        JWT_SECRET,
        algorithm=JWT_ALG,
    )
    return {"token": token, "username": body.username}


@app.post("/api/auth/login")
def login(body: LoginIn):
    with db() as con:
        row = con.execute(
            "SELECT id, username, pass_hash, salt FROM users WHERE username=?", (body.username,)
        ).fetchone()
    if row is None:
        raise HTTPException(401, "用户名或密码错误")
    if not secrets.compare_digest(hash_password(body.password, row["salt"]), row["pass_hash"]):
        raise HTTPException(401, "用户名或密码错误")
    token = jwt.encode(
        {"sub": str(row["id"]), "exp": time.time() + JWT_DAYS * 86400, "iat": time.time()},
        JWT_SECRET,
        algorithm=JWT_ALG,
    )
    return {"token": token, "username": row["username"]}


@app.get("/api/me")
def me(user: sqlite3.Row = Depends(current_user)):
    return {"username": user["username"]}


@app.get("/api/data/{key}")
def get_data(key: str, user: sqlite3.Row = Depends(current_user)):
    if key not in ALLOWED_KEYS:
        raise HTTPException(404, "未知模块")
    with db() as con:
        row = con.execute(
            "SELECT payload, updated_at FROM user_data WHERE user_id=? AND mod_key=?",
            (user["id"], key),
        ).fetchone()
    if row is None:
        return {"key": key, "payload": None, "updated_at": None}
    return {"key": key, "payload": json.loads(row["payload"]), "updated_at": row["updated_at"]}


@app.put("/api/data/{key}")
def put_data(key: str, body: DataIn, user: sqlite3.Row = Depends(current_user)):
    if key not in ALLOWED_KEYS:
        raise HTTPException(404, "未知模块")
    payload = json.dumps(body.payload, ensure_ascii=False)
    with db() as con:
        con.execute(
            """
            INSERT INTO user_data(user_id, mod_key, payload, updated_at) VALUES(?,?,?,?)
            ON CONFLICT(user_id, mod_key) DO UPDATE SET payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (user["id"], key, payload, now_iso()),
        )
        con.commit()
    return {"key": key, "saved": True, "size": len(payload)}
