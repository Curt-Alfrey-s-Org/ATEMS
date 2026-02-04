#!/usr/bin/env python3
"""Seed tools from top 10 industries for testing. Run from ATEMS dir with app context."""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atems import create_app
from extensions import db
from models.tools import Tools

# Tools by industry: (short_id, name, is_calibrated)
# Format: INDUSTRY-TYPE-NNN, e.g. CONS-HAM-001
TOOLS_BY_INDUSTRY = {
    "CONS": [  # Construction
        ("HAM-001", "Claw Hammer 16oz", False),
        ("TAPE-001", "Tape Measure 25ft", False),
        ("SQ-001", "Framing Square", False),
        ("CHIS-001", "Wood Chisel Set", False),
        ("LEV-001", "Spirit Level 24in", False),
        ("PB-001", "Pry Bar", False),
        ("KNIF-001", "Utility Knife", False),
        ("DRILL-001", "Cordless Drill", False),
        ("CIRC-001", "Circular Saw", False),
        ("RECIP-001", "Reciprocating Saw", False),
        ("IMP-001", "Impact Driver", False),
    ],
    "MANF": [  # Manufacturing
        ("CAL-001", "Digital Calipers 6in", True),
        ("WRENCH-001", "Combination Wrench Set", False),
        ("SCREW-001", "Screwdriver Set", False),
        ("FILE-001", "Metal Files Set", False),
        ("PUNCH-001", "Center Punch Set", False),
        ("DRILLP-001", "Drill Press", False),
        ("GRIND-001", "Bench Grinder", False),
        ("BELT-001", "Belt Sander", False),
        ("BAND-001", "Band Saw", False),
    ],
    "AUTO": [  # Automotive
        ("SOCKET-001", "Socket Set 1/2in", False),
        ("TORQ-001", "Torque Wrench", True),
        ("OIL-001", "Oil Filter Wrench", False),
        ("BLEED-001", "Brake Bleeder", False),
        ("IMPW-001", "Impact Wrench", False),
        ("ANGLE-001", "Angle Grinder", False),
        ("POL-001", "Polisher", False),
    ],
    "OILGAS": [  # Oil & Gas
        ("PIPE-001", "Pipe Wrench 24in", False),
        ("TUBE-001", "Tubing Cutter", False),
        ("THREAD-001", "Thread Gauge", True),
        ("PNEU-001", "Pneumatic Drill", False),
        ("HYDRO-001", "Hydraulic Torque Wrench", True),
    ],
    "AERO": [  # Aerospace
        ("PREC-001", "Precision Screwdriver Set", False),
        ("TD-001", "Torque Driver", True),
        ("RIVET-001", "Rivet Gun", False),
        ("PREDRILL-001", "Precision Drill", False),
        ("DEBUR-001", "Deburring Tool", False),
    ],
    "ELEC": [  # Electrical/Utilities
        ("STRIP-001", "Wire Strippers", False),
        ("MULTI-001", "Digital Multimeter", True),
        ("VOLT-001", "Voltage Tester", False),
        ("FISH-001", "Fish Tape", False),
        ("HOLE-001", "Hole Saw Kit", False),
        ("CRIMP-001", "Cable Crimper", False),
    ],
    "PLUMB": [  # Plumbing/HVAC
        ("PCUT-001", "Pipe Cutter", False),
        ("BASIN-001", "Basin Wrench", False),
        ("BEND-001", "Tube Bender", False),
        ("SNAKE-001", "Drain Snake", False),
        ("THREADP-001", "Pipe Threader", False),
    ],
    "AGRI": [  # Agriculture
        ("PRUNE-001", "Pruning Shears", False),
        ("FENCE-001", "Fencing Pliers", False),
        ("POST-001", "Post Driver", False),
        ("CHAIN-001", "Chainsaw", False),
        ("BRUSH-001", "Brush Cutter", False),
        ("AUG-001", "Earth Auger", False),
    ],
    "MINE": [  # Mining
        ("ROCK-001", "Rock Pick", False),
        ("SLEDGE-001", "Sledgehammer", False),
        ("CROW-001", "Crowbar", False),
        ("JACK-001", "Jackleg Drill", False),
        ("ROOF-001", "Roof Bolter", False),
    ],
    "MED": [  # Healthcare (Med Devices)
        ("SURG-001", "Surgical Instrument Set", True),
        ("CALG-001", "Calibration Gauge", True),
        ("STERIL-001", "Sterilization Equipment", True),
        ("ORDRIL-001", "OR Power Drill", False),
    ],
}

# Bin locations for storage
BINS = ["A1-01", "A1-02", "A1-03", "A2-01", "A2-02", "A2-03", "B1-01", "B1-02", "B2-01", "B2-02", "C1-01", "C1-02"]


def main():
    app = create_app()
    with app.app_context():
        count = 0
        bin_idx = 0
        today = datetime.now()
        cal_due = (today + timedelta(days=90)).strftime("%Y-%m-%d")
        cal_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        for industry, tools in TOOLS_BY_INDUSTRY.items():
            for short_id, name, is_calibrated in tools:
                tool_id = f"{industry}-{short_id}"
                if Tools.query.filter_by(tool_id_number=tool_id).first():
                    continue
                loc = BINS[bin_idx % len(BINS)]
                bin_idx += 1
                t = Tools(
                    tool_id_number=tool_id,
                    tool_name=name,
                    tool_location=loc,
                    tool_status="In Stock",
                    tool_calibration_due=cal_due if is_calibrated else "N/A",
                    tool_calibration_date=cal_date if is_calibrated else "N/A",
                    tool_calibration_cert="CERT-001" if is_calibrated else "N/A",
                    tool_calibration_schedule="90 days" if is_calibrated else "N/A",
                )
                db.session.add(t)
                count += 1
        db.session.commit()
        print(f"Created {count} tools across {len(TOOLS_BY_INDUSTRY)} industries.")


if __name__ == "__main__":
    main()
