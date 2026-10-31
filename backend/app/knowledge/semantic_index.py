import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from fastembed import TextEmbedding
from app.knowledge.pdf_parser import PDFReportParser
from app.knowledge.chunker import ReportChunker
from app.knowledge.document_qa import DocumentQAEngine

_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_root_dir = os.path.dirname(_base_dir)
DATA_DIR = os.getenv(
    "DATA_DIR",
    os.path.join(_base_dir, "data") if os.path.exists(os.path.join(_base_dir, "data")) else os.path.join(_root_dir, "data")
)

PRIORITY_REPORTS_DIR = os.path.join(DATA_DIR, "priority_reports")
INDEX_RECORDS_PATH = os.path.join(DATA_DIR, "priority_knowledge_records.json")
INDEX_EMBEDDINGS_PATH = os.path.join(DATA_DIR, "priority_knowledge_embeddings.npy")

class SemanticKnowledgeIndex:
    """
    Semantic Search & Retrieval Engine for Priority Industrial Safety Investigation Reports:
    1. IOCL Haldia Refinery (OISD)
    2. Tesoro Anacortes Refinery (CSB)
    3. Chevron Richmond Refinery (CSB)
    Plus support for dynamic PDF upload and indexing.
    Preserves exact document provenance, page citations, fact types, and IOGP Life-Saving Rules.
    """

    _model: Optional[TextEmbedding] = None
    _records: List[Dict[str, Any]] = []
    _embeddings: Optional[np.ndarray] = None

    @classmethod
    def get_model(cls) -> TextEmbedding:
        if cls._model is None:
            # Using default pretrained BAAI/bge-small-en-v1.5
            cls._model = TextEmbedding()
        return cls._model

    @classmethod
    def build_or_load_index(cls, force_rebuild: bool = False) -> Dict[str, Any]:
        if not force_rebuild and os.path.exists(INDEX_RECORDS_PATH) and os.path.exists(INDEX_EMBEDDINGS_PATH):
            with open(INDEX_RECORDS_PATH, "r", encoding="utf-8") as f:
                cls._records = json.load(f)
            cls._embeddings = np.load(INDEX_EMBEDDINGS_PATH)
            return {
                "status": "loaded_from_disk",
                "total_records": len(cls._records),
                "embedding_shape": list(cls._embeddings.shape)
            }

        # Parse all PDFs in the priority reports directory
        all_pages = []
        if not os.path.exists(PRIORITY_REPORTS_DIR):
            os.makedirs(PRIORITY_REPORTS_DIR, exist_ok=True)

        pdf_files = [f for f in os.listdir(PRIORITY_REPORTS_DIR) if f.endswith(".pdf")]
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {PRIORITY_REPORTS_DIR}")

        for pdf_name in sorted(pdf_files):
            pdf_path = os.path.join(PRIORITY_REPORTS_DIR, pdf_name)
            pages = PDFReportParser.parse_pdf(pdf_path)
            all_pages.extend(pages)

        # Segment into structured records
        chunks = ReportChunker.chunk_report_pages(all_pages)

        # Generate embeddings
        model = cls.get_model()
        texts = [
            f"Report: {c['source_report']} | Page: {c['page_number']} | Section: {c['section_type']} | Hazard: {c['hazard']} | {c['supporting_text']}"
            for c in chunks
        ]
        
        embeddings_generator = model.embed(texts)
        embeddings_matrix = np.array(list(embeddings_generator), dtype=np.float32)

        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        normalized_embeddings = embeddings_matrix / norms

        # Save to disk
        with open(INDEX_RECORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        np.save(INDEX_EMBEDDINGS_PATH, normalized_embeddings)

        cls._records = chunks
        cls._embeddings = normalized_embeddings

        return {
            "status": "built_and_saved",
            "total_documents": len(pdf_files),
            "total_pages": len(all_pages),
            "total_records": len(chunks),
            "embedding_shape": list(normalized_embeddings.shape)
        }

    @classmethod
    def search(
        cls,
        query: str,
        top_k: int = 5,
        filter_report: Optional[str] = None,
        filter_fact_type: Optional[str] = None,
        filter_section: Optional[str] = None,
        filter_iogp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if cls._embeddings is None or not cls._records:
            cls.build_or_load_index()

        model = cls.get_model()
        query_vec = np.array(list(model.embed([query])), dtype=np.float32)[0]
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        # Cosine similarity dot product
        similarities = np.dot(cls._embeddings, query_vec)

        # Apply filters
        indices = np.argsort(similarities)[::-1]
        results = []

        for idx in indices:
            rec = cls._records[idx]
            sim_score = float(similarities[idx])

            if filter_report and filter_report.lower() not in rec["source_report"].lower() and filter_report.lower() not in rec.get("pdf_filename", "").lower():
                continue
            if filter_fact_type and rec["fact_type"] != filter_fact_type:
                continue
            if filter_section and filter_section.lower() not in rec["section_type"].lower():
                continue
            if filter_iogp:
                rules = rec.get("iogp_rules", [])
                if not any(r.get("rule_name", "").lower() == filter_iogp.lower() for r in rules):
                    continue

            results.append({
                "score": round(sim_score * 100, 1),
                "source_report": rec["source_report"],
                "pdf_filename": rec.get("pdf_filename", ""),
                "report_id": rec.get("report_id", ""),
                "page_number": rec["page_number"],
                "section_type": rec["section_type"],
                "fact_type": rec["fact_type"],
                "incident": rec["incident"],
                "hazard": rec["hazard"],
                "failed_safeguard": rec["failed_safeguard"],
                "contributing_factor": rec["contributing_factor"],
                "recommendation": rec["recommendation"],
                "supporting_text": rec["supporting_text"],
                "ai_interpretation": rec["ai_interpretation"],
                "iogp_rules": rec.get("iogp_rules", [])
            })

            if len(results) >= top_k:
                break

        return results

    @classmethod
    def qa(
        cls,
        query: str,
        filter_report: Optional[str] = None,
        top_k: int = 6
    ) -> Dict[str, Any]:
        """
        Executes question answering using strictly retrieved investigation evidence.
        """
        retrieved = cls.search(
            query=query,
            top_k=top_k,
            filter_report=filter_report
        )
        return DocumentQAEngine.answer_query(
            query=query,
            retrieved_passages=retrieved
        )

    @classmethod
    def add_pdf_to_index(cls, pdf_path: str) -> Dict[str, Any]:
        """
        Incrementally processes and adds an uploaded investigation report to the knowledge index.
        """
        if cls._embeddings is None or not cls._records:
            cls.build_or_load_index()

        filename = os.path.basename(pdf_path)
        pages = PDFReportParser.parse_pdf(pdf_path)
        if not pages:
            return {"status": "error", "message": "Failed to extract text from PDF."}

        new_chunks = ReportChunker.chunk_report_pages(pages)
        if not new_chunks:
            return {"status": "error", "message": "No substantive paragraphs extracted."}

        model = cls.get_model()
        texts = [
            f"Report: {c['source_report']} | Page: {c['page_number']} | Section: {c['section_type']} | Hazard: {c['hazard']} | {c['supporting_text']}"
            for c in new_chunks
        ]
        new_embeddings = np.array(list(model.embed(texts)), dtype=np.float32)
        norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        norm_new_embeddings = new_embeddings / norms

        # Concatenate with existing index
        cls._records.extend(new_chunks)
        cls._embeddings = np.vstack([cls._embeddings, norm_new_embeddings])

        # Save to disk
        with open(INDEX_RECORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(cls._records, f, indent=2, ensure_ascii=False)
        np.save(INDEX_EMBEDDINGS_PATH, cls._embeddings)

        return {
            "status": "success",
            "filename": filename,
            "pages_parsed": len(pages),
            "chunks_added": len(new_chunks),
            "total_corpus_chunks": len(cls._records)
        }

    @classmethod
    def get_corpus_summary(cls) -> Dict[str, Any]:
        if not cls._records:
            cls.build_or_load_index()

        by_report = {}
        by_fact_type = {}
        by_section = {}
        by_iogp = {}

        for r in cls._records:
            rep = r["source_report"]
            by_report[rep] = by_report.get(rep, 0) + 1

            ft = r["fact_type"]
            by_fact_type[ft] = by_fact_type.get(ft, 0) + 1

            sec = r["section_type"]
            by_section[sec] = by_section.get(sec, 0) + 1

            for rule in r.get("iogp_rules", []):
                r_name = rule.get("rule_name")
                if r_name:
                    by_iogp[r_name] = by_iogp.get(r_name, 0) + 1

        return {
            "total_chunks": len(cls._records),
            "reports_breakdown": by_report,
            "fact_type_breakdown": by_fact_type,
            "section_breakdown": by_section,
            "iogp_rules_breakdown": by_iogp
        }
