"""
Domain Taxonomy and Safety Ontology for SAJAG
Derived from Campbell Institute SIF Precursor Framework, OSHA 1910/1926 Standards,
and Energy-Based Safety Principles (Energy Wheel).
"""

HIGH_ENERGY_HAZARDS = {
    "Gravity / Falls from Height": {
        "keywords": ["fall from height", "scaffold", "ladder", "roof", "floor opening", "unprotected edge", "harness", "lanyard", "elevated", "catwalk", "grating", "fall protection"],
        "min_severity": "Critical / Fatal",
        "energy_type": "Kinetic (Gravity)",
        "default_barrier": "Fall Arrest Harness & Anchor"
    },
    "Suspended / Heavy Loads": {
        "keywords": ["suspended load", "crane", "rigging", "hoist", "slings", "overhead load", "dropped object", "derrick", "winch", "rigging failure", "line of fire under load"],
        "min_severity": "Critical / Fatal",
        "energy_type": "Kinetic / Potential",
        "default_barrier": "Rigging Inspection & Exclusion Zone"
    },
    "Electrical (Arc Flash / High Voltage)": {
        "keywords": ["electrical", "arc flash", "high voltage", "switchgear", "transformer", "energized panel", "busbar", "shock", "electrocution", "overhead line", "live wire"],
        "min_severity": "Critical / Fatal",
        "energy_type": "Electrical (> 50V)",
        "default_barrier": "LOTO & Voltage Verification"
    },
    "Pressurized Fluid / Gas / Steam": {
        "keywords": ["high pressure", "pressurized line", "hydraulic hose", "steam leak", "relief valve", "blowout", "piping rupture", "flange leak", "gas leak", "hydrocarbon leak", "pipeline burst", "psv", "vapor leak", "packing leak"],
        "min_severity": "Critical / Fatal",
        "energy_type": "Pressure (> 100 psi)",
        "default_barrier": "Isolation Valves & Depressurization"
    },
    "Hazardous Chemical / Toxic Atmosphere": {
        "keywords": [
            "h2s", "hydrogen sulfide", "toxic gas", "benzene", "chlorine", "ammonia",
            "acid leak", "acid spill", "chemical spill", "asphyxiation", "asphyxiant", "asphyxiating",
            "flammable vapor", "chemical burn", "corrosive spill", "butane", "butane vapor",
            "flammable gas", "residual nitrogen", "nitrogen release", "nitrogen leak", "nitrogen escaped",
            "oxygen deficiency", "oxygen deficient", "oxygen-deficient"
        ],
        "min_severity": "Critical / Fatal",
        "energy_type": "Chemical / Toxic",
        "default_barrier": "Gas Detector & Scrubbers / PPE"
    },
    "Confined Space": {
        "keywords": [
            "confined space", "vessel entry", "storage tank", "sewer", "manhole",
            "nitrogen purge", "nitrogen-purged", "nitrogen purged", "oxygen deficiency",
            "oxygen deficient", "vault", "atmospheric testing", "entry permit", "partially enclosed"
        ],
        "min_severity": "Critical / Fatal",
        "energy_type": "Atmospheric / Entrapment",
        "default_barrier": "Continuous Gas Monitor & Attendant"
    },
    "Mechanical / Rotating Equipment / Pinch Point": {
        "keywords": ["conveyor", "pinch point", "rotating shaft", "nip point", "crushed", "entanglement", "machine guard", "hydraulic press", "punch press", "press ram", "lathe", "roller", "stamping"],
        "min_severity": "High / Amputation",
        "energy_type": "Mechanical / Kinetic",
        "default_barrier": "Fixed Interlock Machine Guard"
    },
    "Heavy Mobile Equipment / Traffic": {
        "keywords": ["forklift", "haul truck", "loader", "excavator", "pedestrian", "blind spot", "struck by vehicle", "traffic interface", "dump truck", "crushed against wall"],
        "min_severity": "Critical / Fatal",
        "energy_type": "Mobile Kinetic",
        "default_barrier": "Physical Pedestrian Segregation"
    },
    "Thermal / Fire / Explosion": {
        "keywords": ["explosion", "fire", "flash fire", "furnace", "molten metal", "hot work", "ignition source", "spark", "welding fumes", "boiler flare"],
        "min_severity": "Critical / Fatal",
        "energy_type": "Thermal / Radiation",
        "default_barrier": "Hot Work Permit & Fire Watch"
    }
}

