from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

app.mount("/statics", StaticFiles(directory="statics"), name="statics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    path = os.path.join("statics", "index.html")
    return FileResponse(path)

# --- БАЗА ---
def init_db():
    conn = sqlite3.connect("game.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        score INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()


# --- МОДЕЛЬ ---
class TapRequest(BaseModel):
    user_id: str


# --- ФУНКЦИИ ---
def get_connection():
    return sqlite3.connect("game.db")


def get_rank(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*) + 1 FROM users
    WHERE score > (SELECT score FROM users WHERE id=?)
    """, (user_id,))

    rank = cur.fetchone()[0]
    conn.close()
    return rank


# --- API ---

@app.post("/tap")
def tap(data: TapRequest):
    conn = get_connection()
    cur = conn.cursor()

    # создать пользователя если нет
    cur.execute("SELECT id FROM users WHERE id=?", (data.user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, score) VALUES (?, 0)", (data.user_id,))

    # +1 очко
    cur.execute("UPDATE users SET score = score + 1 WHERE id=?", (data.user_id,))

    conn.commit()

    # получить данные
    cur.execute("SELECT score FROM users WHERE id=?", (data.user_id,))
    score = cur.fetchone()[0]

    rank = get_rank(data.user_id)

    cur.execute("SELECT COUNT(*) FROM users")
    players = cur.fetchone()[0]

    conn.close()

    return {
        "score": score,
        "rank": rank,
        "players": players
    }


@app.get("/stats/{user_id}")
def stats(user_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT score FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        return {"score": 0, "rank": "-", "players": 0}

    score = row[0]
    rank = get_rank(user_id)

    cur.execute("SELECT COUNT(*) FROM users")
    players = cur.fetchone()[0]

    conn.close()

    return {
        "score": score,
        "rank": rank,
        "players": players
    }
