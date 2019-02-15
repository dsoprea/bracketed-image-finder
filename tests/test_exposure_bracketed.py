import unittest
import os
import datetime

import bif.exposure_bracketed

_ASSET_PATH = os.path.join(os.path.dirname(__file__), 'assets')


class TestExposureBracketedAnalysis(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = None
        super(TestExposureBracketedAnalysis, self).__init__(*args, **kwargs)

    def test_is_float_equal__hit(self):
        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        self.assertTrue(ba._is_float_equal(0.1, 0.1))
        self.assertTrue(ba._is_float_equal(0.0001, 0.0001))

    def test_is_float_equal__miss(self):
        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        self.assertFalse(ba._is_float_equal(0.1, 0.2))

    def test_check_for_periodic_bracketing_at_tail__5(self):
        now = datetime.datetime.now()

        history = [
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='aa', timestamp=now, exposure_value=1),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='bb', timestamp=now, exposure_value=2),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='cc', timestamp=now, exposure_value=0),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='dd', timestamp=now, exposure_value=-.7),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='ee', timestamp=now, exposure_value=.7),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='ff', timestamp=now, exposure_value=-1.4),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='gg', timestamp=now, exposure_value=1.4),
        ]

        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        actual_bi = ba._check_for_periodic_bracketing_at_tail(history)
        expected_bi = \
            bif.exposure_bracketed._BRACKET_INFO(
                size=5,
                type=bif.exposure_bracketed.BT_PERIODIC,
                sequence=history[-5:])

        self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

    def test_check_for_sequential_bracketing_at_tail__5(self):
        now = datetime.datetime.now()

        history = [
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='aa', timestamp=now, exposure_value=1),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='bb', timestamp=now, exposure_value=2),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='ff', timestamp=now, exposure_value=-1.4),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='dd', timestamp=now, exposure_value=-.7),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='cc', timestamp=now, exposure_value=0),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='ee', timestamp=now, exposure_value=.7),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='gg', timestamp=now, exposure_value=1.4),
        ]

        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        actual_bi = ba._check_for_sequential_bracketing_at_tail(history)
        expected_bi = \
            bif.exposure_bracketed._BRACKET_INFO(
                size=5,
                type=bif.exposure_bracketed.BT_SEQUENTIAL,
                sequence=history[-5:])

        self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

    def test_check_for_periodic_bracketing_at_tail__3(self):
        now = datetime.datetime.now()

        history = [
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='aa', timestamp=now, exposure_value=1),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='bb', timestamp=now, exposure_value=2),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='cc', timestamp=now, exposure_value=0),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='dd', timestamp=now, exposure_value=-.7),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='ee', timestamp=now, exposure_value=.7),
        ]

        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        actual_bi = ba._check_for_periodic_bracketing_at_tail(history)

        expected_bi = \
            bif.exposure_bracketed._BRACKET_INFO(
                size=3,
                type=bif.exposure_bracketed.BT_PERIODIC,
                sequence=history[-3:])

        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

    def test_check_for_sequential_bracketing_at_tail__3(self):
        now = datetime.datetime.now()

        history = [
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='aa', timestamp=now, exposure_value=1),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='bb', timestamp=now, exposure_value=2),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='dd', timestamp=now, exposure_value=-.7),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='cc', timestamp=now, exposure_value=0),
            bif.exposure_bracketed._HISTORY_ITEM(rel_filepath='ee', timestamp=now, exposure_value=.7),
        ]

        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        actual_bi = ba._check_for_sequential_bracketing_at_tail(history)
        expected_bi = \
            bif.exposure_bracketed._BRACKET_INFO(
                size=3,
                type=bif.exposure_bracketed.BT_SEQUENTIAL,
                sequence=history[-3:])

        self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

    def test_read_image_metadata(self):
        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()

        filepath = os.path.join(_ASSET_PATH, 'images', 'DSC08198.JPG')
        metadata = ba._read_image_metadata(filepath)

        self.assertEquals(metadata['exposure_value'], 0.70)

    def test_find_bracketed_images(self):
        root_path = os.path.join(_ASSET_PATH, 'images')

        ba = bif.exposure_bracketed.ExposureBracketedAnalysis()
        groups_raw = ba.find_bracketed_images(root_path)

        actual = []
        for type_, entries in groups_raw:
            files = [hi.rel_filepath for hi in entries]
            actual.append((type_, files))

        actual = sorted(actual)

        expected = [
            ('periodic', ['DSC08196.JPG', 'DSC08197.JPG', 'DSC08198.JPG', 'DSC08199.JPG', 'DSC08200.JPG']),
            ('periodic', ['DSC08201.JPG', 'DSC08202.JPG', 'DSC08203.JPG', 'DSC08204.JPG', 'DSC08205.JPG']),
        ]

        self.assertEquals(actual, expected)
