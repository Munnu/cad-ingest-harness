"""
Batch Evaluation Harness for CAD Vendor Ingestion Pipeline.

This script automates the validation of synthetic and real-world vendor
export fixtures stored in the /data directory. It runs each payload through the
Pydantic parsing layer, catches schema drift or parsing errors gracefully,
and generates a consolidated scorecard summary.

Usage:
    python evaluate.py
"""

import logging
from json import JSONDecodeError
from pathlib import Path

from .parser import BoardParsingError, parse_vendor_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_batch_evaluation(data_dir: str = "data/json"):
    """
    Scans the data/json directory, runs our Pydantic parser across all synthetic vendor fixtures,
    then generates a summary report of the parsing results.
    """
    path = Path(data_dir)

    if not path.exists():
        logger.error(
            f"Data directory does not exist: '{data_dir}'. Run generate_fixtures.py first.)"
        )
        return

    # Find all export JSON files in our structured folder
    json_files = list(path.glob("*_export.json"))

    if not json_files:
        logger.warning(f"No JSON files found in '{data_dir}'.")
        return

    print(f"--- STARTING CAD BATCH EVALUATION ({len(json_files)} files found) ---")

    total_files = len(json_files)
    passed_files = 0
    failed_files = 0

    for i, file_path in enumerate(json_files, start=1):
        print("--------------------")
        print(f"{i}")
        try:
            # pass the file through our Pydantic parser
            parsed_boards = parse_vendor_file(str(file_path))

            if parsed_boards:
                logger.info(f"[PASS] {file_path.name} -> Successfully parsed board.")
                passed_files += 1
            else:
                logger.error(
                    f"  [FAIL] {file_path.name} -> Parser returned zero boards."
                )
                failed_files += 1

        except (
            FileNotFoundError,
            JSONDecodeError,
            ValueError,
            BoardParsingError,
        ) as e:
            logger.error(
                f"[FAIL] {file_path.name} -> Rejected due to malformed data: {e}"
            )
            failed_files += 1

    # Print out the final scorecard summary
    print("\n" + "=" * 50)
    print("           EVALUATION SCORECARD SUMMARY")
    print("=" * 50)
    print(f" Total Files Processed : {total_files}")
    print(f" Successfully Parsed   : {passed_files}")
    print(f" Rejected / Failed     : {failed_files}")
    print("=" * 50)


if __name__ == "__main__":
    run_batch_evaluation()
