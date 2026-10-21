import asyncio

from config import settings
from database import init_db
from exports import export_database
from logging_config import configure_logging
from scraper import run_pipeline
import logging


logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging(settings.log_file)
    try:
        logger.info(
            "Initializing local database",
            extra={"event": "database_initializing"},
        )
        await init_db(settings.database_path)

        logger.info(
            "Starting Playwright data extraction pipeline",
            extra={"event": "pipeline_started"},
        )
        count = await run_pipeline()
        csv_path, json_path = await export_database()
        logger.info(
            "Pipeline completed successfully",
            extra={
                "event": "pipeline_completed",
                "items_saved": count,
                "csv_path": str(csv_path),
                "json_path": str(json_path),
            },
        )
    except Exception:
        logger.exception("Pipeline execution failed", extra={"event": "pipeline_failed"})
        raise

if __name__ == "__main__":
    asyncio.run(main())