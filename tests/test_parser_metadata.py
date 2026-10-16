"""Tests for board metadata validation in src.parser."""

import json
import os
import unittest

from src.parser import BoardParsingError, parse_vendor_file


class TestBoardMetadataParser(unittest.TestCase):
    def setUp(self):
        self.test_filename = "temp_test_metadata.json"

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def _parse_with_board_metadata(self, board_metadata):
        """Write a complete test export with the supplied board metadata."""
        mock_data = {
            "board_metadata": board_metadata,
            "components": [
                {
                    "comp_id": "R1",
                    "type": "Resistor",
                    "coordinates": {"x": 10.0, "y": 20.0},
                }
            ],
        }
        with open(self.test_filename, "w", encoding="utf-8") as file:
            json.dump(mock_data, file, ensure_ascii=False)
        return parse_vendor_file(self.test_filename)

    def test_board_name_missing(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"units": "mm"})

    def test_board_name_none(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"board_name": None, "units": "mm"})

    def test_board_name_only_whitespace(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"board_name": "   ", "units": "mm"})

    def test_board_name_empty_string(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"board_name": "", "units": "mm"})

    def test_board_name_wrong_datatype(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"board_name": 12345, "units": "mm"})

    def test_board_name_preserves_surrounding_whitespace(self):
        results = self._parse_with_board_metadata(
            {"board_name": "     Test_Board     ", "units": "mm"}
        )
        self.assertEqual(
            results["board_metadata"]["board_name"],
            "     Test_Board     ",
        )

    def test_board_units_missing(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"board_name": "Test_Board"})

    def test_board_units_unsupported(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata(
                {"board_name": "Test_Board", "units": "lbs"}
            )

    def test_board_units_wrong_datatype(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"board_name": "Test_Board", "units": 123})

    def test_board_units_none(self):
        with self.assertRaisesRegex(BoardParsingError, "Invalid board metadata"):
            self._parse_with_board_metadata({"board_name": "Test_Board", "units": None})

    def test_accepts_every_supported_board_unit(self):
        supported_units = ["mm", "µm", "mil", "in"]
        for unit in supported_units:
            with self.subTest(unit=unit):
                results = self._parse_with_board_metadata(
                    {"board_name": "Test_Board", "units": unit}
                )
                self.assertEqual(results["board_metadata"]["units"], unit)


if __name__ == "__main__":
    unittest.main()
