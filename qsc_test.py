import unittest
import qsc


class QSCTest(unittest.TestCase):
    def can_build_r1(self):
        r1 = qsc.QSC().row(1).build()


if __name__ == '__main__':
    unittest.main()
