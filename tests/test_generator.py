import json
import os
import tempfile
import unittest
from datetime import datetime

from src.generator import generate_vendor_export


class TestGenerator(unittest.TestCase):
    def setUp(self):
        # Sample cleaned components used in multiple tests
        self.sample_components = [
            {"component_id": "R1", "component_type": "Resistor", "x_position": 12.5, "y_position": 45.2},
            {"component_id": "C1", "component_type": "Capacitor", "x_position": 33.1, "y_position": 0.0}
        ]
        
        # Create a temporary file path to write output; tests will remove the file in tearDown
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            self.temp_filepath = tmp.name
            tmp.close()

    def tearDown(self):
        # Ensure no permanent files remain
        if os.path.exists(self.temp_filepath):
            try:
                os.remove(self.temp_filepath)
            except OSError:
                # If removal fails, leave it (the test framework/environment may handle cleanup)
                pass

    def _load_output(self, filepath):
        with open(filepath, 'r') as f:
            return json.load(f)

    def test_output_file_is_created_and_valid_json(self):
        """Generator writes a file and it contains valid JSON."""
        generate_vendor_export(self.sample_components, self.temp_filepath, board_name="Test_Board")
        self.assertTrue(os.path.exists(self.temp_filepath), "Expected output file to exist after generation")
        data = self._load_output(self.temp_filepath)
        self.assertIsInstance(data, dict, "Top-level JSON value should be an object/dict")

    def test_output_contains_expected_top_level_keys(self):
        """Output JSON includes header, board_metadata, and components keys."""
        generate_vendor_export(self.sample_components, self.temp_filepath)
        data = self._load_output(self.temp_filepath)

        # Top-level keys
        self.assertIn("header", data, "Missing 'header' key in export")
        self.assertIn("board_metadata", data, "Missing 'board_metadata' key in export")
        self.assertIn("components", data, "Missing 'components' key in export")

        # Basic checks for header and board_metadata being dicts
        self.assertIsInstance(data["header"], dict, "'header' should be a dictionary")
        self.assertIsInstance(data["board_metadata"], dict, "'board_metadata' should be a dictionary")
        
        # Basic check for components being a list
        self.assertIsInstance(data["components"], list, "'components' should be a list")

    def test_header_metadata_is_correct(self):
            """Test that the header wrapper contains expected metadata and exporter strings."""
            generate_vendor_export(self.sample_components, self.temp_filepath)
            data = self._load_output(self.temp_filepath)

            header = data.get("header", {})
            self.assertIn("exporter", header)
            self.assertIn("schema_version", header)
            
            # Verify specific expected values
            self.assertEqual(header["schema_version"], "2.0")
            self.assertTrue(header["exporter"].startswith("Quilter_AI"))

            # Verify that the date matches today's date dynamically
            expected_date = datetime.now().strftime("%Y-%m-%d")
            self.assertEqual(header["date_exported"], expected_date)

    def test_components_mapped_correctly(self):
        """Each input component is mapped to the vendor structure with expected keys and values."""
        generate_vendor_export(self.sample_components, self.temp_filepath, board_name="MyBoard")
        data = self._load_output(self.temp_filepath)

        components = data.get("components")
        self.assertIsInstance(components, list, "'components' should be a list")
        self.assertEqual(len(components), len(self.sample_components), "Number of components in output should match input")

        # Check mapping for each component
        for src, out in zip(self.sample_components, components):
            # Expected vendor keys: comp_id, type, coordinates with x/y
            self.assertIn("comp_id", out)
            self.assertIn("type", out)
            self.assertIn("coordinates", out)
            coords = out["coordinates"]
            self.assertIn("x", coords)
            self.assertIn("y", coords)

            # Values should match source fields
            self.assertEqual(out["comp_id"], src["component_id"])
            self.assertEqual(out["type"], src["component_type"])
            self.assertEqual(coords["x"], src["x_position"])
            self.assertEqual(coords["y"], src["y_position"])

        # Also assert board_name propagated when provided
        board_meta = data.get("board_metadata", {})
        self.assertEqual(board_meta.get("board_name"), "MyBoard")
        # units default check if present
        self.assertEqual(board_meta.get("units"), "mm")

if __name__ == "__main__":
    unittest.main()