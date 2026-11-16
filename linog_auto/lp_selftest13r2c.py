#!/usr/bin/env python3
"""lp_selftest13r2c.py -- linog_auto v0.13 r2, part C: the part 6 review's items (the ascending record 26.1 and 26.2: P6R-01 to
06, 08 to 11, 13 and 14), the one .xml width helper at four gates (25-b; 25.4, 25.6) and accept under R9 as part 6's subset
built it (18.6, 23.2); called by lp_selftest.py as the suite 13r2c. install.sh's removal of its self-test's mock data after a
PASS (25-c) is not run by the self-test: its harness is the build's own (the report names it).

The frame, on 13p4's mock ground (LINOG_MOCK_V13=1), in this suite's path table cfg/paths_r2c.cfg (the self-test's table and an
ascending section, the installed table's [p447] as it stands): one ascending mixed full-height frame P447 F0310, archive
v13asc (M84's 12 dates moved onto path 447's date law, granules ..__A, 8 FBS and 4 FBD as FBD_3350), root ca, under
--decide auto with LINOG_MOCK_ASC=1 (the mock orbit's vz > 0; the mock topo lays lat.rdr and lon.rdr out ascending, line 0
south and column 0 west, los.rdr's azimuth 101.06) and LINOG_MOCK_HEADING=-11.06 (the mock prep_isce's HEADING), so that
report's G4g.3, mcfg's and sbas's G24 and deliver's D7c read an ascending frame. One frame only: a full-height frame to
accept holds about 5.5 GiB of mock data (measured, r2C_1: unzipped/ 2.4, SLC/ 2.3), and the session's disk is shared; 13p6
runs M84's own frame 3354, and the cases the review placed on it (M84b to M84e) run here on this mixed R9 frame of the same
12 dates. It is run to reference, to stack2 and to bgrid with 25-b's gate cases between (each phase alone on the .xml
edited, then the .xml put back by its bytes and times, so no fingerprint moves), then to rerun (P6R-06); then the package
cases, then the accept cases, each one thing changed, accept alone (--only accept --force accept), the thing put back;
datum's case last.
The backups' state (25.4): an .xml as isce2 2.6.3 writes it (ElementTree's form: F0280's 28 fields; XML_LINES below makes
P448 F0280's five copies byte for byte, M110) whose width property is the image's width while coordinate1's size, its
endingValue and the xmax property are 32 samples more, as SLC/20091111/20091111.slc.xml.bak9376 (9,344 and 9,376).

Cases:
  M84b (P6R-05) an FBS secondary's dates/ azimuth moved 2e-6 lines: G16 FAIL by R9's plan, its off dates listed; N22 PASS
  M84c (P6R-04, 05) an FBD secondary's dates/ folder aside: N22 and G16 FAIL naming it "in the plan only"
  M84d (P6R-04, 05) the datum record's plan without that date: N22 and G16 FAIL naming it "in dates/ only"
  M84e (P6R-05) the datum record aside (a frame without status/P4c_datum.json): G16's relation, which R9's values FAIL on N22
  M84f (P6R-05; the review's "M86", taken by drop1's guard in 19.6) v0.12's datum planted on the mixed frame (dates/ set to
       datum's own r9.v12, G16's plan of invertMisreg's values, the record's method G16; the hook LINOG_MOCK_DATUM_V12's whole
       run would need a second frame): N22 PASS by G16's relation with the table's 0.5 on its 4 FBD dates; put back: R9 again
  M100 (P6R-01) an FBD secondary's dates/ range constant NaN: N22 FAIL naming it (the old form read it as on)
  M100b (P6R-01, 03) a plan value NaN in the record: N22 and G16 FAIL naming the record and the date
  M100c (P6R-01) the NaN form against the old one at the function level: the verifier copy's R9 lines and G16 relation, datum's
       G16 (g16_off): the same verdict on every finite value and on inf, the new one off on NaN
  M100d (P6R-01) one pair's referenceShelve copy's SLR NaN: datum alone, G4c.8 FAIL naming it (the old form passed it)
  M101 (P6R-02) the pre-datum copy aside: accept PASS by R9's plan (the old copy: WARN N23, then G6b.5 FAIL)
  M102a to M102e (P6R-03) the datum record not JSON, R9 with verdict FAIL, a dry run's, R9 with no plan, a list: N22 and G16
       FAIL naming the record and what it lacks; G6b.5 PASS
  M103 (P6R-06) the ascending frame recon to rerun: G0.6 A, G3b ASCENDING, package _xfer/LINOG_ASC_P447F0310_v0.1_<day>_review
       with G6c.0 and G6c.2 PASS, its fingerprint by LINOG_ASC, rerun PASS, RUN_MANIFEST.json ascending
  M103b (P6R-06) package forced again: G6c.2 DECISION naming the LINOG_ASC package
  M103c (P6R-06) deliver forced again: G6a.5 DECISION, the later phases' glob by the direction naming the LINOG_ASC package
  M104 (P6R-08) the copy's R9 line on the frame's accept: the plan = x by the record's SLR and PRF on 12 dates, PASS
  M104b, M104c (P6R-08) one date's r9.x_rg moved 0.01, one date's SLR doubled, in the record: R9 FAIL naming it; N22 PASS
  M105 (P6R-09) the ascending path's direction X in a copy of the table: package's --state prints a state word, a run FAILs
       G6c.0 with a record (it raised before any record)
  M106 (P6R-13) the datum record rewritten with one field more: accept STALE; put back: CURRENT; its md5 in accept's record
  M107 (P6R-10) a date out of recon/modes.json on the R9 frame: N22 FAIL naming it; M107b the reference out of it on M84f's
       planted G16 frame: N22 FAIL naming it (it read as FBD)
  M108 (P6R-14) the fineResamp configs aside: the copy names the reference by recon/reference.json, accept PASS (the old
       heuristic names the earliest FBS date); M108b coreg_ref's heuristic on synthetic frames: one date not 4640 wide by
       isce2's reading named, two not, or one in the backups' state: none
  M109 (P6R-11) the package aside and a LINOG_DESC folder of the frame and version under _xfer/: G6c.2 DECISION naming it
  M110 (25-b, 25.4) XML_LINES gives P448 F0280's five .xml byte for byte; lp_xmlwidth reads 9,344 on the two .xml and 9,376
       with the property named on the two backups and raw_fbs_unpacked/'s; the old readers' 9,344 on all five
  M111 (25-b) lp_xmlwidth on variants as isce2 2.6.3's own Configurable.load reads them (the section 25 emulation, run at the
       build: 24 of 24): name case and spacing, the three value styles, floats, a name given twice, a field absent, the
       ends and xmax against start + size x delta, the length, the mock unpacker's form, not XML, absent
  M112 (25-b) reference's G17: the reference .xml in isce2's form PASS, in the backups' state FAIL, put back PASS
  M113 (25-b) topo's G3a.14 in the backups' state FAIL; put back, topo again: PASS
  M114 (25-b) igram's G17 in the backups' state FAIL, run_08 not run; put back: PASS
Changed v0.13 case (lp_selftest13p6.py, suite 13p6): M84 reads accept's LOGIC 3 (r2, the part 6 review's items), not 2.
Changed in the kit: selftest_kit/mock_stack3/topo.py lays the geometry out ascending under LINOG_MOCK_ASC=1 (no other suite
runs that hook past verify; T31 stops at G3b), so that P6R-06's frame can run past report.
"""
import configparser
import contextlib
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

import lp_selftest13p1 as P13

LF = 18432
AP, AF = '447', '0310'                 # the ascending frame (the test root's cell)
EO447, ED447 = 5230, '20070117'        # [p447]'s date law anchor in linog_paths.cfg

