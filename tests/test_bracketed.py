import unittest
import os
import datetime

import bif.bracketed

_ASSET_PATH = os.path.join(os.path.dirname(__file__), 'assets')


class TestBracketed(unittest.TestCase):
	def test_sequence_matches__hit_exact(self):
		seq1 = [1.0, 2.0, 3.0, 4.0, 5.0]
		seq2 = [1.0, 2.0, 3.0, 4.0, 5.0]

		ba = bif.bracketed.BracketedAnalysis()
		self.assertTrue(ba._sequence_matches(seq1, seq2))

	def test_sequence_matches__hit__within_precision(self):
		seq1 = [1.0, 2.0, 3.0, 4.0, 5.0]
		seq2 = [1.0, 2.0, 3.000001, 4.0, 5.000001]

		ba = bif.bracketed.BracketedAnalysis()
		self.assertTrue(ba._sequence_matches(seq1, seq2))

	def test_sequence_matches__miss(self):
		seq1 = [1.0, 2.0, 3.0, 4.2, 5.0]
		seq2 = [1.0, 2.0, 3.000001, 4.0, 5.000001]

		ba = bif.bracketed.BracketedAnalysis()
		self.assertFalse(ba._sequence_matches(seq1, seq2))

	def test_is_float_equal__hit(self):
		ba = bif.bracketed.BracketedAnalysis()
		self.assertTrue(ba._is_float_equal(0.1, 0.1))
		self.assertTrue(ba._is_float_equal(0.0001, 0.0001))

	def test_is_float_equal__miss(self):
		ba = bif.bracketed.BracketedAnalysis()
		self.assertFalse(ba._is_float_equal(0.1, 0.2))

	def test_get_accepted_exposure_sequence_dot7_5(self):
		history = [bif.bracketed._HISTORY_ITEM(exposure_value=0, timestamp=None, filepath=None)] * 5
		
		ba = bif.bracketed.BracketedAnalysis()
		actual_sequences = ba._get_accepted_exposure_sequence(history, .7, 5)
		self.assertEquals(len(actual_sequences), 2)

		expected_sequences = [
			[0, -0.7, 0.7, -1.4, 1.4], 
			[-1.4, -0.7, 0.0, 0.6999999999999997, 1.4],
		]

		self.assertTrue(ba._sequence_matches(actual_sequences[0], expected_sequences[0]))
		self.assertTrue(ba._sequence_matches(actual_sequences[1], expected_sequences[1]))

	def test_find_bracketing_sequence_at_tail__5__oscillating(self):
		now = datetime.datetime.now()

		history = [
			bif.bracketed._HISTORY_ITEM(filepath='aa', timestamp=now, exposure_value=1),
			bif.bracketed._HISTORY_ITEM(filepath='bb', timestamp=now, exposure_value=2),
			bif.bracketed._HISTORY_ITEM(filepath='cc', timestamp=now, exposure_value=0),
			bif.bracketed._HISTORY_ITEM(filepath='dd', timestamp=now, exposure_value=-.7),
			bif.bracketed._HISTORY_ITEM(filepath='ee', timestamp=now, exposure_value=.7),
			bif.bracketed._HISTORY_ITEM(filepath='ff', timestamp=now, exposure_value=-1.4),
			bif.bracketed._HISTORY_ITEM(filepath='gg', timestamp=now, exposure_value=1.4),
		]

		ba = bif.bracketed.BracketedAnalysis()
		actual_bi = ba._find_bracketing_sequence_at_tail(history)
		expected_bi = \
			bif.bracketed._BRACKET_INFO(
				size=5, 
				exposure_delta=0.7, 
				sequence=[0, -0.7, 0.7, -1.4, 1.4])

		self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

	def test_find_bracketing_sequence_at_tail__5__increasing(self):
		now = datetime.datetime.now()

		history = [
			bif.bracketed._HISTORY_ITEM(filepath='aa', timestamp=now, exposure_value=1),
			bif.bracketed._HISTORY_ITEM(filepath='bb', timestamp=now, exposure_value=2),
			bif.bracketed._HISTORY_ITEM(filepath='ff', timestamp=now, exposure_value=-1.4),
			bif.bracketed._HISTORY_ITEM(filepath='dd', timestamp=now, exposure_value=-.7),
			bif.bracketed._HISTORY_ITEM(filepath='cc', timestamp=now, exposure_value=0),
			bif.bracketed._HISTORY_ITEM(filepath='ee', timestamp=now, exposure_value=.7),
			bif.bracketed._HISTORY_ITEM(filepath='gg', timestamp=now, exposure_value=1.4),
		]

		ba = bif.bracketed.BracketedAnalysis()
		actual_bi = ba._find_bracketing_sequence_at_tail(history)
		expected_bi = \
			bif.bracketed._BRACKET_INFO(
				size=5, 
				exposure_delta=0.7, 
				sequence=[-1.4, -0.7, 0, 0.7, 1.4])

		self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

	def test_find_bracketing_sequence_at_tail__3__oscillating(self):
		now = datetime.datetime.now()

		history = [
			bif.bracketed._HISTORY_ITEM(filepath='aa', timestamp=now, exposure_value=1),
			bif.bracketed._HISTORY_ITEM(filepath='bb', timestamp=now, exposure_value=2),
			bif.bracketed._HISTORY_ITEM(filepath='cc', timestamp=now, exposure_value=0),
			bif.bracketed._HISTORY_ITEM(filepath='dd', timestamp=now, exposure_value=-.7),
			bif.bracketed._HISTORY_ITEM(filepath='ee', timestamp=now, exposure_value=.7),
		]

		ba = bif.bracketed.BracketedAnalysis()
		actual_bi = ba._find_bracketing_sequence_at_tail(history)
		expected_bi = \
			bif.bracketed._BRACKET_INFO(
				size=3, 
				exposure_delta=0.7, 
				sequence=[0, -0.7, 0.7])

		ba = bif.bracketed.BracketedAnalysis()
		self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

	def test_find_bracketing_sequence_at_tail__3__increasing(self):
		now = datetime.datetime.now()

		history = [
			bif.bracketed._HISTORY_ITEM(filepath='aa', timestamp=now, exposure_value=1),
			bif.bracketed._HISTORY_ITEM(filepath='bb', timestamp=now, exposure_value=2),
			bif.bracketed._HISTORY_ITEM(filepath='dd', timestamp=now, exposure_value=-.7),
			bif.bracketed._HISTORY_ITEM(filepath='cc', timestamp=now, exposure_value=0),
			bif.bracketed._HISTORY_ITEM(filepath='ee', timestamp=now, exposure_value=.7),
		]

		ba = bif.bracketed.BracketedAnalysis()
		actual_bi = ba._find_bracketing_sequence_at_tail(history)
		expected_bi = \
			bif.bracketed._BRACKET_INFO(
				size=3, 
				exposure_delta=0.7, 
				sequence=[-0.7, 0, 0.7])

		self.assertTrue(ba._bracketinfo_matches(actual_bi, expected_bi))

	def test_read_tag(self):
		filepath = os.path.join(_ASSET_PATH, 'images', 'DSC08191.JPG')
		ba = bif.bracketed.BracketedAnalysis()
		value = ba._read_tag(filepath, bif.bracketed._EXPOSURE_TAG_ID)

		self.assertEquals(value, '2.97 EV (f/2.8)')

	def test_get_exposure(self):
		filepath = os.path.join(_ASSET_PATH, 'images', 'DSC08191.JPG')
		
		ba = bif.bracketed.BracketedAnalysis()
		exposure_value = ba._get_exposure(filepath)

		self.assertEquals(exposure_value, 2.97)

	def test_find_bracketed_images(self):
		root_path = os.path.join(_ASSET_PATH, 'images')
		
		ba = bif.bracketed.BracketedAnalysis()
		groups = ba.find_bracketed_images(root_path)

		for exposure_delta, entries in groups:
			print(exposure_delta)
			print([hi.filepath for hi in entries])
			print('')
