"""MOCK mintpy.utils.writefile (linog_auto self-test only, v0.7): write() of a dict of datasets with the metadata as the
file's attributes, as the kit's linog_watermask.py calls it."""
import os

import h5py


def write(datasetDict, out_file, metadata=None, ref_file=None, compression=None, ds_unit_dict=None, print_msg=True):
    d = os.path.dirname(os.path.abspath(out_file))
    os.makedirs(d, exist_ok=True)
    with h5py.File(out_file, 'w') as f:
        for k, v in datasetDict.items():
            f.create_dataset(k, data=v)
        for k, v in (metadata or {}).items():
            f.attrs[k] = str(v)
    if print_msg:
        print('MOCK writefile: %s' % out_file)
    return out_file
