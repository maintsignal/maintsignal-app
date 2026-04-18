"""
MaintSignal — Industry Knowledge Base
Contains abbreviation dictionaries, failure taxonomies, and industry-specific
terminology for all major manufacturing sectors.

This is the "brain" that makes the LLM normalization smart.
"""

# ============================================================
# GLOBAL MAINTENANCE ABBREVIATIONS
# Every industry uses these. Built from real CMMS data patterns.
# ============================================================

GLOBAL_ABBREVIATIONS = {
    # Equipment types
    "XMTR": "Transmitter",
    "XMITTER": "Transmitter",
    "BRG": "Bearing",
    "BRNG": "Bearing",
    "VLV": "Valve",
    "MTR": "Motor",
    "MOT": "Motor",
    "PMP": "Pump",
    "PP": "Pump",
    "COMP": "Compressor",
    "COMPR": "Compressor",
    "HX": "Heat Exchanger",
    "H/E": "Heat Exchanger",
    "HTEX": "Heat Exchanger",
    "XCHGR": "Heat Exchanger",
    "CONV": "Conveyor",
    "CNVYR": "Conveyor",
    "AGIT": "Agitator",
    "BLR": "Boiler",
    "BOILR": "Boiler",
    "GBX": "Gearbox",
    "G/B": "Gearbox",
    "CYL": "Cylinder",
    "TURB": "Turbine",
    "GEN": "Generator",
    "GENR": "Generator",
    "TRANS": "Transformer",
    "XFMR": "Transformer",
    "FAN": "Fan",
    "BLWR": "Blower",
    "CHLR": "Chiller",
    "AHU": "Air Handling Unit",
    "RTU": "Rooftop Unit",
    "VFD": "Variable Frequency Drive",
    "MCC": "Motor Control Center",
    "SWGR": "Switchgear",
    "PNL": "Panel",
    "CKT": "Circuit",
    "BKR": "Breaker",
    "CKT BKR": "Circuit Breaker",
    "CB": "Circuit Breaker",
    "DSCHGR": "Discharger",
    "SCRN": "Screen",
    "FLTR": "Filter",
    "STRN": "Strainer",
    "SEP": "Separator",
    "RX": "Reactor",
    "RXTR": "Reactor",
    "COL": "Column",
    "TWR": "Tower",
    "TNK": "Tank",
    "VSL": "Vessel",
    "RCVR": "Receiver",
    "ACCUM": "Accumulator",
    "DMPN": "Dampener",

    # Components
    "MECH SEAL": "Mechanical Seal",
    "M/S": "Mechanical Seal",
    "MSEAL": "Mechanical Seal",
    "IMP": "Impeller",
    "IMPLR": "Impeller",
    "CPLG": "Coupling",
    "CPLN": "Coupling",
    "SHFT": "Shaft",
    "PKG": "Packing",
    "GSKT": "Gasket",
    "GASK": "Gasket",
    "FLNG": "Flange",
    "ACT": "Actuator",
    "ACTR": "Actuator",
    "POSN": "Positioner",
    "POSNR": "Positioner",
    "SOL": "Solenoid",
    "SOLN": "Solenoid",
    "THRM": "Thermocouple",
    "T/C": "Thermocouple",
    "TC": "Thermocouple",
    "RTD": "RTD (Resistance Temperature Detector)",
    "PT": "Pressure Transmitter",
    "LT": "Level Transmitter",
    "FT": "Flow Transmitter",
    "TT": "Temperature Transmitter",
    "PDT": "Pressure Differential Transmitter",
    "PCV": "Pressure Control Valve",
    "FCV": "Flow Control Valve",
    "TCV": "Temperature Control Valve",
    "LCV": "Level Control Valve",
    "PRV": "Pressure Relief Valve",
    "PSV": "Pressure Safety Valve",
    "BPV": "Back Pressure Valve",
    "NRV": "Non-Return Valve",
    "CHK VLV": "Check Valve",
    "ISOL": "Isolation Valve",
    "BFLY": "Butterfly Valve",
    "DE": "Drive End",
    "NDE": "Non-Drive End",
    "FW": "Flywheel",
    "CRTG": "Cartridge",

    # Actions
    "REPL": "Replaced",
    "RPL": "Replaced",
    "R&R": "Remove and Replace",
    "R/R": "Remove and Replace",
    "REPR": "Repaired",
    "RPR": "Repaired",
    "ADJ": "Adjusted",
    "ADJST": "Adjusted",
    "ALGN": "Aligned",
    "ALIGN": "Aligned",
    "CALIB": "Calibrated",
    "CAL": "Calibrated",
    "INSP": "Inspected",
    "INSPT": "Inspected",
    "INSTL": "Installed",
    "INST": "Installed",
    "RMVD": "Removed",
    "RMV": "Removed",
    "RBLDT": "Rebuilt",
    "REBLT": "Rebuilt",
    "OVRHLD": "Overhauled",
    "O/H": "Overhauled",
    "TRBLSHT": "Troubleshooted",
    "T/S": "Troubleshooted",
    "TBLSHT": "Troubleshooted",
    "MAINT": "Maintenance",
    "PM": "Preventive Maintenance",
    "CM": "Corrective Maintenance",
    "CBM": "Condition-Based Maintenance",
    "PdM": "Predictive Maintenance",
    "LUBE": "Lubricated",
    "GREAS": "Greased",
    "TORQ": "Torqued",
    "CLND": "Cleaned",
    "CLN": "Cleaned",
    "FLSHD": "Flushed",

    # Conditions / Failures
    "LKG": "Leaking",
    "LK": "Leak",
    "CORRN": "Corrosion",
    "CORR": "Corroded",
    "VIBN": "Vibration",
    "VIB": "Vibration",
    "OVHT": "Overheating",
    "O/H": "Overheating",
    "OVRLD": "Overloaded",
    "O/L": "Overloaded",
    "TRPD": "Tripped",
    "NOISY": "Noise / Noisy",
    "WRN": "Worn",
    "WRNG": "Warning",
    "FTGD": "Fatigued",
    "CRCKD": "Cracked",
    "SEIZ": "Seized",
    "SEZD": "Seized",
    "STCK": "Stuck",
    "BLCKD": "Blocked",
    "CLGD": "Clogged",
    "CONTAM": "Contaminated",
    "MISALGN": "Misaligned",
    "CAVIT": "Cavitation",
    "EROSN": "Erosion",
    "PTTNG": "Pitting",

    # General
    "W/O": "Work Order",
    "WO": "Work Order",
    "N/A": "Not Applicable",
    "TBD": "To Be Determined",
    "OOS": "Out of Service",
    "OOT": "Out of Tolerance",
    "NFF": "No Fault Found",
    "NFR": "No Further Repair",
    "EMER": "Emergency",
    "EMRG": "Emergency",
    "SCHED": "Scheduled",
    "UNSCHED": "Unscheduled",
    "BKD": "Breakdown",
    "BD": "Breakdown",
}