# XML_LINES: P448 F0280's SLC/20091111/20091111.slc.xml.bak9376 as S42b copied it (af04e533...), its nine numbers and two names
# as fields (generated from the file at the build, not typed)
XML_LINES = (
    "<?xml version='1.0' encoding='utf-8'?>",
    '<imageFile>',
    '    <property name="ISCE_VERSION">',
    '        <value>Release: 2.6.3, svn-, 20230418. Current: svn-.</value>',
    '    </property>',
    '    <property name="access_mode">',
    '        <value>read</value>',
    '        <doc>Image access mode.</doc>',
    '    </property>',
    '    <property name="byte_order">',
    '        <value>l</value>',
    '        <doc>Endianness of the image.</doc>',
    '    </property>',
    '    <component name="coordinate1">',
    '        <factorymodule>isceobj.Image</factorymodule>',
    '        <factoryname>createCoordinate</factoryname>',
    '        <doc>First coordinate of a 2D image (width).</doc>',
    '        <property name="delta">',
    '            <value>1</value>',
    '            <doc>Coordinate quantization.</doc>',
    '        </property>',
    '        <property name="endingvalue">',
    '            <value>%(c1_end)s</value>',
    '            <doc>Ending value of the coordinate.</doc>',
    '        </property>',
    '        <property name="family">',
    '            <value>imagecoordinate</value>',
    '            <doc>Instance family name</doc>',
    '        </property>',
    '        <property name="name">',
    '            <value>imagecoordinate_name</value>',
    '            <doc>Instance name</doc>',
    '        </property>',
    '        <property name="size">',
    '            <value>%(c1_size)s</value>',
    '            <doc>Coordinate size.</doc>',
    '        </property>',
    '        <property name="startingvalue">',
    '            <value>0</value>',
    '            <doc>Starting value of the coordinate.</doc>',
    '        </property>',
    '    </component>',
    '    <component name="coordinate2">',
    '        <factorymodule>isceobj.Image</factorymodule>',
    '        <factoryname>createCoordinate</factoryname>',
    '        <doc>Second coordinate of a 2D image (length).</doc>',
    '        <property name="delta">',
    '            <value>1</value>',
    '            <doc>Coordinate quantization.</doc>',
    '        </property>',
    '        <property name="endingvalue">',
    '            <value>%(c2_end)s</value>',
    '            <doc>Ending value of the coordinate.</doc>',
    '        </property>',
    '        <property name="family">',
    '            <value>imagecoordinate</value>',
    '            <doc>Instance family name</doc>',
    '        </property>',
    '        <property name="name">',
    '            <value>imagecoordinate_name</value>',
    '            <doc>Instance name</doc>',
    '        </property>',
    '        <property name="size">',
    '            <value>%(c2_size)s</value>',
    '            <doc>Coordinate size.</doc>',
    '        </property>',
    '        <property name="startingvalue">',
    '            <value>0</value>',
    '            <doc>Starting value of the coordinate.</doc>',
    '        </property>',
    '    </component>',
    '    <property name="data_type">',
    '        <value>cfloat</value>',
    '        <doc>Image data type.</doc>',
    '    </property>',
    '    <property name="description">',
    "        <value>['Single look complex image.']</value>",
    '        <doc>Image description</doc>',
    '    </property>',
    '    <property name="extra_file_name">',
    '        <value>%(vrt)s</value>',
    '        <doc>For example name of vrt metadata.</doc>',
    '    </property>',
    '    <property name="family">',
    '        <value>slcimage</value>',
    '        <doc>Instance family name</doc>',
    '    </property>',
    '    <property name="file_name">',
    '        <value>%(file)s</value>',
    '        <doc>Name of the image file.</doc>',
    '    </property>',
    '    <property name="image_type">',
    '        <value>slc</value>',
    '        <doc>Image type used for displaying.</doc>',
    '    </property>',
    '    <property name="length">',
    '        <value>%(length)s</value>',
    '        <doc>Image length</doc>',
    '    </property>',
    '    <property name="name">',
    '        <value>slcimage_name</value>',
    '        <doc>Instance name</doc>',
    '    </property>',
    '    <property name="number_bands">',
    '        <value>1</value>',
    '        <doc>Number of image bands.</doc>',
    '    </property>',
    '    <property name="scheme">',
    '        <value>BIP</value>',
    '        <doc>Interleaving scheme of the image.</doc>',
    '    </property>',
    '    <property name="width">',
    '        <value>%(width)s</value>',
    '        <doc>Image width</doc>',
    '    </property>',
    '    <property name="xmax">',
    '        <value>%(xmax)s</value>',
    '        <doc>Maximum range value</doc>',
    '    </property>',
    '    <property name="xmin">',
    '        <value>0</value>',
    '        <doc>Minimum range value</doc>',
    '    </property>',
    '</imageFile>',
)

F0280 = (   # (folder, width property, coordinate1's size, endingValue, xmax, md5) of S42b's xml_copies/ (25.4's table)
    ('SLC', 9344, 9344, 9344, 9344, '8f9b1d358272cc5ac78ee61f11e5732e'),
    ('SLC', 9344, 9376, 9376, 9376, 'af04e5337e50919be512624cea763af7'),
    ('merged/SLC', 9344, 9344, 9344, 9344, 'c570c373ee94f4f3182f066855b85ce3'),
    ('merged/SLC', 9344, 9376, 9376, 9376, '7eba4a9f3a40cf4a0592f2276d7b0483'),
    ('raw_fbs_unpacked', 9344, 9376, 9376, 9376, '62c0252653ba4816fdf80bb32e03f837'))


def isce_xml(file_rel, width, size, end, xmax, length=18432):
    """An image .xml in the form isce2 2.6.3 wrote F0280's (ElementTree's: a declaration, no final newline)."""
    return '\n'.join(XML_LINES) % dict(c1_end=end, c1_size=size, c2_end=length, c2_size=length, vrt=file_rel + '.vrt',
                                       file=file_rel, length=length, width=width, xmax=xmax)


def old_width(text):
    """The readers before r2 (lp_verify.xml_int, lp_reg3.xml_int, lp_reference's xi): the first name="width" field's value."""
    m = re.search(r'name="%s".*?<value>\s*(\d+)' % 'width', text, re.S)
    return int(m.group(1)) if m else None


# The frame's misreg shelves in the mock env (Poly2D unpickles there): argv[1] the frame; argv[2] read, set <date> <az|rg>
# <value>, plant <json {date: [az, rg]}>, or pairslr <pair> <referenceShelve|secondaryShelve> <value> (that copy's
# frame.instrument.rangePixelSize)
SHELVES = r'''
import glob, json, os, shelve, sys
W = sys.argv[1]
R = os.path.join(W, 'refineSecondaryTiming')
def val(base):
    with shelve.open(base, 'r') as db:
        return [float(db['azpoly'].getCoeffs()[0][0]), float(db['rgpoly'].getCoeffs()[0][0])]
op = sys.argv[2]
if op == 'set':
    key = 'azpoly' if sys.argv[4] == 'az' else 'rgpoly'
    with shelve.open(os.path.join(R, 'dates', sys.argv[3], 'misreg'), 'w') as db:
        p = db[key]
        old = float(p.getCoeffs()[0][0])
        p.initPoly(rangeOrder=0, azimuthOrder=0, coeffs=[[float(sys.argv[5])]])
        db[key] = p
    print(json.dumps(dict(date=sys.argv[3], key=key, old=old, new=float(sys.argv[5]))))
elif op == 'plant':   # plant <json {date: [az, rg]}>: both constants of every date given
    n = 0
    for d, (az, rg) in sorted(json.loads(sys.argv[3]).items()):
        with shelve.open(os.path.join(R, 'dates', d, 'misreg'), 'w') as db:
            for key, v in (('azpoly', az), ('rgpoly', rg)):
                p = db[key]
                p.initPoly(rangeOrder=0, azimuthOrder=0, coeffs=[[float(v)]])
                db[key] = p
        n += 1
    print(json.dumps(dict(planted=n)))
elif op == 'pairslr':
    with shelve.open(os.path.join(R, 'pairs', sys.argv[3], sys.argv[4], 'data'), 'w') as db:
        f = db['frame']
        old = float(f.instrument.rangePixelSize)
        f.instrument.rangePixelSize = float(sys.argv[5])
        db['frame'] = f
    print(json.dumps(dict(pair=sys.argv[3], side=sys.argv[4], old=old, new=float(sys.argv[5]))))
else:
    baks = sorted(glob.glob(os.path.join(R, 'dates_predatum_bak_*')))
    out = dict(post=dict((os.path.basename(os.path.dirname(p)), val(p[:-4])) for p in glob.glob(os.path.join(R, 'dates', '*', 'misreg.dat'))),
               pre=dict((os.path.basename(os.path.dirname(p)), val(p[:-4])) for p in glob.glob(os.path.join(baks[-1], '*', 'misreg.dat')))
               if baks else {})
    print(json.dumps(out))
'''


def law_date(orb, eo, ed):
    import datetime
    k, rem = divmod(orb - eo, 671)
    assert rem == 0, (orb, eo)
    return (datetime.datetime.strptime(ed, '%Y%m%d') + datetime.timedelta(days=46 * k)).strftime('%Y%m%d')


