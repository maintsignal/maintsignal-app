"""
MaintSignal — Synthetic SAP PM Data Generator
Generates realistic work order data with intentional quality issues.
Run this to create demo CSV files for testing and client presentations.

Usage:
    python generate_data.py                    # Default 2000 records
    python generate_data.py --records 5000     # Custom record count
    python generate_data.py --clean            # Generate clean data (for comparison)
"""

import pandas as pd
import numpy as np
import random
import argparse
from datetime import datetime, timedelta


# ============================================================
# EQUIPMENT MASTER DATA
# ============================================================

EQUIPMENT = {
    "P-101": {"name": "Feed Pump A", "location": "PLANT1-PROD-LINE1", "type": "Centrifugal Pump", "criticality": "A"},
    "P-102": {"name": "Feed Pump B", "location": "PLANT1-PROD-LINE1", "type": "Centrifugal Pump", "criticality": "A"},
    "P-103": {"name": "Transfer Pump", "location": "PLANT1-PROD-LINE2", "type": "Centrifugal Pump", "criticality": "B"},
    "P-104": {"name": "Coolant Pump", "location": "PLANT1-UTIL-COOL", "type": "Centrifugal Pump", "criticality": "B"},
    "P-105": {"name": "Discharge Pump", "location": "PLANT1-PROD-LINE2", "type": "Positive Displacement", "criticality": "B"},
    "P-106": {"name": "Boiler Feed Pump", "location": "PLANT1-UTIL-STEAM", "type": "Centrifugal Pump", "criticality": "A"},
    "C-301": {"name": "Main Conveyor", "location": "PLANT1-PROD-CONV", "type": "Belt Conveyor", "criticality": "A"},
    "C-302": {"name": "Sorting Conveyor", "location": "PLANT1-PROD-CONV", "type": "Belt Conveyor", "criticality": "B"},
    "C-303": {"name": "Discharge Conveyor", "location": "PLANT1-PROD-CONV", "type": "Belt Conveyor", "criticality": "C"},
    "C-304": {"name": "Infeed Conveyor", "location": "PLANT1-PROD-CONV", "type": "Roller Conveyor", "criticality": "B"},
    "K-201": {"name": "Air Compressor A", "location": "PLANT1-UTIL-COMP", "type": "Screw Compressor", "criticality": "A"},
    "K-202": {"name": "Air Compressor B", "location": "PLANT1-UTIL-COMP", "type": "Screw Compressor", "criticality": "A"},
    "M-105": {"name": "Drive Motor Line 1", "location": "PLANT1-PROD-LINE1", "type": "AC Induction Motor", "criticality": "A"},
    "M-106": {"name": "Drive Motor Line 2", "location": "PLANT1-PROD-LINE2", "type": "AC Induction Motor", "criticality": "A"},
    "M-107": {"name": "Blower Motor", "location": "PLANT1-UTIL-HVAC", "type": "AC Induction Motor", "criticality": "B"},
    "M-108": {"name": "Mixer Motor", "location": "PLANT1-PROD-MIX", "type": "AC Induction Motor", "criticality": "B"},
    "M-109": {"name": "Exhaust Fan Motor", "location": "PLANT1-UTIL-HVAC", "type": "AC Induction Motor", "criticality": "C"},
    "HX-401": {"name": "Heat Exchanger 1", "location": "PLANT1-UTIL-HX", "type": "Shell & Tube", "criticality": "B"},
    "HX-402": {"name": "Heat Exchanger 2", "location": "PLANT1-UTIL-HX", "type": "Plate Heat Exchanger", "criticality": "B"},
    "V-501": {"name": "Control Valve CV-1", "location": "PLANT1-PROD-LINE1", "type": "Globe Valve", "criticality": "A"},
    "V-502": {"name": "Control Valve CV-2", "location": "PLANT1-PROD-LINE2", "type": "Globe Valve", "criticality": "B"},
    "V-503": {"name": "Safety Relief Valve", "location": "PLANT1-UTIL-STEAM", "type": "Relief Valve", "criticality": "A"},
    "AG-601": {"name": "Agitator A", "location": "PLANT1-PROD-MIX", "type": "Top Entry Agitator", "criticality": "B"},
    "AG-602": {"name": "Agitator B", "location": "PLANT1-PROD-MIX", "type": "Top Entry Agitator", "criticality": "B"},
    "T-701": {"name": "Storage Tank 1", "location": "PLANT1-STOR-TANKS", "type": "Atmospheric Tank", "criticality": "C"},
    "T-702": {"name": "Storage Tank 2", "location": "PLANT1-STOR-TANKS", "type": "Atmospheric Tank", "criticality": "C"},
    "CR-801": {"name": "Crusher Unit", "location": "PLANT1-PROD-LINE1", "type": "Jaw Crusher", "criticality": "A"},
    "SC-901": {"name": "Screen Separator", "location": "PLANT1-PROD-LINE1", "type": "Vibrating Screen", "criticality": "B"},
}


