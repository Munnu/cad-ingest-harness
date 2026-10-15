import json
import os
import unittest

from parser import ComponentParsingError, parse_vendor_file
from src.parser import ComponentParsingError, parse_vendor_file


class TestVendorParser(unittest.TestCase):
    def setUp(self):
        """This runs before every test to create a temporary test file."""
        self.test_filename = "temp_test_export.json"

    def tearDown(self):
        """Clean up the temporary file after each test finishes."""
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_parses_valid_components_correctly(self):
        """Test that normal, well-formed components parse without issues."""
        mock_data = {
            "components": [
                {
                    "comp_id": "R1",
                    "type": "Resistor",
                    "coordinates": {"x": 10.0, "y": 20.0},
                }
            ]
        }
        with open(self.test_filename, "w") as f:
            json.dump(mock_data, f)

        results = parse_vendor_file(self.test_filename)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["component_id"], "R1")
        self.assertEqual(results[0]["y_position"], 20.0)

    def test_handles_missing_y_coordinate_gracefully(self):
        """Test that a missing 'y' coordinate strictly raises a ComponentParsingError."""
        mock_data = {
            "components": [
                {
                    "comp_id": "C1",
                    "type": "Capacitor",
                    "coordinates": {"x": 15.0},  # Missing 'y'
                }
            ]
        }
        with open(self.test_filename, "w") as f:
            json.dump(mock_data, f)

        # Check that an ERROR log occurs AND that the custom exception is raised
        with (
            self.assertLogs(level="ERROR") as log_watcher,
            self.assertRaises(ComponentParsingError),
        ):
            parse_vendor_file(self.test_filename)

        # Check for the exact string formatting from parser.py
        expected_log = "Schema structure failed at index 0: Missing coordinate(s) for component C1 at index 0. No longer parsing the board."

        self.assertTrue(
            any(expected_log in log for log in log_watcher.output),
            f"Expected log message not found in: {log_watcher.output}",
        )

    def test_handles_missing_x_coordinate_gracefully(self):
        """Test that a missing 'x' coordinate strictly raises a ComponentParsingError."""
        mock_data = {
            "components": [
                {
                    "comp_id": "C1",
                    "type": "Capacitor",
                    "coordinates": {"y": 15.0},  # Missing 'x'
                }
            ]
        }
        with open(self.test_filename, "w") as f:
            json.dump(mock_data, f)

        # Check that an ERROR log occurs AND that the custom exception is raised
        with (
            self.assertLogs(level="ERROR") as log_watcher,
            self.assertRaises(ComponentParsingError),
        ):
            parse_vendor_file(self.test_filename)

        # Check for the exact string formatting from parser.py
        expected_log = "Schema structure failed at index 0: Missing coordinate(s) for component C1 at index 0. No longer parsing the board."

        self.assertTrue(
            any(expected_log in log for log in log_watcher.output),
            f"Expected log message not found in: {log_watcher.output}",
        )

    def test_completely_broken_record_skipped(self):
        """Test that records missing an ID entirely are skipped safely."""
        mock_data = {
            "components": [
                {"type": "TestPoint", "coordinates": {"x": 5.0, "y": 5.0}}  # No ID!
            ]
        }
        with open(self.test_filename, "w") as f:
            json.dump(mock_data, f)

        # Verify that an ERROR logger message occurs
        with (
            self.assertLogs(level="ERROR") as log_watcher,
            self.assertRaises(ComponentParsingError),
        ):
            parse_vendor_file(self.test_filename)

        expected_log = "Missing component ID in item at index 0"

        self.assertTrue(
            any(expected_log in log for log in log_watcher.output),
            f"Expected log message not found in: {log_watcher.output}",
        )


if __name__ == "__main__":
    unittest.main()