# ============================================================
# INDUSTRY-SPECIFIC FAILURE TAXONOMIES
# Based on ISO 14224, SMRP standards, and real plant data patterns
# ============================================================

INDUSTRY_TAXONOMIES = {
    "pharmaceutical": {
        "name": "Pharmaceutical / Life Sciences",
        "description": "FDA-regulated environments with strict GMP requirements",
        "common_equipment": [
            "Reactors", "Centrifuges", "Lyophilizers (Freeze Dryers)", "Autoclaves",
            "Tablet Presses", "Coating Machines", "Granulators", "Blenders/Mixers",
            "HVAC/Cleanroom Systems", "WFI (Water for Injection) Systems",
            "CIP (Clean-in-Place) Systems", "Filling Machines", "Packaging Lines",
            "Compressed Air Systems (Oil-Free)", "Steam Generators",
        ],
        "failure_categories": {
            "Mechanical Seal Failure": "Seal leak, wear, or failure on pumps and agitators",
            "Bearing Failure": "Rolling element or journal bearing degradation",
            "Motor / Drive Failure": "Electric motor overheating, VFD fault, winding failure",
            "Valve Malfunction": "Control valve, diaphragm valve, or sterile valve issue",
            "Instrumentation Drift": "Sensor out of calibration, transmitter fault",
            "Gasket / O-Ring Failure": "Seal failure on vessels, reactors, or piping",
            "Corrosion / Material Degradation": "Product or chemical attack on equipment surfaces",
            "CIP System Failure": "Clean-in-place system malfunction affecting sterility",
            "HVAC / Cleanroom Failure": "Air handling, differential pressure, or temperature control failure",
            "Filter / Strainer Blockage": "Filtration system clogged or damaged",
            "Pump Failure": "Pump body, impeller, or drive train failure",
            "Electrical Fault": "Wiring, breaker, power supply, or grounding issue",
            "Contamination Event": "Cross-contamination, particulate, or microbial event",
            "Software / PLC Fault": "Control system, recipe, or automation error",
            "Preventive Maintenance": "Scheduled PM task or inspection",
            "Calibration": "Instrument calibration or verification",
        },
        "specific_abbreviations": {
            "GMP": "Good Manufacturing Practice",
            "CIP": "Clean-in-Place",
            "SIP": "Sterilize-in-Place",
            "WFI": "Water for Injection",
            "PW": "Purified Water",
            "HEPA": "High-Efficiency Particulate Air",
            "LAF": "Laminar Air Flow",
            "DP": "Differential Pressure",
            "BPV": "Bio-Process Vessel",
            "IQ/OQ/PQ": "Installation/Operational/Performance Qualification",
            "FAT": "Factory Acceptance Test",
            "SAT": "Site Acceptance Test",
        },
    },

    "food_and_beverage": {
        "name": "Food & Beverage",
        "description": "FSMA-regulated food safety environments",
        "common_equipment": [
            "Mixers / Blenders", "Ovens / Fryers", "Pasteurizers", "Homogenizers",
            "Fillers / Cappers", "Packaging Machines", "Conveyors", "Refrigeration Units",
            "Boilers / Steam Systems", "CIP Systems", "Pumps (Sanitary)",
            "Metal Detectors / X-Ray", "Palletizers", "Labelers",
        ],
        "failure_categories": {
            "Mechanical Seal Failure": "Sanitary pump seal leak or degradation",
            "Bearing Failure": "Bearing wear on conveyors, motors, or mixers",
            "Motor / Drive Failure": "Motor overheating, VFD fault, gearbox failure",
            "Belt / Chain Failure": "Conveyor belt, drive chain, or timing belt issue",
            "Valve Malfunction": "Sanitary valve, mix-proof valve, or control valve fault",
            "Refrigeration Failure": "Compressor, condenser, evaporator, or refrigerant issue",
            "CIP Failure": "Clean-in-place system, chemical dosing, or spray ball failure",
            "Sensor / Instrument Fault": "Temperature, flow, level, or weight sensor issue",
            "Packaging Machine Fault": "Filler, capper, labeler, or wrapper malfunction",
            "Electrical Fault": "Wiring, breaker, contactor, or safety circuit issue",
            "Corrosion / Sanitation Issue": "Surface degradation affecting food safety",
            "Foreign Material Risk": "Metal detector, x-ray, or sieve/screen failure",
            "Pneumatic System Failure": "Air cylinder, solenoid, or airline issue",
            "Boiler / Steam Failure": "Steam generation, trap, or distribution issue",
            "Preventive Maintenance": "Scheduled PM, lubrication, or sanitation task",
        },
        "specific_abbreviations": {
            "CIP": "Clean-in-Place",
            "COP": "Clean-out-of-Place",
            "FSMA": "Food Safety Modernization Act",
            "HACCP": "Hazard Analysis Critical Control Points",
            "SQF": "Safe Quality Food",
            "BRC": "British Retail Consortium",
            "UHT": "Ultra-High Temperature",
            "HTST": "High Temperature Short Time",
            "BBD": "Best Before Date",
            "FMR": "Foreign Material Risk",
        },
    },

    "oil_and_gas": {
        "name": "Oil & Gas / Petrochemical",
        "description": "High-hazard environments with API and ISO 14224 standards",
        "common_equipment": [
            "Centrifugal Pumps", "Reciprocating Compressors", "Gas Turbines",
            "Heat Exchangers", "Pressure Vessels", "Distillation Columns",
            "Fired Heaters / Furnaces", "Cooling Towers", "Fin-Fan Coolers",
            "Control Valves", "Safety Valves (PSV)", "Rotating Equipment",
            "Electrical Substations", "Instrument Air Systems", "Flare Systems",
        ],
        "failure_categories": {
            "Mechanical Seal Failure": "Pump or compressor seal leak/failure",
            "Bearing Failure": "Journal bearing, thrust bearing, or rolling element failure",
            "Impeller / Rotor Damage": "Erosion, corrosion, or mechanical damage to rotating parts",
            "Valve Failure — Control": "Control valve, positioner, or actuator malfunction",
            "Valve Failure — Safety": "PSV/PRV lifting, leaking, or failing to operate",
            "Valve Failure — Isolation": "Gate, globe, ball, or butterfly valve stuck/leaking",
            "Compressor Failure": "Compressor valve, piston, cylinder, or driver failure",
            "Turbine Failure": "Gas turbine, steam turbine, or expander issue",
            "Heat Exchanger Failure": "Tube leak, fouling, or baffle damage",
            "Corrosion / Erosion": "Internal or external material loss from corrosion or erosion",
            "Piping Failure": "Pipe leak, crack, or support failure",
            "Electrical Failure": "Motor, switchgear, transformer, or cable failure",
            "Instrumentation Fault": "Transmitter, analyzer, or control system fault",
            "Fired Equipment Failure": "Furnace, heater, or boiler tube/burner failure",
            "Structural Failure": "Foundation, platform, or support structure issue",
            "Preventive Maintenance": "Scheduled inspection, overhaul, or turnaround task",
        },
        "specific_abbreviations": {
            "PSV": "Pressure Safety Valve",
            "PRV": "Pressure Relief Valve",
            "MOV": "Motor Operated Valve",
            "ESD": "Emergency Shutdown",
            "SIS": "Safety Instrumented System",
            "SIL": "Safety Integrity Level",
            "RBI": "Risk-Based Inspection",
            "API": "American Petroleum Institute",
            "ASME": "American Society of Mechanical Engineers",
            "NDT": "Non-Destructive Testing",
            "UT": "Ultrasonic Testing",
            "MT": "Magnetic Testing",
            "HAZ": "Hazardous Area",
            "LEL": "Lower Explosive Limit",
            "H2S": "Hydrogen Sulfide",
            "FCCU": "Fluid Catalytic Cracking Unit",
            "CDU": "Crude Distillation Unit",
            "VDU": "Vacuum Distillation Unit",
            "TA": "Turnaround",
        },
    },

    "automotive_manufacturing": {
        "name": "Automotive Manufacturing",
        "description": "High-volume production with JIT and lean manufacturing",
        "common_equipment": [
            "Stamping Presses", "Welding Robots", "Paint Booth Systems",
            "Conveyor Systems", "Assembly Robots", "CNC Machines",
            "Hydraulic Presses", "Air Compressors", "Cooling Systems",
            "Electrical Systems", "PLC/SCADA Systems", "Material Handling",
            "Testing Equipment", "Vision Systems", "Torque Tools",
        ],
        "failure_categories": {
            "Robot / Servo Failure": "Robot arm, servo motor, encoder, or controller fault",
            "Hydraulic System Failure": "Pump, cylinder, valve, or hose failure in hydraulic system",
            "Pneumatic System Failure": "Air cylinder, solenoid, airline, or FRL unit failure",
            "Bearing Failure": "Bearing wear on presses, conveyors, or rotating equipment",
            "Motor / Drive Failure": "Electric motor, VFD, servo drive, or gearbox failure",
            "Welding Equipment Failure": "Weld gun, tip, transformer, or controller fault",
            "Conveyor Failure": "Belt, chain, roller, or drive unit failure",
            "Press / Stamping Failure": "Die, ram, clutch, brake, or slide issue",
            "Electrical / Controls Fault": "PLC, wiring, sensor, safety relay, or HMI issue",
            "Tooling Wear / Breakage": "Cutting tool, die, fixture, or jig failure",
            "Paint System Failure": "Spray gun, booth, oven, or circulation system failure",
            "Cooling System Failure": "Chiller, coolant pump, or heat exchanger failure",
            "Safety System Fault": "Light curtain, E-stop, interlock, or guard failure",
            "Vision / Inspection Fault": "Camera, sensor, or quality inspection system failure",
            "Preventive Maintenance": "Scheduled PM, lubrication, or inspection task",
        },
        "specific_abbreviations": {
            "OEE": "Overall Equipment Effectiveness",
            "MTBF": "Mean Time Between Failures",
            "MTTR": "Mean Time To Repair",
            "JIT": "Just-In-Time",
            "TPM": "Total Productive Maintenance",
            "SMED": "Single Minute Exchange of Die",
            "CNC": "Computer Numerical Control",
            "PLC": "Programmable Logic Controller",
            "HMI": "Human Machine Interface",
            "SCADA": "Supervisory Control and Data Acquisition",
            "BIW": "Body-in-White",
            "GA": "General Assembly",
            "PBS": "Paint Body Shop",
            "EOL": "End of Line",
            "SPC": "Statistical Process Control",
            "PPM": "Parts Per Million (defect rate)",
        },
    },

    "general_manufacturing": {
        "name": "General / Discrete Manufacturing",
        "description": "Broad manufacturing covering metals, plastics, chemicals, paper, etc.",
        "common_equipment": [
            "Pumps", "Motors", "Compressors", "Conveyors",
            "Heat Exchangers", "Boilers", "Cooling Towers", "Chillers",
            "Mixers / Agitators", "Crushers / Grinders", "Screens / Separators",
            "Fans / Blowers", "Valves", "Instruments / Sensors",
            "Electrical Distribution", "Material Handling",
        ],
        "failure_categories": {
            "Seal Failure": "Mechanical seal, packing, or gasket leak/failure",
            "Bearing Failure": "Rolling element or journal bearing degradation",
            "Motor / Drive Failure": "Electric motor, VFD, or gearbox issue",
            "Valve Failure": "Control, isolation, or safety valve malfunction",
            "Pump Failure": "Pump body, impeller, or drive train failure",
            "Compressor Failure": "Compressor valve, motor, or driver issue",
            "Conveyor / Belt Failure": "Belt, chain, roller, or drive unit failure",
            "Electrical Fault": "Wiring, breaker, contactor, or power supply issue",
            "Instrumentation Fault": "Sensor, transmitter, or controller malfunction",
            "Corrosion / Erosion": "Material degradation from corrosion or wear",
            "Hydraulic Failure": "Pump, cylinder, valve, or hose in hydraulic circuit",
            "Pneumatic Failure": "Air cylinder, solenoid, or airline issue",
            "Lubrication Issue": "Insufficient lube, contamination, or system failure",
            "Structural / Fatigue": "Crack, fracture, or structural degradation",
            "Software / Controls Fault": "PLC, SCADA, or automation system error",
            "Preventive Maintenance": "Scheduled inspection, service, or overhaul",
            "Calibration": "Instrument calibration or verification",
        },
        "specific_abbreviations": {},
    },
}


