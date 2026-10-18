"""Tests for generating vendor-compatible EDA export files."""

import json
import os
import tempfile
import unittest
from datetime import date

from src.generator import generate_vendor_export


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.sample_data = {
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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_filepath = os.path.join(self.temp_dir.name, "vendor_export.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _load_output(self):
        with open(self.temp_filepath, "r", encoding="utf-8") as file:
            return json.load(file)

    def _generate(self, data=None):
        generate_vendor_export(
            self.sample_data if data is None else data,
            self.temp_filepath,
        )

    def test_output_file_is_created_and_valid_json(self):
        self._generate()
        self.assertTrue(os.path.isfile(self.temp_filepath))
        self.assertIsInstance(self._load_output(), dict)

    def test_output_contains_expected_top_level_keys(self):
        self._generate()
        data = self._load_output()
        self.assertEqual(set(data), {"header", "board_metadata", "components"})
        self.assertIsInstance(data["header"], dict)
        self.assertIsInstance(data["board_metadata"], dict)
        self.assertIsInstance(data["components"], list)

    def test_generated_header_has_expected_fields(self):
        self._generate()
        header = self._load_output()["header"]

        # check if the header has exactly these specific keys, nothing more
        self.assertEqual(set(header), {"exporter", "schema_version", "date_exported"})

        self.assertEqual(header["exporter"], "Quilter_AI_FileIO_v1.0")
        self.assertEqual(header["schema_version"], "2.0")
        self.assertEqual(
            date.fromisoformat(header["date_exported"]).isoformat(),
            header["date_exported"],
        )

    def test_header_metadata_is_correct(self):
        self._generate()
        header = self._load_output()["header"]
        self.assertEqual(header["exporter"], "Quilter_AI_FileIO_v1.0")
        self.assertEqual(header["schema_version"], "2.0")
        self.assertEqual(header["date_exported"], date.today().isoformat())

    def test_board_metadata_is_preserved(self):
        self._generate()
        metadata = self._load_output()["board_metadata"]
        self.assertEqual(metadata["board_name"], "Power_Distribution_RevA")
        self.assertEqual(metadata["units"], "mm")

    def test_components_are_mapped_correctly(self):
        self._generate()
        output_components = self._load_output()["components"]
        self.assertEqual(len(output_components), len(self.sample_data["components"]))

        for source, output in zip(self.sample_data["components"], output_components):
            self.assertEqual(output["comp_id"], source["component_id"])
            self.assertEqual(output["type"], source["component_type"])
            self.assertEqual(output["coordinates"]["x"], source["x_position"])
            self.assertEqual(output["coordinates"]["y"], source["y_position"])

    def test_optional_eda_fields_are_preserved(self):
        self._generate()
        component = self._load_output()["components"][0]
        self.assertEqual(component["value"], "10k_ohm")
        self.assertEqual(component["package"], "0805")
        self.assertEqual(component["pins"], ["1", "2"])

    def test_missing_optional_fields_are_omitted(self):
        self._generate()
        component = self._load_output()["components"][1]
        self.assertNotIn("value", component)
        self.assertNotIn("package", component)
        self.assertNotIn("pins", component)

    def test_supported_board_units_are_preserved(self):
        for unit in ("mm", "µm", "mil", "in"):
            with self.subTest(unit=unit):
                data = {
                    **self.sample_data,
                    "board_metadata": {
                        **self.sample_data["board_metadata"],
                        "units": unit,
                    },
                }
                self._generate(data)
                output = self._load_output()
                self.assertEqual(output["board_metadata"]["units"], unit)
                self.assertEqual(output["components"][0]["coordinates"]["x"], 12.5)

    def test_non_dictionary_input_raises_type_error(self):
        with self.assertRaises(TypeError):
            self._generate([])

    def test_missing_board_metadata_raises_type_error(self):
        with self.assertRaises(TypeError):
            self._generate({"components": self.sample_data["components"]})

    def test_unsupported_units_raise_value_error(self):
        data = {
            **self.sample_data,
            "board_metadata": {"board_name": "Test_Board", "units": "yards"},
        }
        with self.assertRaises(ValueError):
            self._generate(data)

    def test_empty_components_raise_value_error(self):
        with self.assertRaises(ValueError):
            self._generate({**self.sample_data, "components": []})

    def test_invalid_coordinate_raises_value_error(self):
        data = {
            **self.sample_data,
            "components": [
                {
                    "component_id": "R1",
                    "component_type": "Resistor",
                    "x_position": float("inf"),
                    "y_position": 10.0,
                }
            ],
        }
        with self.assertRaises(ValueError):
            self._generate(data)

    def test_duplicate_component_ids_raise_value_error(self):
        data = {
            **self.sample_data,
            "components": [
                {
                    "component_id": "R1",
                    "component_type": "Resistor",
                    "x_position": 1.0,
                    "y_position": 2.0,
                },
                {
                    "component_id": "r1",
                    "component_type": "Resistor",
                    "x_position": 3.0,
                    "y_position": 4.0,
                },
            ],
        }
        with self.assertRaisesRegex(ValueError, "Duplicate component ID"):
            self._generate(data)


if __name__ == "__main__":
    unittest.main()
