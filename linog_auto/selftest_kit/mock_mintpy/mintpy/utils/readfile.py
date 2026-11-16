"""MOCK mintpy.utils.readfile (linog_auto self-test only, v0.7): read() and read_attribute() on HDF5 files, as the kit's
linog_watermask.py calls them (a dataset by name, or the file's main one; the attributes as strings)."""
import h5py
import numpy as np

MAIN = ('mask', 'velocity', 'timeseries', 'temporalCoherence', 'coherence', 'waterFlag', 'height', 'dem')


def _s(v):
    if isinstance(v, bytes):
        return v.decode()
    if isinstance(v, np.ndarray):
        return ' '.join(str(x) for x in v.ravel())
    return str(v)


def read_attribute(fname, datasetName=None, metafile_ext=None):
    with h5py.File(fname, 'r') as f:
        atr = {k: _s(v) for k, v in f.attrs.items()}
        keys = list(f.keys())
    if 'FILE_TYPE' not in atr:
        atr['FILE_TYPE'] = next((k for k in MAIN if k in keys), keys[0] if keys else 'unknown')
    atr.setdefault('LENGTH', '0')
    atr.setdefault('WIDTH', '0')
    return atr


def read(fname, box=None, datasetName=None, print_msg=True, xstep=1, ystep=1, data_type=None, no_data_values=None):
    with h5py.File(fname, 'r') as f:
        name = datasetName or next((k for k in MAIN if k in f), list(f.keys())[0])
        data = f[name][()]
    if box is not None:
        x0, y0, x1, y1 = box
        data = data[..., y0:y1, x0:x1]
    if print_msg:
        print('MOCK readfile: %s %s %s' % (fname, name, data.shape))
    return data, read_attribute(fname)
