from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def site():
    return FileResponse(os.path.join("static", "index.html"))


# ---------------- DATABASE ----------------

def get_connection():
    return sqlite3.connect("game.db")


conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    score INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()


# ---------------- MODELS ----------------

class TapRequest(BaseModel):
    user_id: str


# ---------------- HELPERS ----------------

def get_rank(user_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*) + 1
    FROM users
    WHERE score > (
        SELECT score
        FROM users
        WHERE id=?
    )
    """, (user_id,))

    rank = cur.fetchone()[0]

    conn.close()

    return rank


# ---------------- API ----------------

@app.post("/tap")
def tap(data: TapRequest):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE id=?",
        (data.user_id,)
    )

    if not cur.fetchone():

        cur.execute(
            "INSERT INTO users (id, score) VALUES (?, 0)",
            (data.user_id,)
        )

    cur.execute(
        "UPDATE users SET score = score + 1 WHERE id=?",
        (data.user_id,)
    )

    conn.commit()

    cur.execute(
        "SELECT score FROM users WHERE id=?",
        (data.user_id,)
    )

    score = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    players = cur.fetchone()[0]

    rank = get_rank(data.user_id)

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

    cur.execute(
        "SELECT score FROM users WHERE id=?",
        (user_id,)
    )

    row = cur.fetchone()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    players = cur.fetchone()[0]

    conn.close()

    if not row:

        return {
            "score": 0,
            "rank": 0,
            "players": players
        }

    return {
        "score": row[0],
        "rank": get_rank(user_id),
        "players": players
    }
