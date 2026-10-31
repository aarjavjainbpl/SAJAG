import re
import json
from typing import Dict, Any, List, Tuple, Optional
from app.services.taxonomy_data import HIGH_ENERGY_HAZARDS, BARRIER_TAXONOMY, ROUTINE_LOW_RISK_TERMS

class SIFIntelligenceEngine:
    """
    Transparent, explainable SIF-Precursor and Risk Intelligence Engine.
    Combines deterministic domain rules, energy-barrier scoring, and sentence-level evidence extraction.
    """

    @classmethod
    def analyze_report(cls, text: str, reported_outcome: str = "Unknown") -> Dict[str, Any]:
        cleaned_text = (text or "").strip()
        lower_text = cleaned_text.lower()
        sentences = cls._split_into_sentences(cleaned_text)

        # 1. Extract High-Energy Hazard Categories
        matched_hazards, hazard_snippets = cls._extract_hazards(lower_text, sentences)

        # 2. Check for routine low-risk signals
        # Safety boundary: observations with matched high-energy hazards are NEVER routine
        if matched_hazards:
            is_routine = False
            routine_term = ""
        else:
            is_routine, routine_term = cls._check_routine(lower_text)

        # 3. Extract Barrier Failures (with multi-barrier evidence detection)
        barrier_status, barrier_name, barrier_snippets, secondary_barriers = cls._extract_barriers(lower_text, sentences)

        # 3b. Safeguard & Routine Consistency Boundaries (Milestone 4 Proposals A & B)
        # Ordinary office facility maintenance (e.g., loose cabinet door knob, loose carpet)
        # must not inherit an industrial barrier-degradation penalty when no safety equipment is involved.
        if is_routine and barrier_status == "Degraded" and barrier_name == "Administrative / PPE":
            barrier_status = "Intact"

        # A routine classification must NEVER override a genuinely failed, bypassed, or missing safeguard.
        # If an observation contains evidence of a critical barrier failure, it cannot be suppressed as routine housekeeping.
        if is_routine and barrier_status in ["Failed", "Bypassed", "Missing"]:
            is_routine = False
            routine_term = ""

        # 4. Determine Energy Source Name & Base Severity
        if matched_hazards:
            primary_hazard_name = matched_hazards[0]["name"]
            energy_source = matched_hazards[0]["energy_type"]
            potential_severity = matched_hazards[0]["min_severity"]
            energy_weight = 1.0
        else:
            primary_hazard_name = "General Hazard / Unclassified"
            energy_source = "Low / Undetermined"
            potential_severity = "Low" if is_routine else "Medium"
            energy_weight = 0.2 if is_routine else 0.45

        barrier_weight = BARRIER_TAXONOMY.get(barrier_status, {}).get("score_weight", 0.5)

        # 5. Distinguish Actual Outcome vs. Potential Severity
        actual_outcome = cls._normalize_actual_outcome(reported_outcome, lower_text)

        # 6. SIF Precursor Assessment Decision Logic
        # A SIF Precursor is present when:
        # High-energy source exists AND (Barrier is failed/bypassed/missing OR worker was in line of fire)
        is_sif_precursor = False
        if energy_weight >= 0.8 and barrier_weight >= 0.7:
            is_sif_precursor = True
        elif "fatal" in lower_text or "amputation" in lower_text or "severe burn" in lower_text or "hospitalized" in lower_text:
            is_sif_precursor = True
            potential_severity = "Critical / Fatal"

        if is_routine:
            is_sif_precursor = False
            potential_severity = "Low"

        # 7. Calculate Transparent Risk Score (0 - 100)
        # Base formula: (Energy Weight * 50) + (Barrier Weight * 40) + (Exposure/Outcome Modifier * 10)
        exposure_modifier = 10 if is_sif_precursor else (2 if is_routine else 5)
        raw_score = (energy_weight * 50) + (barrier_weight * 40) + exposure_modifier
        risk_score = round(min(100.0, max(5.0, raw_score)), 1)

        # 8. Assign Priority Badge
        if is_sif_precursor or risk_score >= 80.0:
            risk_priority = "CRITICAL_SIF"
        elif risk_score >= 60.0:
            risk_priority = "HIGH_PRECURSOR"
        elif risk_score >= 35.0:
            risk_priority = "MEDIUM_RISK"
        else:
            risk_priority = "LOW_ROUTINE"

        # 9. Extract Verifiable Evidence Snippets (exact quotes from original text)
        evidence_snippets = list(set(hazard_snippets + barrier_snippets))
        if not evidence_snippets and sentences:
            evidence_snippets = [sentences[0]]

        # 10. Generate Transparent Rationale
        explanation = cls._generate_explanation(
            primary_hazard_name=primary_hazard_name,
            energy_source=energy_source,
            barrier_status=barrier_status,
            barrier_name=barrier_name,
            is_sif_precursor=is_sif_precursor,
            risk_priority=risk_priority,
            actual_outcome=actual_outcome,
            potential_severity=potential_severity,
            is_routine=is_routine,
            routine_term=routine_term,
            secondary_barriers=secondary_barriers,
            raw_text=cleaned_text,
            matched_hazards=matched_hazards
        )

        # 10b. Evidence-Based Precursor Detection Confidence Calculation
        confidence_meta = cls._calculate_detection_confidence(
            cleaned_text=cleaned_text,
            lower_text=lower_text,
            sentences=sentences,
            matched_hazards=matched_hazards,
            is_routine=is_routine,
            routine_term=routine_term,
            barrier_status=barrier_status,
            barrier_name=barrier_name,
            secondary_barriers=secondary_barriers,
            is_sif_precursor=is_sif_precursor,
            risk_priority=risk_priority,
            potential_severity=potential_severity,
            actual_outcome=actual_outcome,
            hazard_snippets=hazard_snippets,
            barrier_snippets=barrier_snippets
        )

        # 11. Cross-reference with OSHA High-Energy Fatal Reference Registry
        # Note: Empirical reference lookup only. Does NOT override or force SIF precursor classification.
        from app.services.osha_matcher import OshaReferenceMatcher
        historical_ref = OshaReferenceMatcher.get_instance().find_reference(
            observation_text=cleaned_text,
            detected_hazard_name=primary_hazard_name if matched_hazards else None,
            is_routine=is_routine
        )

        return {
            "energy_source": energy_source,
            "barrier_status": barrier_status,
            "barrier_name": barrier_name,
            "secondary_barriers": secondary_barriers,
            "potential_severity": potential_severity,
            "actual_outcome": actual_outcome,
            "sif_precursor_flag": is_sif_precursor,
            "risk_priority": risk_priority,
            "risk_score": risk_score,
            "confidence_score": confidence_meta["score"],
            "confidence_band": confidence_meta["band"],
            "confidence_explanation": confidence_meta["explanation"],
            "confidence_supporting_evidence": confidence_meta["supporting_evidence"],
            "confidence_missing_information": confidence_meta["missing_information"],
            "explanation": explanation,
            "evidence_snippets": json.dumps(evidence_snippets),
            "historical_reference": historical_ref
        }

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        if not text:
            return []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def _check_routine(cls, lower_text: str) -> Tuple[bool, str]:
        # High-risk clues and industrial substances that immediately disqualify an observation from being routine
        high_risk_clues = [
            "fell from", "fall from", "fall", "falling", "high voltage", "crane", "toxic",
            "amputation", "steam", "rupture", "chemical", "acid", "hydrocarbon", "oil",
            "fuel", "solvent", "ammonia", "chlorine", "caustic", "gas leak", "h2s",
            "scaffold", "ladder", "roof", "catwalk", "elevated", "mezzanine",
            "trench", "confined space", "pressure", "flange", "explosion", "fire",
            "hot work", "boiler", "forklift", "pinch point", "fracture", "hospitalized"
        ]
        if any(hr in lower_text for hr in high_risk_clues):
            return False, ""

        from app.services.taxonomy_data import ROUTINE_LOW_RISK_PATTERNS
        for pattern_str, canonical in ROUTINE_LOW_RISK_PATTERNS:
            if re.search(pattern_str, lower_text):
                return True, canonical

        for term in ROUTINE_LOW_RISK_TERMS:
            if term in lower_text:
                return True, term

        return False, ""

    @classmethod
    def _extract_hazards(cls, lower_text: str, sentences: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
        matches = []
        snippets = []
        for name, data in HIGH_ENERGY_HAZARDS.items():
            matched_kws = [kw for kw in data["keywords"] if kw in lower_text]
            if matched_kws:
                # Context-sensitive discrimination: floor-level tripping hazard over conduit is NOT electrical exposure
                if name == "Electrical (Arc Flash / High Voltage)" and matched_kws == ["electrical"]:
                    is_floor_conduit_trip = (
                        "conduit" in lower_text and
                        any(tp in lower_text for tp in ["tripped", "trip", "tripping", "stumbled", "bruised", "walkway", "floor"]) and
                        not any(el in lower_text for el in ["shock", "arc", "voltage", "energized", "live wire", "electrocution", "burn"])
                    )
                    if is_floor_conduit_trip:
                        continue

                # Context-sensitive discrimination: verified 0 ppm gas reading without active process release or danger evidence
                if name == "Hazardous Chemical / Toxic Atmosphere" and all(kw in ["h2s", "hydrogen sulfide", "toxic gas"] for kw in matched_kws):
                    has_zero_ppm = bool(re.search(r'\b(?:0\s*ppm|zero\s*ppm|0\.0\s*ppm)\b', lower_text))
                    has_active_danger = any(clue in lower_text for clue in [
                        "leak", "spill", "rupture", "cloud", "spray", "line break",
                        "burst", "exposure", "burned", "hospitalized", "evacuat",
                        "containment loss", "release"
                    ])
                    if has_zero_ppm and not has_active_danger:
                        continue

                # Context-sensitive discrimination: offsite municipal sewer wind drift is not a confined space entry hazard
                if name == "Confined Space" and "sewer" in matched_kws:
                    is_offsite_sewer_drift = (
                        any(w in lower_text for w in ["municipal sewer", "wind drift", "fence line"]) and
                        not any(w in lower_text for w in ["entry", "inside", "entered", "permit", "cleaning", "manhole"])
                    )
                    if is_offsite_sewer_drift:
                        matched_kws = [k for k in matched_kws if k != "sewer"]
                        if not matched_kws:
                            continue

                # Context-sensitive discrimination: inert nitrogen purge/storage without release or exposure is not an active atmospheric hazard
                if (name == "Confined Space" or name == "Hazardous Chemical / Toxic Atmosphere") and all(kw in ["nitrogen purge", "nitrogen-purged", "nitrogen purged", "partially enclosed"] for kw in matched_kws):
                    has_release_or_exposure = any(clue in lower_text for clue in [
                        "leak", "escaped", "release", "dizzy", "unconscious", "collapse", "asphyxiat",
                        "oxygen", "deficient", "deficiency", "entry", "inside", "entered", "breach", "exposed"
                    ])
                    if not has_release_or_exposure:
                        continue

                matches.append({
                    "name": name,
                    "energy_type": data["energy_type"],
                    "min_severity": data["min_severity"],
                    "matched_keywords": matched_kws,
                    "default_barrier": data["default_barrier"]
                })
                # Find sentences containing the keyword
                for s in sentences:
                    s_lower = s.lower()
                    if any(kw in s_lower for kw in matched_kws):
                        snippets.append(s)
        return matches, snippets

    @classmethod
    def _extract_barriers(cls, lower_text: str, sentences: List[str]) -> Tuple[str, str, List[str], List[Dict[str, Any]]]:
        detected_status = "Intact"
        barrier_name = "Administrative / PPE"
        snippets = []
        secondary_barriers = []

        # 1. Multi-barrier reasoning: check if secondary accessory failed while primary physical exclusion barrier held
        has_barrier_held = any(kw in lower_text for kw in ["barrier held", "prevented harm", "caught by harness", "stopped by interlock"])
        has_exclusion = any(kw in lower_text for kw in ["exclusion barricade", "exclusion zone", "kept all personnel outside", "outside drop zone"])
        has_tagline_auxiliary = any(kw in lower_text for kw in ["tagline broke", "tag line broke", "tagline snapped"])

        if has_tagline_auxiliary and (has_exclusion or has_barrier_held):
            detected_status = "Effective"
            barrier_name = "Physical Barricade / Exclusion Zone"
            for s in sentences:
                s_lower = s.lower()
                if any(kw in s_lower for kw in ["tagline", "barricade", "exclusion", "barrier held", "drop zone"]):
                    snippets.append(s)
            return detected_status, barrier_name, snippets, secondary_barriers

        # 2. Confined space entry violations: expired permit or low oxygen inside cannot be overridden by warning alarm
        has_permit_expired = any(kw in lower_text for kw in ["permit expired", "expired permit", "expired entry permit"])
        has_low_oxygen_entry = ("low oxygen" in lower_text or "oxygen deficiency" in lower_text) and any(w in lower_text for w in ["inside", "vessel", "confined space"])

        if has_permit_expired or has_low_oxygen_entry:
            detected_status = "Bypassed" if has_permit_expired else "Failed"
            barrier_name = "Confined Space Entry Permit"
            for s in sentences:
                s_lower = s.lower()
                if any(kw in s_lower for kw in ["permit", "expired", "sniffer", "alarm", "low oxygen", "confined space"]):
                    snippets.append(s)
            return detected_status, barrier_name, snippets, secondary_barriers

        # 3. Paired safeguard failure detection: damaged critical safety component or unstable working platform
        # Note: The generic word "damaged" is NEVER sufficient on its own (e.g. damaged cardboard box).
        # It must be explicitly paired with critical fall protection, machine guarding, or suspended scaffolding.
        has_damaged_safety_gear = (
            "damaged" in lower_text and
            any(gear in lower_text for gear in ["lanyard", "harness", "lifeline", "static line", "anchor point", "interlock", "machine guard", "rigging sling", "shackle", "safety cable"]) and
            any(w in lower_text for w in [
                "damaged lanyard", "damaged connection", "connection was damaged", "lanyard connection was damaged",
                "lanyard was damaged", "damaged harness", "damaged lifeline", "damaged anchor", "damaged interlock",
                "damaged guard", "damaged sling", "damaged shackle"
            ])
        )
        has_unstable_scaffold = (
            "unstable" in lower_text and
            any(sc in lower_text for sc in [
                "scaffold", "scaffolding", "suspended scaffold", "scaffold platform", "staging"
            ]) and
            any(w in lower_text for w in [
                "unstable scaffold", "scaffold platform was unstable", "suspended scaffold platform was unstable",
                "unstable platform", "platform was unstable", "unstable suspended scaffold"
            ])
        )
        if (has_damaged_safety_gear or has_unstable_scaffold) and not has_barrier_held:
            detected_status = "Failed"
            barrier_name = "Fall Arrest Harness" if any(k in lower_text for k in ["lanyard", "harness", "lifeline", "anchor"]) else "Scaffold Physical Support & Guardrail"
            for s in sentences:
                s_lower = s.lower()
                if any(w in s_lower for w in ["damaged", "unstable", "lanyard", "scaffold", "connection", "platform"]):
                    snippets.append(s)
            return detected_status, barrier_name, snippets, secondary_barriers

        # 4. Multi-barrier evidence detection across equipment categories
        equipment_rules = {
            "LOTO / Lockout-Tagout": {
                "mentions": ["loto", "lockout", "tagout", "padlock", "isolation", "isolation diagram", "isolation verification"],
                "failed": [
                    "outdated isolation", "outdated isolation diagram", "unverified isolation",
                    "isolation failed", "failed isolation", "not isolated", "valve left open",
                    "no loto", "missing isolation", "without isolation", "lock jumped",
                    "require independent verification of the vessel's isolation"
                ],
                "missing": ["missing loto", "no lockout", "no tagout"],
                "effective": ["isolation blinds were in place", "zero pressure verified", "zero energy verified", "isolated and tagged", "loto verified", "locked out"]
            },
            "Continuous Gas Detector": {
                "mentions": ["gas detector", "sniffer", "lels", "h2s monitor", "multi-gas", "oxygen monitor", "o2 monitor", "atmospheric monitor", "oxygen detector"],
                "missing": [
                    "missing oxygen monitor", "oxygen monitor had been removed", "removed for calibration",
                    "had not been replaced", "missing gas detector", "without gas detector",
                    "no gas detector", "no sniffer", "detector removed", "did not identify the missing oxygen monitor"
                ],
                "failed": ["detector failed", "expired calibration", "detector malfunctioned", "sensor failed", "sniffer failed", "malfunctioned and had expired calibration sensor"],
                "effective": ["alarm sounded", "gas check showed 0 ppm", "detector showed 0 ppm", "continuous gas detector alarm sounded", "sniffer gas alarm sounded"]
            },
            "Interlock Machine Guard": {
                "mentions": ["guard", "interlock", "light curtain", "barrier gate", "shield"],
                "failed": ["guard fell off", "interlock failed", "guard bypassed", "no guard", "guard removed", "detached guard", "fell off mounting bracket"],
                "missing": ["no guard", "missing guard"],
                "effective": ["interlock tripped", "light curtain interlock tripped", "stopped ram", "stopped by interlock"]
            },
            "Fall Arrest Harness": {
                "mentions": ["harness", "lanyard", "lifeline", "anchor point", "static line"],
                "failed": ["damaged lanyard", "connection was damaged", "lanyard connection was damaged", "damaged harness", "lanyard snap", "snapped lanyard"],
                "missing": ["not tied off", "without attaching lanyard", "without attaching lanyards", "no harness"],
                "effective": ["caught by harness", "harness arrested", "fall arrest held"]
            },
            "Confined Space Entry Permit": {
                "mentions": ["entry permit", "confined space permit", "vessel entry permit"],
                "failed": ["permit expired", "expired permit", "without permit", "expired entry permit"],
                "effective": ["permit verified", "entry permit authorized"]
            },
            "Scaffold Physical Support & Guardrail": {
                "mentions": ["scaffold", "scaffolding", "scaffold platform", "suspended scaffold"],
                "failed": ["unstable scaffold", "platform was unstable", "scaffold platform was unstable", "plank snapped"],
                "missing": ["incomplete handrail", "missing guardrail", "no handrail"],
                "effective": ["scaffold inspected", "guardrail intact"]
            },
            "Pressure Safety Valve (PSV)": {
                "mentions": ["psv", "safety valve", "rupture disk", "pressure relief"],
                "failed": ["psv failed", "relief valve offline", "valve blew out"],
                "effective": ["psv lifted", "relief valve opened"]
            },
            "Rigging / Slings": {
                "mentions": ["sling", "shackle", "rigging wire", "crane hook", "hoist cable", "rigging cable", "crane hoist cable"],
                "failed": ["frayed", "broken strands", "cable frayed", "snapped", "dropped load", "damaged sling", "damaged shackle"],
                "effective": ["rigging inspected", "load held"]
            },
            "Physical Barricade / Exclusion Zone": {
                "mentions": ["barricade", "exclusion zone", "drop zone", "exclusion barricade"],
                "failed": ["no barricade", "barrier broken", "tape was torn", "torn", "breached"],
                "effective": ["barrier held", "exclusion zone held", "kept all personnel outside", "outside drop zone"]
            }
        }

        detected_barriers = []
        for equip_name, rdata in equipment_rules.items():
            if any(m in lower_text for m in rdata["mentions"]):
                eq_status = None
                evidence_kw = None
                
                # Check status evidence in priority: Failed, Missing, Bypassed, Effective
                for kw in rdata.get("failed", []):
                    if kw in lower_text:
                        eq_status = "Failed"
                        evidence_kw = kw
                        break
                if not eq_status:
                    for kw in rdata.get("missing", []):
                        if kw in lower_text:
                            eq_status = "Missing"
                            evidence_kw = kw
                            break
                if not eq_status:
                    for kw in rdata.get("effective", []):
                        if kw in lower_text:
                            eq_status = "Effective"
                            evidence_kw = kw
                            break
                
                if eq_status:
                    b_sentences = []
                    for s in sentences:
                        s_lower = s.lower()
                        if (evidence_kw and evidence_kw in s_lower) or any(m in s_lower for m in rdata["mentions"]):
                            b_sentences.append(s)
                    detected_barriers.append({
                        "name": equip_name,
                        "status": eq_status,
                        "evidence_keyword": evidence_kw,
                        "sentences": b_sentences
                    })

        if detected_barriers:
            # Prioritize primary: LOTO or first failed barrier
            primary = detected_barriers[0]
            for b in detected_barriers:
                if b["name"] == "LOTO / Lockout-Tagout":
                    primary = b
                    break
            
            detected_status = primary["status"]
            barrier_name = primary["name"]
            for s in primary["sentences"]:
                if s not in snippets:
                    snippets.append(s)

            for b in detected_barriers:
                if b["name"] != primary["name"]:
                    secondary_barriers.append({
                        "name": b["name"],
                        "status": b["status"],
                        "evidence": b["sentences"][0] if b["sentences"] else ""
                    })
                    for s in b["sentences"]:
                        if s not in snippets:
                            snippets.append(s)

            return detected_status, barrier_name, snippets, secondary_barriers

        # Standard taxonomy scan fallback
        for status, bdata in BARRIER_TAXONOMY.items():
            matched_kws = [kw for kw in bdata["keywords"] if kw in lower_text]
            if matched_kws:
                detected_status = status
                for s in sentences:
                    s_lower = s.lower()
                    if any(kw in s_lower for kw in matched_kws):
                        snippets.append(s)
                break

        barrier_mentions = {
            "LOTO / Lockout-Tagout": ["loto", "lockout", "tagout", "padlock", "isolation", "isolation diagram", "isolation verification"],
            "Interlock Machine Guard": ["guard", "interlock", "light curtain", "barrier gate", "shield"],
            "Fall Arrest Harness": ["harness", "lanyard", "lifeline", "anchor point", "static line"],
            "Continuous Gas Detector": ["gas detector", "sniffer", "lels", "h2s monitor", "multi-gas", "oxygen monitor", "o2 monitor", "atmospheric monitor", "oxygen detector"],
            "Pressure Safety Valve (PSV)": ["psv", "safety valve", "rupture disk", "pressure relief"],
            "Rigging / Slings": ["sling", "shackle", "rigging wire", "crane hook"],
            "Physical Barricade / Exclusion Zone": ["barricade", "exclusion zone", "drop zone", "exclusion barricade"],
            "Confined Space Entry Permit": ["entry permit", "confined space permit", "vessel entry permit", "permit expired"],
            "Scaffold Physical Support & Guardrail": ["scaffold", "scaffolding", "scaffold platform", "suspended scaffold"]
        }
        for b_name, kws in barrier_mentions.items():
            if any(k in lower_text for k in kws):
                barrier_name = b_name
                break

        return detected_status, barrier_name, snippets, secondary_barriers

    @classmethod
    def _normalize_actual_outcome(cls, reported: str, lower_text: str) -> str:
        if "fatality" in lower_text or "deceased" in lower_text:
            return "Fatality"
        if "amputation" in lower_text or "lost time" in lower_text or "fracture" in lower_text or "hospitalized" in lower_text:
            return "Lost-Time Serious Injury"
        if "medical assessment" in lower_text or "medical evaluation" in lower_text or "medical treatment" in lower_text or "clinic" in lower_text:
            return "Medical Treatment"
        if "first aid" in lower_text or "cut on finger" in lower_text or "bruise" in lower_text:
            return "First Aid"
        if "near miss" in lower_text or "almost" in lower_text or "narrowly avoided" in lower_text or "unharmed" in lower_text:
            return "Near Miss (No Physical Harm)"
        if reported and reported.lower() != "unknown":
            return reported
        return "Unsafe Condition / Observation"

    @classmethod
    def _natural_hazard_name(cls, name: str) -> str:
        mapping = {
            "Gravity / Falls from Height": "falls from height",
            "Hazardous Chemical / Toxic Atmosphere": "toxic chemical release",
            "Pressurized Fluid / Gas / Steam": "high-pressure gas or fluid release",
            "Electrical (Arc Flash / High Voltage)": "electrical arc flash or energized equipment",
            "Suspended / Heavy Loads": "suspended overhead loads",
            "Rotating Equipment / Machine Nip Points": "machinery nip points or moving equipment",
            "Flammable Liquid / Fire / Explosion": "flammable material or fire hazards",
            "Confined Space": "confined space entry hazards",
            "Thermal (Hot Surfaces / Steam)": "extreme thermal or steam exposure",
            "Mobile Heavy Equipment": "mobile heavy equipment or vehicle interaction",
            "General Hazard / Unclassified": "general workplace conditions"
        }
        return mapping.get(name, name.lower())

    @classmethod
    def _natural_barrier_name(cls, name: str) -> str:
        mapping = {
            "LOTO / Lockout-Tagout": "lockout-tagout isolation",
            "Continuous Gas Detector": "continuous gas detection",
            "Interlock Machine Guard": "interlocked machine guarding",
            "Fall Arrest Harness": "fall arrest personal equipment",
            "Confined Space Entry Permit": "confined space entry permitting",
            "Scaffold Physical Support & Guardrail": "scaffold guardrails and platform support",
            "Pressure Safety Valve (PSV)": "pressure relief valves",
            "Rigging / Slings": "crane rigging and slings",
            "Physical Barricade / Exclusion Zone": "physical barricading and exclusion zones",
            "Administrative / PPE": "administrative controls and personal protective equipment",
            "None Specified": "safety barriers"
        }
        return mapping.get(name, name.lower())

    @classmethod
    def _extract_event_snippet(cls, text: str) -> str:
        if not text:
            return ""
        s = text.strip()
        sentences = re.split(r'(?<=[.!?])\s+', s)
        first_s = sentences[0].strip() if sentences else s
        if len(first_s) > 130:
            first_s = first_s[:127].rsplit(' ', 1)[0] + "..."
        return first_s.rstrip('.')

    @classmethod
    def _generate_explanation(
        cls,
        primary_hazard_name: str,
        energy_source: str,
        barrier_status: str,
        barrier_name: str,
        is_sif_precursor: bool,
        risk_priority: str,
        actual_outcome: str,
        potential_severity: str,
        is_routine: bool,
        routine_term: str,
        secondary_barriers: Optional[List[Dict[str, Any]]] = None,
        raw_text: str = "",
        matched_hazards: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generates a clear, detailed, human-readable safety assessment answering:
        1. What happened?
        2. What does the risk level mean?
        3. Which hazard or safety barrier matters?
        4. What could have happened?
        5. What should happen next?
        """
        # 1. WHAT HAPPENED?
        if not raw_text or len(raw_text.strip()) < 15:
            what_happened = "This report logs an incident with limited narrative detail; specific event circumstances are unknown."
        elif is_routine:
            what_happened = f"This report describes a routine facility observation involving {routine_term or 'routine workplace housekeeping'} in which no physical injury was reported."
        else:
            snippet = cls._extract_event_snippet(raw_text)
            clean_s = snippet[0].lower() + snippet[1:] if snippet else ""
            if "Near Miss" in actual_outcome or "near miss" in raw_text.lower():
                if not matched_hazards or primary_hazard_name == "General Hazard / Unclassified":
                    what_happened = "This report describes a near miss in which no physical injury was reported."
                elif clean_s and not clean_s.startswith("near miss"):
                    what_happened = f"This report describes a near miss in which {clean_s}; no physical injury was reported."
                else:
                    what_happened = "This report describes a near miss in which no physical injury was reported."
            elif actual_outcome in ["First Aid", "Medical Treatment"]:
                what_happened = f"This report documents an incident in which {clean_s}, resulting in {actual_outcome.lower()}."
            elif actual_outcome in ["Lost-Time Serious Injury", "Fatality"]:
                what_happened = f"This report documents a serious industrial event in which {clean_s}, logged as {actual_outcome.lower()}."
            else:
                what_happened = f"This report documents an operational safety observation regarding {clean_s}."

        # 2 & 3. RISK LEVEL & HAZARD / BARRIER EVALUATION
        natural_hazard = cls._natural_hazard_name(primary_hazard_name)
        natural_barrier = cls._natural_barrier_name(barrier_name)

        if is_routine:
            risk_and_barriers = (
                "SAJAG classified the case as Low Routine Priority, as the observation represents standard facility housekeeping "
                "rather than an active industrial safety hazard. No high-energy sources or life-safety precursors were detected, "
                "and baseline administrative controls remained intact."
            )
        elif is_sif_precursor:
            barrier_clause = (
                f"{natural_barrier} was recorded as {barrier_status.lower()}"
                if barrier_name not in ["Administrative / PPE", "None Specified"]
                else f"safety barriers were evaluated as {barrier_status.lower()}"
            )
            sec_clause = ""
            if secondary_barriers:
                sec_items = [f"{cls._natural_barrier_name(b['name'])} ({b['status'].lower()})" for b in secondary_barriers]
                sec_clause = f" Additional safeguard breakdowns were identified on {', '.join(sec_items)}."

            risk_and_barriers = (
                f"SAJAG classified the case as Critical SIF Priority because uncontrolled high energy was present with compromised physical safeguards, "
                f"creating credible potential for fatal or life-altering consequences. The primary hazard involves {natural_hazard}, where {barrier_clause}.{sec_clause}"
            )
        elif risk_priority == "HIGH_PRECURSOR":
            barrier_clause = (
                f"{natural_barrier} was recorded as {barrier_status.lower()}"
                if barrier_name not in ["Administrative / PPE", "None Specified"]
                else f"safety barriers were evaluated as {barrier_status.lower()}"
            )
            sec_clause = ""
            if secondary_barriers:
                sec_items = [f"{cls._natural_barrier_name(b['name'])} ({b['status'].lower()})" for b in secondary_barriers]
                sec_clause = f" Additional safeguard breakdowns were identified on {', '.join(sec_items)}."

            risk_and_barriers = (
                f"SAJAG classified the case as High Risk Priority due to significant hazardous energy exposure involving {natural_hazard}, "
                f"where {barrier_clause}.{sec_clause}"
            )
        else:  # MEDIUM_RISK or general
            if not raw_text or len(raw_text.strip()) < 15:
                risk_and_barriers = "Specific hazards and safety barrier conditions are not established from the available report and remain unknown."
            else:
                if not matched_hazards or primary_hazard_name == "General Hazard / Unclassified":
                    hazard_desc = "a general or unclassified hazard"
                else:
                    hazard_desc = f"an identified {natural_hazard}"

                if barrier_status == "Intact" and barrier_name in ["Administrative / PPE", "None Specified"]:
                    barrier_desc = "an administrative/PPE barrier recorded as intact"
                else:
                    barrier_desc = f"{natural_barrier} recorded as {barrier_status.lower()}"

                sec_clause = ""
                if secondary_barriers:
                    sec_items = [f"{cls._natural_barrier_name(b['name'])} ({b['status'].lower()})" for b in secondary_barriers]
                    sec_clause = f" Additional safeguard breakdowns were identified on {', '.join(sec_items)}."

                risk_and_barriers = (
                    f"SAJAG classified the case as Medium Risk, with {hazard_desc} and {barrier_desc}.{sec_clause}"
                )

        # 4. WHAT COULD HAVE HAPPENED? (Potential consequence vs Actual outcome)
        if is_routine:
            consequence_text = (
                "The credible potential consequence remains Low, consistent with routine non-hazardous operations."
            )
        elif is_sif_precursor:
            consequence_text = (
                f"While the actual event outcome was recorded as '{actual_outcome}', the potential consequence is evaluated "
                f"as '{potential_severity}' because uncontrolled high energy without a reliable barrier presents a credible "
                f"risk of life-altering injury or fatality under slightly altered circumstances."
            )
        elif risk_priority == "HIGH_PRECURSOR":
            consequence_text = (
                f"While the recorded outcome was '{actual_outcome}', the potential consequence is evaluated as '{potential_severity}'. "
                f"The underlying energy levels warrant strict containment to prevent escalation."
            )
        else:  # Medium risk
            if not raw_text or len(raw_text.strip()) < 15:
                consequence_text = "Potential consequence severity cannot be determined reliably without additional incident facts."
            elif barrier_status == "Intact" and (not matched_hazards or primary_hazard_name == "General Hazard / Unclassified"):
                consequence_text = (
                    "The available information does not establish a specific failed safety barrier or a more severe potential consequence."
                )
            else:
                consequence_text = (
                    f"While the actual outcome was logged as '{actual_outcome}', the potential consequence is evaluated as '{potential_severity}'. "
                    f"The available information does not establish a more severe potential consequence or catastrophic escalation mechanism."
                )

        # 5. WHAT SHOULD HAPPEN NEXT?
        if is_sif_precursor:
            next_steps = (
                "Operations and safety leadership should immediately verify physical barrier integrity, conduct a job safety review "
                "with the affected work party, and track verified engineering corrective controls through formal verification."
            )
        elif risk_priority == "HIGH_PRECURSOR":
            next_steps = (
                "The area supervisor should inspect physical safeguards, review the applicable operating permit or procedure, "
                "and implement corrective work orders."
            )
        elif is_routine:
            next_steps = (
                "Address through local area housekeeping or supervisor walk-throughs; no urgent engineering intervention is required."
            )
        elif not raw_text or len(raw_text.strip()) < 15:
            next_steps = (
                "The safety coordinator should follow up with the reporting party to gather missing operational details and verify "
                "safeguard status before assigning corrective actions."
            )
        else:
            next_steps = (
                "The safety team should review the original report, confirm that the listed safeguards were appropriate for the situation, "
                "and assign standard corrective actions if required."
            )

        return f"{what_happened} {risk_and_barriers} {consequence_text} {next_steps}"


    @classmethod
    def _calculate_detection_confidence(
        cls,
        cleaned_text: str,
        lower_text: str,
        sentences: List[str],
        matched_hazards: List[Dict[str, Any]],
        is_routine: bool,
        routine_term: str,
        barrier_status: str,
        barrier_name: str,
        secondary_barriers: List[Dict[str, Any]],
        is_sif_precursor: bool,
        risk_priority: str,
        potential_severity: str,
        actual_outcome: str,
        hazard_snippets: List[str],
        barrier_snippets: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate an evidence-based, rule-based precursor detection confidence estimate (0 - 100%).
        Independent of risk level. Bounded and never treats missing data as certainty.
        """
        stripped = (cleaned_text or "").strip()
        words = stripped.split() if stripped else []

        # 1. Missing report data / insufficient evidence boundary
        if not stripped or len(stripped) < 15 or len(words) < 4:
            return {
                "score": None,
                "band": "Unavailable",
                "rating_label": "Confidence unavailable — insufficient evidence",
                "explanation": (
                    "Confidence unavailable — insufficient evidence. The incident report narrative "
                    "contains insufficient factual detail to evaluate hazard presence or safety barrier integrity."
                ),
                "supporting_evidence": [],
                "missing_information": [
                    "Report narrative is missing or too brief to identify operational facts",
                    "No identified physical energy source or hazard mechanism",
                    "No identified safeguard or barrier operational status"
                ],
                "is_rule_based": True
            }

        has_specific_signal = bool(
            matched_hazards
            or is_routine
            or (barrier_status in ["Failed", "Bypassed", "Missing", "Effective", "Degraded"] and barrier_name not in ["Administrative / PPE", "None Specified"])
            or secondary_barriers
        )

        if not has_specific_signal and len(words) < 8:
            return {
                "score": None,
                "band": "Unavailable",
                "rating_label": "Confidence unavailable — insufficient evidence",
                "explanation": (
                    "Confidence unavailable — insufficient evidence. The narrative lacks identifiable "
                    "energy sources, specific equipment, or safety barrier conditions."
                ),
                "supporting_evidence": [],
                "missing_information": [
                    "Specific physical energy source or hazard mechanism",
                    "Safeguard or barrier operational status",
                    "Equipment, unit, or operational task context"
                ],
                "is_rule_based": True
            }

        supporting_evidence: List[str] = []
        missing_information: List[str] = []

        # PILLAR 1: Hazard Evidence & Match Strength (0 - 30 pts)
        hazard_score = 0.0
        if matched_hazards:
            primary_hazard = matched_hazards[0]
            matched_kws = primary_hazard.get("matched_keywords", [])
            has_multi_word_kw = any(
                len(kw.split()) > 1 or kw in [
                    "h2s", "ammonia", "chlorine", "caustic", "flange", "boiler", "scaffold", "amputation", "nitrogen purge"
                ] for kw in matched_kws
            )
            if has_multi_word_kw:
                hazard_score += 24.0
                supporting_evidence.append(f"Identified specific high-energy hazard: [{primary_hazard['name']}] ({', '.join(matched_kws)})")
            else:
                hazard_score += 15.0
                supporting_evidence.append(f"Identified hazard keyword: '{matched_kws[0]}' matching [{primary_hazard['name']}]")

            if len(matched_hazards) > 1 or len(matched_kws) > 1:
                hazard_score += 4.0
                if len(matched_hazards) > 1:
                    supporting_evidence.append(f"Multiple energy sources detected ({len(matched_hazards)} hazard categories)")

            if hazard_snippets:
                hazard_score += 2.0
            hazard_score = min(30.0, hazard_score)
        elif is_routine:
            hazard_score = 26.0
            supporting_evidence.append(f"Recognized low-risk routine housekeeping pattern: '{routine_term}'")
        else:
            hazard_score = 8.0
            missing_information.append("Specific physical energy source or hazard category is unverified")

        # PILLAR 2: Barrier Evidence & Rule Match Strength (0 - 30 pts)
        barrier_score = 0.0
        is_equipment_barrier = barrier_name not in ["Administrative / PPE", "None Specified"]

        if is_equipment_barrier:
            if barrier_status in ["Failed", "Bypassed", "Missing"]:
                barrier_score += 24.0
                supporting_evidence.append(f"Explicit safeguard breakdown '{barrier_status}' identified on [{barrier_name}]")
            elif barrier_status == "Effective":
                barrier_score += 24.0
                supporting_evidence.append(f"Verified safeguard '{barrier_status}' confirmed on [{barrier_name}]")
            elif barrier_status == "Degraded":
                barrier_score += 18.0
                supporting_evidence.append(f"Safeguard degradation detected on [{barrier_name}]")
            else:
                barrier_score += 12.0

            if secondary_barriers:
                barrier_score += 4.0
                sec_summary = ", ".join(f"{b['name']} ({b['status']})" for b in secondary_barriers)
                supporting_evidence.append(f"Secondary safeguard telemetry: {sec_summary}")

            if barrier_snippets:
                barrier_score += 2.0
            barrier_score = min(30.0, barrier_score)
        elif is_routine:
            barrier_score = 25.0
            supporting_evidence.append("Routine observation with intact baseline administrative safeguards")
        else:
            if barrier_status in ["Failed", "Bypassed", "Missing"]:
                barrier_score = 14.0
                supporting_evidence.append(f"Safeguard status evaluated as '{barrier_status}' from general taxonomy")
            else:
                barrier_score = 6.0
                missing_information.append("Specific safety barrier or safeguard operational status is unstated")

        # PILLAR 3: Narrative Richness & Operational Context (0 - 20 pts)
        completeness_score = 0.0
        if len(words) >= 25 or len(sentences) >= 2:
            completeness_score += 8.0
        elif len(words) >= 12:
            completeness_score += 4.0
        else:
            completeness_score += 2.0

        equipment_terms = [
            "vessel", "tank", "valve", "pipe", "flange", "line", "compressor", "pump", "motor",
            "boiler", "scaffold", "crane", "rigging", "hoist", "panel", "conduit", "enclosure",
            "catwalk", "trench", "reactor", "column", "manifold", "cylinder", "furnace",
            "maintenance", "inspection", "turnaround", "purging", "cleaning", "lifting"
        ]
        matched_equip = [eq for eq in equipment_terms if eq in lower_text]
        if matched_equip:
            completeness_score += 6.0
            supporting_evidence.append(f"Report specifies operational equipment/task: {', '.join(matched_equip[:2])}")
        else:
            completeness_score += 2.0
            missing_information.append("Specific operational equipment or industrial task is unstated")

        outcome_terms = [
            "near miss", "unharmed", "first aid", "medical", "hospital", "hospitalized",
            "dizzy", "burn", "cut", "evacuat", "no harm", "no injury", "fatal", "amputation"
        ]
        if any(ot in lower_text for ot in outcome_terms) or (actual_outcome and actual_outcome != "Unsafe Condition / Observation"):
            completeness_score += 6.0
        else:
            completeness_score += 2.0
            missing_information.append("Worker exposure outcome or physical consequences are unconfirmed")

        completeness_score = min(20.0, completeness_score)

        # PILLAR 4: Information Consistency vs Conflict / Ambiguity (0 - 20 pts)
        consistency_score = 20.0

        speculative_phrases = [
            "might have", "maybe", "possibly", "allegedly", "suspected", "unconfirmed",
            "not sure", "unclear if", "unknown if", "rumored", "cause unknown",
            "details unknown", "unverified", "could not determine"
        ]
        found_speculative = [sp for sp in speculative_phrases if sp in lower_text]
        if found_speculative:
            consistency_score -= 15.0
            missing_information.append(f"Report contains speculative or unconfirmed assertions ('{found_speculative[0]}')")

        contradictions = []
        has_barrier_held = any(kw in lower_text for kw in ["barrier held", "prevented harm", "effective", "zero ppm", "held perfectly"])
        has_severe_damage = any(kw in lower_text for kw in ["hospitalized", "fatal", "rupture", "severe burn", "amputation", "explosion"])
        if has_barrier_held and has_severe_damage and not secondary_barriers:
            contradictions.append("Report asserts barrier held while simultaneously logging severe consequence/rupture")

        if "electrical" in lower_text and "conduit" in lower_text and any(tp in lower_text for tp in ["tripped", "stumbled"]):
            if not any(el in lower_text for el in ["shock", "arc", "voltage", "energized"]):
                contradictions.append("Narrative describes floor trip over conduit but references electrical hazard")

        if any(c in lower_text for c in ["zero electrical equipment", "no electrical equipment", "barrier held perfectly"]):
            if any(s in lower_text for s in ["sparking", "arc flash", "live wire", "unlatched and sparking"]):
                contradictions.append("Conflicting statements between electrical sparking and absent electrical equipment")

        if contradictions:
            consistency_score -= 20.0
            for c in contradictions:
                missing_information.append(f"Contradictory evidence: {c}")

        is_severe_claim = (
            "hospitalized" in lower_text or "fatal" in lower_text or "critical" in lower_text or
            potential_severity == "Critical / Fatal" or actual_outcome in ["Fatality", "Lost-Time Serious Injury"]
        )
        if is_severe_claim and not matched_hazards and not is_equipment_barrier:
            consistency_score -= 15.0
            missing_information.append("High severity logged without documented physical energy mechanism or barrier breakdown")

        consistency_score = max(-15.0, min(20.0, consistency_score))

        raw_score = hazard_score + barrier_score + completeness_score + consistency_score
        # Bound score strictly between 20.0 and 92.0 (never 95% or 100% for heuristic rules)
        final_score = round(min(92.0, max(20.0, raw_score)), 0)

        # Confidence display bands (provisional non-statistical thresholds)
        if final_score >= 80.0:
            band = "High Confidence"
        elif final_score >= 60.0:
            band = "Moderate Confidence"
        else:
            band = "Low Confidence"

        # Construct short explanation
        evidence_summary_parts = []
        if is_sif_precursor:
            if matched_hazards:
                kw = matched_hazards[0]['matched_keywords'][0]
                desc_kw = f"the reported {kw} release" if ("release" in lower_text or "purge" in lower_text or "gas" in lower_text or "leak" in lower_text) else f"the reported {kw} hazard"
                evidence_summary_parts.append(desc_kw)
            if is_equipment_barrier and barrier_status in ["Failed", "Bypassed", "Missing"]:
                evidence_summary_parts.append(f"{barrier_status.lower()} {barrier_name} safeguards")
            if secondary_barriers:
                sec_desc = " and ".join(f"{b['status'].lower()} {b['name']}" for b in secondary_barriers)
                evidence_summary_parts.append(f"{sec_desc} evidence")

            if evidence_summary_parts:
                if len(evidence_summary_parts) > 1:
                    joined_evidence = ", ".join(evidence_summary_parts[:-1]) + ", and " + evidence_summary_parts[-1]
                else:
                    joined_evidence = evidence_summary_parts[0]
            else:
                joined_evidence = "the documented high-energy source and compromised safeguard condition"

            explanation = (
                f"Rule-based confidence estimate: {int(final_score)}% — {band}. "
                f"SAJAG identified a potential SIF precursor based on {joined_evidence}."
            )
        elif is_routine:
            explanation = (
                f"Rule-based confidence estimate: {int(final_score)}% — {band}. "
                f"SAJAG identified a routine housekeeping observation based on '{routine_term}' with intact baseline safeguards and no high-energy industrial hazard."
            )
        else:
            explanation = (
                f"Rule-based confidence estimate: {int(final_score)}% — {band}. "
                f"Evaluated as {risk_priority.replace('_', ' ')} based on {barrier_status.lower()} barrier condition and operational context."
            )

        if missing_information:
            explanation += f" Important missing or unverified information: {'; '.join(missing_information[:2])}."

        return {
            "score": final_score,
            "band": band,
            "rating_label": f"{int(final_score)}% — {band}",
            "explanation": explanation,
            "supporting_evidence": supporting_evidence,
            "missing_information": missing_information,
            "is_rule_based": True
        }

    @classmethod
    def get_confidence_metadata(
        cls,
        text: str,
        stored_score: Optional[float] = None,
        hazard_name: Optional[str] = None,
        barrier_name: Optional[str] = None,
        barrier_status: Optional[str] = None,
        sif_flag: Optional[bool] = None,
        priority: Optional[str] = None,
        outcome: Optional[str] = None,
        explanation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Helper method to derive or retrieve full confidence metadata for a safety report.
        """
        if not text or len(text.strip()) < 15:
            return {
                "score": None,
                "band": "Unavailable",
                "rating_label": "Confidence unavailable — insufficient evidence",
                "explanation": "Confidence unavailable — insufficient evidence. The incident report contains insufficient narrative data.",
                "supporting_evidence": [],
                "missing_information": ["Report narrative is missing or insufficient to evaluate precursor evidence"],
                "is_rule_based": True
            }

        # If a stored score is already calibrated on the 0-100 scale, evaluate text to produce rich metadata
        analysis = cls.analyze_report(text, reported_outcome=outcome or "Unknown")
        return {
            "score": analysis["confidence_score"],
            "band": analysis["confidence_band"],
            "rating_label": f"{int(analysis['confidence_score'])}% — {analysis['confidence_band']}" if analysis["confidence_score"] is not None else "Confidence unavailable — insufficient evidence",
            "explanation": analysis["confidence_explanation"],
            "supporting_evidence": analysis["confidence_supporting_evidence"],
            "missing_information": analysis["confidence_missing_information"],
            "is_rule_based": True
        }

