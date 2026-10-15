import json
import logging
import sys

from pydantic import BaseModel, ValidationError

# Set up logging to track what our parser is doing
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ComponentParsingError(ValueError):
    """Raised when an individual component fails validation, invalidating the board."""


# Define a Pydantic model for the component data, what Quilter wants our data to look like
class StandardComponent(BaseModel):
    component_id: str
    component_type: str
    x_position: float
    y_position: float


def parse_vendor_file(filepath: str):
    """
    Parses a vendor export JSON file strictly. Raises ValueError or
    ValueError if any component data is missing or malformed.
    """
    try:
        with open(filepath, "r") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise

    # Navigate past the header to get straight to the components list
    raw_components = raw_data.get("components", [])
    if not raw_components:
        raise ValueError("File contains no components list.")

    cleaned_components = []

    for index, item in enumerate(raw_components):
        try:
            # Handle schema drift: Check both 'comp_id' and 'id' for the component ID
            component_id = item.get("comp_id") or item.get("id")
            if not component_id:
                raise ValueError(f"Missing component ID in item at index {index}")

            # Handle schema drift: Check both 'type' and 'part_type' for the component type
            component_type = item.get("type") or item.get("part_type") or "unknown"

            # Handle nested coordinates defensively with fallback defaults
            coords = item.get("coordinates", {})
            if "x" not in coords or "y" not in coords:
                raise ValueError(
                    f"Missing coordinate(s) for component {component_id} at index {index}"
                )

            x = coords["x"]
            y = coords["y"]

            # Build a normalized dictionary matching our Pydantic model
            normalized_dict = {
                "component_id": component_id,
                "component_type": component_type,
                "x_position": x,
                "y_position": y,
            }

            # Pass through the Pydantic model for validation and normalization
            validated_item = StandardComponent(**normalized_dict)
            cleaned_components.append(validated_item.model_dump())

        except ValidationError as e:
            logger.error(
                f"Pydantic type validation failed at index {index}: {e}. No longer parsing the board."
            )
            raise ComponentParsingError(f"Data type mismatch: {e}")

        except (KeyError, TypeError, ValueError) as e:
            logger.error(
                f"Schema structure failed at index {index}: {e}. No longer parsing the board."
            )
            raise ComponentParsingError(
                f"Board parsing aborted at index {index} due to: {e}"
            )

    return cleaned_components


if __name__ == "__main__":
    target_file = "vendor_export.json"

    logger.info("--- STARTING VENDOR EXPORT PARSER ---")
    try:
        logger.info(f"Processing: {target_file}")

        results = parse_vendor_file(target_file)

        logger.info(f"Successfully parsed and standardized {len(results)} components:")
        for comp in results:
            print(comp)

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Process failed due to data or file validation error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