# ============================================================
# COLUMN MAPPING INTELLIGENCE
# Common field names across different CMMS/ERP systems
# ============================================================

COLUMN_ALIASES = {
    "order_id": [
        "Order_Number", "AUFNR", "Work Order", "WO Number", "WO#", "WO_NUM",
        "WONUM", "Work Order Number", "WorkOrderID", "work_order_id",
        "ticket_id", "Ticket Number", "SR Number", "Service Request",
        "order_no", "ORDER", "wo_number", "workorder", "job_number",
        "JOB_NO", "job_id", "maintenance_order",
    ],
    "asset_id": [
        "Equipment_ID", "EQUNR", "Asset ID", "Asset Number", "Asset_No",
        "ASSETNUM", "Equipment Number", "Equip_ID", "equip_no",
        "machine_id", "Machine", "Unit", "Tag Number", "TAG_NO",
        "asset_tag", "equipment_tag", "functional_location",
        "TPLNR", "location_id", "asset_code",
    ],
    "asset_name": [
        "Equipment_Name", "EQKTX", "Asset Description", "Asset Name",
        "DESCRIPTION", "Equip_Desc", "equipment_description",
        "machine_name", "asset_description", "unit_name",
    ],
    "order_type": [
        "Order_Type", "AUART", "Work Type", "WO Type", "Type",
        "WORKTYPE", "work_type", "maintenance_type", "order_category",
        "wo_type", "activity_type", "task_type",
    ],
    "priority": [
        "Priority", "PRIESSION", "WOPRIORITY", "priority_code",
        "urgency", "criticality", "severity", "PRIOR",
    ],
    "created_date": [
        "Created_Date", "ERDAT", "Created", "Date Created", "Open Date",
        "REPORTDATE", "created_at", "date_created", "entry_date",
        "report_date", "logged_date", "CDATE",
    ],
    "completed_date": [
        "Completed_Date", "GETRI", "Completed", "Date Completed",
        "Close Date", "ACTFINISH", "closed_date", "finished_date",
        "completion_date", "resolved_date", "FDATE",
    ],
    "downtime_start": [
        "Malfunction_Start", "AUSVN", "Down Start", "Downtime Start",
        "DOWNSTART", "failure_start", "breakdown_start",
        "outage_start", "event_start",
    ],
    "downtime_end": [
        "Malfunction_End", "AUSBS", "Down End", "Downtime End",
        "DOWNEND", "failure_end", "breakdown_end",
        "outage_end", "event_end",
    ],
    "description": [
        "Short_Text", "KTEXT", "Description", "WO Description",
        "DESCRIPTION_LONGDESCRIPTION", "description", "Short Description",
        "work_description", "problem_description", "summary",
        "notes", "LDTEXT", "long_text", "comment", "details",
        "failure_description", "symptom",
    ],
    "failure_code": [
        "Damage_Code", "FECOD", "Failure Code", "Problem Code",
        "FAILURECODE", "failure_class", "fault_code", "defect_code",
        "OTGRP", "object_part", "damage_code", "symptom_code",
    ],
    "cause_code": [
        "Cause_Code", "URSCO", "Cause", "Root Cause",
        "CAUSECODE", "cause_class", "root_cause_code",
        "reason_code", "URCOD",
    ],
    "labor_hours": [
        "Actual_Hours", "ARBEI", "Labor Hours", "Work Hours",
        "ACTLABHRS", "actual_labor", "hours_worked",
        "man_hours", "duration_hours", "wrench_time",
    ],
    "cost": [
        "Actual_Cost", "IDAT1", "Total Cost", "WO Cost",
        "ACTCOST", "actual_cost", "total_cost", "repair_cost",
        "maintenance_cost",
    ],
    "status": [
        "Status", "STAT", "WO Status", "WOSTATUS",
        "status_code", "order_status", "state",
    ],
}


