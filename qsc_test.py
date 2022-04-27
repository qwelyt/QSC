import sys
import unittest
import logging

from qsc import QSC


class QSCTest(unittest.TestCase):
    def setUp(self) -> None:
        loglevel = logging.DEBUG
        logging.basicConfig(level=loglevel, stream=sys.stdout)

    class Rows():
        def __init__(self, testFunc):
            self._func = testFunc
            self.test()

        def _test_r1(self, width):
            self._func(1, width)

        def _test_r2(self, width):
            self._func(2, width)

        def _test_r3(self, width):
            self._func(3, width)

        def _test_r4(self, width):
            self._func(4, width)

        def test(self):
            for w in [1,1.75,2,2.25,2.75,6.25,7]:
                self._test_r1(w)
                self._test_r2(w)
                self._test_r3(w)
                self._test_r4(w)

    def test_normal(self):
        self.Rows(self._can_build_row)

    def test_inverted(self):
        self.Rows(self._can_build_inverted_row)

    def test_stepped(self):
        self.Rows(self._can_build_stepped_row)

    def test_unable_to_fillet_error(self):
        with self.assertRaises(ValueError):
            QSC().row(1).fillet(30).dishThickness(3).build()

    def _can_build_row(self, row, width):
        qsc = QSC().row(row).width(width)
        self.assertTrue(qsc.isValid())
        self.assertIsNotNone(qsc.build())

    def _can_build_inverted_row(self, row, width):
        qsc = QSC().row(row).width(width).inverted()
        self.assertTrue(qsc.isValid())
        self.assertIsNotNone(qsc.build())

    def _can_build_stepped_row(self, row, width):
        qsc = QSC().row(row).width(width).stepped()
        self.assertTrue(qsc.isValid())
        self.assertIsNotNone(qsc.build())


if __name__ == '__main__':
    unittest.main()
