import pytest
from app.knowledge.semantic_index import SemanticKnowledgeIndex

@pytest.fixture(scope="module")
def index():
    res = SemanticKnowledgeIndex.build_or_load_index()
    assert res["total_records"] > 0
    return SemanticKnowledgeIndex

def test_corpus_summary_stats(index):
    summary = index.get_corpus_summary()
    assert summary["total_chunks"] >= 300
    assert "Investigation Committee Report on Fire Incident at IOCL Haldia Refinery" in summary["reports_breakdown"]
    assert "Catastrophic Rupture of Heat Exchanger at Tesoro Anacortes Refinery" in summary["reports_breakdown"]
    assert "Chevron Richmond Refinery Pipe Rupture and Fire" in summary["reports_breakdown"]
    assert "Hot Work" in summary["iogp_rules_breakdown"]
    assert "Energy Isolation" in summary["iogp_rules_breakdown"]

def test_search_iocl_haldia_naphtha_fire(index):
    query = "IOCL Haldia refinery naphtha leak during reboiler inlet blinding and gas cutting fire"
    results = index.search(query, top_k=3, filter_report="Haldia")
    assert len(results) > 0
    top = results[0]
    assert "Haldia" in top["source_report"]
    assert top["page_number"] in [2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert any(term in top["supporting_text"].lower() for term in ["naphtha", "reboiler", "fire", "flange", "stabilizer"])

def test_search_tesoro_anacortes_htha_exchanger(index):
    query = "Tesoro Anacortes high temperature hydrogen attack HTHA heat exchanger E-6600E rupture"
    results = index.search(query, top_k=3, filter_report="Tesoro")
    assert len(results) > 0
    top = results[0]
    assert "Tesoro" in top["source_report"]
    assert any(term in top["supporting_text"].lower() for term in ["htha", "exchanger", "rupture", "nelson", "hydrogen"])

def test_search_chevron_richmond_sulfidation_corrosion(index):
    query = "Chevron Richmond crude unit 4-sidecut sulfidation corrosion pipe rupture low silicon"
    results = index.search(query, top_k=3, filter_report="Chevron")
    assert len(results) > 0
    top = results[0]
    assert "Chevron" in top["source_report"]
    assert any(term in top["supporting_text"].lower() for term in ["sulfidation", "sidecut", "corrosion", "pipe", "silicon"])

def test_qa_evidence_grounding_and_separation(index):
    query = "What caused the naphtha fire at IOCL Haldia refinery and which safeguards failed?"
    ans = index.qa(query)
    assert ans["has_evidence"] is True
    assert len(ans["documented_facts"]) > 0
    assert "Page" in ans["executive_summary"]
    assert len(ans["failed_safeguards"]) > 0
    assert len(ans["iogp_rules"]) > 0
    assert "AI INTERPRETATION" in ans["ai_interpretation"]
    assert len(ans["missing_information"]) > 0
    assert len(ans["evidence_citations"]) > 0
    # Provenance citation check
    first_fact = ans["documented_facts"][0]
    assert "[" in first_fact["citation"] and "Page" in first_fact["citation"]

def test_qa_insufficient_evidence_fallback(index):
    query = "quantum teleportation and spacecraft warp drive navigation error"
    ans = index.qa(query)
    assert ans["has_evidence"] is False
    assert "insufficient" in ans["executive_summary"].lower() or "no relevant" in ans["executive_summary"].lower()
