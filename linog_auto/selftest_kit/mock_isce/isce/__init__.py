"""MOCK isce (linog_auto self-test only): puts components/ on sys.path, as ISCE2's isce/__init__.py does."""
import os
import sys

__version__ = '2.6.3-mock'
# ISCE2's isce/__init__.py reads its defaults/logging/logging.conf with logging.config.fileConfig. The mock reads the
# same file (ISCE2 v2.6.3's, md5 21a67de3, Apache License 2.0) the same way: the loggers that exist then are disabled;
# the root logger and ISCE's own 'isce' logger (propagate 0) print DEBUG on stdout in ISCE's format and write isce.log
# into the working folder from their first record (felix, S14: matplotlib's start-up lines on the console after
# `import isce`, and isce.log beside the stack passes; F50).
from logging.config import fileConfig as _fc
_fc(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'defaults', 'logging', 'logging.conf'))
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'components')
if _p not in sys.path:
    sys.path.insert(1, _p)
if os.environ.get('LINOG_MOCK_THREAD'):
    # felix: ISCE's objects load numpy, whose OpenBLAS starts a thread per core; a signal sent to the process can go
    # to one of them (self-test T95): one idle thread here
    import threading
    import time
    threading.Thread(target=time.sleep, args=(3600,), daemon=True).start()
