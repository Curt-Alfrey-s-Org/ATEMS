#!/usr/bin/env python3
"""
Seed 50,000 tools from top 10 US industries for demo site.
Generates realistic tool data with varied calibration dates and locations.
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atems import create_app
from extensions import db
from models.tools import Tools

# Top 10 US Industries Tool Categories
INDUSTRY_TOOLS = {
    "CONS": [  # Construction - 8,000 tools
        ("HAM", "Hammer", ["Claw 16oz", "Framing 20oz", "Ball Peen 12oz", "Sledge 8lb", "Dead Blow 3lb"], False),
        ("TAPE", "Tape Measure", ["25ft", "30ft", "100ft", "Laser 200ft"], False),
        ("LEV", "Level", ["24in Spirit", "48in Box", "Torpedo", "Laser Rotary", "Digital Angle"], False),
        ("SAW", "Saw", ["Circular 7.25in", "Miter 10in", "Reciprocating", "Jigsaw", "Table 10in"], False),
        ("DRILL", "Drill", ["Cordless 18V", "Hammer Drill", "Right Angle", "Magnetic Base"], False),
        ("GRIND", "Grinder", ["Angle 4.5in", "Angle 9in", "Bench 8in", "Die 1/4in"], False),
        ("NAILER", "Nailer", ["Framing Pneumatic", "Finish Brad", "Roofing Coil", "Stapler"], False),
        ("WRENCH", "Wrench", ["Adjustable 12in", "Pipe 18in", "Torque 1/2in", "Impact 1/2in"], False),
    ],
    "MANF": [  # Manufacturing - 10,000 tools
        ("CAL", "Caliper", ["Digital 6in", "Digital 12in", "Dial 8in", "Vernier 6in"], True),
        ("MICRO", "Micrometer", ["Outside 0-1in", "Outside 1-2in", "Inside 0.2-1.2in", "Depth 0-6in"], True),
        ("GAUGE", "Gauge", ["Pin Set", "Thread Ring", "Height 12in", "Bore Dial", "Snap"], True),
        ("MILL", "Milling Machine", ["Vertical 3HP", "Horizontal 5HP", "CNC 3-Axis", "Benchtop"], False),
        ("LATHE", "Lathe", ["Engine 12x36", "CNC 8x20", "Benchtop 7x14", "Wood 16in"], False),
        ("PRESS", "Press", ["Drill 1HP", "Hydraulic 20T", "Arbor 2T", "Pneumatic"], False),
        ("GRIND", "Grinder", ["Surface 6x12", "Cylindrical", "Tool & Cutter", "Bench 6in"], False),
        ("BAND", "Band Saw", ["Metal 7x12", "Vertical 14in", "Horizontal 4x6", "Portable"], False),
    ],
    "AUTO": [  # Automotive - 7,000 tools
        ("SOCKET", "Socket Set", ["1/4in SAE", "3/8in Metric", "1/2in Deep", "Impact 1/2in"], False),
        ("TORQ", "Torque Wrench", ["1/4in 20-200in-lb", "3/8in 10-80ft-lb", "1/2in 30-250ft-lb", "Digital 1/2in"], True),
        ("IMP", "Impact Wrench", ["Pneumatic 1/2in", "Cordless 18V", "Cordless 1in", "Pneumatic 3/4in"], False),
        ("JACK", "Jack", ["Floor 3T", "Bottle 6T", "Transmission 1T", "Scissor 2T"], False),
        ("LIFT", "Lift", ["2-Post 10K", "4-Post 12K", "Mobile Column", "Scissor 6K"], False),
        ("SCAN", "Scanner", ["OBD2 Basic", "OBD2 Pro", "Bi-Directional", "Oscilloscope"], False),
        ("COMP", "Compressor", ["Air 60gal", "Air 80gal", "Portable 6gal", "AC Recovery"], False),
        ("BRAKE", "Brake Tool", ["Bleeder Vacuum", "Caliper Tool", "Spring Pliers", "Rotor Micrometer"], True),
    ],
    "OILGAS": [  # Oil & Gas - 5,000 tools
        ("PIPE", "Pipe Wrench", ["18in", "24in", "36in", "48in Chain"], False),
        ("THREAD", "Threading Tool", ["Pipe Dies 1/2-2in", "Tap Set NPT", "Thread Gauge", "Pipe Cutter"], True),
        ("TORQ", "Torque Tool", ["Hydraulic Wrench 1000ft-lb", "Pneumatic 500ft-lb", "Multiplier 4000ft-lb"], True),
        ("VALVE", "Valve Tool", ["Gate Wrench", "Actuator Tool", "Seat Grinder", "Lapping Kit"], False),
        ("WELD", "Welding Equipment", ["Stick 225A", "MIG 180A", "TIG 200A", "Plasma Cutter 40A"], False),
        ("DRILL", "Drill", ["Pneumatic 1/2in", "Magnetic Base", "Core Drill", "Right Angle"], False),
        ("GRIND", "Grinder", ["Angle 7in", "Angle 9in", "Bench 8in", "Die 1/4in"], False),
    ],
    "AERO": [  # Aerospace - 6,000 tools
        ("TORQ", "Torque Tool", ["Driver 5-50in-lb", "Wrench 10-100in-lb", "Analyzer Digital", "Multiplier"], True),
        ("PREC", "Precision Tool", ["Screwdriver Set", "Hex Key Set", "Pin Punch Set", "Tweezer Set"], False),
        ("RIVET", "Rivet Tool", ["Gun Pneumatic", "Squeezer C-Frame", "Drill #30", "Dimpler"], False),
        ("INSPECT", "Inspection Tool", ["Borescope", "Ultrasonic Tester", "Eddy Current", "Dye Penetrant Kit"], True),
        ("COMP", "Composite Tool", ["Trim Router", "Sander Orbital", "Shears", "Vacuum Bag Pump"], False),
        ("DRILL", "Drill", ["Right Angle", "Precision 1/4in", "Micro Set", "Countersink Set"], False),
        ("DEBUR", "Deburring Tool", ["Hand Set", "Rotary", "Countersink", "Blade Set"], False),
    ],
    "ELEC": [  # Electrical/Utilities - 6,000 tools
        ("MULTI", "Multimeter", ["Digital Basic", "Digital RMS", "Clamp 600A", "Insulation Tester"], True),
        ("STRIP", "Wire Tool", ["Stripper 10-22AWG", "Crimper", "Cutter", "Fish Tape 50ft"], False),
        ("TEST", "Tester", ["Voltage Non-Contact", "Voltage Solenoid", "Outlet", "GFCI"], True),
        ("DRILL", "Drill", ["Hammer 18V", "Right Angle", "Hole Saw Kit", "Magnetic Base"], False),
        ("BEND", "Conduit Tool", ["Bender 1/2in", "Bender 3/4in", "Reamer", "Cutter"], False),
        ("FISH", "Fish Tape", ["50ft Steel", "100ft Fiberglass", "200ft", "Glow Rod Set"], False),
        ("LADDER", "Ladder", ["Step 6ft", "Extension 24ft", "Platform 4ft", "Telescoping"], False),
    ],
    "PLUMB": [  # Plumbing/HVAC - 5,000 tools
        ("WRENCH", "Wrench", ["Basin", "Pipe 14in", "Adjustable 12in", "Strap"], False),
        ("CUTTER", "Cutter", ["Pipe 1/8-2in", "Tubing 1/4-1in", "PVC Ratchet", "Copper Wheel"], False),
        ("TORCH", "Torch", ["Propane", "MAPP", "Acetylene Set", "Solder Iron 100W"], False),
        ("SNAKE", "Snake", ["Drain 25ft", "Closet Auger", "Power 50ft", "Drum 100ft"], False),
        ("PRESS", "Press Tool", ["PEX Crimp", "ProPress 1/2-2in", "Expansion", "Clamp"], False),
        ("GAUGE", "Gauge", ["Pressure 0-300psi", "Vacuum", "Manifold R410A", "Temperature"], True),
        ("PUMP", "Pump", ["Vacuum 4CFM", "Vacuum 8CFM", "Test Hydro", "Transfer"], False),
    ],
    "AGRI": [  # Agriculture - 4,000 tools
        ("CHAIN", "Chainsaw", ["16in Gas", "18in Gas", "14in Electric", "20in Pro"], False),
        ("TRIM", "Trimmer", ["String Gas", "String Battery", "Brush Cutter", "Hedge 24in"], False),
        ("FENCE", "Fence Tool", ["Post Driver", "Pliers", "Stretcher", "Wire Unroller"], False),
        ("PRUNE", "Pruning Tool", ["Shears Hand", "Lopper 28in", "Saw Pole", "Hedge Shear"], False),
        ("AUG", "Auger", ["Post Hole Gas", "Earth 1-Man", "Earth 2-Man", "Ice 8in"], False),
        ("SPRAY", "Sprayer", ["Backpack 4gal", "ATV 25gal", "Handheld 1gal", "Boom 60ft"], False),
        ("TILL", "Tiller", ["Front Tine", "Rear Tine", "Cultivator", "Mini"], False),
    ],
    "MINE": [  # Mining - 3,000 tools
        ("DRILL", "Drill", ["Jackleg Pneumatic", "Drifter", "Rock DTH", "Core NQ"], False),
        ("HAMMER", "Hammer", ["Sledge 16lb", "Rock Pick", "Scaling", "Chipping Pneumatic"], False),
        ("BOLT", "Bolting Tool", ["Roof Bolter", "Rock Drill", "Resin Mixer", "Torque Wrench"], False),
        ("DETECT", "Detector", ["Gas Multi", "Oxygen", "Methane", "CO Monitor"], True),
        ("LIGHT", "Lighting", ["Cap Lamp LED", "Portable Flood", "Explosion Proof", "Emergency"], False),
        ("PUMP", "Pump", ["Dewatering 3in", "Slurry 4in", "Submersible 2in", "Trash 6in"], False),
    ],
    "MED": [  # Healthcare/Medical Devices - 6,000 tools
        ("SURG", "Surgical Instrument", ["Scalpel Set", "Forceps Set", "Scissors Set", "Retractor Set"], True),
        ("DRILL", "Medical Drill", ["Orthopedic Battery", "Cranial Pneumatic", "Bone Saw", "Wire Driver"], True),
        ("CALIB", "Calibration Tool", ["Pressure 0-300mmHg", "Flow 0-15LPM", "Temperature Probe", "Electrical Safety"], True),
        ("STERIL", "Sterilization", ["Autoclave 18L", "Autoclave 45L", "UV Cabinet", "Washer"], True),
        ("DIAG", "Diagnostic Tool", ["Stethoscope", "Otoscope", "Ophthalmoscope", "BP Monitor"], True),
        ("DEFIB", "Defibrillator", ["AED Trainer", "AED", "Manual Biphasic", "Analyzer"], True),
        ("PUMP", "Infusion Pump", ["Syringe", "Volumetric", "PCA", "Enteral"], True),
    ],
}

# Bin locations (expanded for 50K tools)
def generate_bins():
    """Generate realistic bin locations."""
    bins = []
    for row in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for bay in range(1, 21):  # 20 bays per row
            for shelf in range(1, 11):  # 10 shelves per bay
                bins.append(f"{row}{bay:02d}-{shelf:02d}")
    return bins

BINS = generate_bins()


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        existing_count = Tools.query.count()
        if existing_count >= 50000:
            print(f"✓ Database already has {existing_count} tools")
            return
        
        print(f"Starting seed: {existing_count} tools exist, adding more to reach 50,000...")
        
        count = existing_count
        today = datetime.now()
        
        # Calculate tools per industry
        industries = list(INDUSTRY_TOOLS.keys())
        weights = [8000, 10000, 7000, 5000, 6000, 6000, 5000, 4000, 3000, 6000]
        total_weight = sum(weights)
        
        batch_size = 1000
        batch = []
        
        for industry, target_count in zip(industries, weights):
            tool_types = INDUSTRY_TOOLS[industry]
            tools_per_type = target_count // len(tool_types)
            
            for tool_code, base_name, variants, is_calibrated in tool_types:
                for i in range(tools_per_type):
                    if count >= 50000:
                        break
                    
                    variant = variants[i % len(variants)]
                    tool_id = f"{industry}-{tool_code}-{i+1:05d}"
                    
                    # Check if exists
                    if Tools.query.filter_by(tool_id_number=tool_id).first():
                        continue
                    
                    # Random location
                    loc = random.choice(BINS)
                    
                    # Calibration dates
                    if is_calibrated:
                        cal_date = (today - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
                        cal_due = (today + timedelta(days=random.randint(-30, 180))).strftime("%Y-%m-%d")
                        cal_cert = f"CERT-{random.randint(1000, 9999)}"
                        cal_schedule = random.choice(["30 days", "90 days", "180 days", "365 days"])
                    else:
                        cal_date = "N/A"
                        cal_due = "N/A"
                        cal_cert = "N/A"
                        cal_schedule = "N/A"
                    
                    # Status (most in stock, some checked out)
                    status = "In Stock" if random.random() > 0.15 else "Checked Out"
                    checked_out_by = None if status == "In Stock" else f"USER{random.randint(1, 200):03d}"
                    
                    t = Tools(
                        tool_id_number=tool_id,
                        tool_name=f"{base_name} {variant}",
                        tool_location=loc,
                        tool_status=status,
                        tool_calibration_due=cal_due,
                        tool_calibration_date=cal_date,
                        tool_calibration_cert=cal_cert,
                        tool_calibration_schedule=cal_schedule,
                        checked_out_by=checked_out_by,
                    )
                    batch.append(t)
                    count += 1
                    
                    if len(batch) >= batch_size:
                        db.session.bulk_save_objects(batch)
                        db.session.commit()
                        print(f"  Progress: {count:,} / 50,000 tools")
                        batch = []
                
                if count >= 50000:
                    break
            
            if count >= 50000:
                break
        
        # Commit remaining
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
        
        final_count = Tools.query.count()
        print(f"\n✓ Seeding complete: {final_count:,} total tools in database")


if __name__ == "__main__":
    main()
