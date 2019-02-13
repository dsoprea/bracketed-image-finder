import unittest
import os
import subprocess
import json

_APP_PATH = os.path.join(os.path.dirname(__file__), '..', '..')
_ASSET_PATH = os.path.join(_APP_PATH, 'tests', 'assets')
_SCRIPT_PATH = os.path.join(_APP_PATH, 'bif', 'resources', 'scripts')
_TOOL_FILEPATH = os.path.join(_SCRIPT_PATH, 'bif_find')


class TestCommand(unittest.TestCase):
    def test_run__text(self):
        cmd = [_TOOL_FILEPATH, _ASSET_PATH]
        raw = subprocess.check_output(cmd)
        actual = raw.decode('utf-8')

        expected = """\
periodic images/DSC08196.JPG images/DSC08197.JPG images/DSC08198.JPG images/DSC08199.JPG images/DSC08200.JPG
periodic images/DSC08201.JPG images/DSC08202.JPG images/DSC08203.JPG images/DSC08204.JPG images/DSC08205.JPG
"""

        self.assertEquals(actual, expected)

    def test_run__json(self):
        cmd = [_TOOL_FILEPATH, '--json', _ASSET_PATH]
        raw = subprocess.check_output(cmd)
        raw = raw.decode('utf-8')

        actual = json.loads(raw)

        expected = [
            {
                'entries': [
                    {'exposure_value': 0.0, 'rel_filepath': 'images/DSC08196.JPG', 'timestamp': '2019-02-13T00:31:50'}, 
                    {'exposure_value': -0.7, 'rel_filepath': 'images/DSC08197.JPG', 'timestamp': '2019-02-13T00:31:50'}, 
                    {'exposure_value': 0.7, 'rel_filepath': 'images/DSC08198.JPG', 'timestamp': '2019-02-13T00:31:50'}, 
                    {'exposure_value': -1.3, 'rel_filepath': 'images/DSC08199.JPG', 'timestamp': '2019-02-13T00:31:50'}, 
                    {'exposure_value': 1.3, 'rel_filepath': 'images/DSC08200.JPG', 'timestamp': '2019-02-13T00:31:51'}
                ], 
                'type': 'periodic'
            }, {
                'entries': [
                    {'exposure_value': 0.0, 'rel_filepath': 'images/DSC08201.JPG', 'timestamp': '2019-02-13T00:32:09'}, 
                    {'exposure_value': -0.7, 'rel_filepath': 'images/DSC08202.JPG', 'timestamp': '2019-02-13T00:32:09'}, 
                    {'exposure_value': 0.7, 'rel_filepath': 'images/DSC08203.JPG', 'timestamp': '2019-02-13T00:32:10'}, 
                    {'exposure_value': -1.3, 'rel_filepath': 'images/DSC08204.JPG', 'timestamp': '2019-02-13T00:32:10'}, 
                    {'exposure_value': 1.3, 'rel_filepath': 'images/DSC08205.JPG', 'timestamp': '2019-02-13T00:32:10'}
                ], 
                'type': 'periodic'
            }
        ]

        self.assertEquals(actual, expected)
