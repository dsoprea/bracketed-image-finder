import logging
import os
import subprocess
import re
import collections
import fnmatch

import dateutil.parser

_EXPOSURE_TAG_ID = 0x9204
_EXPOSURE_MODE_TAG_ID = 0xa402
_DATETIME_TAG_ID = 0x0132

_SONY_BRACKETING_EXPOSURE_MODE = 'Auto bracket'

# Example: 2.97 EV (f/2.8)
_EXPOSURE_VALUE_RE = re.compile(r'(\-?[0-9]*(\.[0-9]+)?) EV')

_TAG_NOT_FOUND_ERROR = 1

# The various number of images produced by complete bracketing processes. 
# - These must be odd.
# - These must be in descending order (to make sure that any larger sequences 
#   that might contain smaller sequences are allowed to match first).
_BRACKETING_SEQUENCE_SIZES = (7, 5, 3)
_MAX_BRACKET_SIZE = max(_BRACKETING_SEQUENCE_SIZES)

# The maximum amount of time a sequence should've been captured in.
_MAX_ALLOW_SEQUENCE_DURATION_S = 3

_LOGGER = logging.getLogger(__name__)

_HISTORY_ITEM = \
	collections.namedtuple(
		'_HISTORY_ITEM', [
			'filepath',
			'exposure_value',
			'timestamp',
		])

_BRACKET_INFO = \
	collections.namedtuple(
		'_BRACKET_INFO', [
			'size',
			'exposure_delta',
			'sequence',
		])


class TagNotFoundException(Exception):
	def __init__(self, tag_id):
		self.__tag_id = tag_id

		message = "Tag ({:02x}) not found.".format(tag_id)
		super(TagNotFoundException, self).__init__(message)

	@property
	def tag_id(self):
		return self.__tag_id
	

class BracketedAnalysis(object):
	def _read_tag(self, filepath, tag_id):
		cmd = ['exif', filepath, '--tag', hex(tag_id), '--machine-readable']

		try:
			output = subprocess.check_output(cmd)
		except subprocess.CalledProcessError as e:
			if e.returncode != _TAG_NOT_FOUND_ERROR:
				raise
		else:
			return output.decode('utf-8').strip()

		# If we get here, the tag was not found.
		raise TagNotFoundException(tag_id)

	def _get_exposure(self, filepath):
		exposure_value = self._read_tag(filepath, _EXPOSURE_TAG_ID)

		# Expecting something like "-0.70 EV".
		m = _EXPOSURE_VALUE_RE.match(exposure_value)

		assert \
			m is not None, \
			"Exposure value [{}] doesn't look right.".format(exposure_value)

		return float(m.group(1))

	def _is_float_equal(self, a, b):
		"""Account for epsilon."""

		return abs(a - b) < 0.0001

	def _find_bracketing_sequence_at_tail(self, history):
		len_ = len(history)
		for expected_size in _BRACKETING_SEQUENCE_SIZES:
			assert \
				expected_size % 2 == 1, \
				"Bracketing sequences sizes must be odd: ({})".format(
				expected_size)

			if len_ <= expected_size:
				continue

			last_n_entries = history[-expected_size:]

			sequence_duration_td = \
				last_n_entries[-1].timestamp - last_n_entries[0].timestamp

			sequence_duration_s = int(sequence_duration_td.total_seconds())
			if sequence_duration_s > _MAX_ALLOW_SEQUENCE_DURATION_S:
				continue

			# For bracketed images:
			#
			# - The absolute difference between image exposures will be the same.
			# - The polarity oscillation will fit one of two patterns: 0,-,+ or -,0,+

			sequence_exposure_delta = \
				abs(last_n_entries[0].exposure_value - last_n_entries[1].exposure_value)
			
			# No exposure difference between the two adjacent images.
			if self._is_float_equal(sequence_exposure_delta, 0.0) is True:
				continue

			# Check if the polarity oscillation matches a known pattern.
			sequences = \
				self._get_accepted_exposure_sequence(
					last_n_entries,
					sequence_exposure_delta, 
					expected_size)

			current_sequence = [hi.exposure_value for hi in last_n_entries]
			for accepted_sequence in sequences:
				if self._sequence_matches(current_sequence, accepted_sequence) is True:
					return \
						_BRACKET_INFO(
							size=expected_size, 
							exposure_delta=sequence_exposure_delta,
							sequence=accepted_sequence)

	def _sequence_matches(self, sequence1, sequence2):
		len1 = len(sequence1)
		len2 = len(sequence2)

		assert \
			len1 == len2, \
			"Sequences are not the same length: ({}) != ({})".format(len1, len2)

		for i, x in enumerate(sequence1):
			if self._is_float_equal(x, sequence2[i]) is False:
				return False

		return True


	def _get_accepted_exposure_sequence(self, last_n_entries, exposure_delta, n):
		sequences = []


		# Build for 0,-,+.

		origin_exposure_value = last_n_entries[0].exposure_value

		sequence = [origin_exposure_value]
		steps = (n - 1) // 2
		current_step = 1
		for _ in range(steps):
			sequence.append(origin_exposure_value - exposure_delta * current_step)
			sequence.append(origin_exposure_value + exposure_delta * current_step)

			current_step += 1

		sequences.append(sequence)


		# Build for -,0,+.

		periods = (n - 1) // 2

		# The origin is in the middle, so reuse the value of `period`.
		origin_exposure_value = last_n_entries[periods].exposure_value

		start = origin_exposure_value - exposure_delta * periods

		sequence = [
			(start + exposure_delta * i) for i in range(n)
		]

		sequences.append(sequence)

		return sequences


	def find_bracketed_images(self, root_path):
		_HISTORY = []
		for path, folders, files in os.walk(root_path):
			# We depend on the files`being sorted and we use that sorting the files 
			# will be them in sequence of when they were created. We do not handle 
			# rollover in the numbering.

			files = sorted(files)

			for filename in files:
				if fnmatch.fnmatch(filename.lower(), '*.jpg') is False:
					continue

				filepath = os.path.join(path, filename)

				try:
					exposure_mode_value = self._read_tag(filepath, _EXPOSURE_MODE_TAG_ID)

					# Only Sony bracketing supported at this time (for lack of 
					# information on implementation by other brands).
					if exposure_mode_value != _SONY_BRACKETING_EXPOSURE_MODE:
						continue

					exposure_value = self._get_exposure(filepath)

					timestamp_raw = self._read_tag(filepath, _DATETIME_TAG_ID)
					timestamp = dateutil.parser.parse(timestamp_raw)
				except TagNotFoundException:
					continue
				except AssertionError as e:
					_LOGGER.exception("Validation issue: [{}]".format(filepath))
					continue

				# We definitely have a picture that was involved in bracketing.
				
				hi = _HISTORY_ITEM(
						filepath=filepath, 
						exposure_value=exposure_value, 
						timestamp=timestamp)

				_HISTORY.append(hi)

				# Discard old entries.
				if len(_HISTORY) > _MAX_BRACKET_SIZE:
					_HISTORY = _HISTORY[1:]

				print("CURRENT HISTORY:")
				print('')
				
				for hi in _HISTORY:
					print(hi)

				print('')

				bi = self._find_bracketing_sequence_at_tail(_HISTORY)
				if bi is None:
					continue

				yield bi.exposure_delta, _HISTORY[-bi.size:]

	def _bracketinfo_matches(self, bi1, bi2):
		return \
			bi1.size == bi2.size and \
			bi1.exposure_delta == bi2.exposure_delta and \
			self._sequence_matches(bi1.sequence, bi2.sequence) is True