def phase13_r2c(T, case, S):
    print('-- v0.13 r2, part C: the part 6 review\'s items (P6R-01 to 06, 08 to 11, 13, 14) and 25-b\'s .xml width helper (reference\'s '
          'G17, topo\'s G3a.14, igram\'s G17) on one ascending mixed full-height frame P447 F0310 run to rerun (LINOG_MOCK_V13)')
    sys.path.insert(0, S.HERE)
    import lp_xmlwidth as XW
    import lp_common as C
    function_cases(T, case, S, XW, C)
    if not S.DATA_OK[0] or not S.MOCKPY[0]:
        case('M84b-M114 not run: the mock ground needs numpy, and neither Python tried has it', False)
        return
    base = open(os.path.join(T, 'cfg', 'paths.cfg')).read()
    real = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    real.read(os.path.join(S.HERE, 'linog_paths.cfg'))
    p447 = '[p447]\n' + ''.join('%s = %s\n' % kv for kv in real['p447'].items())

    def table(name, direction=None):
        sec = p447 if direction is None else re.sub(r'^direction = A$', 'direction = %s' % direction, p447, flags=re.M)
        with open(os.path.join(T, 'cfg', name), 'w') as fh:
            fh.write(base.rstrip('\n') + '\n# v0.13 r2 (part C): an ascending section, the installed table\'s [p447] as it stands (the '
                     'review\'s P6R-06)\n%s' % sec)
        return name
    cfg = table('paths_r2c.cfg')
    ORB = S.ORBITS[:12]
    ORBA = [EO447 + 671 * ((o - ORB[0]) // 671) for o in ORB]   # M84's 12 dates' cycles, on path 447's law
    full = dict(lines=LF, rows13=True)
    aa = P13.make_variant(T, S, 'v13asc', dict((i, dict(full, sfx='A', date=law_date(o, EO447, ED447))) for i, o in enumerate(ORBA)),
                          frame=AF, orbs=ORBA, fbd=S.FBD_3350)
    if not aa:
        case('M84b-M114 not run: the full-height mock archive could not be made (numpy)', False)
        return
    frame_asc(T, case, S, Helpers(T, S, cfg, aa), XW, C, table)


class Helpers(object):
    """The runs and records of this suite's frame (S.rec and S.fdir name path 084 only)."""

    def __init__(self, T, S, cfg, aa):
        self.T, self.S, self.cfg, self.aa = T, S, cfg, aa

    def fd(self, root):
        return os.path.join(self.T, root, 'p' + AP, 'f' + AF)

    def run(self, root, args, extra=None, cfg=None):
        # the mock orbit ascending (vz > 0), the mock topo's geometry with it, and the mock prep_isce's HEADING (selftest_kit)
        e = {'LINOG_ROOT': os.path.join(self.T, root), 'LINOG_MOCK_V13': '1', 'LINOG_ARCHIVE': self.aa, 'LINOG_MOCK_ASC': '1',
             'LINOG_MOCK_HEADING': '-11.06'}
        e.update(extra or {})
        return self.S.run(self.T, [AP, AF, '--decide', 'auto'] + args, cfg=cfg or self.cfg, env_extra=e)

    def rec(self, root, idx, ph):
        f = os.path.join(self.fd(root), 'status', 'P%s_%s.json' % (idx, ph))
        return json.load(open(f)) if os.path.isfile(f) else {}

    def state(self, root, ph, cfg=None):
        """(rc, the last line) of lp_<ph>.py --state as the driver calls it (its python3, the self-test's settings)."""
        T = self.T
        env = dict((k, v) for k, v in os.environ.items() if not k.startswith('LINOG_'))
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', cfg or self.cfg), LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'),
                   LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'), LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'),
                   LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'), LINOG_ROOT=os.path.join(T, root), LINOG_ARCHIVE=self.aa)
        p = subprocess.run(['python3', '-E', '-B', os.path.join(self.S.HERE, 'lp_%s.py' % ph), '--path', AP, '--frame', AF, '--state'],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        w = p.stdout.decode('utf-8', 'replace').strip().splitlines()
        return p.returncode, (w[-1] if w else '')

    def in_env(self, W, args):
        env = dict((k, v) for k, v in os.environ.items() if not k.startswith('LINOG_'))
        env['LINOG_ENV_CFG'] = os.path.join(self.T, 'cfg', 'env_mock.cfg')
        q = subprocess.run(['bash', os.path.join(self.S.HERE, 'lp_env.sh')] + args, cwd=W, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        out = q.stdout.decode('utf-8', 'replace')
        try:
            return q.returncode, json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return q.returncode, out[-600:]

    def shelves(self, W, *args):
        return self.in_env(W, ['python3', '-B', '-c', SHELVES, W] + list(args))

    def keep(self, path, tag):
        """A copy of a file (copy2: its bytes and times) or a folder, kept to put back (put)."""
        dst = os.path.join(self.T, '_r2c_keep', tag, os.path.basename(path))
        if os.path.lexists(dst):
            self.S.aside(self.T, dst, 'r2c_keep_%s' % tag)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(path):
            shutil.copytree(path, dst, symlinks=True, copy_function=shutil.copy2)
        else:
            shutil.copy2(path, dst)
        return dst

    def put(self, kept, path, tag):
        """path back as kept: what is there now aside (into T/_archive/; the self-test never deletes), the copy in its place."""
        if os.path.lexists(path):
            self.S.aside(self.T, path, 'r2c_%s' % tag)
        if os.path.isdir(kept):
            shutil.copytree(kept, path, symlinks=True, copy_function=shutil.copy2)
        else:
            shutil.copy2(kept, path)


def gates(r):
    return dict((x['id'], x['verdict']) for x in (r or {}).get('gates', []))


def gval(r, gid):
    x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
    return x[-1]['value'] + (' | ' + x[-1]['note'] if x[-1].get('note') else '') if x else ''


def gthr(r, gid):
    x = [g for g in (r or {}).get('gates', []) if g['id'] == gid]
    return x[-1].get('threshold') if x else None


def vlines(r, tag):
    return [(v, t, x) for v, t, x in ((r or {}).get('outputs') or {}).get('lines') or [] if t == tag]


def first(r, tag):
    ls = vlines(r, tag)
    return ls[-1] if ls else (None, tag, '')


# ======================================================================================================== function level
def function_cases(T, case, S, XW, C):
    D = os.path.join(T, 'r2c_fn')
    os.makedirs(D)
    # ---- M110: the fixture against F0280's files, the helper against the old readers
    got, rows = [], []
    for fo, w, s, e, x, m5 in F0280:
        t = isce_xml('%s/20091111/20091111.slc' % fo, w, s, e, x)
        f = os.path.join(D, '%s__20091111.slc.xml%s' % (fo.replace('/', '__'), '' if s == w else '.bak9376'))
        open(f, 'w').write(t)
        wi, le, pr = XW.check(f)
        got.append(hashlib.md5(t.encode()).hexdigest() == m5)
        rows.append((fo, s == w, wi, le, pr, old_width(t)))
    ok = all(got) and all(o == 9344 for *_, o in rows) and all(
        (wi, le) == ((9344, 18432) if same else (9376, 18432)) and (not pr if same else
                                                                     pr == ['the width property 9344, coordinate1\'s size 9376: isce2 loads 9376 (25.4)'])
        for _, same, wi, le, pr, _ in rows)
    wbak, _, pbak = XW.check(os.path.join(D, 'SLC__20091111.slc.xml.bak9376'), 9344, 'the shelve\'s samples')
    case('M110 (25-b, 25.4) the fixture: XML_LINES with F0280\'s values gives its five .xml byte for byte (S42b\'s md5s); lp_xmlwidth '
         'reads the two .xml 9,344 by 18,432 with no problem, the two .xml.bak9376 and raw_fbs_unpacked/\'s 9,376 (isce2\'s width) '
         'with the width property 9,344 named; the old readers read 9,344 on all five; with the gate\'s 9,344 given, its size named too',
         ok and wbak == 9376 and any('the shelve\'s samples 9344' in x for x in pbak),
         'md5 %s; %s; with want: %s' % (got, [(fo, wi, le, len(pr), o) for fo, _, wi, le, pr, o in rows], pbak))

    # ---- M111: the helper's rules on variants, as isce2 2.6.3 loads them (the emulation's widths, run at the build)
    good = isce_xml('SLC/20091111/20091111.slc', 9344, 9344, 9344, 9344)
    bak = isce_xml('SLC/20091111/20091111.slc', 9344, 9376, 9376, 9376)

    def sub(pat, rep, s):
        r, n = re.subn(pat, rep, s, count=1, flags=re.S)
        assert n == 1, pat
        return r
    sz = r'<property name="size">\s*<value>%d</value>\s*<doc>Coordinate size.</doc>\s*</property>'
    mock = ('<imageFile>\n    <property name="data_type">\n        <value>CFLOAT</value>\n    </property>\n    <property name="file_name">'
            '\n        <value>SLC/x/x.slc</value>\n    </property>\n    <property name="length">\n        <value>18432</value>\n    '
            '</property>\n    <property name="width">\n        <value>1000</value>\n    </property>\n    <component name="coordinate1">'
            '\n    <property name="size">\n        <value>1000</value>\n    </property>\n    </component>\n    <component '
            'name="coordinate2">\n    <property name="size">\n        <value>18432</value>\n    </property>\n    </component>\n</imageFile>\n')
    V = [   # (tag, text, the width isce2 loads, a problem expected, a word the problem holds)
        ('width1234', sub(r'(<property name="width">\s*<value>)9344(</value>)', r'\g<1>1234\2', bak), 9376, True, 'property 1234'),
        ('nowidth', sub(r'\s*<property name="width">.*?</property>', '', bak), 9376, True, 'no width property'),
        ('size1234', sub(r'(<property name="size">\s*<value>)9376(</value>)', r'\g<1>1234\2', bak), 1234, True, 'endingValue 9376'),
        ('nocoord1', sub(r'\s*<component name="coordinate1">.*?</component>', '', bak), None, True, 'no coordinate1'),
        ('w9376c9344', sub(r'(<property name="width">\s*<value>)9344(</value>)', r'\g<1>9376\2', good), 9344, True, 'property 9376'),
        ('good_upper', good.replace('name="width"', 'name="WIDTH"').replace('name="coordinate1"', 'name="COORDINATE1"')
         .replace('name="size"', 'name=" Size "'), 9344, False, ''),
        ('bak_upper', bak.replace('name="size"', 'name="SIZE"').replace('name="coordinate1"', 'name="Coordinate1"'), 9376, True,
         'property 9344'),
        ('good_attr', sub(sz % 9344, '<property name="size" value="9344"/>', good), 9344, False, ''),
        ('bak_attr', sub(sz % 9376, '<property name="size" value="9376"/>', bak), 9376, True, 'property 9344'),
        ('good_text', sub(sz % 9344, '<property name="size">9344</property>', good), 9344, False, ''),
        ('good_float', good.replace('<value>9344</value>', '<value>9344.0</value>'), 9344, False, ''),
        ('good_delta2', sub(r'(<property name="delta">\s*<value>)1(</value>)', r'\g<1>2\2', good), 9344, True, '= 18688'),
        ('good_start10', sub(r'(<property name="startingvalue">\s*<value>)0(</value>)', r'\g<1>10\2', good), 9344, True, '= 9354'),
        ('good_noend', sub(r'\s*<property name="endingvalue">.*?</property>', '', good), 9344, False, ''),
        ('good_noxmax', sub(r'\s*<property name="xmax">.*?</property>', '', good), 9344, False, ''),
        ('good_dupwidth', good.replace('</imageFile>', '    <property name="width">\n        <value>9376</value>\n    </property>\n'
                                                       '</imageFile>'), 9344, True, 'property 9376'),
        ('good_len_off', sub(r'(<property name="length">\s*<value>)18432(</value>)', r'\g<1>18400\2', good), 9344, True,
         'length property 18400'),
        ('good_nosize', sub(r'\s*<property name="size">\s*<value>9344</value>.*?</property>', '', good), None, True, 'has no size'),
        ('mock_render', mock, 1000, False, ''),
        ('notxml', '<imageFile><property name="width"><value>9344</value></property>', None, True, 'malformed'),
    ]
    bad, same_old = [], []
    for tag, text, wexp, pexp, word in V:
        f = os.path.join(D, 'variant_%s.xml' % tag)
        open(f, 'w').write(text)
        w, _, pr = XW.check(f)
        if w != wexp or bool(pr) != pexp or (word and not any(word in x for x in pr)):
            bad.append('%s: width %s, problems %s' % (tag, w, pr))
        if not pexp and old_width(text) is not None:
            same_old.append(w == old_width(text))
    w0, _, p0 = XW.check(os.path.join(D, 'absent.xml'))
    case('M111 (25-b) lp_xmlwidth on %d variants of the fixture reads the width isce2 2.6.3\'s own Configurable.load gives (name case '
         'and spacing, the value attribute and text styles, floats, a name given twice keeping the last, the width property or '
         'coordinate1 or its size absent, endingValue and xmax against startingValue + size x delta, the length rule, the mock '
         'unpacker\'s form), a problem exactly where the file disagrees within itself (or is not XML, or absent); where they agree '
         'it reads what the old readers read' % len(V),
         not bad and w0 is None and p0 and p0[0].startswith('unreadable') and same_old and all(same_old),
         '%s; agree with the old reading on %d of %d; absent: %s' % ('; '.join(bad) or 'every variant as isce2 reads it',
                                                                       sum(same_old), len(same_old), p0))

    # ---- M100c: the NaN form against the old form, on finite values, inf and NaN
    import linog_verify_frame_d6 as V6
    import lp_datum as DM
    vals = (0.0, 5e-7, 1e-6, 1.1e-6, -2e-6, 9.9e-5, 1.2e-4, 1e-3, float('inf'), float('-inf'), float('nan'))
    W6 = os.path.join(D, 'w6')
    os.makedirs(os.path.join(W6, 'recon'))
    diff, nanoff = [], []
    for v in vals:   # the copy's R9 lines (datum_r9) on one off date
        plan = {'20070101': (0.0, 0.0), '20070201': (0.5, 1.0), '20070301': (-0.25, 2.0)}
        for key, i in (('rg', 1), ('az', 0)):
            post = dict((d, list(x)) for d, x in plan.items())
            post['20070201'][i] += v
            out = []
            with contextlib.redirect_stdout(io.StringIO()):   # the copy's "N22 modes from" line
                V6.datum_r9(W6, lambda s, t, m: out.append((s, t, m)), dict((d, tuple(x)) for d, x in post.items()), plan, {},
                            '20070101', set(['20070101', '20070201']), 'test', None)
            new = [s for s, t, m in out if t == ('N22' if key == 'rg' else 'G16')][0] == 'FAIL'
            dv = post['20070201'][i] - plan['20070201'][i]
            old = abs(dv) > 1e-6
            if v == v:
                diff.append(new != old)
            else:
                nanoff.append(new and not old)
    W7 = os.path.join(D, 'w7')   # the G16 relation (datum's kit lines) with the shelves read by a stand-in
    os.makedirs(os.path.join(W7, 'refineSecondaryTiming', 'dates_predatum_bak_X'))
    os.makedirs(os.path.join(W7, 'recon'))
    json.dump(dict(dates=[dict(date='20070101', mode='FBS'), dict(date='20070201', mode='FBS'), dict(date='20070301', mode='FBD')]),
              open(os.path.join(W7, 'recon', 'modes.json'), 'w'))
    saved = (V6.load_dates, V6.coreg_ref)
    try:
        V6.coreg_ref = lambda W: ('20070101', 'the test')
        for v in vals:
            for i in (1, 0):
                pre = {'20070101': (0.3, 0.8), '20070201': (0.1, -0.2), '20070301': (0.2, 0.4)}
                post = {'20070101': (0.0, 0.0), '20070201': [0.1 - 0.3, -0.2 - 0.8], '20070301': [0.2 - 0.3, 0.4 - 0.4]}
                post['20070301'][i] += v
                V6.load_dates = lambda root, pre=pre, post=post: dict(pre) if 'predatum' in root else dict(
                    (d, tuple(x)) for d, x in post.items())
                out = []
                with contextlib.redirect_stdout(io.StringIO()):
                    V6.datum(W7, lambda s, t, m: out.append((s, t, m)))
                tag = 'N22' if i == 1 else 'G16'
                new = [s for s, t, m in out if t == tag][-1] == 'FAIL'
                if i == 1:
                    dv = abs((post['20070301'][1] - pre['20070301'][1]) - (-0.8 * 0.5))
                    old = dv > 1e-4
                else:
                    old = abs((post['20070301'][0] - pre['20070301'][0]) - (-0.3)) > 1e-4
                if v == v:
                    diff.append(new != old)
                else:
                    nanoff.append(new and not old)
    finally:
        V6.load_dates, V6.coreg_ref = saved
    for v in vals:   # datum's G16 after the write
        plan = {'20070101': (0.0, 0.0), '20070201': (0.5, 1.0)}
        for i in (0, 1):
            after = dict((d, list(x)) for d, x in plan.items())
            after['20070201'][i] += v
            after = dict((d, tuple(x)) for d, x in after.items())
            new = bool(DM.g16_off(after, plan, '20070101'))
            old = any(abs(az - plan[d][0]) > DM.R9_G16 or abs(rg - plan[d][1]) > DM.R9_G16 for d, (az, rg) in after.items())
            if v == v:
                diff.append(new != old)
            else:
                nanoff.append(new and not old)
    case('M100c (P6R-01) the NaN form against the old one at the function level, on 0, 5e-7, 1e-6, 1.1e-6, -2e-6, 9.9e-5, 1.2e-4, 1e-3, '
         '+-inf and NaN '
         'in range and azimuth: the verifier copy\'s R9 lines (datum_r9), its G16 relation (datum, the kit\'s lines, shelves read by a '
         'stand-in) and datum\'s G16 after the write (lp_datum.g16_off): the same verdict as the old form on every finite value and '
         'inf, and off on NaN where the old form read it as on',
         diff and not any(diff) and nanoff and all(nanoff),
         '%d comparisons on finite and inf values, %d differ; %d on NaN, %d off where the old form was on' % (
             len(diff), sum(diff), len(nanoff), sum(nanoff)))

    # ---- M108b: coreg_ref's fallback on synthetic frames
    def frame(name, widths, bak_date=None, cfg_ref=None, ref_json=None):
        W = os.path.join(D, name)
        for d, w in widths.items():
            os.makedirs(os.path.join(W, 'SLC', d))
            s = w + 32 if d == bak_date else w
            open(os.path.join(W, 'SLC', d, '%s.slc.xml' % d), 'w').write(isce_xml('SLC/%s/%s.slc' % (d, d), w, s, s, s))
        if cfg_ref:
            os.makedirs(os.path.join(W, 'configs'))
            open(os.path.join(W, 'configs', 'config_fineResamp_%s' % cfg_ref), 'w').write('[Common]\nreference : %s/SLC/%s\n' % (W, cfg_ref))
        if ref_json:
            os.makedirs(os.path.join(W, 'recon'))
            json.dump(dict(reference=ref_json), open(os.path.join(W, 'recon', 'reference.json'), 'w'))
        return W
    ws = {'20070101': 4640, '20070201': 9344, '20070301': 4640}
    r1 = V6.coreg_ref(frame('cr1', ws))
    r2 = V6.coreg_ref(frame('cr2', dict(ws, **{'20070301': 9344})))
    r3 = V6.coreg_ref(frame('cr3', ws, bak_date='20070201'))
    r4 = V6.coreg_ref(frame('cr4', ws, cfg_ref='20070301'))
    r5 = V6.coreg_ref(frame('cr5', dict(ws, **{'20070301': 9344}), ref_json='20070301'))
    old2 = [d for d in sorted(ws) if d != '20070101'][0]   # the kit's heuristic: the first SLC/*/ not 4640 wide by the property
    case('M108b (P6R-14, 25-b) coreg_ref\'s fallback on synthetic frames: one date of three not 4640 wide (isce2\'s form) named by the '
         'heuristic; two not 4640 wide: none (the old heuristic named the first, %s); the one in the backups\' state (its property '
         '9,344, coordinate1 9,376): none (the old heuristic named it by its property); a fineResamp config first; '
         'recon/reference.json before the heuristic' % old2,
         r1[0] == '20070201' and 'the one SLC/*/' in r1[1] and r2 == (None, None) and r3 == (None, None)
         and r4 == ('20070301', 'configs/config_fineResamp_*') and r5 == ('20070301', 'recon/reference.json'),
         'one %s; two %s; backups\' state %s; configs %s; reference.json %s' % (r1, r2, r3, r4, r5))


# ======================================================================================================== the ascending frame
def frame_asc(T, case, S, H, XW, C, table):
    """Every phase-level case on one ascending mixed full-height frame (a frame to accept takes about 5.5 GB of the mock's data:
    one such frame in this suite, 13p6 runs M84's own frame 3354): 25-b's gates while it is run a phase at a time, then P6R-06
    to rerun, the package cases, the accept cases (each one thing changed and put back), M84f's planted v0.12 datum, datum last."""
    root = 'ca'
    W = H.fd(root)
    RT = os.path.join(W, 'refineSecondaryTiming')
    rj = os.path.join(W, 'status', 'P4c_datum.json')

    def reference_json():
        f = os.path.join(W, 'recon', 'reference.json')
        return (json.load(open(f)) if os.path.isfile(f) else {}).get('reference')

    # ---- M112 (25-b): reference's G17, the frame to reference first (D1 names the reference)
    rc0, _ = H.run(root, ['--to', 'reference'])
    REF = reference_json()
    xf = os.path.join(W, 'SLC', REF or '-', '%s.slc.xml' % REF)
    if rc0 != 0 or not REF or not os.path.isfile(xf):
        case('M84b-M114 not run: the ascending frame to reference: rc %d, reference %s' % (rc0, REF), False)
        return
    mock_text = open(xf).read()
    width, length, _ = XW.check(xf)
    fn = re.search(r'name="file_name">\s*<value>([^<]*)<', mock_text)
    rel = fn.group(1) if fn else 'SLC/%s/%s.slc' % (REF, REF)
    kept = H.keep(xf, 'xml')

    def edit(size):
        with open(xf, 'w') as fh:
            fh.write(isce_xml(rel, width, size, size, size, length))
    edit(width)
    rca, _ = H.run(root, ['--only', 'reference'])
    ra = H.rec(root, '2b', 'reference')
    edit(width + 32)
    rcb, _ = H.run(root, ['--only', 'reference'])
    rb = H.rec(root, '2b', 'reference')
    H.put(kept, xf, 'm112')
    rcc, _ = H.run(root, ['--to', 'reference'])
    rr = H.rec(root, '2b', 'reference')
    case('M112 (25-b) reference\'s G17 on %s\'s .slc.xml: in isce2\'s form (F0280\'s fields, %d wide by every field): PASS; in the backups\' '
         'state (the width property %d, coordinate1\'s size, endingValue and xmax %d): FAIL naming the property and the size, the .xml '
         'read %d wide among the readers (the property agreed with them: the old reading passed it); the mock\'s .xml put back: PASS' % (
             REF, width, width, width + 32, width + 32),
         rca == 0 and gates(ra).get('G17') == 'PASS' and rcb == 2 and gates(rb).get('G17') == 'FAIL'
         and 'xml %d x %d' % (width + 32, length) in gval(rb, 'G17')
         and 'the width property %d, coordinate1\'s size %d: isce2 loads %d (25.4)' % (width, width + 32, width + 32) in gval(rb, 'G17')
         and old_width(isce_xml(rel, width, width + 32, width + 32, width + 32, length)) == width
         and rcc == 0 and gates(rr).get('G17') == 'PASS' and reference_json() == REF,
         'rc %d %s; rc %d %s; rc %d %s; reference %s' % (rca, gates(ra).get('G17'), rcb, gval(rb, 'G17')[:220], rcc,
                                                      gates(rr).get('G17'), reference_json()))

    # ---- M113 (25-b): topo's G3a.14
    rc1, _ = H.run(root, ['--to', 'stack2'])
    edit(width + 32)
    rc2, _ = H.run(root, ['--only', 'topo'])
    rt = H.rec(root, '3a', 'topo')
    H.put(kept, xf, 'm113')
    moved = []
    for g in ('merged/geom_reference', 'geom_reference'):
        if os.path.isdir(os.path.join(W, g)):
            dst = os.path.join(W, '_archive', 'r2c_m113_%s' % g.replace('/', '_'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(os.path.join(W, g), dst)
            moved.append(g)
    rc3, _ = H.run(root, ['--to', 'topo'])
    rt2 = H.rec(root, '3a', 'topo')
    case('M113 (25-b) topo\'s G3a.14 with %s\'s .slc.xml in the backups\' state (topo alone after stack2): FAIL naming the property and '
         'the size, the reference SLC read %d wide (isce2\'s width) against the geometry\'s %d, rc 2; the .xml put back and topo\'s outputs '
         'moved into the frame\'s _archive/ (%s): topo again, G3a.14 PASS' % (REF, width + 32, width, ', '.join(moved) or 'none'),
         rc1 == 0 and rc2 == 2 and gates(rt).get('G3a.14') == 'FAIL' and 'the reference SLC %d, the geometry %d' % (width + 32, width) in
         gval(rt, 'G3a.14') and 'coordinate1\'s size %d' % (width + 32) in gval(rt, 'G3a.14') and len(moved) == 2 and rc3 == 0
         and gates(rt2).get('G3a.14') == 'PASS',
         'stack2 rc %d; rc %d %s; then rc %d %s' % (rc1, rc2, gval(rt, 'G3a.14')[:220], rc3, gates(rt2).get('G3a.14')))

    # ---- M114 (25-b): igram's G17, then the frame to rerun (M103)
    rc4, _ = H.run(root, ['--to', 'bgrid'])
    edit(width + 32)
    rc5, _ = H.run(root, ['--only', 'igram'])
    ri = H.rec(root, '4f', 'igram')
    no_igrams = not os.path.isdir(os.path.join(W, 'Igrams'))
    H.put(kept, xf, 'm114')
    rc, out = H.run(root, ['--to', 'rerun'])
    ri2 = H.rec(root, '4f', 'igram')
    case('M114 (25-b) igram\'s G17 with %s\'s .slc.xml in the backups\' state (igram alone after bgrid): FAIL naming coordinate1\'s size '
         '%d against the geometry\'s width %d and the width property, run_08 not run (no Igrams/), rc 2 (the old G17 read no width '
         'field of the .xml); put back, the frame on: igram PASS, its G17 "%d wide as isce2 loads it"' % (REF, width + 32, width, width),
         rc4 == 0 and rc5 == 2 and gates(ri).get('G17') == 'FAIL' and no_igrams
         and 'coordinate1\'s size %d (the width isce2 loads), the geometry\'s width %d' % (width + 32, width) in gval(ri, 'G17')
         and 'the width property %d' % width in gval(ri, 'G17') and ri2.get('verdict') == 'PASS'
         and '.slc.xml %d wide as isce2 loads it' % width in gval(ri2, 'G17'),
         'bgrid rc %d; rc %d %s; then %s %s' % (rc4, rc5, gval(ri, 'G17')[-220:], ri2.get('verdict'), gval(ri2, 'G17')[:120]))

    # ---- M103 (P6R-06): the ascending frame through package and rerun
    R = dict((ph, H.rec(root, i, ph)) for i, ph in (('0a', 'recon'), ('1c', 'verify'), ('4g', 'report'), ('6a', 'deliver'),
                                                    ('6b', 'accept'), ('6c', 'package'), ('6d', 'rerun')))
    op = R['package'].get('outputs') or {}
    day = (R['package'].get('start') or '')[:10].replace('-', '')
    pk = '_xfer/LINOG_ASC_P447F0310_v0.1_%s_review' % day
    q = {}
    for ln in open(os.path.join(S.HERE, 'linog_phase6.cfg')):
        if '=' in ln and not ln.lstrip().startswith('#'):
            k_, v_ = ln.strip().split('=', 1)
            q[k_.strip()] = v_.strip()

    def fp(prefix):   # package's fingerprint from the records, by a prefix (lp_package.py's, LOGIC 2)
        return C.md5_obj(dict(logic=2, deliver=(R['deliver'].get('outputs') or {}).get('digest'),
                              report=(R['report'].get('outputs') or {}).get('digest'), accept=R['accept'].get('fingerprint'),
                              keys=[q.get('XFER'), prefix, q.get('PACKAGE_VERSION')]))
    mf = os.path.join(W, 'RUN_MANIFEST.json')
    man = json.load(open(mf)) if os.path.isfile(mf) else {}
    case('M103 (P6R-06) the ascending mixed frame P447 F0310 (M84\'s 12 dates on path 447, 8 FBS and 4 FBD; the installed table\'s '
         '[p447]) on to rerun under --decide auto: rc 0; G0.6 PASS (path table A, frame rule A, suffixes A); verify\'s G3b ASCENDING; '
         'datum R9; package %s with G6c.0 PASS (A) and G6c.2 PASS; package\'s fingerprint by LINOG_ASC (not LINOG_DESC); rerun PASS; '
         'RUN_MANIFEST.json\'s direction ascending' % pk,
         rc == 0 and all(r.get('verdict') == 'PASS' for r in R.values()) and 'path table A, frame rule A' in gval(R['recon'], 'G0.6')
         and 'ASCENDING' in gval(R['verify'], 'G3b') and (H.rec(root, '4c', 'datum').get('outputs') or {}).get('method') == 'R9'
         and op.get('package') == pk and gates(R['package']).get('G6c.0') == 'PASS' and gates(R['package']).get('G6c.2') == 'PASS'
         and R['package'].get('fingerprint') == fp('LINOG_ASC') != fp('LINOG_DESC') and (man.get('frame') or {}).get('direction') == 'ascending',
         'rc %d; %s; G0.6 %s; package %s, fingerprint %s (by LINOG_ASC %s); direction %s' % (
             rc, dict((k, r.get('verdict')) for k, r in R.items()), gval(R['recon'], 'G0.6')[:60], op.get('package'),
             R['package'].get('fingerprint'), fp('LINOG_ASC'), (man.get('frame') or {}).get('direction')))
    if rc != 0 or op.get('package') != pk or R['accept'].get('verdict') != 'PASS':
        case('M84b-M109 not run: the ascending frame did not reach rerun with its package (rc %d, %s)' % (rc, op.get('package')), False)
        return
    MODES = dict((x['date'], x.get('mode')) for x in json.load(open(os.path.join(W, 'recon', 'modes.json'))).get('dates', []))
    FBS = [d for d in sorted(MODES) if MODES[d] == 'FBS' and d != REF]
    FBD = [d for d in sorted(MODES) if MODES[d] == 'FBD']

    # ---- M103b, M109 (P6R-06, P6R-11): package forced again; another prefix in the way
    rc1, _ = H.run(root, ['--only', 'package', '--force', 'package'])
    r1 = H.rec(root, '6c', 'package')
    case('M103b (P6R-06) the ascending frame\'s package forced again: G6c.2 DECISION naming %s, rc 4' % pk,
         rc1 == 4 and gates(r1).get('G6c.2') == 'DECISION' and pk in gval(r1, 'G6c.2'), 'rc %d; G6c.2 %s' % (rc1, gval(r1, 'G6c.2')[:160]))
    arch = os.path.join(W, '_archive')
    os.makedirs(arch, exist_ok=True)
    os.rename(os.path.join(W, pk), os.path.join(arch, os.path.basename(pk)))
    desc = '_xfer/LINOG_DESC_P447F0310_v0.1_20261019_review'
    os.makedirs(os.path.join(W, desc))
    rc2, _ = H.run(root, ['--only', 'package', '--force', 'package'])
    r2 = H.rec(root, '6c', 'package')
    os.rename(os.path.join(W, desc), os.path.join(arch, 'r2c_plant_' + os.path.basename(desc)))
    os.rename(os.path.join(arch, os.path.basename(pk)), os.path.join(W, pk))
    case('M109 (P6R-11) the ascending frame\'s package moved into its _archive/ and a folder %s planted: package forced: G6c.2 '
         'DECISION naming it, under another prefix than LINOG_ASC, its glob _xfer/*_P447F0310_v0.1_*_review (the old glob looked for '
         'LINOG_ASC only: PASS, a second package beside it), rc 4' % desc,
         rc2 == 4 and gates(r2).get('G6c.2') == 'DECISION' and desc in gval(r2, 'G6c.2') and 'another prefix' in gval(r2, 'G6c.2')
         and gthr(r2, 'G6c.2') == '_xfer/*_P447F0310_v0.1_*_review absent',
         'rc %d; G6c.2 %s; its threshold %s' % (rc2, gval(r2, 'G6c.2')[:220], gthr(r2, 'G6c.2')))

    # ---- M104 (P6R-08), M106 (P6R-13) on the run's accept
    ra = R['accept']
    r9l = first(ra, 'R9')
    case('M104 (P6R-08) the run\'s accept (LOGIC 3) PASS: the copy\'s line R9 checks the plan against R9\'s arithmetic in the record (x by '
         'its SLR and PRF, x(REF) 0, each SLR recon/modes.json\'s and the modes\' ratio) on 12 dates: PASS; N22 by R9\'s plan',
         ra.get('logic') == 3 and r9l[0] == 'PASS' and 'on 12 dates: 0 off' in r9l[2] and first(ra, 'N22')[0] == 'PASS'
         and 'by R9\'s plan' in first(ra, 'N22')[2] and gates(ra).get('G6b.6') == 'PASS',
         'logic %s; R9 %s; N22 %s' % (ra.get('logic'), r9l, first(ra, 'N22')[2][:90]))
    s0 = H.state(root, 'accept')
    kj = H.keep(rj, 'm106')
    rec4c = json.load(open(rj))
    rec4c['r2c_probe'] = 'one field more (M106)'
    json.dump(rec4c, open(rj, 'w'), indent=1)
    s1 = H.state(root, 'accept')
    H.put(kj, rj, 'm106')
    s2 = H.state(root, 'accept')
    inp = (ra.get('inputs') or {}).get('datum_record') or {}
    case('M106 (P6R-13) accept and the datum record it reads: --state CURRENT after the run; the record rewritten with one field more '
         '(its plan untouched): STALE (the old fingerprint held no datum record: CURRENT); put back: CURRENT; the record\'s md5 in '
         'accept\'s inputs; G6b.8 PASS',
         s0 == (0, 'CURRENT') and s1 == (0, 'STALE') and s2 == (0, 'CURRENT') and inp.get('md5') == C.md5_file(rj)
         and gates(ra).get('G6b.8') == 'PASS', 'states %s, %s, %s; inputs %s' % (s0, s1, s2, inp))

    def acc():
        rc_, _ = H.run(root, ['--only', 'accept', '--force', 'accept'])
        return rc_, H.rec(root, '6b', 'accept')

    def rewrite(f):
        r = json.load(open(rj))
        out_ = f(r)
        json.dump(r if out_ is None else out_, open(rj, 'w'), indent=1)

    # ---- M84b (P6R-05): an FBS secondary's azimuth moved 2e-6
    d = FBS[0]
    kd = H.keep(os.path.join(RT, 'dates', d), 'm84b')
    _, sh = H.shelves(W, 'read')
    az0 = ((sh or {}).get('post') or {}).get(d, [None])[0] if isinstance(sh, dict) else None
    rce, je = H.shelves(W, 'set', d, 'az', repr(az0 + 2e-6)) if az0 is not None else (1, None)
    rc1, r1 = acc()
    H.put(kd, os.path.join(RT, 'dates', d), 'm84b')
    g16 = first(r1, 'G16')
    case('M84b (P6R-05) %s\'s dates/ azimuth constant moved 2e-6 lines by hand: accept forced: G16 FAIL by R9\'s plan, its off dates '
         'listed as N22 lists its own; N22 PASS; G6b.6 FAIL, rc 2' % d,
         rce == 0 and rc1 == 2 and g16[0] == 'FAIL' and 'by R9\'s plan: 1 off by more than 1e-6' in g16[2] and ': %s)' % d in g16[2]
         and first(r1, 'N22')[0] == 'PASS' and gates(r1).get('G6b.6') == 'FAIL',
         'edit rc %s %s; rc %d; G16 %s; N22 %s' % (rce, je, rc1, g16[2][:140], first(r1, 'N22')[0]))

    # ---- M84c (P6R-04, 05): an FBD secondary's folder aside
    d = FBD[0]
    src, side = os.path.join(RT, 'dates', d), os.path.join(T, '_r2c_keep', 'm84c_%s' % d)
    os.makedirs(os.path.dirname(side), exist_ok=True)
    os.rename(src, side)
    rc1, r1 = acc()
    os.rename(side, src)
    n22, g16 = first(r1, 'N22'), first(r1, 'G16')
    case('M84c (P6R-04, P6R-05) %s\'s dates/ folder moved aside: accept forced: N22 and G16 FAIL naming it "in the plan only" (the old '
         'line: "dates/ and the plan differ in", and G16 named none), rc 2' % d,
         rc1 == 2 and n22[0] == 'FAIL' and g16[0] == 'FAIL' and 'in the plan only: %s' % d in n22[2] and 'in the plan only: %s' % d in g16[2]
         and 'in dates/ only' not in n22[2], 'rc %d; N22 %s | G16 %s' % (rc1, n22[2][-90:], g16[2][-90:]))

    # ---- M84d (P6R-04, 05): the plan without that date
    kj = H.keep(rj, 'm84d')
    rewrite(lambda r: r['outputs']['plan'].pop(d, None) and None)
    rc1, r1 = acc()
    H.put(kj, rj, 'm84d')
    n22, g16 = first(r1, 'N22'), first(r1, 'G16')
    case('M84d (P6R-04, P6R-05) the datum record\'s plan without %s (a copy of the record edited): accept forced: N22 and G16 FAIL '
         'naming it "in dates/ only"; the R9 line on the plan\'s 11 dates PASS, rc 2' % d,
         rc1 == 2 and n22[0] == 'FAIL' and g16[0] == 'FAIL' and 'in dates/ only: %s' % d in n22[2] and 'in dates/ only: %s' % d in g16[2]
         and first(r1, 'R9')[0] == 'PASS' and 'on 11 dates' in first(r1, 'R9')[2],
         'rc %d; N22 %s | G16 %s | R9 %s' % (rc1, n22[2][-70:], g16[2][-70:], first(r1, 'R9')[2][-40:]))

    # ---- M84e (P6R-05): the datum record aside
    kj = H.keep(rj, 'm84e')
    S.aside(T, rj, 'r2c_m84e')
    rc1, r1 = acc()
    H.put(kj, rj, 'm84e')
    n22 = first(r1, 'N22')
    case('M84e (P6R-05) the datum record moved aside (a frame without status/P4c_datum.json): the copy takes G16\'s relation with the '
         'table\'s factors, which R9\'s values do not satisfy: N22 FAIL "range datum: 7 FBS + 4 FBD secondaries, N wrong", no "by '
         'R9\'s plan" line, no R9 line, rc 2',
         rc1 == 2 and n22[0] == 'FAIL' and re.search(r'^range datum: 7 FBS \+ 4 FBD secondaries, \d+ wrong', n22[2])
         and 'R9\'s plan' not in n22[2] and not vlines(r1, 'R9'), 'rc %d; N22 %s; G16 %s' % (rc1, n22[2][:110], first(r1, 'G16')[2][:80]))

    # ---- M100 (P6R-01): an FBD secondary's range constant NaN
    d = FBD[1]
    kd = H.keep(os.path.join(RT, 'dates', d), 'm100')
    rce, je = H.shelves(W, 'set', d, 'rg', 'nan')
    rc1, r1 = acc()
    H.put(kd, os.path.join(RT, 'dates', d), 'm100')
    n22 = first(r1, 'N22')
    case('M100 (P6R-01) %s\'s dates/ range constant set to NaN by hand: accept forced: N22 FAIL naming it (worst off +nan; the old form '
         'abs(nan) > 1e-6 is %s: it read the date as on), G6b.6 FAIL, rc 2' % (d, abs(float('nan')) > 1e-6),
         rce == 0 and rc1 == 2 and n22[0] == 'FAIL' and 'worst %s off +nan: %s' % (d, d) in n22[2] and gates(r1).get('G6b.6') == 'FAIL',
         'edit rc %s %s; rc %d; N22 %s' % (rce, je, rc1, n22[2][-100:]))

    # ---- M100b (P6R-01, 03): a plan value NaN in the record
    kj = H.keep(rj, 'm100b')
    rewrite(lambda r: r['outputs']['plan'].update({d: [float('nan'), r['outputs']['plan'][d][1]]}))
    rc1, r1 = acc()
    H.put(kj, rj, 'm100b')
    n22, g16 = first(r1, 'N22'), first(r1, 'G16')
    case('M100b (P6R-01, P6R-03) the record\'s plan for %s with a NaN: no plan from it: N22 and G16 FAIL naming status/P4c_datum.json '
         'and the date; G6b.5 PASS (the modes line printed), rc 2' % d,
         rc1 == 2 and n22[0] == g16[0] == 'FAIL' and 'status/P4c_datum.json says method R9; its plan\'s values not a pair of finite '
         'numbers: %s' % d in n22[2] and 'status/P4c_datum.json' in g16[2] and gates(r1).get('G6b.5') == 'PASS',
         'rc %d; N22 %s; G6b.5 %s' % (rc1, n22[2][:150], gates(r1).get('G6b.5')))

    # ---- M101 (P6R-02): the pre-datum copy aside
    bk = sorted(glob.glob(os.path.join(RT, 'dates_predatum_bak_*')))
    os.makedirs(os.path.join(T, '_r2c_keep'), exist_ok=True)
    asides = []
    for b in bk:
        x = os.path.join(T, '_r2c_keep', 'm101_%s' % os.path.basename(b))
        os.rename(b, x)
        asides.append((x, b))
    rc1, r1 = acc()
    for x, b in asides:
        os.rename(x, b)
    case('M101 (P6R-02) the frame\'s pre-datum copy (%d folder) moved aside: accept forced: PASS, N22 and G16 by R9\'s plan with no N23 '
         'line, G6b.5 PASS (the old copy read the plan only past the copy\'s checks: WARN N23, then G6b.5 FAIL)' % len(bk),
         len(bk) == 1 and rc1 == 0 and r1.get('verdict') == 'PASS' and 'by R9\'s plan' in first(r1, 'N22')[2] and not vlines(r1, 'N23')
         and gates(r1).get('G6b.5') == 'PASS',
         'rc %d; N22 %s; N23 %s; G6b.5 %s' % (rc1, first(r1, 'N22')[2][:80], vlines(r1, 'N23'), gates(r1).get('G6b.5')))

    # ---- M102a to M102e (P6R-03): the datum record in five forms that give no plan
    for tag, f, want, desc_ in (
            ('M102a', None, 'unreadable (JSONDecodeError)', 'cut short (not JSON)'),
            ('M102b', lambda r: r.update(verdict='FAIL'), 'says method R9 but reads verdict FAIL', 'saying R9 with verdict FAIL'),
            ('M102c', lambda r: r['outputs'].update(planned=True, dryrun=True), 'in a dry run\'s record', 'as a dry run\'s (planned, dryrun)'),
            ('M102d', lambda r: r['outputs'].pop('plan') and None, 'says method R9 with no plan', 'saying R9 with no plan'),
            ('M102e', lambda r: [r], 'is not a datum record (its top level is a list)', 'a list around the record')):
        kj = H.keep(rj, tag)
        if f is None:
            open(rj, 'w').write('{"not JSON')
        else:
            rewrite(f)
        rc1, r1 = acc()
        H.put(kj, rj, tag)
        n22, g16 = first(r1, 'N22'), first(r1, 'G16')
        case('%s (P6R-03) the datum record %s: accept forced: N22 and G16 FAIL naming status/P4c_datum.json and that it %s; G6b.5 PASS, '
             'rc 2' % (tag, desc_, want), rc1 == 2 and n22[0] == g16[0] == 'FAIL' and want in n22[2] and want in g16[2]
             and 'status/P4c_datum.json' in n22[2] and gates(r1).get('G6b.5') == 'PASS', 'rc %d; N22 %s' % (rc1, n22[2][:170]))

    # ---- M104b, M104c (P6R-08): R9's arithmetic against its record
    d = FBD[0]
    for tag, f, want in (
            ('M104b', lambda r: r['outputs']['r9']['x_rg'].update({d: r['outputs']['r9']['x_rg'][d] + 0.01}), 'x by SLR and PRF'),
            ('M104c', lambda r: r['outputs']['r9']['slr_prf'].update({d: [2 * r['outputs']['r9']['slr_prf'][d][0],
                                                                          r['outputs']['r9']['slr_prf'][d][1]]}), 'recon/modes.json\'s slr_m')):
        kj = H.keep(rj, tag)
        rewrite(f)
        rc1, r1 = acc()
        H.put(kj, rj, tag)
        r9l = first(r1, 'R9')
        case('%s (P6R-08) %s\'s %s in the record (its plan untouched): accept forced: R9 FAIL naming the date (%s); N22 and G16 PASS by '
             'the plan, rc 2' % (tag, d, 'r9.x_rg moved 0.01' if tag == 'M104b' else 'SLR in r9.slr_prf doubled', want),
             rc1 == 2 and r9l[0] == 'FAIL' and '%s ' % d in r9l[2] and want in r9l[2] and first(r1, 'N22')[0] == 'PASS'
             and first(r1, 'G16')[0] == 'PASS', 'rc %d; R9 %s' % (rc1, r9l[2][-170:]))

    # ---- M107 (P6R-10): a date out of recon/modes.json
    mj = os.path.join(W, 'recon', 'modes.json')
    km = H.keep(mj, 'm107')
    mo = json.load(open(mj))
    mo['dates'] = [x for x in mo['dates'] if x.get('date') != d]
    json.dump(mo, open(mj, 'w'), indent=1)
    rc1, r1 = acc()
    H.put(km, mj, 'm107')
    n22 = first(r1, 'N22')
    case('M107 (P6R-10) %s\'s row taken out of recon/modes.json (a copy kept): accept forced: N22 FAIL by R9\'s plan naming it "not in '
         'recon/modes.json" (it read as FBD), rc 2' % d,
         rc1 == 2 and n22[0] == 'FAIL' and 'not in recon/modes.json: %s' % d in n22[2], 'rc %d; N22 %s' % (rc1, n22[2][-110:]))

    # ---- M108 (P6R-14): the fineResamp configs aside
    cf = sorted(glob.glob(os.path.join(W, 'configs', 'config_fineResamp_*')))
    os.makedirs(os.path.join(T, '_r2c_keep'), exist_ok=True)
    xs = []
    for c in cf:
        x = os.path.join(T, '_r2c_keep', 'm108_%s' % os.path.basename(c))
        os.rename(c, x)
        xs.append((x, c))
    old_name = None
    for x in sorted(glob.glob(os.path.join(W, 'SLC', '*', '*.slc.xml'))):   # the kit's heuristic as the copy had it
        m = re.search(r'name="width".*?<value>(\d+)</value>', open(x).read(), re.S)
        if m and m.group(1) != '4640':
            old_name = os.path.basename(os.path.dirname(x))
            break
    rc1, r1 = acc()
    for x, c in xs:
        os.rename(x, c)
    zl = [m for v, t, m in vlines(r1, 'G16') if 'coreg reference' in m]
    case('M108 (P6R-14) the fineResamp configs (%d) moved aside: the copy names the reference %s from recon/reference.json, accept PASS '
         '(the old heuristic named %s, the first SLC/*/ .slc.xml not 4640 wide: the earliest FBS date of a mixed frame)' % (
             len(cf), REF, old_name),
         len(cf) >= 1 and rc1 == 0 and r1.get('verdict') == 'PASS' and zl and 'coreg reference %s (from recon/reference.json)' % REF in zl[0]
         and old_name is not None and old_name != REF, 'rc %d; %s' % (rc1, zl[:1]))

    # ---- M84f (P6R-05), M107b (P6R-10): v0.12's datum planted from datum's own record (G16's plan of invertMisreg's values)
    kd = H.keep(os.path.join(RT, 'dates'), 'm84f_dates')
    kj = H.keep(rj, 'm84f')
    v12 = ((json.load(open(rj)).get('outputs') or {}).get('r9') or {}).get('v12') or {}
    rcp, jp = H.shelves(W, 'plant', json.dumps(v12))
    rewrite(lambda r: r['outputs'].update(method='G16'))
    rc1, r1 = acc()
    km = H.keep(mj, 'm107b')
    mo = json.load(open(mj))
    mo['dates'] = [x for x in mo['dates'] if x.get('date') != REF]
    json.dump(mo, open(mj, 'w'), indent=1)
    rc2, r2 = acc()
    H.put(km, mj, 'm107b')
    H.put(kj, rj, 'm84f')
    H.put(kd, os.path.join(RT, 'dates'), 'm84f')
    rc3, r3 = acc()
    n22, n22b = first(r1, 'N22'), first(r2, 'N22')
    case('M84f (P6R-05; the review\'s "M86") v0.12\'s datum on the mixed frame (every date of dates/ set to the record\'s r9.v12, G16\'s '
         'plan of invertMisreg\'s values, and the record\'s method G16; the hook\'s whole run would need a second frame of this size): '
         'accept forced: N22 PASS by G16\'s relation through the table, 0.5 on its 4 FBD secondaries ("7 FBS + 4 FBD secondaries, 0 '
         'wrong"), G16 PASS; all put back: accept PASS by R9\'s plan again',
         rcp == 0 and len(v12) == 12 and rc1 == 0 and r1.get('verdict') == 'PASS' and n22[0] == 'PASS'
         and '7 FBS + 4 FBD secondaries, 0 wrong' in n22[2] and first(r1, 'G16')[0] == 'PASS' and rc3 == 0 and r3.get('verdict') == 'PASS'
         and 'by R9\'s plan' in first(r3, 'N22')[2],
         'plant rc %s %s; rc %d N22 %s; put back rc %d %s' % (rcp, str(jp)[:60], rc1, n22[2][:70], rc3, first(r3, 'N22')[2][:60]))
    case('M107b (P6R-10) on M84f\'s planted G16 frame the reference %s\'s row taken out of recon/modes.json: accept forced: N22 FAIL '
         'naming it "not in recon/modes.json" (the old copy read it as FBD and failed the dates at its factor without naming it), rc 2' % REF,
         rc2 == 2 and n22b[0] == 'FAIL' and 'not in recon/modes.json: %s' % REF in n22b[2], 'rc %d; N22 %s' % (rc2, n22b[2][-120:]))

    # ---- M105 (P6R-09): a direction neither A nor D
    tx = table('paths_r2c_dirX.cfg', direction='X')
    s1 = H.state(root, 'package', cfg=tx)
    rc1, _ = H.run(root, ['--only', 'package', '--force', 'package'], cfg=tx)
    r1 = H.rec(root, '6c', 'package')
    case('M105 (P6R-09) the ascending frame under a copy of the table whose [p447] says direction X: package\'s --state exits 0 with a '
         'state word (it raised before any record: exit 3, no line), and a run FAILs at G6c.0 with a record naming X, rc 2',
         s1[0] == 0 and s1[1].isupper() and rc1 == 2 and r1.get('verdict') == 'FAIL' and gates(r1).get('G6c.0') == 'FAIL'
         and "'X'" in gval(r1, 'G6c.0') and 'G6c.1' not in gates(r1),
         'state %s; rc %d; %s; G6c.0 %s' % (s1, rc1, r1.get('verdict'), gval(r1, 'G6c.0')[:160]))

    # ---- M103c (P6R-06): deliver's G6a.5 by the direction (deliver's record a DECISION after it)
    rc1, _ = H.run(root, ['--only', 'deliver', '--force', 'deliver'])
    r1 = H.rec(root, '6a', 'deliver')
    case('M103c (P6R-06) the ascending frame\'s deliver forced again: G6a.5 DECISION, the outputs in the way and what the later phases '
         'made by the direction\'s glob: %s, rc 4' % pk,
         rc1 == 4 and gates(r1).get('G6a.5') == 'DECISION' and pk in gval(r1, 'G6a.5'), 'rc %d; G6a.5 %s' % (rc1, gval(r1, 'G6a.5')[-200:]))

    # ---- M100d (P6R-01), last: one pair's referenceShelve copy's SLR NaN, datum alone
    def dates_md5():
        h = hashlib.md5()
        for f in sorted(glob.glob(os.path.join(RT, 'dates', '*', '*'))):
            h.update(f.encode())
            h.update(open(f, 'rb').read())
        return h.hexdigest()
    pr = sorted(os.listdir(os.path.join(RT, 'pairs')))[0]
    m0 = dates_md5()
    rce, je = H.shelves(W, 'pairslr', pr, 'referenceShelve', 'nan')
    rc1, _ = H.run(root, ['--only', 'datum', '--force', 'datum'])
    rd1 = H.rec(root, '4c', 'datum')
    a = pr.split('_')[0]
    case('M100d (P6R-01) pair %s\'s referenceShelve copy\'s SLR set to NaN by hand: datum alone (forced): G4c.4 finds R9\'s own complete '
         'apply, G4c.8 FAIL naming %s and the NaN copy (the old form abs(nan / s0 - 1) > 1e-9 is %s: it passed it into R9), rc 2, dates/ '
         'not rewritten' % (pr, a, abs(float('nan') / 4.684 - 1.0) > 1e-9),
         rce == 0 and rc1 == 2 and gates(rd1).get('G4c.4') == 'PASS' and gates(rd1).get('G4c.8') == 'FAIL'
         and '%s: SLR or PRF differs between its copies' % a in gval(rd1, 'G4c.8') and '%s/referenceShelve nan m' % pr in gval(rd1, 'G4c.8')
         and 'G16' not in gates(rd1) and dates_md5() == m0,
         'edit rc %s %s; rc %d; G4c.4 %s; G4c.8 %s' % (rce, je, rc1, gates(rd1).get('G4c.4'), gval(rd1, 'G4c.8')[-160:]))
