"""MOCK osgeo.gdal (linog_auto self-test only): Open() reads an ISCE raster (band interleaved by line) through its .xml;
v0.7: and a mock GeoTIFF (linog_mock6), read-only or GA_Update, with its band's NoData, metadata and statistics.
ComputeStatistics on a file opened GA_Update puts the statistics into the file and removes a stale .aux.xml beside it
(as GDAL does for a GTiff); on a file opened read-only it writes them to <file>.aux.xml unless GDAL_PAM_ENABLED is NO."""
import os
import re

import numpy as np

import linog_mock6 as M6

DT = {'FLOAT': np.float32, 'CFLOAT': np.complex64, 'DOUBLE': np.float64, 'BYTE': np.uint8}
GA_ReadOnly, GA_Update = 0, 1
_CONFIG = {}


def UseExceptions():
    pass


def SetConfigOption(key, value):
    _CONFIG[key] = value


def GetConfigOption(key, default=None):
    return _CONFIG.get(key, os.environ.get(key, default))


class _Band(object):
    def __init__(self, a):
        self._a = a

    def ReadAsArray(self):
        return self._a


class _Dataset(object):
    def __init__(self, path):
        x = open(path + '.xml').read()

        def get(n):
            return re.search(r'name="%s">\s*<value>([^<]+)' % n, x).group(1).strip()
        w, ln, nb = int(get('width')), int(get('length')), int(get('number_bands'))
        self.RasterXSize, self.RasterYSize, self.RasterCount = w, ln, nb
        self._a = np.fromfile(path, dtype=DT[get('data_type')], count=w * ln * nb).reshape(ln, nb, w)

    def GetRasterBand(self, i):
        return _Band(self._a[:, i - 1, :])


class _TiffBand(object):
    def __init__(self, ds):
        self._ds = ds

    def ReadAsArray(self):
        return self._ds._a.copy()

    def GetNoDataValue(self):
        v = self._ds._h.get('nodata')
        return None if v is None else float(v)

    def SetNoDataValue(self, v):
        self._ds._h['nodata'] = 'nan' if np.isnan(v) else float(v)
        self._ds._dirty = True

    def GetMetadataItem(self, key, domain=''):
        return self._ds._h.get('metadata', {}).get(key)

    def GetMetadata(self, domain=''):
        return dict(self._ds._h.get('metadata', {}))

    def SetMetadataItem(self, key, value, domain=''):
        self._ds._h.setdefault('metadata', {})[key] = str(value)
        self._ds._dirty = True

    def ComputeStatistics(self, approx_ok, *args):
        s = M6.stats(self._ds._a, self.GetNoDataValue())
        if s is None:
            raise RuntimeError('MOCK gdal: no valid pixels in %s' % self._ds._path)
        md = dict(STATISTICS_MINIMUM='%.14g' % s[0], STATISTICS_MAXIMUM='%.14g' % s[1], STATISTICS_MEAN='%.14g' % s[2],
                  STATISTICS_STDDEV='%.14g' % s[3], STATISTICS_VALID_PERCENT='%.4g' % s[4])
        if self._ds._mode == GA_Update:
            self._ds._h.setdefault('metadata', {}).update(md)
            self._ds._dirty = True
        elif str(GetConfigOption('GDAL_PAM_ENABLED', 'YES')).upper() != 'NO':
            with open(self._ds._path + '.aux.xml', 'w') as fh:
                fh.write('<PAMDataset><PAMRasterBand band="1"><Metadata>%s</Metadata></PAMRasterBand></PAMDataset>\n' % ''.join(
                    '<MDI key="%s">%s</MDI>' % kv for kv in sorted(md.items())))
        return list(s[:4])

    def GetStatistics(self, approx_ok, force):
        md = self._ds._h.get('metadata', {})
        if 'STATISTICS_MEAN' in md:
            return [float(md['STATISTICS_%s' % k]) for k in ('MINIMUM', 'MAXIMUM', 'MEAN', 'STDDEV')]
        return self.ComputeStatistics(approx_ok) if force else None


class _TiffDataset(object):
    def __init__(self, path, mode):
        self._path, self._mode, self._dirty = path, mode, False
        self._h, self._a = M6.read_tiff(path)
        self.RasterXSize, self.RasterYSize, self.RasterCount = self._h['width'], self._h['height'], 1

    def GetRasterBand(self, i):
        return _TiffBand(self)

    def GetGeoTransform(self):
        return tuple(self._h.get('geotransform') or (0, 1, 0, 0, 0, 1))

    def FlushCache(self):
        if self._mode == GA_Update and self._dirty:
            M6.write_tiff(self._path, self._h, self._a)
            if 'STATISTICS_MEAN' in self._h.get('metadata', {}) and os.path.exists(self._path + '.aux.xml'):
                os.remove(self._path + '.aux.xml')
            self._dirty = False

    def __del__(self):
        try:
            self.FlushCache()
        except Exception:  # noqa: BLE001
            pass


def Open(path, mode=GA_ReadOnly):
    if M6.is_tiff(path):
        return _TiffDataset(path, mode)
    return _Dataset(path)
