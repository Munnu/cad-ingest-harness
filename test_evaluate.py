import json
import os
import unittest

from evaluate import run_batch_evaluation

class TestEvaluator(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    # test case 1: Happy Path
    # generate 3 files that are perfectly fine where all pass
    # assert check the total files, number of pass cases, number of fail cases
    
    # test case 2: Empty Folder
    # create an empty folder
    # outcome: script should not crash, 
    # but should generate a logger.WARNING saying "No JSON files found"
    
    # test case 3: Missing Folder
    # pass in s a path that does not exist
    # script should not crash
    # assert check logger.ERROR message containing "Data directory does not exist"
    
    # test case 4: mixed case
    # generate 5 files that are mixed
    #   file 1: perfectly formatted (pass)
    #   file 2: missing coordinates (fail - ComponentParsingError)
    #   file 3: broken JSON syntax, like a missing trailing brakcet (fail - JSONDecodeError)
    #   file 4: random text file named notes.txt (Should be ignored by the scanner)
    #   file 5: empty json file that has the *_export.json format (generate a logger.ERROR containing 'Rejected due to malformed data')
    #           it will also throw a ValueError
    # also check that there are 4 total files, 1 passed cases, 3 failed cases (notes.txt gets ignored)
