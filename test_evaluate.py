import json
import os
import shutil
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from evaluate import run_batch_evaluation


class TestEvaluator(unittest.TestCase):
    
    def setUp(self):
        """Creates a secure, temporary directory before each test runs."""
        # tempfile.mkdtemp() creates a unique, empty folder in your OS temp directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Recursively deletes the temporary directory and all files inside it."""
        # shutil.rmtree removes the directory and everything it contains safely
        shutil.rmtree(self.test_dir)

    def test_all_files_pass(self):
        """ Generates 3 files using sample happy-path data and checks the total, pass, and fail via the stdout """
        mock_happy_data = {
            "components": [{
                "comp_id": "R1",
                "type": "Resistor",
                "coordinates": {"x": 12.5, "y": 45.2}
            }]
        }
        
        # create file 1
        path1 = os.path.join(self.test_dir, "board1_export.json")
        with open(path1, "w") as f:
            json.dump(mock_happy_data, f)
        
        # create file 2
        path2 = os.path.join(self.test_dir, "board2_export.json")
        with open(path2, "w") as f:
            json.dump(mock_happy_data, f)
            
        # create file 3
        path3 = os.path.join(self.test_dir, "board3_export.json")
        with open(path3, "w") as f:
            json.dump(mock_happy_data, f)
        
        # intercept the messages printed to the console using StringIO text buffer
        with patch('sys.stdout', new=StringIO()) as fake_output:
            
            # check the summary results from the evaluation script
            run_batch_evaluation(self.test_dir)
        
            # grab the full text printout as a string
            console_output = fake_output.getvalue()
        
        self.assertIn("Total Files Processed : 3", console_output)
        self.assertIn("Successfully Parsed   : 3", console_output)
        self.assertIn("Rejected / Failed     : 0", console_output)

    def test_empty_folder(self):
        """ Giving the evaluator an empty folder will not crash the script and 
            will result in a logger.WARNING with its associated message """
        empty_folder = os.path.join(self.test_dir, 'empty_subfolder')
        os.mkdir(empty_folder)
        with self.assertLogs(level="WARNING") as log_watcher:
            run_batch_evaluation(empty_folder)
        
        self.assertTrue(
            any("No JSON files found in" in log for log in log_watcher.output),
            f"Expected error message not found in logs. Captured logs: {log_watcher.output}"
        )
    
    def test_missing_folder(self):
        """ Tests the evaluator against a non-existent file path. Assert that a log.ERROR occurs with its expected message. """
        non_existent_directory = "non_existent"
        with self.assertLogs(level="ERROR") as log_watcher:
            run_batch_evaluation(non_existent_directory)
        
        self.assertTrue(
            any("Data directory does not exist" in log for log in log_watcher.output),
            f"Expected error message not found in logs. Captured logs: {log_watcher.output}"
        )

    def test_mixed_case(self):
        """ Test the evaluator against several types of possible conditions:
            happy path data, missing coordinates in the json body, 
            malformed json body, and a non-json file in the source folder """
        file_1_happy_data = {
            "components": [{
                "comp_id": "R1",
                "type": "Resistor",
                "coordinates": {"x": 12.5, "y": 45.2}
            }]
        }
        
        file_2_missing_coords_data = {
            "components": [{
                "comp_id": "R1",
                "type": "Resistor",
                "coordinates": {}
            }]
        }
        
        file_3_broken_json_missing_bracket = """{
            "components": [
                "comp_id": "R1",
                "type": "Resistor",
                "coordinates": {"x": 12.5, "y": 45.2}
            }]
        }"""
        
        # create file 1
        path1 = os.path.join(self.test_dir, "board1_export.json")
        with open(path1, "w") as f:
            json.dump(file_1_happy_data, f)
        
        # create file 2
        path2 = os.path.join(self.test_dir, "board2_export.json")
        with open(path2, "w") as f:
            json.dump(file_2_missing_coords_data, f)
            
        # create file 3
        path3 = os.path.join(self.test_dir, "board3_export.json")
        with open(path3, "w") as f:
            f.write(file_3_broken_json_missing_bracket)
        
        # create file 4
        path4 = os.path.join(self.test_dir, "board4_export.json")
        with open(path4, "w") as f:
            pass

        # create file notes.txt
        path5 = os.path.join(self.test_dir, 'notes.txt')
        with open(path5, "w") as f:
            pass

        # intercept the messages printed to the console using StringIO text buffer
        with patch('sys.stdout', new=StringIO()) as fake_output:
            
            # check the summary results from the evaluation script
            run_batch_evaluation(self.test_dir)
        
            # grab the full text printout as a string
            console_output = fake_output.getvalue()
        
        self.assertIn("Total Files Processed : 4", console_output)
        self.assertIn("Successfully Parsed   : 1", console_output)
        self.assertIn("Rejected / Failed     : 3", console_output)
