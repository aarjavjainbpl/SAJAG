from typing import List, Dict, Any

class ActionEngine:
    """
    Corrective-Action Intelligence and Hierarchy of Controls engine.
    Ensures high-energy precursors receive robust engineering controls rather than weak administrative band-aids,
    and enforces strict evidence verification before action closure.
    """

    RECOMMENDED_CONTROLS = {
        "Gravity / Falls from Height": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Install Rigid Guardrails & Certified Static Anchor Lines",
                "description": "Retrofit physical perimeter edge protection or fixed overhead horizontal lifeline so workers are physically arrested without relying on temporary tie-offs."
            },
            {
                "hierarchy_level": "Elimination",
                "title": "Perform Task from Ground Level / Drone Inspection",
                "description": "Evaluate if elevated inspection can be replaced with remote camera/drone or telescoping tools to eliminate working at height completely."
            }
        ],
        "Suspended / Heavy Loads": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Install Physical Load Exclusion Barricades & Interlocked Warning Beacons",
                "description": "Install physical swing gates and flashing sirens triggered during crane movement to physically prevent personnel from entering the swing radius."
            },
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Decommission Worn Rigging & Implement RFID Tagged Pre-Lift Verification",
                "description": "Quarantine damaged slings and institute mandatory RFID digital pre-lift verification before hoist operation."
            }
        ],
        "Electrical (Arc Flash / High Voltage)": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Install Captive-Key Interlocks & Remote Racking Device",
                "description": "Implement mechanical captive-key interlock system to prevent opening switchgear cabinet doors while energized, plus remote racking to remove operator from arc flash boundary."
            },
            {
                "hierarchy_level": "Engineering Controls",
                "title": "LOTO Physical Padlock Station & Zero-Energy Test Verification Point",
                "description": "Install dedicated LOTO lockout station with verified test points for live-line voltage detectors."
            }
        ],
        "Pressurized Fluid / Gas / Steam": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Install Dual Block & Bleed Valves with Blast Deflection Shields",
                "description": "Upgrade single isolation to certified double block and bleed valves, and fit flange spray shields over high-pressure joints."
            },
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Overhaul PSV & Calibrate Automated High-Pressure Trip Interlock",
                "description": "Test and recertify pressure relief valve and confirm automated emergency depressurization trip activates within spec."
            }
        ],
        "Hazardous Chemical / Toxic Atmosphere": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Interlock Continuous Oxygen Monitoring & Zero-Energy Isolation Verification",
                "description": "Mandate continuous calibrated oxygen monitoring with audible evacuation alarms in enclosed/partially enclosed areas, and require dual-person independent verification of physical isolation blinds prior to opening purged equipment."
            },
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Install Fixed Optical Gas Detectors Interlocked with Emergency Scrubber",
                "description": "Deploy point gas detectors linked directly to plant SCADA to trigger exhaust scrubbers and audible alarms upon LEL threshold breach."
            },
            {
                "hierarchy_level": "Substitution",
                "title": "Substitute Corrosive / Flammable Solvent with Non-Hazardous Medium",
                "description": "Evaluate aqueous cleaning solutions or lower vapor-pressure chemicals to minimize toxic vapor evolution."
            }
        ],
        "Confined Space": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Install Continuous Forced Ventilation with Multi-Point Atmospheric Sampling",
                "description": "Deploy certified positive-pressure blowers and multi-probe continuous gas sniffers before and during entry."
            }
        ],
        "Mechanical / Rotating Equipment / Pinch Point": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Install Interlocked Optical Light Curtain and Emergency Pull-Cord",
                "description": "Install Category 4 safety interlock that cuts power within milliseconds if protective zone is breached."
            }
        ],
        "Heavy Mobile Equipment / Traffic": [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Physical Steel Bollard Segregation & Radar Proximity Detection",
                "description": "Erect heavy steel crash barriers along pedestrian aisles and fit automated ultrasonic/radar braking on mobile machinery."
            }
        ]
    }

    @classmethod
    def suggest_actions(
        cls,
        hazard_category: str,
        is_sif_precursor: bool,
        barrier_name: str = None,
        barrier_status: str = None,
        description: str = None,
        secondary_barriers: list = None
    ) -> List[Dict[str, Any]]:
        desc_lower = (description or "").lower()
        sec_barriers = secondary_barriers or []

        # 1. Non-SIF / Benign scenarios: generate targeted preventive checks without emergency shutdown
        if not is_sif_precursor:
            if any(term in desc_lower for term in ["cylinder storage", "storage rack", "nitrogen cylinder"]):
                return [
                    {
                        "hierarchy_level": "Administrative Controls",
                        "title": "Routine Cylinder Storage & Chain Restraint Walkthrough",
                        "description": "Periodically inspect compressed gas cylinder storage racks and safety chains during routine area walkthroughs; confirm pressure gauges read within normal limits.",
                        "target_barrier": "Administrative / PPE",
                        "verification_required": False,
                        "status": "Recommended",
                        "is_effective": False
                    }
                ]
            if any(term in desc_lower for term in ["spilled coffee", "spilled water", "trash on floor", "dusty glasses", "door knob loose"]):
                return [
                    {
                        "hierarchy_level": "Administrative Controls",
                        "title": "Workplace Housekeeping & Local Maintenance Follow-up",
                        "description": "Address identified minor housekeeping item and confirm completion during routine supervisor walkthrough.",
                        "target_barrier": "Administrative / PPE",
                        "verification_required": False,
                        "status": "Recommended",
                        "is_effective": False
                    }
                ]
            return [
                {
                    "hierarchy_level": "Administrative Controls",
                    "title": "Workplace Housekeeping & Inspection Follow-up",
                    "description": "Correct identified minor deficiency and log confirmation during next shift walkthrough.",
                    "target_barrier": barrier_name or "Administrative / PPE",
                    "verification_required": False,
                    "status": "Recommended",
                    "is_effective": False
                }
            ]

        # 2. High-Energy / SIF Precursor scenarios: generate barrier-grounded actionable recommendations
        tailored_actions = []

        def _check_sec_barrier(target_name: str) -> bool:
            for b in sec_barriers:
                if isinstance(b, dict):
                    if b.get("name") == target_name and b.get("status") in ["Failed", "Bypassed", "Missing", "Degraded"]:
                        return True
                elif isinstance(b, str) and target_name.lower() in b.lower():
                    return True
            return False

        # A. Isolation Integrity: Verify correct diagram, isolate source, and independently verify zero-energy
        has_isolation_issue = (
            (barrier_name == "LOTO / Lockout-Tagout" and barrier_status in ["Failed", "Bypassed", "Missing", "Degraded"]) or
            _check_sec_barrier("LOTO / Lockout-Tagout") or
            any(term in desc_lower for term in ["outdated isolation", "unverified isolation", "isolation diagram", "isolation verification", "nitrogen-purged", "purged vessel", "drain connection"])
        )
        if has_isolation_issue:
            tailored_actions.append({
                "hierarchy_level": "Engineering Controls",
                "title": "Zero-Energy Physical Isolation Verification & Drawing Recertification",
                "description": "Verify the correct current P&ID isolation diagram, isolate the nitrogen/process source using positive mechanical isolation (blinds/spectacle plates), and independently verify zero-energy and safe depressurized conditions before work resumes.",
                "target_barrier": "LOTO / Lockout-Tagout",
                "verification_required": True,
                "status": "Recommended",
                "is_effective": False
            })

        # B. Oxygen Monitoring: Restore calibrated continuous monitoring before entry; assess personal/continuous monitoring
        has_o2_issue = (
            (barrier_name == "Continuous Gas Detector" and barrier_status in ["Failed", "Missing", "Degraded"]) or
            _check_sec_barrier("Continuous Gas Detector") or
            any(term in desc_lower for term in ["oxygen monitor", "missing oxygen", "oxygen deficiency", "nitrogen", "asphyxiat", "gas detector"])
        )
        if has_o2_issue:
            tailored_actions.append({
                "hierarchy_level": "Engineering Controls",
                "title": "Restore Calibrated Continuous Oxygen Monitoring & Deploy Personal Multi-Gas Detectors",
                "description": "Restore suitable calibrated continuous oxygen monitoring with audible evacuation alarms before authorizing entry or work in the potentially oxygen-deficient area; assess and deploy personal wearable 4-gas/O2 monitors for all personnel.",
                "target_barrier": "Continuous Gas Detector",
                "verification_required": True,
                "status": "Recommended",
                "is_effective": False
            })

        # C. Work Authorization: Review permit, missing safeguards, and high-risk work authorization before restart
        has_permit_issue = (
            any(term in desc_lower for term in ["permit", "work authorization", "diagram", "safeguard", "verification"]) or
            is_sif_precursor
        )
        if has_permit_issue:
            tailored_actions.append({
                "hierarchy_level": "Administrative Controls",
                "title": "Permit-to-Work Safeguard Audit & High-Risk Authorization Gate",
                "description": "Review the maintenance permit, missing safeguards, and high-risk work authorization before restarting operations; mandate independent physical sign-off verifying calibrated atmospheric monitors and vessel isolation.",
                "target_barrier": "Work Authorisation & Permitting",
                "verification_required": True,
                "status": "Recommended",
                "is_effective": False
            })

        if tailored_actions:
            return tailored_actions

        # Match from hazard dictionary
        for hazard_key, actions in cls.RECOMMENDED_CONTROLS.items():
            if hazard_key.lower() in hazard_category.lower() or hazard_category.lower() in hazard_key.lower():
                return actions

        # Default fallback controls adhering to Hierarchy of Controls
        return [
            {
                "hierarchy_level": "Engineering Controls",
                "title": "Engineer Physical Safety Barrier or Redundant Interlock",
                "description": "Install physical barrier, interlock, or automated shutdown mechanism to isolate the high-energy hazard from personnel.",
                "target_barrier": barrier_name or "Engineering Barrier",
                "verification_required": True,
                "status": "Recommended",
                "is_effective": False
            },
            {
                "hierarchy_level": "Administrative Controls",
                "title": "Audit Isolation Procedures and Conduct Pre-Job Hazard Analysis",
                "description": "Review standard operating procedures and perform documented JHA with maintenance lead prior to resuming work.",
                "target_barrier": "Administrative / PPE",
                "verification_required": True,
                "status": "Recommended",
                "is_effective": False
            }
        ]

    @staticmethod
    def validate_closure(
        status: str,
        verification_required: bool,
        verification_notes: str,
        verified_by: str
    ) -> Dict[str, Any]:
        """
        Prevents 'False Closure': Ensures action cannot be closed without verified physical proof.
        """
        if status in ["Verified & Closed", "Closed"]:
            if verification_required:
                if not verified_by or len(verified_by.strip()) < 2:
                    return {
                        "allowed": False,
                        "error": "Independent Verification Gate Failed: An authorized verifier name/badge is required before closing this action."
                    }
                if not verification_notes or len(verification_notes.strip()) < 10:
                    return {
                        "allowed": False,
                        "error": "Independent Verification Gate Failed: Substantive verification evidence notes (minimum 10 characters) must be documented."
                    }
        return {"allowed": True, "error": None}
