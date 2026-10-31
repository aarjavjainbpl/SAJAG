"""
OSHA Fatality & Catastrophe Data Normalizer and High-Energy Reference Registry.

This service normalizes historical OSHA incident records across multiple fiscal years
and exports a curated, read-only reference registry (`data/osha_fatal_patterns.json`)
separate from the live operational incident queue.
"""

import os
import re
import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("sajag.osha_normalizer")

US_STATE_CODES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'PR', 'DC', 'VI', 'AS', 'GU', 'MP'
}

STATE_FULL_NAMES = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
    'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
    'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
    'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
    'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
    'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
    'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY',
    'puerto rico': 'PR', 'district of columbia': 'DC', 'virgin islands': 'VI', 'american samoa': 'AS'
}

# Empirical high-energy mechanism keywords for reference categorization
REFERENCE_HAZARD_PATTERNS = {
    "Gravity / Falls from Height": [
        r"\bfell\b", r"\bfall\b", r"\bfalling\b", r"\broof\b", r"\bladder\b",
        r"\bscaffold\b", r"\bmanlift\b", r"\baerial lift\b", r"\bboom lift\b",
        r"\bskylight\b", r"\bfloor opening\b", r"\bcatwalk\b", r"\bmezzanine\b",
        r"\btower\b", r"\bparapet\b", r"\bstairs\b", r"\bbalcony\b", r"\bfrom \d+[- ]feet\b"
    ],
    "Suspended / Heavy Loads & Rigging": [
        r"\bcrane\b", r"\brigging\b", r"\bhoist\b", r"\bderrick\b", r"\bsling\b",
        r"\bwinch\b", r"\bdropped load\b", r"\bsuspended\b", r"\bcounterweight\b",
        r"\bload shifted\b", r"\bpipe fell\b", r"\bsteel beam fell\b", r"\bcoil fell\b"
    ],
    "Electrical (Shock / Arc Flash / High Voltage)": [
        r"\belectrocute\w*\b", r"\belectrical shock\b", r"\barc flash\b", r"\barc blast\b",
        r"\bpowerline\b", r"\bpower line\b", r"\btransmission line\b", r"\bconductors?\b",
        r"\benergized\b", r"\blive wire\b", r"\bswitchgear\b", r"\bvolt\b", r"\bbreaker\b"
    ],
    "Pressurized Equipment / Piping Burst": [
        r"\bhigh pressure\b", r"\bpressurized\b", r"\bpressure test\w*\b", r"\bhose burst\b",
        r"\bpipe burst\b", r"\bpneumatic\b", r"\bhydraulic pressure\b", r"\bpressure vessel\b",
        r"\bruptured\b", r"\bexploding tire\b", r"\btire exploded\b", r"\bwheel rim exploded\b"
    ],
    "Hazardous Chemicals / Toxic Atmosphere / Asphyxiation": [
        r"\bh2s\b", r"\bhydrogen sulfide\b", r"\bcarbon monoxide\b", r"\basphyxiat\w*\b",
        r"\btoxic\b", r"\bchemical\b", r"\bnitrogen\b", r"\bammonia\b", r"\bchlorine\b",
        r"\bmuriatic acid\b", r"\bselenium\b", r"\bsewer gas\b", r"\bfumes\b", r"\bsuffocat\w*\b"
    ],
    "Confined Space / Trench Engulfment": [
        r"\btrench\b", r"\bcave-in\b", r"\bcaved in\b", r"\bengulfed\b", r"\bgrain bin\b",
        r"\bsilo\b", r"\bmanhole\b", r"\bburied under\b", r"\bexcavation\b", r"\bconfined space\b"
    ],
    "Mechanical / Rotating Equipment / Pinch Point": [
        r"\bconveyor\b", r"\bauger\b", r"\blathe\b", r"\bpinch point\b", r"\bcrushed in machine\b",
        r"\bwood chipper\b", r"\bchipper\b", r"\bentangled\b", r"\bbaler\b", r"\broller\b",
        r"\bmachine guard\b", r"\bpto\b", r"\bpower take-off\b", r"\bdrilling rig\b"
    ],
    "Heavy Mobile Equipment / Vehicular": [
        r"\bforklift\b", r"\bdump truck\b", r"\bbackhoe\b", r"\bexcavator\b", r"\bbulldozer\b",
        r"\bskid steer\b", r"\bloader\b", r"\btractor\b", r"\bcompact\w*\b", r"\brun over\b",
        r"\bbacked over\b", r"\btruck\b", r"\btrailer\b", r"\broller\b", r"\bmotor vehicle\b",
        r"\bhit and run\b", r"\bstruck by vehicle\b"
    ],
    "Thermal / Fire / Explosion": [
        r"\bexplosion\b", r"\bexploded\b", r"\bflash fire\b", r"\bfire\b", r"\bburns?\b",
        r"\bignited\b", r"\bignit\w*\b", r"\bhot grease\b", r"\bmolten\b", r"\bhot oil\b",
        r"\bwelding torch\b", r"\bflammable\b"
    ],
    "Environmental / Medical / Other": [
        r"\bheat stroke\b", r"\bheat exhaustion\b", r"\bheat stress\b", r"\bhyperthermia\b",
        r"\bdrowned\b", r"\bdrowning\b", r"\bheart attack\b", r"\bcardiac\b", r"\blightning\b",
        r"\bbee sting\b", r"\binsect sting\b", r"\bspider bite\b", r"\bshot\b", r"\brobbery\b"
    ]
}


