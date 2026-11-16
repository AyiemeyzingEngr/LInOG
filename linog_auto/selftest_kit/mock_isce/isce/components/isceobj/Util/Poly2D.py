"""MOCK Poly2D (linog_auto self-test only): the attributes and methods invertMisreg.py, the kit's G8, G9 and G16 and
lp_p3 use (initPoly, getCoeffs, setCoeffs, the orders, _coeffs), pickled into the misreg shelves."""


class Poly2D(object):
    def __init__(self, **kw):
        self._coeffs, self._rangeOrder, self._azimuthOrder = [[0.0]], 0, 0

    def initPoly(self, rangeOrder=0, azimuthOrder=0, coeffs=None):
        self._rangeOrder, self._azimuthOrder = rangeOrder, azimuthOrder
        self._coeffs = [list(map(float, row)) for row in (coeffs or [[0.0]])]

    def getCoeffs(self):
        return self._coeffs

    def setCoeffs(self, c):
        self._coeffs = c

    def getAzimuthOrder(self):
        return self._azimuthOrder

    def getRangeOrder(self):
        return self._rangeOrder
