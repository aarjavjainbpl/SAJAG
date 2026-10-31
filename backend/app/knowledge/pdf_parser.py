import os
import json
import re
from typing import List, Dict, Any
from pypdf import PdfReader

REPORT_METADATA = {
    "IOCL Report.pdf": {
        "report_id": "OISD-ACCI-06-2022",
        "title": "Investigation Committee Report on Fire Incident at IOCL Haldia Refinery",
        "incident": "IOCL Haldia Refinery MSQ Unit Naphtha Leak, Gas Cutting Fire & Fatalities",
        "facility": "IOCL Haldia Refinery, West Bengal, India",
        "date": "2021-12-21"
    },
    "Tesoro_Anacortes Report.pdf": {
        "report_id": "CSB-2010-08-I-WA",
        "title": "Catastrophic Rupture of Heat Exchanger at Tesoro Anacortes Refinery",
        "incident": "Tesoro Anacortes NHT Heat Exchanger E-6600E HTHA Rupture and Fire",
        "facility": "Tesoro Anacortes Refinery, Washington",
        "date": "2010-04-02"
    },
    "Chevron Report.pdf": {
        "report_id": "CSB-2012-03-I-CA",
        "title": "Chevron Richmond Refinery Pipe Rupture and Fire",
        "incident": "Chevron Richmond Crude Unit 4-Sidecut Sulfidation Corrosion Pipe Rupture",
        "facility": "Chevron Richmond Refinery, California",
        "date": "2012-08-06"
    }
}

_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_root_dir = os.path.dirname(_base_dir)
_data_dir = os.getenv(
    "DATA_DIR",
    os.path.join(_base_dir, "data") if os.path.exists(os.path.join(_base_dir, "data")) else os.path.join(_root_dir, "data")
)
IOCL_JSON_PATH = os.path.join(_data_dir, "priority_reports", "iocl_haldia_pages.json")

class PDFReportParser:
    """
    Extracts text page-by-page from prioritized industrial safety investigation reports:
    1. IOCL Haldia Refinery (OISD)
    2. Tesoro Anacortes Refinery (CSB)
    3. Chevron Richmond Refinery (CSB)
    Preserving document provenance, exact page citations, and section boundaries.
    """

    @classmethod
    def parse_pdf(cls, pdf_path: str) -> List[Dict[str, Any]]:
        filename = os.path.basename(pdf_path)
        meta = REPORT_METADATA.get(filename, {
            "report_id": "REF-DOC",
            "title": filename,
            "incident": filename,
            "facility": "Industrial Refinery",
            "date": "Unknown"
        })

        reader = PdfReader(pdf_path)
        pages_data = []
        current_section = "Background / Overview"

        # Check if scanned document with pre-transcribed pages (e.g. IOCL Haldia)
        iocl_pages = {}
        if filename == "IOCL Report.pdf" and os.path.exists(IOCL_JSON_PATH):
            with open(IOCL_JSON_PATH, "r", encoding="utf-8") as f:
                iocl_pages = json.load(f)

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1

            if filename == "IOCL Report.pdf" and str(page_num) in iocl_pages:
                cleaned_text = iocl_pages[str(page_num)]
            else:
                raw_text = page.extract_text() or ""
                cleaned_text = cls._clean_text(raw_text)

            if not cleaned_text:
                continue

            detected_sec = cls._detect_section_header(cleaned_text)
            if detected_sec:
                current_section = detected_sec

            pages_data.append({
                "filename": filename,
                "report_id": meta["report_id"],
                "source_report": meta["title"],
                "incident": meta["incident"],
                "facility": meta["facility"],
                "incident_date": meta["date"],
                "page_number": page_num,
                "section": current_section,
                "raw_text": cleaned_text
            })

        return pages_data

    @staticmethod
    def _clean_text(text: str) -> str:
        lines = [line.strip() for line in text.split("\n")]
        cleaned_lines = [l for l in lines if l and not (l.isdigit() and len(l) <= 3)]
        return "\n".join(cleaned_lines)

    @staticmethod
    def _detect_section_header(text: str) -> str:
        lower = text[:600].lower()
        if "recommendation" in lower and any(w in lower for w in ["9.0", "8.0", "6.0", "1.5", "committee", "proposes", "makes the following"]):
            return "Recommendations"
        if "root cause" in lower or "probable reasons" in lower or "8.0 root" in lower or "7.0 probable" in lower:
            return "Root Causes & Failure Analysis"
        if "contributing cause" in lower or "contributing factor" in lower:
            return "Contributing Factors"
        if "conclusion" in lower or "8.0 conclusion" in lower:
            return "Investigator Conclusions"
        if "near miss" in lower or "near-miss" in lower or "5.0 near-miss" in lower:
            return "Near-Miss Events & History"
        if "key lesson" in lower or "key lessons" in lower:
            return "Key Lessons Learned"
        if "incident description" in lower or "3.0 incident description" in lower or "4.0 incident description" in lower or "the incident" in lower:
            return "Incident Description & Chronology"
        if "executive summary" in lower or "1.0 executive summary" in lower or "1.0 introduction" in lower:
            return "Executive Summary & Introduction"
        if "technical analysis" in lower or "4.0 technical analysis" in lower or "htha" in lower or "sulfidation" in lower:
            return "Technical & Metallurgical Analysis"
        if "organizational" in lower or "safety culture" in lower or "5.0 organizational" in lower or "5.5 chevron" in lower:
            return "Organizational & Safety Culture Analysis"
        if "regulatory" in lower or "7.0 regulatory" in lower:
            return "Regulatory Oversight Analysis"
        return ""
