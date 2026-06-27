"""
Requests + BeautifulSoup scraper for UGC (University Grants Commission)
fellowship and scholarship pages.

UGC publishes fellowship details on static HTML pages, so a lightweight
requests-based approach works (no JS rendering needed).
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

UGC_BASE_URL = "https://www.ugc.gov.in"
UGC_FELLOWSHIP_URLS = [
    f"{UGC_BASE_URL}/pdfnews/Scheme.html",
    f"{UGC_BASE_URL}/Fellowships",
    f"{UGC_BASE_URL}/scholarships",
]

REQUEST_TIMEOUT = 30  # seconds
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class UGCScraper:
    """Scrapes UGC fellowship / scholarship pages using requests + BeautifulSoup."""

    def __init__(self, urls: list[str] | None = None) -> None:
        self.urls = urls or UGC_FELLOWSHIP_URLS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scrape(self) -> list[dict[str, Any]]:
        """
        Fetch each configured UGC page, parse HTML, and return a list
        of scheme dicts compatible with ``SchemeMetadata``.
        """
        all_schemes: list[dict[str, Any]] = []
        for url in self.urls:
            try:
                logger.info("Fetching UGC page: %s", url)
                resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                schemes = self._parse_page(resp.text, url)
                logger.info("  -> Extracted %d schemes from %s", len(schemes), url)
                all_schemes.extend(schemes)
            except requests.RequestException:
                logger.exception("Failed to fetch %s", url)
        return all_schemes

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------
    def _parse_page(self, html: str, source_url: str) -> list[dict[str, Any]]:
        """Dispatch to the best parser for a given page structure."""
        soup = BeautifulSoup(html, "html.parser")

        # Strategy 1: Table with scheme rows
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) >= 3:  # header + at least 2 data rows
                return self._parse_table(rows, source_url)

        # Strategy 2: Definition-list / accordion sections
        schemes_from_sections = self._parse_sections(soup, source_url)
        if schemes_from_sections:
            return schemes_from_sections

        # Strategy 3: Link list (each scheme is a hyperlink to its detail page)
        return self._parse_link_list(soup, source_url)

    def _parse_table(self, rows: list[Tag], source_url: str) -> list[dict[str, Any]]:
        """Extract schemes from an HTML ``<table>``."""
        results: list[dict[str, Any]] = []
        header_cells = [c.get_text(strip=True).lower() for c in rows[0].find_all(["th", "td"])]

        name_idx = self._find_col(header_cells, ["scheme", "fellowship", "name", "title"])
        cat_idx = self._find_col(header_cells, ["category", "group"])
        benefit_idx = self._find_col(header_cells, ["amount", "benefit", "stipend", "value"])
        elig_idx = self._find_col(header_cells, ["eligibility", "criteria", "qualification"])

        for row in rows[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all("td")]
            if not cells:
                continue

            scheme_name = cells[name_idx] if name_idx < len(cells) else ""
            if not scheme_name or len(scheme_name) < 5:
                continue

            results.append(
                self._build_scheme_dict(
                    scheme_name=scheme_name,
                    categories=self._infer_categories(
                        cells[cat_idx] if cat_idx < len(cells) else ""
                    ),
                    benefits=cells[benefit_idx] if benefit_idx < len(cells) else "",
                    eligibility_text=cells[elig_idx] if elig_idx < len(cells) else "",
                    source_url=source_url,
                )
            )
        return results

    def _parse_sections(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
        """Extract schemes from heading + paragraph sections."""
        results: list[dict[str, Any]] = []
        headings = soup.find_all(["h2", "h3", "h4"])
        for heading in headings:
            title = heading.get_text(strip=True)
            if not title or len(title) < 8:
                continue

            # Collect all text until the next heading
            content_parts: list[str] = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ("h2", "h3", "h4"):
                    break
                content_parts.append(sibling.get_text(strip=True))
            body = "\n".join(content_parts)

            if any(kw in title.lower() for kw in ("fellowship", "scholarship", "scheme", "grant")):
                results.append(
                    self._build_scheme_dict(
                        scheme_name=title,
                        categories=self._infer_categories(body),
                        benefits=self._extract_amount(body),
                        eligibility_text=body[:500],
                        source_url=source_url,
                    )
                )
        return results

    def _parse_link_list(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
        """Fall back to extracting named links that look like scholarship pages."""
        results: list[dict[str, Any]] = []
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            if not text or len(text) < 10:
                continue
            if any(kw in text.lower() for kw in ("fellowship", "scholarship", "scheme")):
                results.append(
                    self._build_scheme_dict(
                        scheme_name=text,
                        categories=[],
                        benefits="",
                        eligibility_text="",
                        source_url=source_url,
                    )
                )
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _find_col(headers: list[str], keywords: list[str]) -> int:
        """Return the column index whose header contains one of *keywords*."""
        for i, h in enumerate(headers):
            if any(kw in h for kw in keywords):
                return i
        return 0  # default to first column

    @staticmethod
    def _build_scheme_dict(
        *,
        scheme_name: str,
        categories: list[str],
        benefits: str,
        eligibility_text: str,
        source_url: str,
    ) -> dict[str, Any]:
        return {
            "scheme_id": scheme_name.lower().replace(" ", "_")[:60],
            "scheme_name": scheme_name,
            "provider": "University Grants Commission (UGC)",
            "categories": categories or ["General"],
            "income_ceiling": None,
            "education_levels": ["Postgraduate", "PhD"],
            "state": "All India",
            "benefits": benefits,
            "deadline": None,
            "eligibility_text": eligibility_text,
            "documents_required": [],
            "application_process": "",
            "source_url": source_url,
            "source": "ugc",
        }

    @staticmethod
    def _infer_categories(text: str) -> list[str]:
        cats: list[str] = []
        text_lower = text.lower()
        for label in ("SC", "ST", "OBC", "Minority", "EBC", "General", "EWS", "Women"):
            if label.lower() in text_lower:
                cats.append(label)
        return cats

    @staticmethod
    def _extract_amount(text: str) -> str:
        """Pull the first monetary figure from text (₹ or Rs.)."""
        m = re.search(r"(?:Rs\.?|₹)\s*[\d,]+(?:\s*(?:per\s+month|p\.m\.|p\.a\.|lakh|/-)?)?", text)
        return m.group(0).strip() if m else ""


# ------------------------------------------------------------------
# Quick CLI smoke test
# ------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = UGCScraper()
    results = scraper.scrape()
    print(f"Scraped {len(results)} schemes from UGC")
    for r in results[:5]:
        print(f"  - {r['scheme_name']}")