BARRIER_TAXONOMY = {
    "Failed": {
        "keywords": [
            "failed", "broke", "snapped", "ruptured", "faulty", "blew out", "malfunctioned", "collapsed", "tripped offline",
            "fell off mounting", "guard fell off", "fell off", "detached guard",
            "scrubber was offline", "scrubber offline", "piping rupture",
            "unrated electrical conduit", "unrated conduit", "unrated anchor", "hooked to unrated",
            "damaged lanyard", "damaged connection", "lanyard connection was damaged", "connection was damaged",
            "lanyard was damaged", "damaged harness", "damaged lifeline", "damaged anchor",
            "unstable scaffold", "scaffold platform was unstable", "suspended scaffold platform was unstable",
            "unstable platform", "unstable suspended scaffold",
            "outdated isolation", "outdated isolation diagram", "unverified isolation"
        ],
        "score_weight": 1.0
    },
    "Bypassed": {
        "keywords": [
            "bypassed", "overridden", "cheated", "disabled", "defeated", "tampered", "bridged", "jumped",
            "permit expired", "expired permit", "expired entry permit"
        ],
        "score_weight": 0.95
    },
    "Missing": {
        "keywords": [
            "missing", "absent", "not installed", "no guard", "no harness", "without permit", "no barricade", "unprotected", "no tagout",
            "without attaching lanyards", "without attaching lanyard", "incomplete handrail", "not tied off",
            "missing oxygen monitor", "oxygen monitor was missing", "missing gas detector",
            "oxygen monitor had been removed", "removed for calibration", "had not been replaced", "missing oxygen monitoring"
        ],
        "score_weight": 0.90
    },
    "Degraded": {
        "keywords": ["degraded", "corroded", "worn out", "frayed", "cracked", "leaking slowly", "loose", "vibrating", "partially blocked"],
        "score_weight": 0.70
    },
    "Effective": {
        "keywords": ["prevented harm", "caught by harness", "stopped by interlock", "barrier held", "alarm sounded", "contained"],
        "score_weight": 0.20
    }
}

ROUTINE_LOW_RISK_TERMS = [
    "spilled coffee", "spilled water", "trash on floor", "dusty glasses", "shoe untied",
    "paper cut", "ergonomic chair", "office desk", "loose carpet", "door knob loose",
    "stapler", "lightbulb dim", "slip on level walkway", "scuff mark"
]

# Patterns supporting common wording variations (passive voice, inverted order, etc.)
ROUTINE_LOW_RISK_PATTERNS = [
    (r"\b(?:coffee\b[^\n\.\;]*?\b(?:spill|spilled|spilling)|(?:spill|spilled|spilling)\b[^\n\.\;]*?\bcoffee)\b", "spilled coffee"),
    (r"\b(?:water\b[^\n\.\;]*?\b(?:spill|spilled|spilling)|(?:spill|spilled|spilling)\b[^\n\.\;]*?\bwater)\b", "spilled water"),
    (r"\b(?:trash|litter)\s+on\s+(?:the\s+)?floor\b", "trash on floor"),
    (r"\bdusty\s+(?:glasses|lenses)\b", "dusty glasses"),
    (r"\b(?:shoe(?:s)?\b[^\n\.\;]*?\buntied|untied\s+shoe(?:s|lace)?)\b", "shoe untied"),
    (r"\bpaper\s+cut\b", "paper cut"),
    (r"\b(?:ergonomic|office)\s+chair\b", "ergonomic chair"),
    (r"\boffice\s+desk\b|\bdesk\s+drawer\b", "office desk"),
    (r"\b(?:carpet\b[^\n\.\;]*?\bloose|loose\s+carpet)\b", "loose carpet"),
    (r"\b(?:door\s*knob\b[^\n\.\;]*?\bloose|loose\s+door\s*knob)\b", "door knob loose"),
    (r"\bstapler\b", "stapler"),
    (r"\b(?:lightbulb\b[^\n\.\;]*?\b(?:dim|flicker|flickering)|(?:dim|flicker|flickering)\b[^\n\.\;]*?\blightbulb)\b", "lightbulb dim"),
    (r"\bslip\s+on\s+level\s+walkway\b", "slip on level walkway"),
    (r"\bscuff\s+mark\b", "scuff mark")
]