def get_all_abbreviations(industry=None):
    """Get combined abbreviation dictionary for a given industry."""
    abbrevs = dict(GLOBAL_ABBREVIATIONS)

    if industry and industry in INDUSTRY_TAXONOMIES:
        industry_abbrevs = INDUSTRY_TAXONOMIES[industry].get("specific_abbreviations", {})
        abbrevs.update(industry_abbrevs)

    return abbrevs


def get_failure_taxonomy(industry=None):
    """Get failure category taxonomy for a given industry."""
    if industry and industry in INDUSTRY_TAXONOMIES:
        return INDUSTRY_TAXONOMIES[industry]["failure_categories"]
    return INDUSTRY_TAXONOMIES["general_manufacturing"]["failure_categories"]


def guess_column_mapping(column_names):
    """
    Given a list of column names from a client file,
    guess what each column maps to in the universal schema.

    Returns: dict of {original_column_name: standard_field_name}
    """
    mapping = {}

    for col in column_names:
        col_clean = col.strip()
        col_lower = col_clean.lower().replace(" ", "_").replace("-", "_")
        best_match = None
        best_score = 0

        for standard_field, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                alias_lower = alias.lower().replace(" ", "_").replace("-", "_")

                # Exact match
                if col_lower == alias_lower or col_clean == alias:
                    best_match = standard_field
                    best_score = 100
                    break

                # Contains match
                if alias_lower in col_lower or col_lower in alias_lower:
                    score = len(alias_lower) / max(len(col_lower), 1) * 80
                    if score > best_score:
                        best_match = standard_field
                        best_score = score

            if best_score == 100:
                break

        if best_match and best_score > 30:
            mapping[col_clean] = {
                "maps_to": best_match,
                "confidence": min(best_score, 100)
            }

    return mapping