# ============================================================
# FAILURE DESCRIPTION TEMPLATES
# ============================================================
# These simulate how real technicians write — inconsistent, abbreviated, varied

DESCRIPTIONS = {
    "seal_failure": [
        "pump leaking from seal area",
        "replaced mech seal on pump",
        "seal failure replaced seal",
        "pump leaking bad need new seal",
        "mechanical seal replaced",
        "pump leak at seal - replaced",
        "seal blew out replaced with new one",
        "found pump leaking fixed seal",
        "replaced worn seal on feed pump",
        "seal leak on pump repaired",
        "mech seal gone again same issue",
        "pump seal shot - replaced",
        "another seal failure on this pump smh",
        "replaced seal per last WO recommendation",
        "seal leaking product into containment",
        "seal dripping replaced with viton seal",
        "pump seal fail third time this quarter",
        "seal worn thru - replaced both seals",
    ],
    "bearing_failure": [
        "bearing noise on conveyor",
        "replaced bearing on main conveyor",
        "conveyor bearing worn out",
        "loud grinding noise replaced bearing",
        "bearing failure on drive end",
        "hot bearing on conveyor drive end",
        "bearing seized up",
        "replaced DE bearing and NDE bearing",
        "bearing making noise - changed it out",
        "drive end bearing bad",
        "bearing temp alarm replaced bearing",
        "found metal shavings in bearing housing",
        "bearing race pitted need replacement",
        "swapped out bad bearing",
        "bearing howling replaced both",
    ],
    "motor_failure": [
        "motor overheating",
        "motor tripped on overload",
        "motor running hot had to shut down",
        "replaced motor - burnt out",
        "motor vibration high",
        "electric motor failed",
        "motor drawing high amps",
        "motor overheated again check cooling",
        "rewound motor installed back",
        "motor trip - reset and monitored",
        "motor winding resistance low need rewind",
        "VFD fault on motor check drive",
        "motor coupling misaligned corrected",
        "motor fan broken running hot",
        "replaced motor starter overload tripped",
    ],
    "valve_failure": [
        "valve stuck open",
        "control valve not responding",
        "valve leaking thru",
        "replaced valve actuator",
        "valve stem packing leak",
        "valve won't close all the way",
        "control valve erratic behavior",
        "replaced valve internals trim kit",
        "valve positioner fault replaced",
        "valve cavitation noise - replaced trim",
        "PRV lifting early needs adjustment",
        "valve seat worn leaking past",
    ],
    "electrical": [
        "breaker tripped reset and tested",
        "loose wire in junction box tightened",
        "sensor reading erratic replaced sensor",
        "PLC fault cleared and reset",
        "power supply failed replaced",
        "contactor burned replaced",
        "cable insulation damaged repaired",
        "ground fault found and fixed",
        "level switch stuck replaced",
        "temperature transmitter reading off recalibrated",
    ],
    "corrosion": [
        "pipe corroded through patched temp",
        "corrosion found on vessel wall",
        "rust on tank bottom needs coating",
        "corroded bolts replaced with SS",
        "corrosion under insulation found and repaired",
        "tank floor corrosion patch welded",
    ],
    "preventive_maintenance": [
        "performed PM inspection per schedule",
        "routine maintenance completed all checks ok",
        "checked alignment and lubrication all ok",
        "annual inspection done no issues",
        "replaced filters and lubed bearings",
        "PM service completed per plan",
        "cleaned and inspected equipment",
        "general maintenance and cleanup",
        "lubrication and inspection per schedule",
        "preventive maintenance per task list",
        "6 month PM completed and signed off",
        "quarterly vibration readings taken all normal",
        "oil sample taken and sent to lab",
        "belt tension checked and adjusted",
        "alignment check performed within spec",
        "calibration completed all instruments ok",
        "greased all fittings per lube route",
    ],
}

