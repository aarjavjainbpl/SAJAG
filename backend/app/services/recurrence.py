import re
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from app.models.report import SafetyReport

class RecurrenceEngine:
    """
    Recurrence and Cross-Site Learning Engine.
    Uses TF-IDF semantic representation and cosine similarity to discover related incidents
    and repeated barrier failures across disparate facilities, overcoming vocabulary differences.
    """

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Normalizes text for duplicate comparison (whitespace, case, punctuation)."""
        if not text:
            return ""
        cleaned = re.sub(r'[^\w\s]', '', text.lower())
        return " ".join(cleaned.split())

    @classmethod
    def _is_exact_or_resubmission_duplicate(cls, text_a: str, text_b: str) -> bool:
        """
        Determines whether two report narratives are exact duplicates or resubmissions
        of the identical incident observation, rather than separate historical occurrences.
        """
        norm_a = cls._normalize_text(text_a)
        norm_b = cls._normalize_text(text_b)
        if not norm_a or not norm_b:
            return False
        if norm_a == norm_b:
            return True
        if len(norm_a) > 80 and len(norm_b) > 80:
            words_a = set(norm_a.split())
            words_b = set(norm_b.split())
            if words_a == words_b:
                return True
        return False

    @classmethod
    def find_similar_reports(
        cls,
        db: Session,
        target_report_id: int,
        top_k: int = 5,
        threshold: float = 0.25
    ) -> List[Dict[str, Any]]:
        target_report = db.query(SafetyReport).filter(SafetyReport.id == target_report_id).first()
        if not target_report or not target_report.description:
            return []

        all_reports = db.query(SafetyReport).filter(SafetyReport.id != target_report_id).all()
        if not all_reports:
            return []

        # Filter candidates: exclude target itself and exact duplicates/resubmissions
        eligible_reports = []
        for r in all_reports:
            if r.id == target_report.id:
                continue
            if target_report.report_uid and r.report_uid == target_report.report_uid:
                continue
            if cls._is_exact_or_resubmission_duplicate(r.description, target_report.description):
                continue
            eligible_reports.append(r)

        if not eligible_reports:
            return []

        corpus = [target_report.description] + [r.description for r in eligible_reports]
        
        # TF-IDF Vectorization with unigrams and bigrams
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), min_df=1)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Cosine similarity of target (index 0) against all other reports (indices 1..)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        matches = []
        for idx, score in enumerate(similarities):
            candidate = eligible_reports[idx]
            # Boost score slightly if hazard category or barrier matches
            boosted_score = float(score)
            if candidate.energy_source == target_report.energy_source and candidate.energy_source != "Low / Undetermined":
                boosted_score = min(1.0, boosted_score + 0.15)
            if candidate.barrier_name == target_report.barrier_name and candidate.barrier_name != "None Specified":
                boosted_score = min(1.0, boosted_score + 0.10)

            if boosted_score >= threshold:
                is_cross_site = (candidate.facility != target_report.facility)
                matches.append({
                    "id": candidate.id,
                    "report_uid": candidate.report_uid,
                    "facility": candidate.facility,
                    "unit_or_area": candidate.unit_or_area,
                    "report_date": candidate.report_date,
                    "risk_priority": candidate.risk_priority,
                    "energy_source": candidate.energy_source,
                    "barrier_status": candidate.barrier_status,
                    "description": candidate.description,
                    "similarity_score": round(boosted_score * 100, 1),
                    "is_cross_site": is_cross_site,
                    "recurrence_type": "Cross-Site Pattern" if is_cross_site else "Local Recurrence"
                })

        # Sort by similarity descending
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:top_k]

    @classmethod
    def get_cross_site_summary(cls, db: Session) -> Dict[str, Any]:
        """
        Calculates aggregate recurring barrier patterns across multiple sites.
        """
        reports = db.query(SafetyReport).all()
        facility_counts = {}
        barrier_counts = {}
        high_energy_by_site = {}

        for r in reports:
            # Facility count
            facility_counts[r.facility] = facility_counts.get(r.facility, 0) + 1
            
            # Barrier failures
            if r.barrier_status in ["Failed", "Bypassed", "Missing", "Degraded"]:
                b_key = f"{r.barrier_name} ({r.barrier_status})"
                barrier_counts[b_key] = barrier_counts.get(b_key, 0) + 1

            # High energy by site
            if r.sif_precursor_flag:
                if r.facility not in high_energy_by_site:
                    high_energy_by_site[r.facility] = 0
                high_energy_by_site[r.facility] += 1

        top_barriers = [
            {"barrier": k, "count": v}
            for k, v in sorted(barrier_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        site_risk_distribution = [
            {"facility": k, "total_reports": facility_counts[k], "sif_precursors": high_energy_by_site.get(k, 0)}
            for k in facility_counts
        ]

        return {
            "total_facilities": len(facility_counts),
            "top_compromised_barriers": top_barriers,
            "site_risk_distribution": site_risk_distribution
        }
