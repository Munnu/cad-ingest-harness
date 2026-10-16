"""
Generate vendor-compatible EDA export files from standardized board data.

This module validates standardized board metadata and component records,
reconstructs the expected vendor JSON structure, preserves supported EDA
fields, and writes the generated export to the requested output path.

Invalid input raises a TypeError or ValueError, while file-system failures raise an
OSError. Board coordinate values and their declared units are preserved;
this module does not perform coordinate-unit conversion.
"""

import json
import logging
import math
import os
import tempfile
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_BOARD_UNITS = {"mm", "µm", "mil", "in"}


def _build_vendor_payload(cleaned_data: dict) -> dict:
    """Validate the standardized data and build the vendor export structure."""

    if not isinstance(cleaned_data, dict):
        raise TypeError("Cleaned data must be a dictionary.")

    board_metadata = cleaned_data.get("board_metadata")
    components = cleaned_data.get("components")

    if not isinstance(board_metadata, dict):
        raise TypeError("Missing or invalid board_metadata.")

    board_name = board_metadata.get("board_name")
    units = board_metadata.get("units")

    if not isinstance(board_name, str) or not board_name.strip():
        raise ValueError("board_name must be a non-empty string.")

    if units not in SUPPORTED_BOARD_UNITS:
        raise ValueError(
            f"Unsupported board units: {units!r}. "
            f"Supported units: {sorted(SUPPORTED_BOARD_UNITS)}"
        )

    if not isinstance(components, list) or not components:
        raise ValueError("components must be a non-empty list.")

    vendor_components = []
    seen_ids = set()

    for index, comp in enumerate(components):
        if not isinstance(comp, dict):
            raise TypeError(f"Component at index {index} must be a dictionary.")

        component_id = comp.get("component_id")
        component_type = comp.get("component_type")

        if not isinstance(component_id, str) or not component_id.strip():
            raise ValueError(f"Missing or invalid component_id at index {index}.")

        if not isinstance(component_type, str) or not component_type.strip():
            raise ValueError(f"Missing or invalid component_type for {component_id}.")

        normalized_id = component_id.casefold()
        if normalized_id in seen_ids:
            raise ValueError(f"Duplicate component ID: {component_id}.")
        seen_ids.add(normalized_id)

        x = comp.get("x_position")
        y = comp.get("y_position")

        for axis, coordinate in (("x", x), ("y", y)):
            if (
                isinstance(coordinate, bool)
                or not isinstance(coordinate, (int, float))
                or not math.isfinite(coordinate)
            ):
                raise ValueError(
                    f"Invalid {axis} coordinate for {component_id}: {coordinate!r}"
                )

        vendor_item = {
            "comp_id": component_id,
            "type": component_type,
            "coordinates": {"x": x, "y": y},
        }

        # Preserve optional EDA fields when supplied.
        for field in ("value", "package"):
            field_value = comp.get(field)
            if field_value is not None:
                if not isinstance(field_value, str):
                    raise ValueError(f"{field} for {component_id} must be a string.")
                vendor_item[field] = field_value

        pins = comp.get("pins")
        if pins is not None:
            if not isinstance(pins, list) or not all(
                isinstance(pin, str) and pin.strip() for pin in pins
            ):
                raise ValueError(
                    f"pins for {component_id} must be a list of non-empty strings."
                )
            vendor_item["pins"] = pins

        vendor_components.append(vendor_item)

    return {
        "header": {
            "exporter": "Quilter_AI_FileIO_v1.0",
            "schema_version": "2.0",
            "date_exported": date.today().isoformat(),
        },
        "board_metadata": {
            "board_name": board_name,
            "units": units,
        },
        "components": vendor_components,
    }


def generate_vendor_export(
    cleaned_components: dict,
    output_filepath: str,
) -> None:
    """Generate a vendor-compatible JSON file from standardized board data.

    Raises ValueError for invalid input and OSError for file-writing failures.
    Coordinates are preserved in the supplied board units; no conversion occurs.
    """

    vendor_payload = _build_vendor_payload(cleaned_components)

    destination = Path(output_filepath)
    temporary_path = None

    try:
        # Create the temporary file in the destination directory so that
        # os.replace can atomically replace the destination.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temporary_path = Path(temp_file.name)
            json.dump(
                vendor_payload,
                temp_file,
                indent=4,
                ensure_ascii=False,
                allow_nan=False,
            )
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temporary_path, destination)
        logger.info("Successfully generated vendor export at: %s", destination)

    except (OSError, TypeError, ValueError):
        logger.exception("Failed to generate export at: %s", destination)
        raise

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    import tempfile

    sample_cleaned_data = {
        "board_metadata": {
            "board_name": "Power_Distribution_RevA",
            "units": "mm",
        },
        "components": [
            {
                "component_id": "R1",
                "component_type": "Resistor",
                "x_position": 12.5,
                "y_position": 45.2,
                "value": "10k_ohm",
                "package": "0805",
                "pins": ["1", "2"],
            },
            {
                "component_id": "C1",
                "component_type": "Capacitor",
                "x_position": 33.1,
                "y_position": 0.0,
            },
        ],
    }

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "vendor_export.json"

            generate_vendor_export(sample_cleaned_data, str(output_path))

            # Read back the file to verify it contains valid JSON.
            with output_path.open("r", encoding="utf-8") as file:
                generated_data = json.load(file)

            print(json.dumps(generated_data, indent=2, ensure_ascii=False))
            print("Generator smoke test passed.")

    except (OSError, ValueError) as exc:
        logger.error("Generator smoke test failed: %s", exc)
        raise
