"""
OSHA High-Energy Reference Registry Matcher for SAJAG SIF Intelligence Engine.

Provides empirical cross-referencing between incoming safety observations
and historical OSHA fatal incident mechanisms without altering deterministic
SIF precursor decision logic or creating false positive SIF classifications.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("sajag.osha_matcher")

# Mapping between SAJAG SIF Intelligence hazard names and OSHA Registry hazard categories
HAZARD_CATEGORY_MAPPING = {
    "Gravity / Falls from Height": "Gravity / Falls from Height",
    "Suspended / Heavy Loads": "Suspended / Heavy Loads & Rigging",
    "Electrical (Arc Flash / High Voltage)": "Electrical (Shock / Arc Flash / High Voltage)",
    "Pressurized Fluid / Gas / Steam": "Pressurized Equipment / Piping Burst",
    "Hazardous Chemical / Toxic Atmosphere": "Hazardous Chemicals / Toxic Atmosphere / Asphyxiation",
    "Confined Space": "Confined Space / Trench Engulfment",
    "Mechanical / Rotating Equipment / Pinch Point": "Mechanical / Rotating Equipment / Pinch Point",
    "Heavy Mobile Equipment / Traffic": "Heavy Mobile Equipment / Vehicular",
    "Thermal / Fire / Explosion": "Thermal / Fire / Explosion"
}

# Generic workplace terms that describe personnel/tasks rather than physical injury mechanisms
GENERIC_WORKPLACE_STOPS = list(TfidfVectorizer(stop_words='english').get_stop_words()) + [
    "worker", "workers", "employee", "employees", "technician", "maintenance", "working"
]

# Domain mechanism keywords to boost relevant situational alignment
DOMAIN_KEYWORDS = {
    "Gravity / Falls from Height": ["scaffold", "ladder", "roof", "harness", "lanyard", "skylight", "floor opening", "catwalk", "beam"],
    "Suspended / Heavy Loads": ["crane", "hoist", "rigging", "sling", "load", "dropped", "derrick", "winch", "cable"],
    "Electrical (Arc Flash / High Voltage)": ["switchgear", "panel", "480v", "breaker", "powerline", "power line", "shock", "electrocuted", "live wire"],
    "Pressurized Fluid / Gas / Steam": ["flange", "valve", "high pressure", "burst", "rupture", "steam", "hose", "piping", "spray"],
    "Hazardous Chemical / Toxic Atmosphere": ["h2s", "toxic", "gas", "ammonia", "acid", "asphyxiation", "asphyxiated", "fumes", "vapor", "nitrogen", "oxygen", "oxygen deficiency", "inert gas"],
    "Confined Space": ["confined space", "trench", "cave-in", "manhole", "vessel", "tank", "engulfed", "sludge", "permit", "nitrogen", "oxygen deficiency"],
    "Mechanical / Rotating Equipment / Pinch Point": ["pinch point", "conveyor", "auger", "lathe", "machine guard", "interlock", "press", "roller", "entangled"],
    "Heavy Mobile Equipment / Traffic": ["forklift", "truck", "loader", "excavator", "dump truck", "run over", "backed over", "traffic"],
    "Thermal / Fire / Explosion": ["explosion", "fire", "flash fire", "ignited", "burn", "hot work", "welding", "torch"]
}

DEFAULT_REGISTRY_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "osha_fatal_patterns.json"),
    os.path.join(os.getcwd(), "data", "osha_fatal_patterns.json"),
    os.path.join(os.getcwd(), "..", "data", "osha_fatal_patterns.json")
]


class OshaReferenceMatcher:
    """
    Singleton service that indexes verified OSHA fatal incident records and
    matches incoming observations against empirical fatal injury mechanisms.
    """
    _instance: Optional['OshaReferenceMatcher'] = None

    def __init__(self, registry_file: Optional[str] = None):
        self.registry_file = registry_file
        self.records: List[Dict[str, Any]] = []
        self.category_indices: Dict[str, List[int]] = {}
        self.category_vectorizers: Dict[str, TfidfVectorizer] = {}
        self.category_matrices: Dict[str, Any] = {}
        self._is_initialized = False

    @classmethod
    def get_instance(cls, registry_file: Optional[str] = None) -> 'OshaReferenceMatcher':
        if cls._instance is None:
            cls._instance = OshaReferenceMatcher(registry_file)
            cls._instance._load_and_index()
        return cls._instance

    def _resolve_registry_path(self) -> Optional[str]:
        if self.registry_file is not None:
            if os.path.exists(self.registry_file):
                return os.path.abspath(self.registry_file)
            return None

        for p in DEFAULT_REGISTRY_PATHS:
            norm_p = os.path.abspath(p)
            if os.path.exists(norm_p):
                return norm_p
        return None

    def _load_and_index(self):
        """Loads records and builds category-level TF-IDF indexes."""
        resolved = self._resolve_registry_path()
        if not resolved:
            logger.warning("OSHA fatal reference registry file not found.")
            self._is_initialized = False
            return

        try:
            with open(resolved, 'r', encoding='utf-8') as f:
                self.records = json.load(f)

            self.category_indices = {}
            for idx, r in enumerate(self.records):
                for cat in r.get("reference_hazard_categories", []):
                    if cat not in self.category_indices:
                        self.category_indices[cat] = []
                    self.category_indices[cat].append(idx)

            # Build category vectorizers lazily or on demand
            self._is_initialized = True
            logger.info(f"Loaded {len(self.records)} OSHA reference records across {len(self.category_indices)} categories.")
        except Exception as e:
            logger.error(f"Failed to load OSHA reference registry: {e}")
            self.records = []
            self._is_initialized = False

    def _get_category_matrix(self, category: str):
        """Builds or retrieves cached TF-IDF matrix for a specific hazard category."""
        if category in self.category_matrices:
            return self.category_vectorizers[category], self.category_matrices[category]

        indices = self.category_indices.get(category, [])
        if not indices:
            return None, None

        narratives = [self.records[i]["cleaned_narrative"] for i in indices]
        vectorizer = TfidfVectorizer(stop_words=GENERIC_WORKPLACE_STOPS, ngram_range=(1, 2), min_df=1, max_features=3000)
        matrix = vectorizer.fit_transform(narratives)

        self.category_vectorizers[category] = vectorizer
        self.category_matrices[category] = matrix
        return vectorizer, matrix

    def find_reference(
        self,
        observation_text: str,
        detected_hazard_name: Optional[str] = None,
        is_routine: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves relevant historical fatal-incident mechanism from the OSHA registry.
        
        Strict Safety Invariants:
        1. If observation is routine or lacks a high-energy mechanism, returns matched: False.
        2. Never overrides or alters current SIF precursor determination.
        3. Clearly marks retrieved data as historical reference only.
        """
        no_match_response = {
            "matched": False,
            "reference_record_id": None,
            "source_file": None,
            "fiscal_year": None,
            "incident_date": None,
            "company_name": None,
            "location": None,
            "hazard_category": None,
            "original_narrative": None,
            "relevance_score": 0.0,
            "relevance_rationale": "No relevant historical OSHA reference found.",
            "disclaimer": "HISTORICAL REFERENCE NOTICE: No matching high-energy fatality mechanism identified in historical reference registry."
        }

        # Guard: Routine observations, empty text, or unclassified hazards
        if not observation_text or not observation_text.strip():
            no_match_response["relevance_rationale"] = "No relevant historical OSHA reference found."
            return no_match_response

        if is_routine:
            no_match_response["relevance_rationale"] = "No relevant historical OSHA reference found."
            return no_match_response

        if not detected_hazard_name or detected_hazard_name == "General Hazard / Unclassified":
            no_match_response["relevance_rationale"] = "No relevant historical OSHA reference found."
            return no_match_response

        if not self._is_initialized or not self.records:
            self._load_and_index()
            if not self._is_initialized or not self.records:
                no_match_response["relevance_rationale"] = "No relevant historical OSHA reference found."
                return no_match_response

        # Map to registry category
        registry_category = HAZARD_CATEGORY_MAPPING.get(detected_hazard_name)
        if not registry_category or registry_category not in self.category_indices:
            no_match_response["relevance_rationale"] = f"No historical fatal incident records indexed under category '{detected_hazard_name}'."
            return no_match_response

        cand_indices = self.category_indices[registry_category]
        if not cand_indices:
            return no_match_response

        # TF-IDF Cosine Similarity within matched category
        vectorizer, matrix = self._get_category_matrix(registry_category)
        if vectorizer is None or matrix is None:
            return no_match_response

        cleaned_query = observation_text.strip()
        q_vec = vectorizer.transform([cleaned_query])
        similarities = cosine_similarity(q_vec, matrix)[0]

        query_lower = cleaned_query.lower()
        key_terms = DOMAIN_KEYWORDS.get(detected_hazard_name, [])
        matched_terms = [t for t in key_terms if t in query_lower]

        # Evaluate combined score across all candidates so causal domain mechanism alignment
        # takes priority over generic word overlap
        best_cand_pos = 0
        best_combined_score = 0.0
        best_shared_terms = []

        for i, rec_idx in enumerate(cand_indices):
            raw_sim = float(similarities[i])
            rec_narr_lower = self.records[rec_idx]["cleaned_narrative"].lower()
            shared = [t for t in matched_terms if t in rec_narr_lower]
            boost = min(0.20, len(shared) * 0.08) if shared else 0.0
            candidate_combined = min(1.0, raw_sim + boost)
            if candidate_combined > best_combined_score:
                best_combined_score = candidate_combined
                best_cand_pos = i
                best_shared_terms = shared

        combined_score = best_combined_score
        shared_terms = best_shared_terms
        best_rec_idx = cand_indices[best_cand_pos]
        best_record = self.records[best_rec_idx]

        # Relevance threshold check: require at least 15% combined alignment
        if combined_score < 0.15:
            no_match_response["relevance_rationale"] = "No relevant historical OSHA reference found."
            return no_match_response

        # Build location string
        loc_str = best_record.get("company_raw") or best_record.get("company_name") or "Unknown"
        if best_record.get("city") and best_record.get("state"):
            loc_str = f"{best_record['company_name']}, {best_record['city']}, {best_record['state']}"

        # Build specific explanation of why it is relevant
        terms_desc = f" involving {', '.join(shared_terms)}" if shared_terms else ""
        rationale = (
            f"Relevant historical mechanism identified: Both the current observation and historical case {best_record['record_id']} "
            f"share the primary high-energy vector [{detected_hazard_name}]{terms_desc}. "
            f"In the historical fatal incident ({best_record['fiscal_year']}), {best_record['cleaned_narrative']} "
            f"The current observation demonstrates an active or degraded barrier on this exact energy path."
        )

        return {
            "matched": True,
            "reference_record_id": best_record["record_id"],
            "source_file": best_record["source_file"],
            "fiscal_year": best_record["fiscal_year"],
            "incident_date": best_record["incident_date"],
            "company_name": best_record["company_name"],
            "location": loc_str,
            "hazard_category": registry_category,
            "original_narrative": best_record["original_narrative"],
            "relevance_score": round(combined_score * 100, 1),
            "relevance_rationale": rationale,
            "disclaimer": (
                "HISTORICAL FATAL REFERENCE ONLY: This record represents an empirical OSHA fatality investigation "
                "provided strictly for safety-barrier benchmarking and organizational learning. "
                "The current observation is evaluated independently and is NOT automatically classified as a SIF precursor."
            )
        }
