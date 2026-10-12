from pydantic import BaseModel
import json
import logging

# Set up logging to track what our parser is doing
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Define a Pydantic model for the component data, what Quilter wants our data to look like
class StandardComponent(BaseModel):
    component_id: str
    component_type: str
    x_position: float
    y_position: float
    
def parse_vendor_file(filepath: str):
    try:
        with open(filepath, 'r') as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return []

    # Navigate past the header to get straight to the components list
    raw_components = raw_data.get('components', [])
    cleaned_components = []
    
    for index, item in enumerate(raw_components):
        try:
            # Handle schema drift: Check both 'comp_id' and 'id' for the component ID
            component_id = item.get('comp_id') or item.get('id')
            if not component_id:
                raise ValueError(f"Missing component ID in item at index {index}")
            
            # Handle schema drift: Check both 'type' and 'part_type' for the component type
            component_type = item.get('type') or item.get('part_type') or "unknown"
            
            # Handle nested coordinates defensively with fallback defaults
            coords = item.get('coordinates', {})
            x = coords.get('x', 0.0)  # Default to 0.0 if missing
            y = coords.get('y', 0.0)  # Default to 0.0 if missing
            
            if "x" not in coords or "y" not in coords:
                logging.warning(f"Missing coordinate(s) for component {component_id} at index {index}. Coordinates are now changed to ({x}, {y}).")
                
            # Build a normalized dictionary matching our Pydantic model
            normalized_dict = {
                "component_id": component_id,
                "component_type": component_type,
                "x_position": x,
                "y_position": y
            }
            
            # Pass through the Pydantic model for validation and normalization
            validated_item = StandardComponent(**normalized_dict)
            cleaned_components.append(validated_item.model_dump())
        
        except Exception as e:
            logging.warning(f"Error processing item at index {index}: {e}. Skipping this item.")
    
    return cleaned_components

if __name__ == "__main__":
    print("--- PARSING VENDOR EXPORT FILE ---")
    results = parse_vendor_file("vendor_export.json")
    
    print("\n--- SUCCESSFULLY PARSED & STANDARDIZED COMPONENTS ---")
    for comp in results:
        print(comp)