IOGP_LIFE_SAVING_RULES = {
    "Hot Work": {
        "rule": "Control flammables and ignition sources",
        "description": "Identify and control all ignition sources, confirm gas test results, and clear flammable atmosphere before hot work.",
        "keywords": ["hot work", "gas cutting", "welding", "torch", "grinding", "spark", "open flame", "ignition source", "explosive gas test", "lel test"]
    },
    "Energy Isolation": {
        "rule": "Verify isolation and zero energy before work begins",
        "description": "Apply physical positive isolation, lock-out/tag-out (LOTO), blinding/spading, depressurize and verify zero energy before opening process equipment.",
        "keywords": ["isolation", "blinding", "positive isolation", "spade", "slip blind", "lockout", "tagout", "loto", "depressurize", "drain line", "residual hydrocarbon", "zero energy"]
    },
    "Bypassing Safety Controls": {
        "rule": "Obtain authorisation before overriding or disabling safety controls",
        "description": "Do not bypass, bridge, or defeat critical interlocks, emergency shutdowns, or alarms without formal MOC authorisation.",
        "keywords": ["bypass", "overridden", "defeat", "disabled", "bridging", "leak clamp", "hot tap", "alarm ignored", "alarm disabled", "safety device bypassed"]
    },
    "Line of Fire": {
        "rule": "Keep yourself and others out of the line of fire",
        "description": "Position yourself away from moving machinery, pressurized discharge trajectories, dropped object paths, and uncontrolled releases.",
        "keywords": ["line of fire", "trajectory", "pressurized release", "projectile", "vapor cloud", "pinch point", "dropped object", "struck by", "adjacent to leaking"]
    },
    "Work Authorisation": {
        "rule": "Work with a valid permit when required",
        "description": "Ensure work permits are verified at site, risk assessments (HIRA/JHA) are completed, and supervisor handover is maintained.",
        "keywords": ["permit to work", "work permit", "hira", "jha", "risk assessment", "supervision", "shift handover", "clearance", "unauthorized work"]
    },
    "Confined Space": {
        "rule": "Obtain authorisation before entering a confined space",
        "description": "Verify atmospheric testing, continuous ventilation, emergency rescue plan, and qualified attendant before entry.",
        "keywords": ["confined space", "vessel entry", "manhole", "nitrogen purge", "oxygen deficit", "atmospheric testing", "entry attendant"]
    },
    "Working at Height": {
        "rule": "Protect yourself against a fall when working at height",
        "description": "Use 100% tie-off fall protection, inspect scaffolding and harnesses, and secure tools against drops.",
        "keywords": ["working at height", "fall protection", "scaffolding", "safety harness", "lanyard", "tie-off", "unprotected edge"]
    },
    "Safe Mechanical Lifting": {
        "rule": "Plan lifting operations and control the area",
        "description": "Do not exceed crane capacity, inspect rigging gear, and establish exclusion barricades under suspended loads.",
        "keywords": ["crane", "rigging", "hoist", "suspended load", "sling", "lifting plan", "exclusion zone"]
    }
}

def match_iogp_rules(text: str) -> list:
    """
    Identifies candidate IOGP Life-Saving Rules implicated by the report narrative or finding text.
    Returns a list of matched rule names and rule directives.
    """
    lower = text.lower()
    matched = []
    for rule_name, rule_data in IOGP_LIFE_SAVING_RULES.items():
        if any(kw in lower for kw in rule_data["keywords"]):
            matched.append({
                "rule_name": rule_name,
                "directive": rule_data["rule"],
                "description": rule_data["description"]
            })
    return matched
