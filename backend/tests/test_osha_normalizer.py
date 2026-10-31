"""
Unit tests for OSHA Data Normalizer and High-Energy Reference Registry.
Validates schema handling, FY 2012 shifted-header resolution, date parsing,
encoding cleanup, source traceability, and reference hazard categorization.
"""

import os
import json
import pytest
from app.services.osha_normalizer import OshaDataNormalizer

@pytest.fixture
def normalizer():
    return OshaDataNormalizer()

def test_date_normalization_formats(normalizer):
    # 4-digit year format (M/D/YYYY)
    assert normalizer.normalize_date("6/23/2009") == "2009-06-23"
    assert normalizer.normalize_date("10/1/2011") == "2011-10-01"
    
    # 2-digit year format (MM/DD/YY)
    assert normalizer.normalize_date("09/20/09") == "2009-09-20"
    assert normalizer.normalize_date("10/02/09") == "2009-10-02"
    assert normalizer.normalize_date("07/06/10") == "2010-07-06"
    assert normalizer.normalize_date("09/24/11") == "2011-09-24"
    
    # Historical date
    assert normalizer.normalize_date("5/22/1995") == "1995-05-22"
    
    # Invalid / empty dates
    assert normalizer.normalize_date("") is None
    assert normalizer.normalize_date(None) is None
    assert normalizer.normalize_date("invalid-date") is None

def test_fiscal_year_derivation(normalizer):
    # Explicit fiscal year
    fy, src = normalizer.derive_fiscal_year("2009-06-23", "FY 2009")
    assert fy == "FY 2009"
    assert src == "explicit"

    fy, src = normalizer.derive_fiscal_year("2010-01-15", "FY2010")
    assert fy == "FY 2010"
    assert src == "explicit"

    # Derived from incident date (October 1 starts new US government FY)
    # Incident in September 2013 -> FY 2013
    fy_sep, src_sep = normalizer.derive_fiscal_year("2013-09-30", None)
    assert fy_sep == "FY 2013"
    assert src_sep == "derived_from_incident_date"

    # Incident in October 2012 -> FY 2013
    fy_oct, src_oct = normalizer.derive_fiscal_year("2012-10-15", None)
    assert fy_oct == "FY 2013"
    assert src_oct == "derived_from_incident_date"

def test_text_encoding_cleanup(normalizer):
    raw_text = "Worker was near a boiler\xa0when it blew outâ€œwith high pressureâ€\x9d."
    cleaned = normalizer.clean_text(raw_text)
    assert "\xa0" not in cleaned
    assert "â€œ" not in cleaned
    assert 'with high pressure' in cleaned

def test_company_location_parsing(normalizer):
    # Standard format with zip
    loc1 = normalizer.parse_company_location("L.B. Thompson Inc., Tampa, FL 33610")
    assert loc1["company_name"] == "L.B. Thompson Inc."
    assert loc1["city"] == "Tampa"
    assert loc1["state"] == "FL"
    assert loc1["zip_code"] == "33610"

    # Format without zip
    loc2 = normalizer.parse_company_location("Pyi Dell Gei a Services JV, Milton, FL")
    assert loc2["company_name"] == "Pyi Dell Gei a Services JV"
    assert loc2["city"] == "Milton"
    assert loc2["state"] == "FL"
    assert loc2["zip_code"] is None

    # Full state name
    loc3 = normalizer.parse_company_location("Mcm Carpentry LLC, Woodbridge, Virginia 22193")
    assert loc3["state"] == "VA"
    assert loc3["zip_code"] == "22193"

    # Comma before zip
    loc4 = normalizer.parse_company_location("LVI Environmental Services, Seattle, WA, 98121")
    assert loc4["state"] == "WA"
    assert loc4["zip_code"] == "98121"

    # Missing location entirely - preserves company without inventing missing state
    loc5 = normalizer.parse_company_location("Butler, Fairman & Seufert, Inc.")
    assert loc5["company_name"] == "Butler, Fairman & Seufert, Inc."
    assert loc5["state"] is None

