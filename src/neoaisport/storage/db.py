"""Leaderboard SQLite tại chỗ (offline ở hội chợ). Chỉ lưu tên 3 ký tự + điểm."""
from __future__ import annotations

import sqlite3
import time


class Leaderboard:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS scores(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                won INTEGER,
                created_at TEXT NOT NULL)"""
        )
        self.conn.commit()

    def add(self, mode: str, name: str, score: int,
            duration_ms: int = 0, won: int | None = None,
            created_at: str | None = None) -> None:
        created_at = created_at or time.strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT INTO scores(mode,player_name,score,duration_ms,won,created_at)"
            " VALUES(?,?,?,?,?,?)",
            (mode, (name or "?")[:3].upper(), int(score), int(duration_ms),
             None if won is None else int(won), created_at),
        )
        self.conn.commit()

    def top(self, mode: str = "solo", limit: int = 5,
            today: bool = False) -> list[tuple[str, int]]:
        q = "SELECT player_name, score FROM scores WHERE mode=?"
        args: list = [mode]
        if today:
            q += " AND date(created_at)=date('now','localtime')"
        q += " ORDER BY score DESC, id ASC LIMIT ?"
        args.append(limit)
        return list(self.conn.execute(q, args).fetchall())

    def best(self, mode: str = "solo") -> int:
        row = self.conn.execute(
            "SELECT MAX(score) FROM scores WHERE mode=?", (mode,)
        ).fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def close(self) -> None:
        self.conn.close()
