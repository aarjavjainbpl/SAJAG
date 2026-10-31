import re
import uuid
from typing import List, Dict, Any
from app.services.sif_intelligence import SIFIntelligenceEngine
from app.services.taxonomy_data import match_iogp_rules

class ReportChunker:
    """
    Transforms parsed PDF pages into structured, auditable knowledge records.
    Strictly separates Reported Facts, Investigator Conclusions, Recommendations,
    and AI-Generated Interpretations.
    """

    @classmethod
    def chunk_report_pages(cls, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records = []

        for p in pages:
            raw_text = p["raw_text"]
            page_num = p["page_number"]
            source = p["source_report"]
            filename = p["filename"]
            incident = p["incident"]
            section = p["section"]

            # Split into natural paragraphs / segments
            paragraphs = cls._split_into_paragraphs(raw_text)

            for para_idx, para in enumerate(paragraphs):
                if len(para.strip()) < 80:
                    continue # Skip non-substantive lines / fragments

                fact_type = cls._determine_fact_type(section, para)
                hazard, failed_safeguard, contributing_factor, recommendation = cls._extract_entities(para, section)
                
                # Apply SAJAG SIF Precursor AI interpretation
                ai_triage = SIFIntelligenceEngine.analyze_report(para)
                ai_interpretation = {
                    "energy_source": ai_triage["energy_source"],
                    "barrier_status": ai_triage["barrier_status"],
                    "sif_precursor_flag": ai_triage["sif_precursor_flag"],
                    "risk_priority": ai_triage["risk_priority"]
                }

                # Map implicated IOGP Life-Saving Rules
                iogp_rules = match_iogp_rules(para)

                chunk_id = f"KB-{p['report_id']}-P{page_num}-{para_idx+1}"

                records.append({
                    "chunk_id": chunk_id,
                    "source_report": source,
                    "pdf_filename": filename,
                    "report_id": p["report_id"],
                    "page_number": page_num,
                    "section_type": section,
                    "fact_type": fact_type,
                    "incident": incident,
                    "hazard": hazard,
                    "failed_safeguard": failed_safeguard,
                    "contributing_factor": contributing_factor,
                    "recommendation": recommendation,
                    "supporting_text": para.strip(),
                    "ai_interpretation": ai_interpretation,
                    "iogp_rules": iogp_rules
                })

        return records

    @staticmethod
    def _split_into_paragraphs(text: str) -> List[str]:
        # Split on double line breaks or bullet points
        raw_paras = re.split(r'\n{2,}|\n(?=[•\-\d]+\. )', text)
        merged = []
        buf = ""
        for p in raw_paras:
            clean = " ".join(p.split())
            if len(buf) + len(clean) < 600:
                buf = (buf + " " + clean).strip()
            else:
                if buf: merged.append(buf)
                buf = clean
        if buf:
            merged.append(buf)
        return merged

    @staticmethod
    def _determine_fact_type(section: str, text: str) -> str:
        lower_sec = section.lower()
        lower_text = text.lower()

        if "recommendation" in lower_sec or "recommend" in lower_text and any(x in lower_text for x in ["api", "epa", "refinery shall", "require"]):
            return "OFFICIAL_RECOMMENDATION"
        if "root cause" in lower_sec or "contributing" in lower_sec or "conclusion" in lower_sec or "causal" in lower_sec:
            return "INVESTIGATOR_CONCLUSION"
        if "csb concludes" in lower_text or "investigators determined" in lower_text or "findings" in lower_text or "csb identified" in lower_text:
            return "INVESTIGATOR_CONCLUSION"
        if "key lesson" in lower_sec or "lesson" in lower_text:
            return "KEY_LESSON"
        if "incident description" in lower_sec or "timeline" in lower_sec or "factual" in lower_sec or "background" in lower_sec:
            return "REPORTED_FACT"
        return "REPORTED_FACT"

    @classmethod
    def _extract_entities(cls, text: str, section: str):
        lower = text.lower()
        
        # Hazard identification
        hazard = "General Chemical / Refining Hazard"
        if "naphtha" in lower or "gas cutting" in lower or "stabilizer reboiler" in lower or "isom" in lower:
            hazard = "Flammable Light Naphtha Vapor & Trapped Hydrocarbon Release"
        elif "htha" in lower or "nelson curve" in lower or "e-6600" in lower or "heat exchanger" in lower and "rupture" in lower:
            hazard = "High-Pressure Hydrogen / NHT Naphtha Exchanger Rupture & Fire"
        elif "sulfidation" in lower or "sidecut" in lower or "corrosion" in lower and "pipe" in lower:
            hazard = "Flammable Light Gas Oil / Crude Sidecut Hydrocarbon Pipe Rupture"
        elif "propane" in lower or "lpg" in lower or "butane" in lower:
            hazard = "Pressurized Flammable Gas / LPG"
        elif "hydrofluoric acid" in lower or " hf " in lower:
            hazard = "Toxic Hydrofluoric Acid (HF) Release"
        elif "blowout" in lower or "pore pressure" in lower or "well kick" in lower:
            hazard = "Subsea Well Blowout / High-Pressure Hydrocarbon Kick"
        elif "electrostatic precipitator" in lower or "esp" in lower:
            hazard = "Flammable Hydrocarbon Ignition in Electrostatic Precipitator"
        elif "chlorine" in lower:
            hazard = "Toxic Chlorine Gas Release"

        # Failed Safeguard identification
        failed_safeguard = "Not explicitly stated"
        # IOCL Haldia Safeguard Failures
        if "reboiler" in lower and ("drain" in lower or "choked" in lower or "flushing" in lower or "steaming" in lower):
            failed_safeguard = "Common reboiler drain choked and inadequate steam flushing prior to equipment opening"
        elif "blind" in lower and ("flange" in lower or "unblinded" in lower or "positive isolation" in lower or "opening" in lower):
            failed_safeguard = "Absence of positive isolation / blinding prior to opening reboiler inlet flange"
        elif "detector" in lower and ("alarm" in lower or "82006ai0301a" in lower or "high-high" in lower):
            failed_safeguard = "Hydrocarbon gas detector high-high alarm activated 100 min prior to fire without job stoppage"
        elif "tool" in lower and ("spark" in lower or "metallic" in lower or "wrench" in lower or "hammer" in lower):
            failed_safeguard = "Use of standard metallic sparking tools in hazardous hydrocarbon zone"
        elif "supervis" in lower and ("shift change" in lower or "reliever" in lower or "lunch" in lower or "absent" in lower):
            failed_safeguard = "Absence of refinery supervisory presence during operator shift change / mock drill"
        # Tesoro Anacortes Safeguard Failures
        elif "htha" in lower or "nelson" in lower or "attack" in lower and "hydrogen" in lower:
            failed_safeguard = "High Temperature Hydrogen Attack (HTHA) in carbon steel shell operating above Nelson curves"
        elif "e-6600" in lower or ("heat exchanger" in lower and "rupture" in lower):
            failed_safeguard = "Catastrophic rupture of NHT heat exchanger E-6600E shell at 440 psig"
        elif "ultrasonic" in lower or "ndt" in lower or "inspection" in lower and "detect" in lower:
            failed_safeguard = "Failure of ultrasonic inspection techniques to detect microscopic sub-surface HTHA fissuring"
        # Chevron Richmond Safeguard Failures
        elif "sulfidation" in lower and ("silicon" in lower or "corrosion" in lower or "thin" in lower):
            failed_safeguard = "Severe sulfidation corrosion in low-silicon (<0.10 wt%) carbon steel 4-sidecut piping"
        elif "clamp" in lower and ("leak" in lower or "hot tap" in lower or "box" in lower):
            failed_safeguard = "Attempting to install temporary mechanical leak clamp on active 640°F hydrocarbon leak"
        elif "rosov" in lower or "emergency isolation valve" in lower or "eiv" in lower or "remotely operated" in lower:
            failed_safeguard = "Absence of remotely operated emergency isolation valves (ROSOVs) on distillation column"
        # Other Industrial Safeguards
        elif "dead-leg" in lower or "dead leg" in lower or "frozen" in lower or "ice" in lower:
            failed_safeguard = "Dead-leg uninsulated piping elbow freeze protection failure"
        elif "scsv" in lower or "spent catalyst slide valve" in lower or "slide valve" in lower:
            failed_safeguard = "Spent Catalyst Slide Valve (SCSV) erosion & failure to seal"
        elif "cement" in lower and ("integrity" in lower or "negative pressure test" in lower or "barrier" in lower):
            failed_safeguard = "Wellbore casing cement barrier integrity and negative pressure test misinterpretation"
        elif "blowout preventer" in lower or " bop " in lower or "blind shear ram" in lower or "annular preventer" in lower:
            failed_safeguard = "Blowout Preventer (BOP) drillpipe buckling & failure to seal wellbore"
        elif "pipe elbow" in lower and ("corroded" in lower or "thin" in lower or "ruptured" in lower or "nickel" in lower):
            failed_safeguard = "Carbon steel pipe elbow severe localized HF thinning (high Ni/Cu content)"

        # Contributing Factor
        contributing_factor = "Not specified"
        # IOCL Contributing Factors
        if "grating" in lower or "gas cutting" in lower or "chlorine guard" in lower or "3 m" in lower:
            contributing_factor = "Simultaneous grating gas cutting job permitted 3m away from open flange releasing naphtha"
        elif "340" in lower or "contract" in lower and "congestion" in lower or "escape route" in lower:
            contributing_factor = "Congested unit with ~340 contract workmen and inadequate emergency escape routes"
        elif "mock drill" in lower or "level-iii" in lower or "level-3" in lower:
            contributing_factor = "Level-3 mock drill caused work stoppage and simultaneous shift change task clustering"
        elif "oisd-std-118" in lower or "inter-distance" in lower:
            contributing_factor = "MSQ block units spacing non-compliance with OISD-STD-118 layout requirements"
        # Tesoro Contributing Factors
        elif "reliance" in lower and "nelson" in lower:
            contributing_factor = "Flawed industry reliance on carbon steel Nelson Curve operating limits"
        elif "tighten" in lower or "startup" in lower and "leak" in lower:
            contributing_factor = "Normalization of startup flange leaks and hot bolt tightening on pressurized equipment"
        elif "cr-mo" in lower or "alloy" in lower or "upgrade" in lower:
            contributing_factor = "Failure to upgrade heat exchanger shell metallurgy from carbon steel to Cr-Mo alloy"
        # Chevron Contributing Factors
        elif "shutdown" in lower and ("delay" in lower or "evacuat" in lower or "order" in lower):
            contributing_factor = "Failure to immediately execute emergency shutdown and evacuate personnel upon leak discovery"
        elif "inspect" in lower and ("circuit" in lower or "component" in lower or "100%" in lower):
            contributing_factor = "Inadequate piping inspection program inspecting only select lines while missing vulnerable runs"
        elif "moc" in lower or "management of change" in lower:
            contributing_factor = "Lack of formal Management of Change (MOC) review for ongoing leak intervention"
        elif "pha" in lower or "hazop" in lower:
            contributing_factor = "Process Hazard Analysis (PHA) failed to identify acute failure scenario"

        # Recommendation
        recommendation = ""
        if "recommend" in section.lower() or "recommend" in lower:
            match = re.search(r'(?:recommend[^\.\n]+[\.\n]|20\d\d-\d\d-i-[a-z]+-r\d+[\s\S]+?)(?=\n\n|$)', text, re.IGNORECASE)
            if match:
                recommendation = match.group(0).strip()
            else:
                recommendation = text.strip()

        return hazard, failed_safeguard, contributing_factor, recommendation
