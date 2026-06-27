"""
Playwright-based scraper for the National Scholarship Portal (https://scholarships.gov.in).

The NSP is a JS-heavy single-page application. Requests/BeautifulSoup won't work —
Playwright renders the page in a real browser context before extracting content.

NOTE: The selectors below target the portal's publicly-visible scholarship listing
pages. Because government portals change layout periodically, selectors may need
adjustment. Always test against the live site before a production scrape run.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

NSP_BASE_URL = "https://scholarships.gov.in"
NSP_LISTING_URL = f"{NSP_BASE_URL}/public/schemeList"


class NSPScraper:
    """Scrapes scholarship listings from the National Scholarship Portal."""

    def __init__(self, headless: bool = True, timeout_ms: int = 60_000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def scrape(self) -> list[dict[str, Any]]:
        """
        Launch a Playwright browser, navigate to the NSP listing page,
        wait for JS-rendered content, and extract scholarship data.

        Returns a list of dicts compatible with the ``SchemeMetadata`` schema
        defined in ``ingestion/schema.py``.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error(
                "playwright is not installed. "
                "Run: pip install playwright && python -m playwright install chromium"
            )
            return []

        schemes: list[dict[str, Any]] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()

            try:
                logger.info("Navigating to NSP listing page: %s", NSP_LISTING_URL)
                await page.goto(NSP_LISTING_URL, wait_until="networkidle", timeout=self.timeout_ms)

                # Wait for the scheme cards / table rows to appear.
                # The NSP portal typically renders scholarship rows inside a table
                # or card container after client-side hydration.
                await page.wait_for_selector(
                    "table tbody tr, .scholarship-card, .scheme-row",
                    timeout=self.timeout_ms,
                )

                # --- Strategy A: Table-based layout ---
                rows = await page.query_selector_all("table tbody tr")
                if rows:
                    schemes = await self._parse_table_rows(rows)
                    logger.info("Extracted %d schemes from table layout", len(schemes))
                else:
                    # --- Strategy B: Card-based layout ---
                    cards = await page.query_selector_all(
                        ".scholarship-card, .scheme-row, .card"
                    )
                    schemes = await self._parse_cards(cards)
                    logger.info("Extracted %d schemes from card layout", len(schemes))

                # Attempt to follow pagination if present
                schemes.extend(await self._handle_pagination(page))

            except Exception:
                logger.exception("Error scraping NSP portal")
            finally:
                await browser.close()

        # Tag every record with its source
        for s in schemes:
            s.setdefault("provider", "National Scholarship Portal")
            s.setdefault("source_url", NSP_LISTING_URL)
            s.setdefault("source", "nsp")
        return schemes

    # ------------------------------------------------------------------
    # Internal parsers
    # ------------------------------------------------------------------
    async def _parse_table_rows(self, rows) -> list[dict[str, Any]]:
        """Parse scholarship data from HTML ``<tr>`` elements."""
        results: list[dict[str, Any]] = []
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) < 3:
                continue

            scheme_name = (await cells[0].inner_text()).strip()
            if not scheme_name:
                continue

            category_text = (await cells[1].inner_text()).strip() if len(cells) > 1 else ""
            benefits_text = (await cells[2].inner_text()).strip() if len(cells) > 2 else ""
            eligibility_text = (await cells[3].inner_text()).strip() if len(cells) > 3 else ""
            deadline_text = (await cells[4].inner_text()).strip() if len(cells) > 4 else ""

            results.append(
                self._build_scheme_dict(
                    scheme_name=scheme_name,
                    categories=self._parse_categories(category_text),
                    benefits=benefits_text,
                    eligibility_text=eligibility_text,
                    deadline=self._parse_deadline(deadline_text),
                )
            )
        return results

    async def _parse_cards(self, cards) -> list[dict[str, Any]]:
        """Parse scholarship data from card-style DOM elements."""
        results: list[dict[str, Any]] = []
        for card in cards:
            title_el = await card.query_selector(
                "h3, h4, .card-title, .scheme-name, strong"
            )
            if not title_el:
                continue
            scheme_name = (await title_el.inner_text()).strip()
            if not scheme_name:
                continue

            full_text = (await card.inner_text()).strip()
            results.append(
                self._build_scheme_dict(
                    scheme_name=scheme_name,
                    categories=self._extract_field(full_text, "category"),
                    benefits=self._extract_field_str(full_text, "benefits"),
                    eligibility_text=self._extract_field_str(full_text, "eligibility"),
                    deadline=self._parse_deadline(
                        self._extract_field_str(full_text, "deadline")
                    ),
                )
            )
        return results

    async def _handle_pagination(self, page) -> list[dict[str, Any]]:
        """Click through pagination if a 'Next' button exists."""
        extra: list[dict[str, Any]] = []
        max_pages = 10  # safety cap
        for _ in range(max_pages):
            next_btn = await page.query_selector(
                "a.next, button.next, li.next a, [aria-label='Next']"
            )
            if not next_btn or await next_btn.is_disabled():
                break
            await next_btn.click()
            await page.wait_for_timeout(2000)
            rows = await page.query_selector_all("table tbody tr")
            if rows:
                extra.extend(await self._parse_table_rows(rows))
            else:
                cards = await page.query_selector_all(
                    ".scholarship-card, .scheme-row, .card"
                )
                extra.extend(await self._parse_cards(cards))
        return extra

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_scheme_dict(
        *,
        scheme_name: str,
        categories: list[str],
        benefits: str,
        eligibility_text: str,
        deadline: str | None,
    ) -> dict[str, Any]:
        """Construct a dict compatible with ``SchemeMetadata``."""
        return {
            "scheme_id": scheme_name.lower().replace(" ", "_")[:60],
            "scheme_name": scheme_name,
            "provider": "National Scholarship Portal",
            "categories": categories,
            "income_ceiling": None,
            "education_levels": [],
            "state": "All India",
            "benefits": benefits,
            "deadline": deadline,
            "eligibility_text": eligibility_text,
            "documents_required": [],
            "application_process": "",
            "source_url": NSP_LISTING_URL,
        }

    @staticmethod
    def _parse_categories(text: str) -> list[str]:
        """Best-effort category extraction from raw text."""
        cats: list[str] = []
        text_lower = text.lower()
        for label in ("SC", "ST", "OBC", "Minority", "EBC", "General", "EWS"):
            if label.lower() in text_lower:
                cats.append(label)
        return cats or ["General"]

    @staticmethod
    def _extract_field(text: str, field: str) -> list[str]:
        """Pull a comma-separated list associated with *field* from freeform text."""
        import re

        pattern = rf"{field}\s*[:\-]\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return [v.strip() for v in match.group(1).split(",") if v.strip()]
        return []

    @staticmethod
    def _extract_field_str(text: str, field: str) -> str:
        import re

        pattern = rf"{field}\s*[:\-]\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_deadline(text: str) -> str | None:
        """Try to normalise a deadline string into ISO date."""
        if not text:
            return None
        import re

        # Attempt dd/mm/yyyy or dd-mm-yyyy
        m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", text)
        if m:
            try:
                dt = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        return text.strip() or None


# ------------------------------------------------------------------
# Quick CLI smoke test
# ------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def _main() -> None:
        scraper = NSPScraper(headless=True)
        results = await scraper.scrape()
        print(f"Scraped {len(results)} schemes from NSP")
        for r in results[:3]:
            print(f"  - {r['scheme_name']}")

    asyncio.run(_main())
