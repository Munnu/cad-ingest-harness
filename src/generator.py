import json
import logging
import os
import tempfile
from datetime import datetime

# Set up logging to track what our generator is doing
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_vendor_export(
    cleaned_components: list, output_filepath: str, board_name: str = "Default_Board"
):
    """Takes Quilter's clean internal component format and generates a valid vendor export file."""

    # Generate the current date dynamically
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 1. Rebuild the vendor's required wrapper structure (Headers, Metadata)
    vendor_payload = {
        "header": {
            "exporter": "Quilter_AI_FileIO_v1.0",
            "schema_version": "2.0",
            "date_exported": current_date,
        },
        "board_metadata": {"board_name": board_name, "units": "mm"},
        "components": [],
    }

    # 2. Map our clean internal keys back to the vendor's expected keys
    for comp in cleaned_components:
        vendor_item = {
            "comp_id": comp["component_id"],
            "type": comp["component_type"],
            "coordinates": {"x": comp["x_position"], "y": comp["y_position"]},
        }
        vendor_payload["components"].append(vendor_item)

    # 3. Write the payload out to disk safely
    try:
        with open(output_filepath, "w") as file:
            json.dump(vendor_payload, file, indent=4)
        logger.info(f"Successfully generated vendor export at: {output_filepath}")
    except (OSError, TypeError) as e:
        logger.error(f"Failed to generate export file: {e}")


if __name__ == "__main__":
    sample_cleaned_data = [
        {
            "component_id": "R1",
            "component_type": "Resistor",
            "x_position": 12.5,
            "y_position": 45.2,
        },
        {
            "component_id": "C1",
            "component_type": "Capacitor",
            "x_position": 33.1,
            "y_position": 0.0,
        },
    ]

    print("--- RUNNING GENERATOR WITH TEMPFILE (NO JUNK FILES) ---")

    # state variables initialized right before the try block
    temp_filename = None
    success = False

    try:
        # Create a secure, temporary file that automatically cleans itself up
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_filename = temp_file.name

        # log the payload to verify what will be written
        logger.info(f"Test Payload: {sample_cleaned_data}")

        # Run our generator pointing to the temporary path
        generate_vendor_export(
            sample_cleaned_data, temp_filename, board_name="Test_Board"
        )

        success = True
        logger.info("File has been successfully generated")

    except (OSError, ValueError) as e:
        logger.error(f"An error occurred during the generation process: {e}")
    finally:
        # Guaranteed cleanup so no junk is left behind
        if temp_filename and os.path.exists(temp_filename):
            if success:
                os.remove(temp_filename)
                logger.info("Test file removed successfully.")
            else:
                logger.error(
                    f"Test file remains for inspection due to failure: {temp_filename}"
                )
