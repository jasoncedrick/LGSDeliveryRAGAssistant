"""Alignment failure tests using synthetic coordinates, without benchmark data."""
import unittest

from scripts.repair_ocbo_page14 import pair_actions_and_times


def line(text, y):
    return {'text': text, 'bbox': [0, y, 100, y + 10]}


class AlignmentTests(unittest.TestCase):
    def test_wrapped_action_and_unsorted_times(self):
        pairs = pair_actions_and_times(
            [line('2.1 Encode and', 20), line('receive documents', 31),
             line('2.2 Route documents', 60)],
            [line('1 Day', 60), line('5 Minutes', 20)])
        self.assertEqual([(p['action'], p['processing_time']) for p in pairs],
                         [('2.1 Encode and receive documents', '5 Minutes'),
                          ('2.2 Route documents', '1 Day')])

    def test_missing_time_rejected(self):
        with self.assertRaisesRegex(ValueError, 'count mismatch'):
            pair_actions_and_times([line('1. Evaluate Documents', 20)], [])

    def test_shifted_time_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            pair_actions_and_times([line('1. Evaluate Documents', 20)],
                                   [line('20 Minutes', 35)])

    def test_multiple_matching_times_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            pair_actions_and_times([line('2.1 First action', 20), line('2.2 Second action', 60)],
                                   [line('5 Minutes', 20), line('1 Day', 20.5)])

    def test_orphan_continuation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no numbered parent'):
            pair_actions_and_times([line('receive documents', 20)], [line('5 Minutes', 20)])


if __name__ == '__main__':
    unittest.main()
