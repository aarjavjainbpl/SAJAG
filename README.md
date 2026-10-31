# SAJAG — AI-Powered Industrial Safety Intelligence Platform

> **SAJAG** is a scalable, multi-industry B2B safety intelligence platform designed to analyze workplace safety observations, near-miss reports, and incident logs to prioritize **Serious Injury and Fatality (SIF) precursors**, recommend **Hierarchy of Controls** corrective actions, and enforce an **Independent Verification Gate** to prevent false task closures.

---

## 🏗️ Architecture Overview

The platform uses a layered, high-explainability hybrid architecture:

- **Frontend:** React 19 + Vite, Vanilla CSS Design System with dark-mode industrial aesthetics, responsive cards, and micro-animations.
- **Backend:** Python 3.11 + FastAPI with REST endpoints, SQLAlchemy ORM, and SQLite auditable local store.
- **AI / NLP Intelligence:**
  - **Deterministic High-Energy Hazard Scanner:** Evaluates 9 high-energy categories (Falls from height, Suspended loads, Arc flash, High pressure, Toxic atmospheres, Confined space, Machinery pinch points, Mobile equipment, Thermal fire).
  - **Critical Barrier Degradation Analyzer:** Evaluates barrier states (`Failed`, `Bypassed`, `Missing`, `Degraded`, `Effective`).
  - **Explainability Trace Engine:** Zero-hallucination guarantee quoting exact sentences from the raw narrative.
  - **Recurrence & Cross-Site Learner:** Dense TF-IDF semantic vector representation and cosine similarity matching across disparate facilities.
  - **Action Verification Gate:** Prevents false closure by enforcing physical inspection notes and authorized inspector sign-off.

---

## 🚀 Running the Platform Locally

### Prerequisites
- **Node.js:** v24+ & npm (already installed)
- **Python:** 3.11+ (installed in `backend/venv`)

### 1. Start the Backend API Server
```powershell
# From the project root:
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Docs (Swagger): `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/api/v1/health`

### 2. Start the Frontend Dashboard
```powershell
# In a separate terminal, from the project root:
cd frontend
npm.cmd run dev
```
- Web Application: `http://127.0.0.1:5173/`

---

## 📦 Core Platform Modules

| Module | Purpose & Capabilities |
| :--- | :--- |
| **🛡️ Triage & Incident Queue** | Real-time queue with SIF precursor badges (`CRITICAL SIF`, `HIGH PRECURSOR`, `MEDIUM RISK`, `LOW ROUTINE`), filterable by facility, priority, and energy source. |
| **📥 Report Ingestion Hub** | Multi-format CSV/Excel file upload with column synonym mapping, plus an interactive manual entry form with **Live Instant AI Triage Preview**. |
| **🔍 SIF Precursor Inspector** | In-depth breakdown separating *Actual Outcome* from *Potential Severity*, diagnosing barrier status, and citing exact sentences from the text. |
| **⚖️ Hierarchy of Controls & Verification Gate** | Recommends Elimination and Engineering controls over weak administrative band-aids; enforces documented physical proof before marking actions closed. |
| **🌐 Recurrence & Cross-Site Learning** | Discovers related barrier failures across sister plants and flags repeated hazards within lookback windows. |
| **📊 Management Analytics** | Auditable leading indicators, SIF precursor ratios, barrier failure hotspots, and cross-facility risk comparisons. |
| **🧪 Benchmark Evaluation** | Transparent evaluation dashboard comparing model predictions against annotated Campbell / OSHA benchmark cases with live Precision, Recall, and Confusion Matrix. |

---

## 🧪 Benchmark Dataset & Evaluation

The benchmark dataset (`data/sample_safety_reports.csv` and seeded benchmark cases) follows the **Campbell Institute SIF Precursor Model** and **OSHA 1910/1926 Standards**. Each benchmark record contains an annotated ground-truth label, allowing real-time auditable evaluation:

- **Precision:** Measures how accurately the engine avoids false alarms on routine observations.
- **Recall:** Measures whether the engine catches true high-energy precursors.
- **F1-Score & Accuracy:** Live traceable metrics visible in the **Benchmark Evaluation** tab.

---

## 🔒 Safety & Operational Guardrails
- **Decision Support Tool:** SAJAG is designed as an assistant for safety managers and EHS engineers, not an autonomous control system.
- **Zero Hallucination:** Explanations and evidence extraction are strictly grounded in cited sentences from the original safety report.