# Weight certain equipment toward certain failure types
EQUIP_FAILURE_BIAS = {
    "P-": ["seal_failure", "seal_failure", "seal_failure", "bearing_failure", "motor_failure"],
    "C-": ["bearing_failure", "bearing_failure", "bearing_failure", "motor_failure", "electrical"],
    "K-": ["motor_failure", "bearing_failure", "valve_failure", "electrical"],
    "M-": ["motor_failure", "motor_failure", "motor_failure", "bearing_failure", "electrical"],
    "HX": ["corrosion", "corrosion", "valve_failure"],
    "V-": ["valve_failure", "valve_failure", "valve_failure", "corrosion"],
    "AG": ["bearing_failure", "motor_failure", "seal_failure"],
    "T-": ["corrosion", "corrosion", "valve_failure"],
    "CR": ["bearing_failure", "bearing_failure", "motor_failure"],
    "SC": ["bearing_failure", "motor_failure", "electrical"],
}

ORDER_TYPES = {
    "PM01": "Breakdown Maintenance",
    "PM02": "Preventive Maintenance",
    "PM03": "Refurbishment / Overhaul",
    "PM04": "Calibration",
}

DAMAGE_CODES = [
    "MECH-WEAR", "MECH-LEAK", "MECH-BREAK", "MECH-MISALIGN", "MECH-VIBRATION",
    "ELEC-SHORT", "ELEC-MOTOR", "ELEC-SENSOR", "ELEC-WIRING",
    "INST-SENSOR", "INST-VALVE", "INST-CONTROL",
    "CORR-PIPE", "CORR-VESSEL", "CORR-STRUCT",
    "OTHER", "UNKNOWN", ""
]

CAUSE_CODES = [
    "AGING", "OVERLOAD", "MISALIGNMENT", "CONTAMINATION", "VIBRATION",
    "CORROSION", "OPERATOR-ERROR", "DESIGN-FLAW", "FATIGUE",
    "LUBRICATION", "TEMPERATURE", "MOISTURE",
    "UNKNOWN", ""
]

PRIORITIES = {
    "1-Emergency": 0.08,
    "2-Urgent": 0.22,
    "3-Normal": 0.50,
    "4-Low": 0.20,
}

WORK_CENTERS = ["MECH-01", "MECH-02", "ELEC-01", "INST-01", "UTIL-01"]

PLANNERS = ["JSMITH", "MJONES", "RWILSON", "KLEE", "TBROWN"]


def get_failure_type(equip_id, order_type):
    """Get a biased failure type based on equipment."""
    if order_type == "PM02":
        return "preventive_maintenance"
    if order_type == "PM04":
        return "preventive_maintenance"

    for prefix, failures in EQUIP_FAILURE_BIAS.items():
        if equip_id.startswith(prefix):
            return random.choice(failures)

    return random.choice(list(DESCRIPTIONS.keys()))


