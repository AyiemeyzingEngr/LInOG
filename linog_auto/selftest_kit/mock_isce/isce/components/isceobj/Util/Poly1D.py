"""MOCK Poly1D (linog_auto self-test only)."""


class Poly1D(object):
    def __init__(self):
        self._coeffs, self._order = [], 0

    def initPoly(self, order=0):
        self._order = order

    def setCoeffs(self, c):
        self._coeffs = list(c)
