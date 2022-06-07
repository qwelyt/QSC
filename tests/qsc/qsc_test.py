import logging
import sys
import unittest

from qsc import QSC, U


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
            for w in [1, 1.25, 1.5, 1.75, 2, 2.25, 2.75, 6.25, 7]:
                self._test_r1(U(w))
                self._test_r2(U(w))
                self._test_r3(U(w))
                self._test_r4(U(w))

    def test_normal(self):
        self.Rows(self._can_build_row)

    def test_inverted(self):
        self.Rows(self._can_build_inverted_row)

    def test_stepped(self):
        self.Rows(self._can_build_stepped_row)

    def test_unable_to_fillet_error(self):
        with self.assertRaises(ValueError):
            QSC().row(1).top_fillet(30).dish_thickness(3).build()

    def test_all_types_same_width(self):
        def bb(cap):
            return cap.findSolid().BoundingBox()

        for row in [1, 2, 3, 4]:
            for width in [1, 2, 3, 6.25, 7]:
                qsc = QSC().row(row).width(U(width))
                s = qsc.clone().stepped()
                i = qsc.clone().inverted()
                normal, _ = qsc.build()
                stepped, _ = s.build()
                inverted, _ = i.build()

                nBB = bb(normal)
                sBB = bb(stepped)
                iBB = bb(inverted)

                delta = 0.05

                self.assertAlmostEqual(nBB.xlen, sBB.xlen, None, "r" + str(row) + " w" + str(width), delta)
                self.assertAlmostEqual(nBB.xlen, iBB.xlen, None, "r" + str(row) + " w" + str(width), delta)
                self.assertAlmostEqual(sBB.xlen, iBB.xlen, None, "r" + str(row) + " w" + str(width), delta)

                self.assertAlmostEqual(nBB.ylen, sBB.ylen, None, "r" + str(row) + " w" + str(width), delta)
                self.assertAlmostEqual(nBB.ylen, iBB.ylen, None, "r" + str(row) + " w" + str(width), delta)
                self.assertAlmostEqual(sBB.ylen, iBB.ylen, None, "r" + str(row) + " w" + str(width), delta)

    def _can_build_row(self, row, width):
        qsc = QSC().row(row).width(width)
        # self.assertTrue(qsc.isValid())
        self.assertIsNotNone(qsc.build())

    def _can_build_inverted_row(self, row, width):
        qsc = QSC().row(row).width(width).inverted()
        # self.assertTrue(qsc.isValid())
        self.assertIsNotNone(qsc.build())

    def _can_build_stepped_row(self, row, width):
        qsc = QSC().row(row).width(width).stepped()
        # self.assertTrue(qsc.isValid())
        self.assertIsNotNone(qsc.build())


if __name__ == '__main__':
    unittest.main()