def generate_data(n_records=2000, clean_mode=False):
    """
    Generate synthetic SAP PM work order data.
    
    Args:
        n_records: Number of work orders to generate
        clean_mode: If True, generates clean data with no quality issues
    """
    np.random.seed(42)
    random.seed(42)

    equipment_ids = list(EQUIPMENT.keys())
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    # Failure rates — some equipment fails more often
    equip_weights = []
    for eid in equipment_ids:
        crit = EQUIPMENT[eid]["criticality"]
        if crit == "A":
            equip_weights.append(3)
        elif crit == "B":
            equip_weights.append(2)
        else:
            equip_weights.append(1)
    equip_weights = np.array(equip_weights, dtype=float)
    equip_weights /= equip_weights.sum()

    records = []

    for i in range(n_records):
        # Pick equipment
        equip_id = np.random.choice(equipment_ids, p=equip_weights)
        equip_info = EQUIPMENT[equip_id]

        # Pick order type
        order_type = np.random.choice(
            ["PM01", "PM02", "PM03", "PM04"],
            p=[0.42, 0.40, 0.12, 0.06]
        )

        # Pick priority
        priority = np.random.choice(
            list(PRIORITIES.keys()),
            p=list(PRIORITIES.values())
        )

        # Dates
        created = start_date + timedelta(days=random.randint(0, date_range_days))

        if order_type == "PM01":
            completion_days = random.randint(0, 7)
        elif order_type == "PM03":
            completion_days = random.randint(7, 45)
        else:
            completion_days = random.randint(0, 14)

        completed = created + timedelta(days=completion_days)

        # Malfunction times (only for breakdowns)
        malf_start = ""
        malf_end = ""
        downtime_hours = 0

        if order_type == "PM01":
            downtime_hours = round(random.uniform(0.5, 72), 1)
            # Weight toward shorter downtimes
            if random.random() < 0.7:
                downtime_hours = round(random.uniform(0.5, 16), 1)
            malf_start = created
            malf_end = created + timedelta(hours=downtime_hours)

        # Description
        failure_type = get_failure_type(equip_id, order_type)
        description = random.choice(DESCRIPTIONS[failure_type])

        # Damage and cause codes
        damage_code = random.choice(DAMAGE_CODES)
        cause_code = random.choice(CAUSE_CODES)

        # Labor
        actual_hours = round(random.uniform(0.5, 24), 1)
        if order_type == "PM02":
            actual_hours = round(random.uniform(0.5, 8), 1)

        # Cost
        labor_rate = random.uniform(75, 150)
        material_cost = random.uniform(0, 8000) if order_type in ["PM01", "PM03"] else random.uniform(0, 500)
        actual_cost = round(actual_hours * labor_rate + material_cost, 2)

        record = {
            "Order_Number": f"40{100000 + i}",
            "Notification": f"10{200000 + i}",
            "Equipment_ID": equip_id,
            "Equipment_Name": equip_info["name"],
            "Equipment_Type": equip_info["type"],
            "Functional_Location": equip_info["location"],
            "Criticality": equip_info["criticality"],
            "Order_Type": order_type,
            "Order_Type_Desc": ORDER_TYPES[order_type],
            "Priority": priority,
            "Work_Center": random.choice(WORK_CENTERS),
            "Planner": random.choice(PLANNERS),
            "Created_Date": created.strftime("%Y-%m-%d"),
            "Completed_Date": completed.strftime("%Y-%m-%d"),
            "Malfunction_Start": malf_start.strftime("%Y-%m-%d %H:%M") if isinstance(malf_start, datetime) else "",
            "Malfunction_End": malf_end.strftime("%Y-%m-%d %H:%M") if isinstance(malf_end, datetime) else "",
            "Downtime_Hours": downtime_hours if downtime_hours > 0 else "",
            "Short_Text": description,
            "Damage_Code": damage_code,
            "Cause_Code": cause_code,
            "Actual_Hours": actual_hours,
            "Actual_Cost": actual_cost,
            "Status": "COMPLETED",
        }

        records.append(record)

    df = pd.DataFrame(records)

    if not clean_mode:
        df = inject_quality_issues(df)

    return df


