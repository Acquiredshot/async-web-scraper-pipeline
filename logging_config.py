import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from rich.logging import RichHandler


class JsonFormatter(logging.Formatter):
    _extra_fields = (
        "event",
        "url",
        "items_saved",
        "item_number",
        "author",
        "csv_path",
        "json_path",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self._extra_fields:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=True,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    json_handler = logging.FileHandler(log_file, encoding="utf-8")
    json_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(console_handler)
    root_logger.addHandler(json_handler)
