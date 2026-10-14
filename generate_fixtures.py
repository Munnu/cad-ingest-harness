"""
This script generates messy JSON fixtures for testing purposes. 
The generated JSON files will contain a variety of data types and structures, representing electronic components in a EDA environment. 
The goal is to create diverse and unpredictable data that can be used to test the robustness of JSON parsers and data processing pipelines.
The generated files will be saved in the specified output directory, and the number of files to generate

This script is AI generated.
"""

import json
import logging
import random
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def generate_messy_fixtures(output_dir="data/json", count=50):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    exporters = ["Altium_v4", "OrCAD_Legacy", "KiCad_Export", "CustomCAD_v1"]
    
    # Define realistic hardware components (Prefix, Type Name, Valid Values)
    component_pool = [
        {"prefix": "R", "type": "Resistor", "values": ["10k", "100ohm", "4.7k", "330ohm"]},
        {"prefix": "C", "type": "Capacitor", "values": ["100uF", "22pF", "10uF", "0.1uF"]},
        {"prefix": "U", "type": "Microcontroller", "values": ["ATmega328P", "STM32", "ESP32"]},
        {"prefix": "J", "type": "Connector", "values": ["USB_C", "Header_1x4", "Terminal_Block"]}
    ]
    
    logger.info(f"Generating {count} realistic vendor JSON files in '{output_dir}/'...")

    for i in range(1, count + 1):
        exporter = random.choice(exporters)
        
        # 20% chance the file is severely malformed
        is_bad_file = random.choice([True, False, False, False, False])
        
        components = []
        # Generate 3 to 7 components per file
        for c_idx in range(1, random.randint(4, 8)):
            # Pick a realistic component template
            template = random.choice(component_pool)
            
            comp = {}
            
            # 1. Schema drift on ID field name, but keep the prefix matching the component type
            id_key = random.choice(["comp_id", "id", "part_number"])
            comp[id_key] = f"{template['prefix']}{c_idx}"
            
            # 2. Schema drift on type field name
            type_key = random.choice(["type", "part_type", "category"])
            comp[type_key] = template["type"]
            
            # 3. Appropriate value based on component type
            comp["value"] = random.choice(template["values"])
            
            # 4. Handle coordinates with occasional intentional missing data
            if is_bad_file and c_idx == 1:
                # Omit coordinates entirely on the first component of bad files
                pass
            else:
                coords = {"x": round(random.uniform(0, 100), 2)}
                # Sometimes drop 'y' to simulate broken coordinate data
                if not (is_bad_file and c_idx == 2):
                    coords["y"] = round(random.uniform(0, 100), 2)
                comp["coordinates"] = coords
                
            components.append(comp)

        # Generate the current date dynamically
        current_date = datetime.now().strftime("%Y-%m-%d")
    
        # Build the full payload structure
        payload = {
            "header": {
                "exporter": exporter,
                "schema_version": "2.0",
                "date_exported": current_date
            },
            "board_metadata": {
                "board_name": f"Board_Rev_{i}",
                "units": "mm"
            },
            "components": components
        }

        # Write out to data/json/
        file_name = output_path / f"vendor_{i:03d}_export.json"
        with open(file_name, "w") as f:
            json.dump(payload, f, indent=2)

    logger.info(f"Successfully generated {count} test files with realistic component mapping!")

if __name__ == "__main__":
    generate_messy_fixtures()
