"""MOCK Frame and parts (linog_auto self-test only): pickled into the shelve, read back by lp_verify and the kit."""


class Platform(object):
    def __init__(self, pointingDirection=-1):
        self.pointingDirection = pointingDirection


class Instrument(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def getRangePixelSize(self):
        return self.rangePixelSize


class Image(object):
    def __init__(self, filename, width, length):
        self.filename, self.width, self.length = filename, width, length

    def renderHdr(self):
        """An .xml in the layout ISCE writes: length and width at the top, then coordinate components with a size."""
        p = '    <property name="%s">\n        <value>%s</value>\n    </property>\n'
        with open(self.filename + '.xml', 'w') as fh:
            fh.write('<imageFile>\n' + p % ('data_type', 'CFLOAT') + p % ('file_name', self.filename)
                     + p % ('length', self.length) + p % ('width', self.width))
            for c, size in (('coordinate1', self.width), ('coordinate2', self.length)):
                fh.write('    <component name="%s">\n' % c + p % ('size', size) + '    </component>\n')
            fh.write('</imageFile>\n')
        with open(self.filename + '.vrt', 'w') as fh:
            # the layout ISCE's renderVRT writes (RD3 on felix: SourceFilename <date>.slc, relative to the vrt)
            import os
            fh.write('<VRTDataset rasterXSize="%d" rasterYSize="%d">\n    <VRTRasterBand dataType="CFloat32" band="1" '
                     'subClass="VRTRawRasterBand">\n        <SourceFilename relativeToVRT="1">%s</SourceFilename>\n'
                     '        <ByteOrder>LSB</ByteOrder>\n        <ImageOffset>0</ImageOffset>\n        <PixelOffset>8</PixelOffset>\n'
                     '        <LineOffset>%d</LineOffset>\n    </VRTRasterBand>\n</VRTDataset>\n'
                     % (self.width, self.length, os.path.basename(self.filename), 8 * self.width))


class StateVector(object):
    def __init__(self, time, position, velocity):
        self.time, self.position, self.velocity = time, position, velocity

    def getTime(self):
        return self.time

    def getVelocity(self):
        return self.velocity


class Orbit(object):
    def __init__(self, sv):
        self._stateVectors = sv

    @property
    def stateVectors(self):
        return self._stateVectors


class Frame(object):
    def __init__(self):
        self.instrument, self.image, self.orbit, self.passDirection = Instrument(), None, None, None

    def getImage(self):
        return self.image

    def getInstrument(self):
        return self.instrument

    def getStartingRange(self):
        return self.startingRange

    def setStartingRange(self, r):
        self.startingRange = r

    def getOrbit(self):
        return self.orbit
