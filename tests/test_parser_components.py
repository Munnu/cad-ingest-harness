"""Tests for component validation in src.parser."""

import json
import os
import unittest

from src.parser import BoardParsingError, parse_vendor_file


class TestBoardComponentsParser(unittest.TestCase):
    def setUp(self):
        self.test_filename = "temp_test_components.json"

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def _parse_with_components(self, components):
        """Write a complete test export with the supplied component list."""
        mock_data = {
            "board_metadata": {
                "board_name": "Test_Board",
                "units": "mm",
            },
            "components": components,
        }
        with open(self.test_filename, "w", encoding="utf-8") as file:
            json.dump(mock_data, file)
        return parse_vendor_file(self.test_filename)

    def test_parses_valid_component(self):
        results = self._parse_with_components(
            [
                {
                    "comp_id": "R1",
                    "type": "Resistor",
                    "coordinates": {"x": 10.0, "y": 20.0},
                }
            ]
        )
        components = results["components"]
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0]["component_id"], "R1")
        self.assertEqual(components[0]["component_type"], "Resistor")
        self.assertEqual(components[0]["x_position"], 10.0)
        self.assertEqual(components[0]["y_position"], 20.0)

    def test_accepts_legacy_component_id_and_type_keys(self):
        results = self._parse_with_components(
            [
                {
                    "id": "C1",
                    "part_type": "Capacitor",
                    "coordinates": {"x": 15.0, "y": 25.0},
                }
            ]
        )
        component = results["components"][0]
        self.assertEqual(component["component_id"], "C1")
        self.assertEqual(component["component_type"], "Capacitor")

    def test_missing_y_coordinate_rejects_board(self):
        with self.assertRaisesRegex(BoardParsingError, "Missing coordinate"):
            self._parse_with_components(
                [
                    {
                        "comp_id": "C1",
                        "type": "Capacitor",
                        "coordinates": {"x": 15.0},
                    }
                ]
            )

    def test_missing_x_coordinate_rejects_board(self):
        with self.assertRaisesRegex(BoardParsingError, "Missing coordinate"):
            self._parse_with_components(
                [
                    {
                        "comp_id": "C1",
                        "type": "Capacitor",
                        "coordinates": {"y": 15.0},
                    }
                ]
            )

    def test_missing_component_id_rejects_board(self):
        with self.assertRaisesRegex(
            BoardParsingError, "Missing or invalid component ID"
        ):
            self._parse_with_components(
                [{"type": "TestPoint", "coordinates": {"x": 5.0, "y": 5.0}}]
            )

    def test_invalid_coordinate_type_rejects_board(self):
        with self.assertRaises(BoardParsingError):
            self._parse_with_components(
                [
                    {
                        "comp_id": "R1",
                        "type": "Resistor",
                        "coordinates": {"x": "not-a-number", "y": 20.0},
                    }
                ]
            )

    def test_empty_components_list_is_rejected(self):
        # The current parser raises ValueError directly for an empty list.
        with self.assertRaises(ValueError):
            self._parse_with_components([])

    def test_preserves_optional_eda_fields(self):
        results = self._parse_with_components(
            [
                {
                    "comp_id": "R1",
                    "type": "Resistor",
                    "value": "10k_ohm",
                    "package": "0805",
                    "coordinates": {"x": 12.5, "y": 45.2},
                    "pins": ["1", "2"],
                }
            ]
        )

        component = results["components"][0]
        self.assertEqual(component["value"], "10k_ohm")
        self.assertEqual(component["package"], "0805")
        self.assertEqual(component["pins"], ["1", "2"])

    def test_missing_component_type_rejects_board(self):
        with self.assertRaisesRegex(BoardParsingError, "component type"):
            self._parse_with_components(
                [
                    {
                        "comp_id": "R1",
                        "coordinates": {"x": 10, "y": 20},
                    }
                ]
            )

    def test_duplicate_component_ids_reject_board(self):
        with self.assertRaisesRegex(BoardParsingError, "Duplicate component ID"):
            self._parse_with_components(
                [
                    {
                        "comp_id": "R1",
                        "type": "Resistor",
                        "coordinates": {"x": 10, "y": 20},
                    },
                    {
                        "comp_id": "r1",
                        "type": "Resistor",
                        "coordinates": {"x": 30, "y": 40},
                    },
                ]
            )

    def test_rejects_non_finite_coordinates(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid x coordinate"):
            self._parse_with_components(
                [
                    {
                        "comp_id": "R1",
                        "type": "Resistor",
                        "coordinates": {"x": float("inf"), "y": 20},
                    }
                ]
            )

    def test_rejects_invalid_pins(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid pins"):
            self._parse_with_components(
                [
                    {
                        "comp_id": "R1",
                        "type": "Resistor",
                        "coordinates": {"x": 10, "y": 20},
                        "pins": "1,2",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
