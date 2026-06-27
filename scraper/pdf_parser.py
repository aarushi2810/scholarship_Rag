"""
PDF parser for scholarship notification documents.

Government departments publish scholarship circulars, guidelines, and
notifications as PDFs.  This module uses ``pdfplumber`` to extract text,
then applies regex heuristics to pull out structured fields.

Usage:
    from scraper.pdf_parser import parse_scholarship_pdf, parse_pdf_directory

    scheme = parse_scholarship_pdf("data/raw/pdfs/nsp_notification.pdf")
    all_schemes = parse_pdf_directory("data/raw/pdfs/")
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def parse_scholarship_pdf(pdf_path: str) -> dict[str, Any]:
    """
    Open a scholarship notification PDF and extract structured fields.

    Parameters
    ----------
    pdf_path : str
        Path to the PDF file.

    Returns
    -------
    dict
        A dict with keys matching ``SchemeMetadata``:
        scheme_name, eligibility_text, income_ceiling, deadline, benefits,
        categories, education_levels, documents_required, raw_text, etc.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber is not installed. Run: pip install pdfplumber")
        return {"error": "pdfplumber not installed", "source_file": pdf_path}

    path = Path(pdf_path)
    if not path.exists():
        logger.error("PDF not found: %s", pdf_path)
        return {"error": "file not found", "source_file": pdf_path}

    logger.info("Parsing PDF: %s", pdf_path)

    pages_text: list[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
    except Exception:
        logger.exception("Failed to read PDF: %s", pdf_path)
        return {"error": "failed to read PDF", "source_file": pdf_path}

    full_text = "\n\n".join(pages_text)
    if not full_text.strip():
        logger.warning("PDF appears empty: %s", pdf_path)
        return {"error": "empty PDF", "source_file": pdf_path}

    # ----------------------------------------------------------------
    # Field extraction via regex patterns
    # ----------------------------------------------------------------
    scheme_name = _extract_scheme_name(full_text, path.stem)
    eligibility_text = _extract_section(
        full_text,
        [
            r"eligibility",
            r"who\s+can\s+apply",
            r"qualifying\s+criteria",
            r"conditions\s+for\s+eligibility",
        ],
    )
    income_ceiling = _extract_income_limit(full_text)
    deadline = _extract_deadline(full_text)
    benefits = _extract_section(
        full_text,
        [r"benefits?", r"scholarship\s+amount", r"financial\s+assistance", r"stipend"],
    )
    documents_required = _extract_documents(full_text)
    categories = _infer_categories(full_text)
    education_levels = _infer_education_levels(full_text)
    application_process = _extract_section(
        full_text,
        [r"how\s+to\s+apply", r"application\s+process", r"procedure"],
    )

    return {
        "scheme_id": scheme_name.lower().replace(" ", "_")[:60],
        "scheme_name": scheme_name,
        "provider": "PDF Notification",
        "categories": categories,
        "income_ceiling": income_ceiling,
        "education_levels": education_levels,
        "state": "All India",
        "benefits": benefits,
        "deadline": deadline,
        "eligibility_text": eligibility_text,
        "documents_required": documents_required,
        "application_process": application_process,
        "source_url": "",
        "source": "pdf",
        "source_file": str(pdf_path),
        "raw_text": full_text[:5000],  # cap for downstream storage
    }


def parse_pdf_directory(dir_path: str) -> list[dict[str, Any]]:
    """
    Process every ``.pdf`` file in *dir_path* and return a list of
    parsed scheme dicts.

    Parameters
    ----------
    dir_path : str
        Directory containing PDF files.

    Returns
    -------
    list[dict]
    """
    directory = Path(dir_path)
    if not directory.is_dir():
        logger.error("Directory not found: %s", dir_path)
        return []

    pdf_files = sorted(directory.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", dir_path)
        return []

    logger.info("Found %d PDFs in %s", len(pdf_files), dir_path)
    results: list[dict[str, Any]] = []
    for pdf_file in pdf_files:
        parsed = parse_scholarship_pdf(str(pdf_file))
        if "error" not in parsed:
            results.append(parsed)
        else:
            logger.warning("Skipping %s: %s", pdf_file.name, parsed.get("error"))
    return results


# ====================================================================
# Internal extraction helpers
# ====================================================================

def _extract_scheme_name(text: str, fallback: str) -> str:
    """
    Try to find the scheme/scholarship name near the top of the document.
    Government PDFs typically have the name in the first few lines as a
    heading, often in all-caps or following "Subject:" / "Scheme Name:".
    """
    # Pattern 1: "Scheme Name: XYZ"
    m = re.search(
        r"(?:scheme\s*name|name\s*of\s*(?:the\s*)?scheme|subject)\s*[:\-]\s*(.+)",
        text[:2000],
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().split("\n")[0]

    # Pattern 2: First all-caps line longer than 15 chars (likely a title)
    for line in text[:1500].split("\n"):
        stripped = line.strip()
        if len(stripped) > 15 and stripped == stripped.upper() and stripped.isascii():
            return stripped.title()

    # Fallback to filename
    return fallback.replace("_", " ").replace("-", " ").title()


def _extract_section(text: str, heading_patterns: list[str]) -> str:
    """
    Find the first matching section heading and return the text until
    the next heading-like line (all-caps or numbered heading).
    """
    for pat in heading_patterns:
        m = re.search(
            rf"(?:^|\n)\s*\d*\.?\s*{pat}\s*[:\-]?\s*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\n[A-Z]{{3,}}|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if m:
            section = m.group(1).strip()
            # Cap at ~1000 chars to avoid returning half the document
            return section[:1000]
    return ""


def _extract_income_limit(text: str) -> float | None:
    """Pull the family income ceiling from the text."""
    patterns = [
        r"(?:annual|family)\s+income\s+(?:should\s+)?(?:not\s+exceed|be\s+(?:below|less\s+than|within)|upto|up\s+to|limit|ceiling)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)?",
        r"income\s+(?:ceiling|limit|cap)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)?",
        r"(?:Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)?\s*(?:per\s+annum|p\.a\.)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                value = float(raw)
                # Normalise: if value < 100, assume it's in lakhs
                if value < 100:
                    value *= 100_000
                return value
            except ValueError:
                continue
    return None


def _extract_deadline(text: str) -> str | None:
    """Find the application deadline date."""
    patterns = [
        r"(?:last\s+date|deadline|closing\s+date|apply\s+(?:by|before))\s*[:\-]?\s*(\d{1,2}[\s/\-]\w+[\s/\-]\d{4})",
        r"(?:last\s+date|deadline)\s*[:\-]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _extract_documents(text: str) -> list[str]:
    """Extract a list of required documents."""
    section = _extract_section(
        text,
        [r"documents?\s+required", r"documents?\s+to\s+be\s+(?:submitted|uploaded|attached)"],
    )
    if not section:
        return []

    docs: list[str] = []
    # Look for numbered or bulleted items
    for line in section.split("\n"):
        stripped = line.strip()
        cleaned = re.sub(r"^[\d\.\)\-\•\*]+\s*", "", stripped)
        if cleaned and len(cleaned) > 5:
            docs.append(cleaned)
    return docs[:15]  # cap


def _infer_categories(text: str) -> list[str]:
    cats: list[str] = []
    text_lower = text.lower()
    for label in ("SC", "ST", "OBC", "Minority", "EBC", "General", "EWS"):
        if label.lower() in text_lower:
            cats.append(label)
    return cats or ["General"]


def _infer_education_levels(text: str) -> list[str]:
    levels: list[str] = []
    text_lower = text.lower()
    mapping = {
        "Pre-Matric": ["pre-matric", "pre matric", "class 1", "class 9", "class 10"],
        "Post-Matric": ["post-matric", "post matric", "class 11", "class 12"],
        "Undergraduate": ["undergraduate", "under graduate", "ug ", "graduation", "bachelor"],
        "Postgraduate": ["postgraduate", "post graduate", "pg ", "master"],
        "PhD": ["phd", "ph.d", "doctoral", "research fellow"],
    }
    for level, keywords in mapping.items():
        if any(kw in text_lower for kw in keywords):
            levels.append(level)
    return levels or ["Post-Matric"]


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python -m scraper.pdf_parser <pdf_path_or_directory>")
        sys.exit(1)

    target = sys.argv[1]
    if os.path.isdir(target):
        results = parse_pdf_directory(target)
    else:
        results = [parse_scholarship_pdf(target)]

    import json

    print(json.dumps(results, indent=2, ensure_ascii=False))
