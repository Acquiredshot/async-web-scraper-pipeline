from pathlib import Path
from typing import Any

import aiosqlite


async def init_db(db_path: str | Path = "extracted_data.db") -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scraped_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                author TEXT,
                tag TEXT,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_item(
    item: dict[str, str], db_path: str | Path = "extracted_data.db"
) -> None:
    if not item.get("title") or not item.get("author"):
        raise ValueError("Scraped items must include a title and author.")

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO scraped_items (title, author, tag) VALUES (?, ?, ?)",
            (item.get("title"), item.get("author"), item.get("tag"))
        )
        await db.commit()


async def get_items(db_path: str | Path = "extracted_data.db") -> list[dict[str, Any]]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, title, author, tag, captured_at "
            "FROM scraped_items ORDER BY id"
        )
        return [dict(row) for row in await cursor.fetchall()]