# ============================================================
# LLM PROMPT TEMPLATES
# ============================================================

def build_normalization_prompt(descriptions, industry=None, client_abbreviations=None):
    """
    Build the optimal prompt for LLM-based failure normalization.
    This is the core intelligence — the prompt IS the product.
    """
    taxonomy = get_failure_taxonomy(industry)
    abbrevs = get_all_abbreviations(industry)

    # Add client-specific abbreviations if provided
    if client_abbreviations:
        abbrevs.update(client_abbreviations)

    # Build taxonomy string
    taxonomy_str = "\n".join(
        f"  - {cat}: {desc}" for cat, desc in taxonomy.items()
    )

    # Build top abbreviations (don't dump all 200+ — LLM can figure out obvious ones)
    # Focus on the tricky ones that are ambiguous
    key_abbrevs = "\n".join(
        f"  {k} = {v}" for k, v in list(abbrevs.items())[:60]
    )

    # Number the descriptions
    numbered = "\n".join(
        f"  {i+1}. \"{d}\"" for i, d in enumerate(descriptions)
    )

    industry_name = "general manufacturing"
    if industry and industry in INDUSTRY_TAXONOMIES:
        industry_name = INDUSTRY_TAXONOMIES[industry]["name"]

    prompt = f"""You are a senior maintenance & reliability engineer with 20+ years of experience in {industry_name}. You specialize in analyzing CMMS work order data.

CONTEXT:
These are real technician-written work order descriptions from a {industry_name} plant. Technicians write under time pressure, use heavy abbreviations, shorthand, and plant-specific jargon. The same failure can be described dozens of different ways.

YOUR TASK:
Classify each description into exactly ONE failure category. Extract the affected component. Expand all abbreviations in your interpretation.

FAILURE CATEGORIES (use these exact names):
{taxonomy_str}

COMMON ABBREVIATIONS (non-exhaustive — use your expertise for unlisted ones):
{key_abbrevs}

WORK ORDER DESCRIPTIONS TO CLASSIFY:
{numbered}

RULES:
1. Classify based on the ROOT FAILURE, not the repair action. "Replaced bearing" = Bearing Failure, not "Replacement."
2. If a description mentions multiple issues, classify by the PRIMARY failure.
3. "PM", "inspection", "routine", "scheduled" = Preventive Maintenance unless a specific failure is described.
4. Empty, nonsensical, or single-word descriptions with no failure context = "Preventive Maintenance" if it seems routine, otherwise flag as "Unknown."
5. Expand ALL abbreviations in the "interpretation" field.
6. If unsure between two categories, pick the more specific one.

RESPOND WITH ONLY a JSON array. No other text, no markdown, no explanation:
[
  {{
    "index": 1,
    "original": "the original text",
    "interpretation": "expanded plain-English interpretation of what the technician meant",
    "category": "exact category name from the list above",
    "component": "the specific component affected (e.g., mechanical seal, drive end bearing, control valve positioner)",
    "confidence": "high" | "medium" | "low"
  }}
]

JSON:"""

    return prompt


