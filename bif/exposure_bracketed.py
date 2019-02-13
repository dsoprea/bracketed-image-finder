import sys
import os
import logging
import subprocess
import re
import collections
import fnmatch

import exif

import dateutil.parser

_IMAGE_FILESPEC = '*.jpg'

# 0xa402
# 
# Values:
# 0: Auto exposure
# 1: Manual exposure
# 2: Auto bracket
# <everything else>: Reserved
_SONY_BRACKETING_EXPOSURE_MODE = 2

# The various number of images produced by complete bracketing processes. 
# - These must be odd.
# - These must be in descending order (to make sure that any larger sequences 
#   that might contain smaller sequences are allowed to match first).
_BRACKETING_SEQUENCE_SIZES = (7, 5, 3)
_MAX_BRACKET_SIZE = max(_BRACKETING_SEQUENCE_SIZES)

_LOGGER = logging.getLogger(__name__)

_HISTORY_ITEM = \
    collections.namedtuple(
        '_HISTORY_ITEM', [
            'rel_filepath',
            'exposure_value',
            'timestamp',
        ])

BT_SEQUENTIAL = 'sequential'
BT_PERIODIC = 'periodic'

_BRACKET_INFO = \
    collections.namedtuple(
        '_BRACKET_INFO', [
            'size',
            'sequence',
            'type',
        ])


class MetadataNotFoundException(Exception):
    pass


class ExposureBracketedAnalysis(object):
    def _read_image_metadata(self, filepath):
        with open(filepath, 'rb') as f:
            image_metadata = exif.Image(f)

        try:
            info = {
                'timestamp': dateutil.parser.parse(image_metadata.datetime),
                'exposure_value': image_metadata.exposure_bias_value,
                'exposure_mode': image_metadata.exposure_mode,
            }
        except AttributeError as e:
            pass
        else:
            return info

        # If we get here, the tag was not found.
        raise MetadataNotFoundException()

    def _is_float_equal(self, a, b):
        """Account for epsilon."""

        return abs(a - b) < 0.0001

    def _check_for_sequential_bracketing_at_tail(self, history):
        """Detect a sequence like -1.4, -.7, 0, .7, 1.4 ."""

        len_ = len(history)
        for expected_size in _BRACKETING_SEQUENCE_SIZES:
            if expected_size > len_:
                continue

            last_n_entries = history[-expected_size:]
            middle_index = (expected_size - 1) // 2
            middle_exposure_value = last_n_entries[middle_index].exposure_value

            i = 0
            found = True
            while i < middle_index:
                inverse_i = expected_size - i - 1
                front_exposure_value = last_n_entries[i].exposure_value
                rear_exposure_value = last_n_entries[inverse_i].exposure_value

                if front_exposure_value >= rear_exposure_value:
                    found = False
                    break
                elif self._is_float_equal(front_exposure_value, -rear_exposure_value) is False:
                    found = False
                    break
                elif (front_exposure_value < middle_exposure_value < rear_exposure_value) is False:
                    found = False
                    break

                i += 1

            if found is True:
                return \
                    _BRACKET_INFO(
                        size=expected_size,
                        sequence=last_n_entries,
                        type=BT_SEQUENTIAL)

        return None

    def _check_for_periodic_bracketing_at_tail(self, history):
        """Detect a sequence like 0, -.7, .7, -1.4, 1.4 ."""

        len_ = len(history)
        for expected_size in _BRACKETING_SEQUENCE_SIZES:
            if expected_size > len_:
                continue

            last_n_entries = history[-expected_size:]
            base_exposure_value = last_n_entries[0].exposure_value

            found = True
            for i in range(1, expected_size, 2):
                hi1, hi2 = last_n_entries[i], last_n_entries[i + 1]

                if hi1.exposure_value >= hi2.exposure_value:
                    found = False
                    break
                elif self._is_float_equal(hi1.exposure_value, -hi2.exposure_value) is False:
                    found = False
                    break
                elif self._is_float_equal(base_exposure_value - hi1.exposure_value, hi2.exposure_value - base_exposure_value) is False:
                    found = False
                    break

            if found is True:
                return \
                    _BRACKET_INFO(
                        size=expected_size,
                        sequence=last_n_entries,
                        type=BT_PERIODIC)

        return None
    
    def _sequence_matches(self, sequence1, sequence2):
        len1 = len(sequence1)
        len2 = len(sequence2)

        assert \
            len1 == len2, \
            "Sequences are not the same length: ({}) != ({})".format(len1, len2)

        for i, x in enumerate(sequence1):
            if self._is_float_equal(x.exposure_value, sequence2[i].exposure_value) is False:
                return False

        return True

    def find_bracketed_images(self, root_path):
        root_path_len = len(root_path)

        _HISTORY = []
        usage_index = {}
        for path, folders, files in os.walk(root_path):
            # We depend on the files`being sorted and we use that sorting the files 
            # will be them in sequence of when they were created. We do not handle 
            # rollover in the numbering.

            files = sorted(files)

            for filename in files:
                if fnmatch.fnmatch(filename.lower(), _IMAGE_FILESPEC) is False:
                    continue

                filepath = os.path.join(path, filename)
                rel_filepath = filepath[root_path_len + 1:]

                try:
                    metadata = self._read_image_metadata(filepath)

                    # Only Sony bracketing supported at this time (for lack of 
                    # information on implementation by other brands).
                    if metadata['exposure_mode'] != _SONY_BRACKETING_EXPOSURE_MODE:
                        continue
                except MetadataNotFoundException:
                    continue
                except AssertionError as e:
                    _LOGGER.exception("Validation issue: [{}]".format(filepath))
                    continue

                # We definitely have a picture that was involved in bracketing.
                
                hi = _HISTORY_ITEM(
                        rel_filepath=rel_filepath, 
                        exposure_value=metadata['exposure_value'], 
                        timestamp=metadata['timestamp'])

                _HISTORY.append(hi)

                # Discard old entries.
                if len(_HISTORY) > _MAX_BRACKET_SIZE:
                    _HISTORY = _HISTORY[1:]

                check_fns = [
                    self._check_for_sequential_bracketing_at_tail,
                    self._check_for_periodic_bracketing_at_tail,
                ]

                for check_fn in check_fns:
                    bi = check_fn(_HISTORY)
                    if bi is not None:
                        # If the file was matched both in smaller sequences and 
                        # larger sequences (which happens), only remember the 
                        # larger ones. Due to this tracking, we can't emit the 
                        # found sequences until the end.
                        for hi in bi.sequence:
                            try:
                                previous_bi = usage_index[hi.rel_filepath]
                            except KeyError:
                                # This file hasn't yet been found in a sequence.
                                usage_index[hi.rel_filepath] = bi
                            else:
                                # This file has previously been found in a 
                                # sequence; keep whichever is larger.
                                if len(bi.sequence) > len(previous_bi.sequence):
                                    usage_index[hi.rel_filepath] = bi

        unique_sequences = {
            frozenset(bi.sequence): bi
            for _, bi
            in usage_index.items()
        }

        for bi in unique_sequences.values():
            yield bi.type, bi.sequence

    def _bracketinfo_matches(self, bi1, bi2):
        return \
            bi1 is not None and bi2 is not None and \
            bi1.size == bi2.size and \
            bi1.type == bi2.type and \
            self._sequence_matches(bi1.sequence, bi2.sequence) is True
