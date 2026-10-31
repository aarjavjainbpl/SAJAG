import os
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from app.knowledge.semantic_index import SemanticKnowledgeIndex, PRIORITY_REPORTS_DIR

router = APIRouter(prefix="/knowledge", tags=["AI Safety Document Intelligence & Q&A"])

class AskKnowledgeRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Safety or technical query to ask about the reports")
    filter_report: Optional[str] = Field(None, description="Optional report filter (e.g. Haldia, Tesoro, Chevron)")
    top_k: Optional[int] = Field(6, ge=1, le=15, description="Number of evidence chunks to retrieve and synthesize")

@router.get("/summary")
def get_knowledge_summary():
    """
    Returns corpus statistics: report breakdown, fact type counts, section distributions,
    and IOGP Life-Saving Rules representation.
    """
    return SemanticKnowledgeIndex.get_corpus_summary()

@router.get("/search")
def search_knowledge(
    query: str = Query(..., min_length=2, description="Hazard description or technical query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return"),
    filter_report: Optional[str] = Query(None, description="Filter by report title"),
    filter_fact_type: Optional[str] = Query(None, description="REPORTED_FACT, INVESTIGATOR_CONCLUSION, OFFICIAL_RECOMMENDATION, KEY_LESSON"),
    filter_section: Optional[str] = Query(None, description="Filter by report section"),
    filter_iogp: Optional[str] = Query(None, description="Filter by IOGP Life-Saving Rule")
):
    """
    Performs dense semantic vector search across investigation reports.
    Every result displays source report, exact page reference, fact type,
    failed safeguard, and verbatim supporting text.
    """
    results = SemanticKnowledgeIndex.search(
        query=query,
        top_k=top_k,
        filter_report=filter_report,
        filter_fact_type=filter_fact_type,
        filter_section=filter_section,
        filter_iogp=filter_iogp
    )
    return {
        "query": query,
        "match_count": len(results),
        "results": results
    }

@router.post("/ask")
def ask_knowledge(req: AskKnowledgeRequest):
    """
    Answers questions grounded strictly in the available investigation evidence.
    Returns:
    - Executive summary
    - Documented facts with exact report & page citations
    - Failed safeguards and contributing factors
    - Implicated IOGP Life-Saving Rules
    - Official recommendations
    - Labeled AI interpretation and hypotheses
    - Missing or uncertain evidence disclosures
    - Verbatim cited passages
    """
    return SemanticKnowledgeIndex.qa(
        query=req.query,
        filter_report=req.filter_report,
        top_k=req.top_k
    )

@router.post("/upload")
async def upload_investigation_report(file: UploadFile = File(...)):
    """
    Uploads a new PDF investigation report, extracts text page-by-page,
    chunks paragraphs, generates vector embeddings, and indexes it into the knowledge base.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    os.makedirs(PRIORITY_REPORTS_DIR, exist_ok=True)
    target_path = os.path.join(PRIORITY_REPORTS_DIR, file.filename)
    
    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)
        
    result = SemanticKnowledgeIndex.add_pdf_to_index(target_path)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
        
    return {
        "message": f"Successfully ingested and indexed {file.filename}",
        "details": result
    }

@router.post("/rebuild")
def rebuild_knowledge_index():
    """
    Forces re-parsing the priority investigation PDFs and regenerating vector embeddings.
    """
    res = SemanticKnowledgeIndex.build_or_load_index(force_rebuild=True)
    return {
        "message": "Priority Investigation Reports successfully re-indexed.",
        "details": res
    }
