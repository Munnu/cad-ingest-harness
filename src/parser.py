"""
Parse and validate vendor EDA export files into a standardized format.

This module reads vendor-exported JSON files, validates board metadata and
component records, and normalizes component identifiers, types, coordinates,
and supported EDA fields into a consistent internal representation.

Invalid board metadata or malformed component data causes parsing to fail
with a BoardParsingError. Supported board coordinate units are preserved
as declared in the input; this module does not convert coordinate units.
"""

import json
import logging
import sys
from math import isfinite

from pydantic import BaseModel, ValidationError

# Set up logging to track what our parser is doing
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class BoardParsingError(ValueError):
    """Raised when board metadata is fails validation or an
    individual component fails validation, invalidating the board."""


# Define a Pydantic model for the board metadata
class BoardMetadata(BaseModel):
    board_name: str
    units: str


# Define a Pydantic model for the component data, what Quilter wants our data to look like
class StandardComponent(BaseModel):
    component_id: str
    component_type: str
    x_position: float
    y_position: float

    value: str | None = None
    package: str | None = None
    pins: list[str] | None = None


def _validate_metadata(metadata_body: dict) -> BoardMetadata:
    """Validate the metadata body, must be a dict as the requiremenet"""
    _supported_board_units = {"mm", "µm", "mil", "in"}

    try:
        # 1. validate that it is a dictionary
        if not isinstance(metadata_body, dict):
            raise TypeError(
                f"Wrong datatype for board metadata body {type(metadata_body)}"
            )

        # 2. validate that board_metadata.boardname is a nonempty string
        board_name = metadata_body.get("board_name")
        if not isinstance(board_name, str) or board_name.strip() == "":
            raise TypeError(
                f"Wrong datatype for board name: {type(board_name)} or empty board name: {board_name}"
            )

        # 3. validate that board_metadata.units is a supported unit
        board_unit = metadata_body.get("units")
        if not isinstance(board_unit, str) or board_unit not in _supported_board_units:
            raise ValueError(
                f"Wrong datatype for board unit: {type(board_unit)}"
                + f" or unsupported board unit: {board_unit};"
                + f" supported units: {_supported_board_units}"
            )

        # 4. all is fine, so pass through the Pydantic model for validation and normalization
        normalized_dict = {"board_name": board_name, "units": board_unit}
        return BoardMetadata(**normalized_dict)
    except (KeyError, TypeError, ValueError) as e:
        logger.error(
            f"Schema structure failed during board_metadata parsing: {e}. No longer parsing the board."
        )
        raise BoardParsingError(f"Invalid board metadata: {e}") from e


def _validate_component_record(item: dict, index: int) -> StandardComponent:
    """Validate and normalize one component record."""

    if not isinstance(item, dict):
        raise BoardParsingError(f"Component at index {index} must be a dictionary.")

    # 1. Component ID is required.
    component_id = item.get("comp_id") or item.get("id")

    if not isinstance(component_id, str) or not component_id.strip():
        raise BoardParsingError(f"Missing or invalid component ID at index {index}.")

    component_id = component_id.strip()

    # 2. Component type is required.
    component_type = item.get("type") or item.get("part_type")

    if not isinstance(component_type, str) or not component_type.strip():
        raise BoardParsingError(
            f"Missing or invalid component type for {component_id}."
        )

    component_type = component_type.strip()

    # 3. Coordinates must be present and correctly structured.
    coords = item.get("coordinates")

    if not isinstance(coords, dict):
        raise BoardParsingError(f"Missing or invalid coordinates for {component_id}.")

    if "x" not in coords or "y" not in coords:
        raise BoardParsingError(f"Missing coordinate(s) for component {component_id}.")

    x = coords["x"]
    y = coords["y"]

    # Reject strings, booleans, NaN, and infinity (not isfinite).
    for axis, coordinate in (("x", x), ("y", y)):
        if (
            isinstance(coordinate, bool)
            or not isinstance(coordinate, (int, float))
            or not isfinite(coordinate)
        ):
            raise BoardParsingError(
                f"Invalid {axis} coordinate for component {component_id}: "
                f"{coordinate!r}"
            )

    # 4. Optional descriptive fields must have valid types.
    value = item.get("value")
    package = item.get("package")

    for field_name, field_value in (
        ("value", value),
        ("package", package),
    ):
        if field_value is not None and not isinstance(field_value, str):
            raise BoardParsingError(
                f"Invalid {field_name} for component {component_id}: "
                f"expected a string or null."
            )

    # 5. Pins are optional, but must be a list when supplied.
    pins = item.get("pins")

    if pins is not None:
        if not isinstance(pins, list):
            raise BoardParsingError(
                f"Invalid pins for component {component_id}: expected a list."
            )

        normalized_pins = []

        for pin in pins:
            # Numeric pin identifiers are converted to strings.
            # Booleans are deliberately excluded, despite being integers in Python.
            if isinstance(pin, bool) or not isinstance(pin, (str, int)):
                raise BoardParsingError(
                    f"Invalid pin identifier for component {component_id}: {pin!r}"
                )

            pin_id = str(pin)

            if not pin_id.strip():
                raise BoardParsingError(
                    f"Empty pin identifier for component {component_id}."
                )

            normalized_pins.append(pin_id)

        pins = normalized_pins

    # 6. Build the standardized component.
    try:
        return StandardComponent(
            component_id=component_id,
            component_type=component_type,
            x_position=x,
            y_position=y,
            value=value,
            package=package,
            pins=pins,
        )
    except ValidationError as e:
        raise BoardParsingError(
            f"Component validation failed at index {index}: {e}"
        ) from e


def _validate_components(raw_components: list) -> list[dict]:
    """Validate all components and reject duplicate component IDs."""

    if not isinstance(raw_components, list) or not raw_components:
        raise BoardParsingError("File must contain a non-empty components list.")

    cleaned_components = []
    seen_ids = set()

    for index, item in enumerate(raw_components):
        component = _validate_component_record(item, index)

        # Component references should be unique within the board.
        normalized_id = component.component_id.casefold()

        if normalized_id in seen_ids:
            raise BoardParsingError(
                f"Duplicate component ID: {component.component_id}."
            )

        seen_ids.add(normalized_id)
        cleaned_components.append(component.model_dump())

    return cleaned_components


def parse_vendor_file(filepath: str) -> dict:
    """
    Parses a vendor export JSON file strictly.
    If the JSON file is poorly formatted or fails board validation, the board gets rejected.
    """
    try:
        with open(filepath, "r") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise

    # parse the various parts fo the vendor file
    cleaned_metadata = _validate_metadata(raw_data.get("board_metadata", {}))
    cleaned_components = _validate_components(raw_data.get("components", []))

    return {
        "board_metadata": {
            "board_name": cleaned_metadata.board_name,
            "units": cleaned_metadata.units,
        },
        "components": cleaned_components,
    }


if __name__ == "__main__":
    target_file = "samples/vendor_export.json"

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
