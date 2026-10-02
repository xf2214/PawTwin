"""Transactional local household store; never controls a feeding device."""

import json
import sqlite3
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_id() -> str:
    return str(uuid4())


def initial_home() -> dict[str, Any]:
    member = {"id": new_id(), "name": "主人"}
    return {
        "version": 1,
        "pets": [
            {
                "id": "mochi",
                "name": "Mochi",
                "species": "cat",
                "breed": "",
                "gender": "unknown",
                "birthday": None,
                "age_years": None,
                "coat": "gold",
                "pattern": "solid",
                "size": "medium",
                "likes": "",
                "dislikes": "",
                "photo_id": None,
                "source": "demo",
            }
        ],
        "members": [member],
        "objects": [
            {
                "id": new_id(),
                "pet_id": "mochi",
                "kind": "nest",
                "name": "窗边小窝",
                "x": 19,
                "y": 74,
                "note": "初始展示物品，可修改",
            },
            {
                "id": new_id(),
                "pet_id": "mochi",
                "kind": "toy",
                "name": "羽毛棒",
                "x": 38,
                "y": 70,
                "note": "初始展示物品，可修改",
            },
            {
                "id": new_id(),
                "pet_id": "mochi",
                "kind": "feeder",
                "name": "模拟喂食器",
                "x": 82,
                "y": 48,
                "note": "模拟设备，不连接真实硬件",
            },
            {
                "id": new_id(),
                "pet_id": "mochi",
                "kind": "water",
                "name": "水碗",
                "x": 81,
                "y": 72,
                "note": "初始展示物品，可修改",
            },
        ],
        "tasks": [],
        "notes": [],
        "diary": [],
        "history": [],
        "processed_actions": [],
    }


class HomeStore:
    def __init__(self, path: str) -> None:
        self.lock = RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False, timeout=15)
        self.conn.execute("PRAGMA busy_timeout=15000")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS pet_home_documents
                           (owner TEXT PRIMARY KEY, document TEXT NOT NULL)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS pet_home_photos
                           (id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                            mime TEXT NOT NULL, image BLOB NOT NULL)""")
        self.conn.commit()

    def close(self) -> None:
        with self.lock:
            self.conn.close()

    def _load(self, owner: str) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT document FROM pet_home_documents WHERE owner=?", (owner,)
        ).fetchone()
        return json.loads(row[0]) if row else initial_home()

    def read(self, owner: str) -> dict[str, Any]:
        # Persist the initial member IDs too, so a subsequent write uses the same IDs.
        return self.mutate(owner, lambda home: None)

    def mutate(self, owner: str, change) -> dict[str, Any]:
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                home = self._load(owner)
                change(home)
                self.conn.execute(
                    "INSERT OR REPLACE INTO pet_home_documents VALUES (?,?)",
                    (owner, json.dumps(home, ensure_ascii=False)),
                )
                self.conn.commit()
                return home
            except Exception:
                self.conn.rollback()
                raise

    def photo(self, owner: str, photo_id: str):
        with self.lock:
            return self.conn.execute(
                "SELECT mime,image FROM pet_home_photos WHERE owner=? AND id=?",
                (owner, photo_id),
            ).fetchone()

    def save_photo(self, owner: str, mime: str, image: bytes) -> str:
        photo_id = new_id()
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT INTO pet_home_photos VALUES (?,?,?,?)",
                (photo_id, owner, mime, image),
            )
        return photo_id
