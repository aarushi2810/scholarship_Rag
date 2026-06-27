"""
State-portal scraper for Punjab and Maharashtra scholarship websites.

Each state portal has a different HTML structure, so this class dispatches
to state-specific parsing logic based on the ``state`` parameter.

Supported portals:
  - Punjab:       https://scholarships.punjab.gov.in
  - Maharashtra:  https://mahadbt.maharashtra.gov.in
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

PORTAL_CONFIG: dict[str, dict[str, str]] = {
    "Punjab": {
        "base_url": "https://scholarships.punjab.gov.in",
        "listing_path": "/",
        "label": "Punjab Scholarship Portal",
    },
    "Maharashtra": {
        "base_url": "https://mahadbt.maharashtra.gov.in",
        "listing_path": "/SchemeData/SchemeData",
        "label": "MahaDBT – Maharashtra",
    },
}

REQUEST_TIMEOUT = 30
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class StatePortalScraper:
    """Scrape scholarship listings from a supported Indian state portal."""

    def __init__(self, state: str) -> None:
        state_key = state.strip().title()
        if state_key not in PORTAL_CONFIG:
            raise ValueError(
                f"Unsupported state '{state}'. Supported: {list(PORTAL_CONFIG)}"
            )
        self.state = state_key
        self.config = PORTAL_CONFIG[state_key]
        self.base_url: str = self.config["base_url"]
        self.listing_url: str = f"{self.base_url}{self.config['listing_path']}"
        self.provider: str = self.config["label"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scrape(self) -> list[dict[str, Any]]:
        """
        Fetch the state portal's listing page and return scheme dicts.

        Returns a list compatible with ``SchemeMetadata``.
        """
        try:
            logger.info("Fetching %s portal: %s", self.state, self.listing_url)
            resp = requests.get(
                self.listing_url, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to fetch %s portal", self.state)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Dispatch to state-specific parser
        if self.state == "Punjab":
            schemes = self._parse_punjab(soup)
        elif self.state == "Maharashtra":
            schemes = self._parse_maharashtra(soup)
        else:
            schemes = self._parse_generic(soup)

        logger.info("Extracted %d schemes from %s portal", len(schemes), self.state)

        # Tag every record
        for s in schemes:
            s["source"] = self.state.lower()
            s.setdefault("state", self.state)
            s.setdefault("provider", self.provider)
            s.setdefault("source_url", self.listing_url)
        return schemes

    # ------------------------------------------------------------------
    # Punjab-specific parser
    # ------------------------------------------------------------------
    def _parse_punjab(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse the Punjab scholarship portal's listing page."""
        results: list[dict[str, Any]] = []

        # Strategy 1: Table rows
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows[1:]:  # skip header
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) < 2:
                    continue
                scheme_name = cells[0]
                if not scheme_name or len(scheme_name) < 5:
                    continue
                results.append(
                    self._build_scheme_dict(
                        scheme_name=scheme_name,
                        categories=self._infer_categories(
                            cells[1] if len(cells) > 1 else ""
                        ),
                        benefits=cells[2] if len(cells) > 2 else "",
                        eligibility_text=cells[3] if len(cells) > 3 else "",
                    )
                )

        if results:
            return results

        # Strategy 2: Card / div sections
        cards = soup.find_all(["div", "li"], class_=re.compile(r"scheme|card|item", re.I))
        for card in cards:
            title_el = card.find(["h3", "h4", "h5", "strong", "a"])
            if not title_el:
                continue
            name = title_el.get_text(strip=True)
            if not name or len(name) < 5:
                continue
            body = card.get_text(strip=True)
            results.append(
                self._build_scheme_dict(
                    scheme_name=name,
                    categories=self._infer_categories(body),
                    benefits=self._extract_amount(body),
                    eligibility_text=body[:500],
                )
            )

        # Strategy 3: Any headings that mention scholarship / scheme
        if not results:
            results = self._parse_headings(soup)

        return results

    # ------------------------------------------------------------------
    # Maharashtra-specific parser
    # ------------------------------------------------------------------
    def _parse_maharashtra(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse the MahaDBT scholarship portal."""
        results: list[dict[str, Any]] = []

        # MahaDBT typically shows an accordion or department-wise listing
        panels = soup.find_all(
            ["div", "section"],
            class_=re.compile(r"panel|accordion|scheme|card|department", re.I),
        )
        for panel in panels:
            title_el = panel.find(
                ["h3", "h4", "h5", "a", "span"],
                class_=re.compile(r"title|heading|name", re.I),
            )
            if not title_el:
                title_el = panel.find(["h3", "h4", "h5", "strong"])
            if not title_el:
                continue
            name = title_el.get_text(strip=True)
            if not name or len(name) < 5:
                continue

            body = panel.get_text(strip=True)
            results.append(
                self._build_scheme_dict(
                    scheme_name=name,
                    categories=self._infer_categories(body),
                    benefits=self._extract_amount(body),
                    eligibility_text=body[:500],
                )
            )

        if results:
            return results

        # Fallback: table parsing
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) < 2 or not cells[0]:
                    continue
                results.append(
                    self._build_scheme_dict(
                        scheme_name=cells[0],
                        categories=self._infer_categories(
                            cells[1] if len(cells) > 1 else ""
                        ),
                        benefits=cells[2] if len(cells) > 2 else "",
                        eligibility_text=cells[3] if len(cells) > 3 else "",
                    )
                )

        if not results:
            results = self._parse_headings(soup)

        return results

    # ------------------------------------------------------------------
    # Fallback generic parser
    # ------------------------------------------------------------------
    def _parse_generic(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        return self._parse_headings(soup)

    def _parse_headings(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract schemes from heading elements."""
        results: list[dict[str, Any]] = []
        for heading in soup.find_all(["h2", "h3", "h4"]):
            text = heading.get_text(strip=True)
            if any(kw in text.lower() for kw in ("scholarship", "scheme", "fellowship")):
                body_parts: list[str] = []
                for sib in heading.find_next_siblings():
                    if sib.name in ("h2", "h3", "h4"):
                        break
                    body_parts.append(sib.get_text(strip=True))
                body = "\n".join(body_parts)
                results.append(
                    self._build_scheme_dict(
                        scheme_name=text,
                        categories=self._infer_categories(body),
                        benefits=self._extract_amount(body),
                        eligibility_text=body[:500],
                    )
                )
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_scheme_dict(
        self,
        *,
        scheme_name: str,
        categories: list[str],
        benefits: str,
        eligibility_text: str,
    ) -> dict[str, Any]:
        return {
            "scheme_id": scheme_name.lower().replace(" ", "_")[:60],
            "scheme_name": scheme_name,
            "provider": self.provider,
            "categories": categories or ["General"],
            "income_ceiling": None,
            "education_levels": [],
            "state": self.state,
            "benefits": benefits,
            "deadline": None,
            "eligibility_text": eligibility_text,
            "documents_required": [],
            "application_process": "",
            "source_url": self.listing_url,
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
        m = re.search(
            r"(?:Rs\.?|₹)\s*[\d,]+(?:\s*(?:per\s+month|p\.m\.|p\.a\.|lakh|/-)?)?",
            text,
        )
        return m.group(0).strip() if m else ""


# ------------------------------------------------------------------
# Quick CLI smoke test
# ------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for state in ("Punjab", "Maharashtra"):
        scraper = StatePortalScraper(state)
        results = scraper.scrape()
        print(f"[{state}] Scraped {len(results)} schemes")
        for r in results[:3]:
            print(f"  - {r['scheme_name']}")
