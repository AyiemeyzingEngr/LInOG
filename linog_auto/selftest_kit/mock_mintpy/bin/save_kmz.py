#!/usr/bin/env python3
"""MOCK save_kmz.py (linog_auto self-test only, v0.7): `save_kmz.py FILE -m MASK -v MIN MAX -u UNIT -o OUT.kmz` (the kit's
step 7): a KMZ (doc.kml with a GroundOverlay and its PNG), the range and unit in the KML's description. v0.11: planted,
LINOG_MOCK_KMZ_EXTRA=1 gives doc.kml an extra field (Info-ZIP's 0x5455 timestamp), which deliver's G6a.10 refuses."""
import os
import sys
import zipfile

import linog_mock6 as M6

M6.planted_fail('save_kmz.py')
pos, opt = M6.args(sys.argv[1:], {'-m': 1, '-v': 2, '-u': 1, '-o': 1})
out = opt['-o']
png = out + '.mockpng'
M6.png(png)
doc = 'doc.kml'
if os.environ.get('LINOG_MOCK_KMZ_EXTRA'):   # v0.11 plant: an extended-timestamp extra field on doc.kml
    import struct
    import time
    doc = zipfile.ZipInfo('doc.kml', time.localtime(time.time())[:6])
    doc.compress_type = zipfile.ZIP_DEFLATED
    doc.extra = b'UT\x05\x00\x01' + struct.pack('<I', int(time.time()))
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr(doc, '<?xml version="1.0" encoding="UTF-8"?><kml><Document><name>%s</name><description>MOCK %s %s to %s %s, '
               'mask %s</description><GroundOverlay><Icon><href>%s.png</href></Icon></GroundOverlay></Document></kml>' % (
                   os.path.basename(out), pos[0], opt['-v'][0], opt['-v'][1], opt.get('-u'), opt.get('-m'),
                   os.path.splitext(os.path.basename(out))[0]))
    z.write(png, os.path.splitext(os.path.basename(out))[0] + '.png')
os.remove(png)
print('MOCK save_kmz.py: %s -> %s' % (pos[0], out))