class OshaDataNormalizer:
    """Normalizes and catalogs raw OSHA weekly fatality and catastrophe datasets."""

    def __init__(self):
        self.state_clean_regex = re.compile(r'([A-Z]{2})\*?')

    def clean_text(self, text: Any) -> str:
        """Removes encoding corruption and normalizes whitespace."""
        if text is None:
            return ""
        s = str(text)
        # Fix non-breaking spaces and common CP1252 / ISO artifacts
        s = s.replace('\xa0', ' ')
        s = s.replace('\ufffd', ' ')
        s = s.replace('â€œ', '"').replace('â€\x9d', '"').replace('â€™', "'").replace('â€“', '-')
        s = re.sub(r'[\x80-\x9f]', ' ', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    def normalize_date(self, date_str: str) -> Optional[str]:
        """Normalizes M/D/YYYY, MM/DD/YY, and ISO date strings to YYYY-MM-DD."""
        if not date_str:
            return None
        cleaned = self.clean_text(date_str).replace('\\', '/').replace('-', '/')
        
        # Match standard M/D/Y parts
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', cleaned)
        if not match:
            return None
            
        m, d, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if y < 100:
            # 2-digit year pivot: 00-40 -> 2000-2040, 41-99 -> 1941-1999
            y = 2000 + y if y <= 40 else 1900 + y
            
        try:
            dt = datetime(year=y, month=m, day=d)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return None

    def derive_fiscal_year(self, incident_date_iso: Optional[str], raw_fy: Optional[str]) -> Tuple[str, str]:
        """Returns standard (Fiscal Year, Source) e.g. ('FY 2012', 'explicit')."""
        if raw_fy and raw_fy.strip():
            cleaned = self.clean_text(raw_fy).upper()
            if not cleaned.startswith('FY'):
                cleaned = f"FY {cleaned}"
            # Standardize spacing e.g. 'FY 2010'
            cleaned = re.sub(r'FY\s*(\d+)', r'FY \1', cleaned)
            return cleaned, "explicit"
            
        if incident_date_iso:
            try:
                dt = datetime.strptime(incident_date_iso, '%Y-%m-%d')
                # US Government fiscal year starts October 1
                fy_year = dt.year + 1 if dt.month >= 10 else dt.year
                return f"FY {fy_year}", "derived_from_incident_date"
            except Exception:
                pass
                
        return "FY Unknown", "unresolved"

    def parse_company_location(self, raw_str: str) -> Dict[str, Optional[str]]:
        """
        Parses unnormalized company string into company_name, city, state, zip_code.
        Preserves raw string regardless of parsing outcome.
        """
        raw_clean = self.clean_text(raw_str)
        if not raw_clean:
            return {
                "raw_location": "",
                "company_name": "",
                "city": None,
                "state": None,
                "zip_code": None
            }

        text = raw_clean
        # Remove trailing double punctuation
        text = re.sub(r',+', ',', text).strip(', ')

        # 1. Check for standard trailing: ", City, ST 12345" or ", ST 12345" or ", ST, 12345"
        # Also handles "ST,. 12345", "ST12345", or trailing name after zip ", PA 17402, Employee"
        m_zip_trailing = re.search(r',\s*([^,]+?)[,\s]+([A-Za-z]{2}|\b[A-Za-z\s]{4,15}\b)\*?[,\.\s]*(\d{5}(?:-\d{4})?)', text)
        if m_zip_trailing:
            potential_city = m_zip_trailing.group(1).strip()
            potential_state = m_zip_trailing.group(2).strip().upper()
            potential_zip = m_zip_trailing.group(3)

            resolved_state = None
            if potential_state in US_STATE_CODES:
                resolved_state = potential_state
            elif potential_state.lower() in STATE_FULL_NAMES:
                resolved_state = STATE_FULL_NAMES[potential_state.lower()]

            if resolved_state:
                comp = text[:m_zip_trailing.start()].strip(', ')
                return {
                    "raw_location": raw_clean,
                    "company_name": comp if comp else raw_clean,
                    "city": potential_city if potential_city else None,
                    "state": resolved_state,
                    "zip_code": potential_zip
                }

        # 2. Token based approach scanning right-to-left
        tokens = [t.strip(' ,*') for t in text.split(',') if t.strip(' ,*')]
        if len(tokens) >= 2:
            last_tok = tokens[-1]
            # Match state and optional zip in last token
            m_state = re.search(r'\b([A-Z]{2})\b(?:\s*(\d{5}))?', last_tok)
            if m_state and m_state.group(1) in US_STATE_CODES:
                st = m_state.group(1)
                zp = m_state.group(2)
                city = tokens[-2] if len(tokens) >= 3 else None
                comp = ', '.join(tokens[:-2]) if len(tokens) >= 3 else tokens[0]
                return {
                    "raw_location": raw_clean,
                    "company_name": comp,
                    "city": city,
                    "state": st,
                    "zip_code": zp
                }

            # Check full state name in last token
            for fname, fcode in STATE_FULL_NAMES.items():
                if fname in last_tok.lower():
                    m_zip = re.search(r'\b(\d{5})\b', last_tok)
                    zp = m_zip.group(1) if m_zip else None
                    city = tokens[-2] if len(tokens) >= 3 else None
                    comp = ', '.join(tokens[:-2]) if len(tokens) >= 3 else tokens[0]
                    return {
                        "raw_location": raw_clean,
                        "company_name": comp,
                        "city": city,
                        "state": fcode,
                        "zip_code": zp
                    }

        # Fallback: company is whole text, location unresolved
        return {
            "raw_location": raw_clean,
            "company_name": raw_clean,
            "city": None,
            "state": None,
            "zip_code": None
        }

    def categorize_reference_hazards(self, narrative: str) -> List[str]:
        """
        Extracts reference hazard categories based solely on explicit keywords in narrative.
        Tagged as empirical reference patterns, NOT as confirmed SIF labels.
        """
        if not narrative:
            return ["Uncategorized / Routine"]
            
        text_lower = narrative.lower()
        matched_categories = []
        
        for category, patterns in REFERENCE_HAZARD_PATTERNS.items():
            for p in patterns:
                if re.search(p, text_lower):
                    matched_categories.append(category)
                    break
                    
        return matched_categories if matched_categories else ["Uncategorized / General Event"]

    def parse_csv_file(self, file_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parses a single raw OSHA CSV file with full error and schema handling.
        Preserves original rows and flags any anomalies.
        """
        filename = os.path.basename(file_path)
        stats = {
            "source_file": filename,
            "total_rows_read": 0,
            "schema_detected": "unknown",
            "shifted_headers_corrected": 0,
            "duplicates_in_file": 0,
            "dates_parsed": 0,
            "dates_failed": 0,
            "states_parsed": 0,
            "states_missing": 0,
            "encoding_artifacts_cleaned": 0
        }
        
        records: List[Dict[str, Any]] = []
        seen_narratives = set()

        with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
            reader = list(csv.reader(f))

        if not reader:
            return records, stats

        raw_header = [col.strip() for col in reader[0]]
        rows = reader[1:]
        stats["total_rows_read"] = len(rows)

        # Detect schema type
        is_4_column = (len(raw_header) == 4 and 'Fatality or Catastrophe' in raw_header[3])
        # Detect FY 2012 shifted header where col 3 is description and col 4 is empty in header
        is_fy2012_shifted = (
            len(raw_header) == 5 and
            raw_header[3] == 'Preliminary Description of Incident' and
            raw_header[4] == ''
        )

        if is_4_column:
            stats["schema_detected"] = "4_column_2013_format"
        elif is_fy2012_shifted:
            stats["schema_detected"] = "5_column_fy2012_shifted_header"
        else:
            stats["schema_detected"] = "5_column_standard_format"

        for row_idx, r in enumerate(rows, start=1):
            raw_encoding_count = sum(cell.count('\ufffd') + cell.count('\xa0') for cell in r)
            if raw_encoding_count > 0:
                stats["encoding_artifacts_cleaned"] += 1

            # Extract fields according to detected schema
            raw_fy = None
            raw_summary_date = None
            raw_incident_date = None
            raw_company = ""
            raw_narrative = ""
            raw_outcome_type = None

            if is_4_column:
                raw_incident_date = r[0] if len(r) > 0 else ""
                raw_company = r[1] if len(r) > 1 else ""
                raw_narrative = r[2] if len(r) > 2 else ""
                raw_outcome_type = r[3] if len(r) > 3 else "Fatality"
            elif is_fy2012_shifted:
                stats["shifted_headers_corrected"] += 1
                raw_fy = r[0] if len(r) > 0 else "FY 2012"
                raw_summary_date = r[1] if len(r) > 1 else ""
                raw_incident_date = r[2] if len(r) > 2 else ""
                # Row index 3 is actually Company; index 4 is Preliminary Description
                raw_company = r[3] if len(r) > 3 else ""
                raw_narrative = r[4] if len(r) > 4 else ""
                raw_outcome_type = "Fatality"
            else:
                raw_fy = r[0] if len(r) > 0 else ""
                raw_summary_date = r[1] if len(r) > 1 else ""
                raw_incident_date = r[2] if len(r) > 2 else ""
                raw_company = r[3] if len(r) > 3 else ""
                raw_narrative = r[4] if len(r) > 4 else ""
                raw_outcome_type = "Fatality"

            # Check for duplicate narratives in file
            clean_narr = self.clean_text(raw_narrative)
            dup_key = (self.clean_text(raw_incident_date), clean_narr)
            if dup_key in seen_narratives:
                stats["duplicates_in_file"] += 1
            seen_narratives.add(dup_key)

            # Date normalization
            norm_incident_date = self.normalize_date(raw_incident_date)
            norm_summary_date = self.normalize_date(raw_summary_date)
            if norm_incident_date:
                stats["dates_parsed"] += 1
            else:
                stats["dates_failed"] += 1

            # Fiscal year determination
            fy_str, fy_source = self.derive_fiscal_year(norm_incident_date, raw_fy)

            # Location parsing
            loc_data = self.parse_company_location(raw_company)
            if loc_data["state"]:
                stats["states_parsed"] += 1
            else:
                stats["states_missing"] += 1

            # Hazard categorization
            hazards = self.categorize_reference_hazards(clean_narr)

            # Form record
            rec_id = f"OSHA-{fy_str.replace(' ', '')}-{filename[:8]}-{row_idx:04d}"
            record = {
                "record_id": rec_id,
                "source_file": filename,
                "source_row_index": row_idx,
                "fiscal_year": fy_str,
                "fiscal_year_source": fy_source,
                "summary_report_date": norm_summary_date,
                "incident_date_raw": self.clean_text(raw_incident_date),
                "incident_date": norm_incident_date,
                "company_raw": self.clean_text(raw_company),
                "company_name": loc_data["company_name"],
                "city": loc_data["city"],
                "state": loc_data["state"],
                "zip_code": loc_data["zip_code"],
                "reported_event_type": self.clean_text(raw_outcome_type),
                "original_narrative": raw_narrative,
                "cleaned_narrative": clean_narr,
                "reference_hazard_categories": hazards,
                "classification_nature": "Empirical reference pattern (Non-prescriptive; NOT verified SIF precursor label)"
            }
            records.append(record)

        return records, stats

    def normalize_datasets(
        self,
        file_paths: List[str],
        output_json_path: str,
        report_json_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes all given OSHA CSV files, writes the reference registry JSON,
        and generates a data quality report.
        """
        all_records: List[Dict[str, Any]] = []
        file_summaries: List[Dict[str, Any]] = []
        overall_stats = {
            "execution_timestamp": datetime.now().isoformat(),
            "total_files_processed": len(file_paths),
            "total_records_processed": 0,
            "total_duplicates_found": 0,
            "total_encoding_cleanups": 0,
            "shifted_headers_corrected": 0,
            "dates_parsed_successfully": 0,
            "dates_unresolved": 0,
            "states_parsed_successfully": 0,
            "states_unresolved": 0,
            "hazard_category_distribution": {},
            "file_summaries": []
        }

        for path in file_paths:
            recs, stats = self.parse_csv_file(path)
            all_records.extend(recs)
            file_summaries.append(stats)

            overall_stats["total_records_processed"] += stats["total_rows_read"]
            overall_stats["total_duplicates_found"] += stats["duplicates_in_file"]
            overall_stats["total_encoding_cleanups"] += stats["encoding_artifacts_cleaned"]
            overall_stats["shifted_headers_corrected"] += stats["shifted_headers_corrected"]
            overall_stats["dates_parsed_successfully"] += stats["dates_parsed"]
            overall_stats["dates_unresolved"] += stats["dates_failed"]
            overall_stats["states_parsed_successfully"] += stats["states_parsed"]
            overall_stats["states_unresolved"] += stats["states_missing"]

        # Aggregate hazard category counts
        cat_counts: Dict[str, int] = {}
        for r in all_records:
            for cat in r.get("reference_hazard_categories", []):
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        overall_stats["hazard_category_distribution"] = cat_counts
        overall_stats["file_summaries"] = file_summaries

        # Save registry to JSON
        os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, indent=2, ensure_ascii=False)

        # Save report if requested
        if report_json_path:
            os.makedirs(os.path.dirname(os.path.abspath(report_json_path)), exist_ok=True)
            with open(report_json_path, 'w', encoding='utf-8') as f:
                json.dump(overall_stats, f, indent=2, ensure_ascii=False)

        return overall_stats
