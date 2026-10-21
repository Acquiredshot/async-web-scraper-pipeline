import logging

from rich.console import Console, Group
from rich.live import Live
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from database import save_item
from config import settings

logger = logging.getLogger(__name__)
console = Console()


def _status_table(status: str, url: str, saved: int) -> Table:
    table = Table(title="Playwright Scraper", expand=True)
    table.add_column("Status", style="cyan")
    table.add_column("Target", overflow="fold")
    table.add_column("Records saved", justify="right", style="green")
    table.add_row(status, url, str(saved))
    return table


async def run_pipeline() -> int:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.headless_mode)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            )
            page = await context.new_page()
            await page.route(
                "**/*.{png,jpg,jpeg,svg,css,font,woff}",
                lambda route: route.abort(),
            )

            logger.info(
                "Navigating to target page",
                extra={"event": "navigation_started", "url": settings.target_url},
            )
            await page.goto(settings.target_url, wait_until="domcontentloaded")

            try:
                await page.wait_for_selector(".quote", timeout=10000)
            except PlaywrightTimeoutError as error:
                raise RuntimeError(
                    f"No quote elements appeared at {settings.target_url}"
                ) from error

            quotes = page.locator(".quote")
            quote_count = await quotes.count()
            if quote_count == 0:
                raise RuntimeError(f"No quotes found at {settings.target_url}")

            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            )
            task = progress.add_task("Extracting quotes", total=quote_count)
            saved_count = 0
            table = _status_table("Extracting", settings.target_url, saved_count)

            with Live(Group(table, progress), console=console, refresh_per_second=8) as live:
                for index in range(quote_count):
                    quote = quotes.nth(index)
                    title = (await quote.locator(".text").inner_text()).strip()
                    author = (await quote.locator(".author").inner_text()).strip()
                    tags = await quote.locator(".tags .tag").all_inner_texts()
                    await save_item(
                        {
                            "title": title,
                            "author": author,
                            "tag": ",".join(tag.strip() for tag in tags),
                        },
                        db_path=settings.database_path,
                    )
                    saved_count += 1
                    progress.update(task, advance=1)
                    table = _status_table(
                        f"Saved {saved_count}/{quote_count}",
                        settings.target_url,
                        saved_count,
                    )
                    live.update(Group(table, progress))
                    logger.info(
                        "Scraped item saved",
                        extra={
                            "event": "item_saved",
                            "author": author,
                            "item_number": saved_count,
                        },
                    )

            logger.info(
                "Scraping completed",
                extra={"event": "scrape_completed", "items_saved": saved_count},
            )
            return saved_count
        except Exception:
            logger.exception(
                "Scraper pipeline failed",
                extra={"event": "scrape_failed", "url": settings.target_url},
            )
            raise
        finally:
            await browser.close()