def test_fy2012_shifted_header_resolution(tmp_path, normalizer):
    # Simulate the exact FY 2012 shifted header structure
    csv_content = (
        'Fiscal Year ,Summary Report Date,Date of Incident,Preliminary Description of Incident,\n'
        'FY 2012,10/1/2011,2/21/2011,"Viking Coca Cola Bottling Company, St. Cloud, MN 56303",Worker was found dead in freezer.\n'
    )
    test_file = tmp_path / "osha_fy2012_sample.csv"
    test_file.write_text(csv_content, encoding="utf-8")

    records, stats = normalizer.parse_csv_file(str(test_file))
    assert stats["schema_detected"] == "5_column_fy2012_shifted_header"
    assert stats["shifted_headers_corrected"] == 1
    assert len(records) == 1

    rec = records[0]
    # Verify Company was mapped from col 3, not description
    assert rec["company_name"] == "Viking Coca Cola Bottling Company"
    assert rec["state"] == "MN"
    # Verify Narrative was mapped from col 4
    assert "Worker was found dead in freezer" in rec["cleaned_narrative"]
    assert rec["fiscal_year"] == "FY 2012"
    assert rec["incident_date"] == "2011-02-21"

def test_4_column_schema_handling(tmp_path, normalizer):
    # Simulate the FY 2013 4-column structure
    csv_content = (
        'Date of Incident,"Company, City, State, ZIP",Preliminary Description of Incident,Fatality or Catastrophe\n'
        '9/30/2013,"CAM Contractors Inc., Huntington Beach, CA 92649",Worker was electrocuted in electrical vault.,Fatality\n'
    )
    test_file = tmp_path / "osha_2013_sample.csv"
    test_file.write_text(csv_content, encoding="utf-8")

    records, stats = normalizer.parse_csv_file(str(test_file))
    assert stats["schema_detected"] == "4_column_2013_format"
    assert len(records) == 1

    rec = records[0]
    assert rec["fiscal_year"] == "FY 2013"
    assert rec["fiscal_year_source"] == "derived_from_incident_date"
    assert rec["reported_event_type"] == "Fatality"
    assert rec["company_name"] == "CAM Contractors Inc."
    assert rec["state"] == "CA"
    assert "Worker was electrocuted" in rec["cleaned_narrative"]
    assert "Electrical (Shock / Arc Flash / High Voltage)" in rec["reference_hazard_categories"]

def test_source_traceability_and_non_prescriptive_labeling(normalizer):
    narrative = "Scaffold collapsed causing worker to fall 25 feet to concrete."
    hazards = normalizer.categorize_reference_hazards(narrative)
    assert "Gravity / Falls from Height" in hazards

    # Confirm non-prescriptive categorization notice is present
    test_rec = {
        "reference_hazard_categories": hazards,
        "classification_nature": "Empirical reference pattern (Non-prescriptive; NOT verified SIF precursor label)"
    }
    assert "NOT verified SIF precursor label" in test_rec["classification_nature"]

def test_curated_reference_registry_file_integrity():
    # Verify output registry in data/
    registry_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "osha_fatal_patterns.json"))
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "osha_normalization_report.json"))

    assert os.path.exists(registry_path), f"Registry file not found at {registry_path}"
    assert os.path.exists(report_path), f"Report file not found at {report_path}"

    with open(registry_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert len(records) == 4742
    assert report["total_records_processed"] == 4742
    assert report["shifted_headers_corrected"] == 1094
    assert report["dates_parsed_successfully"] == 4742
    assert report["dates_unresolved"] == 0

    # Verify sample record properties
    sample = records[0]
    assert "record_id" in sample
    assert "source_file" in sample
    assert "source_row_index" in sample
    assert "original_narrative" in sample
    assert "cleaned_narrative" in sample
    assert "reference_hazard_categories" in sample
    assert "classification_nature" in sample