def inject_quality_issues(df):
    """Inject realistic data quality problems into the dataset."""
    df = df.copy()
    n = len(df)

    # 1. Missing Equipment IDs (15%)
    mask = np.random.random(n) < 0.15
    df.loc[mask, "Equipment_ID"] = ""
    df.loc[mask, "Equipment_Name"] = ""
    df.loc[mask, "Equipment_Type"] = ""

    # 2. Missing Functional Locations (10%)
    mask = np.random.random(n) < 0.10
    df.loc[mask, "Functional_Location"] = ""

    # 3. Missing Damage Codes (40% — this is the big one)
    mask = np.random.random(n) < 0.40
    df.loc[mask, "Damage_Code"] = ""

    # 4. Missing Cause Codes (45%)
    mask = np.random.random(n) < 0.45
    df.loc[mask, "Cause_Code"] = ""

    # 5. Missing Notification Numbers (15%)
    mask = np.random.random(n) < 0.15
    df.loc[mask, "Notification"] = ""

    # 6. Missing Malfunction Times on breakdown orders (30%)
    breakdown_mask = df["Order_Type"] == "PM01"
    malf_missing_mask = breakdown_mask & (np.random.random(n) < 0.30)
    df.loc[malf_missing_mask, "Malfunction_Start"] = ""
    df.loc[malf_missing_mask, "Malfunction_End"] = ""
    df.loc[malf_missing_mask, "Downtime_Hours"] = ""

    # 7. Date inconsistencies — completion before creation (8%)
    mask = np.random.random(n) < 0.08
    for idx in df[mask].index:
        created = pd.to_datetime(df.loc[idx, "Created_Date"])
        df.loc[idx, "Completed_Date"] = (created - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")

    # 8. Duplicate records (3%)
    n_dupes = int(n * 0.03)
    dupe_indices = np.random.choice(df.index, size=n_dupes, replace=True)
    dupes = df.loc[dupe_indices].copy()
    df = pd.concat([df, dupes], ignore_index=True)

    # 9. Missing descriptions (2%)
    mask = np.random.random(len(df)) < 0.02
    df.loc[mask, "Short_Text"] = ""

    # 10. Inconsistent priority formats (5%)
    mask = np.random.random(len(df)) < 0.05
    df.loc[mask, "Priority"] = df.loc[mask, "Priority"].str.replace("-", " - ")

    # Shuffle to mix duplicates in
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    return df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic SAP PM data")
    parser.add_argument("--records", type=int, default=2000, help="Number of records (default: 2000)")
    parser.add_argument("--clean", action="store_true", help="Generate clean data without quality issues")
    parser.add_argument("--output", type=str, default=None, help="Output filename")
    args = parser.parse_args()

    suffix = "clean" if args.clean else "messy"
    filename = args.output or f"sap_pm_workorders_{args.records}_{suffix}.csv"

    print(f"Generating {args.records} work order records ({'clean' if args.clean else 'with quality issues'})...")
    df = generate_data(args.records, clean_mode=args.clean)
    df.to_csv(filename, index=False)
    print(f"Saved to {filename}")
    print(f"Total records (including duplicates): {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Print summary
    print(f"\n--- Data Summary ---")
    print(f"Order Types:")
    for ot, count in df["Order_Type"].value_counts().items():
        desc = ORDER_TYPES.get(ot, ot)
        print(f"  {ot} ({desc}): {count}")
    print(f"\nEquipment with missing IDs: {(df['Equipment_ID'] == '').sum()}")
    print(f"Missing Damage Codes: {(df['Damage_Code'] == '').sum()}")
    print(f"Missing Cause Codes: {(df['Cause_Code'] == '').sum()}")
    print(f"Duplicate Order Numbers: {df['Order_Number'].duplicated().sum()}")


if __name__ == "__main__":
    main()
