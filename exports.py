import csv
import json
from pathlib import Path
from typing import Any

from config import settings
from database import get_items


def write_exports(items: list[dict[str, Any]], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "scraped_items.csv"
    json_path = output_dir / "scraped_items.json"
    fieldnames = ["id", "title", "author", "tag", "captured_at"]

    with csv_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

    json_path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return csv_path, json_path


async def export_database() -> tuple[Path, Path]:
    items = await get_items(settings.database_path)
    return write_exports(items, settings.report_dir)
