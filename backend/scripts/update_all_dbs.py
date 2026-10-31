import sqlite3
from app.services.sif_intelligence import SIFIntelligenceEngine

for path in ["sajag.db", "backend/sajag.db"]:
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        rows = c.execute("SELECT id, description, actual_outcome FROM safety_reports").fetchall()
        updated = 0
        for rid, desc, outcome in rows:
            res = SIFIntelligenceEngine.analyze_report(desc, reported_outcome=outcome or "Unknown")
            c.execute("UPDATE safety_reports SET explanation = ?, confidence_score = ? WHERE id = ?", (res["explanation"], res["confidence_score"], rid))
            updated += 1
        conn.commit()
        conn.close()
        print(f"Updated {updated} records in {path}")
    except Exception as e:
        print(f"Error updating {path}: {e}")
