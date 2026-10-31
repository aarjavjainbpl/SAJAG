import sqlite3

conn = sqlite3.connect("sajag.db")
c = conn.cursor()
rows = c.execute("SELECT report_uid, risk_priority, explanation FROM safety_reports LIMIT 10").fetchall()
for r in rows:
    print(r[0], r[1])
    print(r[2])
    print("-" * 40)