def build_column_mapping_prompt(column_names, sample_rows):
    """
    Build a prompt for LLM-based column mapping when auto-detection fails.
    """
    cols = ", ".join(f'"{c}"' for c in column_names)
    sample = "\n".join(
        "  " + " | ".join(str(v) for v in row)
        for row in sample_rows[:5]
    )

    prompt = f"""You are a data engineer specializing in industrial maintenance management systems (CMMS/EAM/ERP).

A client has uploaded a maintenance data file. Here are the column names and sample data:

COLUMNS: {cols}

SAMPLE ROWS:
{sample}

MAP each column to one of these standard fields (or "unknown" if it doesn't match):
- order_id: Work order or ticket identifier
- asset_id: Equipment or asset identifier/tag number
- asset_name: Human-readable equipment name or description
- order_type: Type of maintenance (breakdown, preventive, corrective, etc.)
- priority: Urgency or priority level
- created_date: When the work order was created/opened
- completed_date: When the work order was closed/completed
- downtime_start: When the equipment failure/downtime began
- downtime_end: When the equipment was returned to service
- description: Free-text description of the work performed or problem observed
- failure_code: Failure classification code
- cause_code: Root cause classification code
- labor_hours: Hours of labor recorded
- cost: Cost of the maintenance activity
- status: Current status of the work order
- location: Physical location or functional location in the plant
- unknown: Column doesn't map to any standard field

RESPOND with ONLY a JSON object mapping each original column name to the standard field:
{{"original_column": "standard_field", ...}}

JSON:"""

    return prompt
