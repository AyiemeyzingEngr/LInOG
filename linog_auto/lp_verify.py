#!/usr/bin/env python3
"""lp_verify.py -- linog_auto Phase 1c: verify every unpacked date from its shelve, run the kit's own post-unpack
checks, and write recon/modes.json, the per-date table every later phase reads (no step infers a mode from a folder).
v0.5: runs after rwin (Phase 1br), which sets each shelve's r0 from its CEOS image records; G1c.1 needs rwin PASS on
record and made from the same unpack record; the identity of SLC/<date>/ is the files the unpacker writes (F21).

Runs inside lp_env.sh: unpickling a shelve needs <isce>/components on the PYTHONPATH (RD2). Each SLC/<date>/data
is opened read-only; the attribute names are the ones RD2 read on felix (26 Sept 2026). ISCE's ALOS reader leaves
passDirection None, so the pass direction comes from the orbit: the velocity's z component at the state vector
nearest the scene centre. Writes only recon/modes.json (atomically), logs/verify/ and its status record.

v0.13 (ascending record 4.2, 4.4, 4.5, 12.3 item 4, 18.5): G1c.1 adds bandlimit (P1bs) PASS on record, made from the same
unpack and rwin records, each band-limited .slc and .prefilter and each FBD .slc as bandlimit recorded them (size and
mtime); G1c.2 checks the env's prefix too; G4 reads the FBD dates' polarisation from the data (the method of the kit's
linog_pol_gate.py, ported); G1c.8 is DA1's shelve check (every branch); the identity of SLC/<date>/ adds <date>.slc.prefilter;
recon/modes.json's rows add each date's shelve sampling rate, wavelength and pixel size, and an FBD date's G4 reading.

Gates
  G1c.1 unpack, rwin and bandlimit PASS on record, rwin and bandlimit made from that unpack record (bandlimit from that
        rwin record), the shelves as rwin left them (md5), the band-limited files as bandlimit left them (size, mtime);
        RECON.json unchanged since recon wrote it                                                FAIL
  G1c.2 environment: the pinned env at its prefix (CONDA_PREFIX = linog_stack.cfg's ENV_PREFIX), `import isce`   ERROR
  G3    shelve keys exactly doppler, fmrate, frame (the LInOG unpacker, not the stock one)      FAIL
  G6    widths: shelve samples = recon CEOS width = .slc.xml width; lines = summary.txt = .xml length;
        <date>.slc = samples x lines x 8 B                                                      FAIL
  G1c.3 each shelve names its own date: image SLC/<date>/<date>.slc (relative, as the kit's frames),
        sensing start on <date>                                                                 FAIL
  G3b   pass direction: vz < 0 for a D path, > 0 for an A path, at the state vector nearest the scene centre   FAIL
  G5    chirp bandwidth |chirpSlope| x pulseLength = 28 MHz (FBS) or 14 MHz (FBD), +/- 0.5 MHz     FAIL
  G1c.4 r0 on the ALOS range-gate grid the kit uses (linog_env.cfg), within 1 m                  FAIL
  G1c.5 PRF not synthetic (the kit's test: 100000 / PRF is not an integer)                       FAIL
  G4    polarisation (the HV lottery), FBD dates: the mean amplitude of SLC/<d>/<d>.slc over 200 lines from line 9000
        (the middle 200 on a frame without them) nearer IMG-HH's than IMG-HV's over the same lines, and within 1e-4 of
        IMG-HH's (relative); the HH/HV ratio recorded. N/A on an FBS-only frame (no IMG-HV member, G1a.4)   FAIL
  G1c.8 the shelves' instruments (DA1): one wavelength (each within 1e-7 of the median, relative); the sampling rate
        32 or 16 MHz within 1 Hz, its mode the date's (recon's IMG-HV witness); the pixel c / (2 fs) within 1e-6 m;
        on an FBS+FBD frame the FBD pixel twice the FBS pixel within 1e-7                               FAIL
  G1c.6 the kit's linog_unpack_verify.py and linog_shelve_gate.py at their pinned md5s: rc 0,
        every date counted, none flagged                                                        FAIL
  G1c.7 recon/modes.json written, one row per date                                              FAIL
--dryrun DIR: G1c.1, G1c.2 and the kit pins on the plan; writes only DIR/status/P1c_verify.json.
Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

import lp_common as C
import lp_p1 as P1

VERSION1C = C.VERSION   # v0.13 (v0.5 to v0.12: 'linog_auto v0.5 (2026-09-27)')
TOOLS = ('lp_verify.py', 'lp_p1.py', 'lp_common.py', 'lp_bandlimit.py', 'lp_p2.py')   # v0.13: the two modules it imports
# (the part 2 review's P2-16); v0.13 moves every Phase 1 fingerprint anyway (lp_common.py, lp_p1.py)
SLC_NAMES = ('data', 'data.dat', 'data.dir', 'data.bak', 'data.db')   # and <date>.slc, .slc.xml, .slc.vrt
KIT_CHECKS = (('linog_unpack_verify.py', 'KIT_UNPACK_VERIFY_MD5', r'scenes=(\d+)\s+flagged=(\d+)'),
              ('linog_shelve_gate.py', 'KIT_SHELVE_GATE_MD5', r'shelves=(\d+)\s+bad=(\d+)'))
BW_TOL_MHZ = 0.5
GRID_TOL_M = 1.0
ABSENT = object()
CLIGHT = 299792458.0
POL_L0, POL_NL, POL_TOL = 9000, 200, 1e-4      # G4: linog_pol_gate.py's window; the relative line to IMG-HH's mean (new)
LAM_TOL, FS_TOL_HZ, SLR_TOL_M, RATIO_TOL = 1e-7, 1.0, 1e-6, 1e-7   # G1c.8 (DA1, ascending record 4.5)
FS_HZ = {'FBS': 32000000.0, 'FBD': 16000000.0}


class LiveStatus(C.Status):
    """The record written again after every gate (F25, v0.5); lp_common.py stays byte-identical."""

    def gate(self, *a, **k):
        C.Status.gate(self, *a, **k)
        self.write()


def g(o, *names):
    """The first of names that o has (a get... name is called); ABSENT if none."""
    for n in names:
        try:
            v = getattr(o, n)
        except Exception:  # noqa: BLE001
            continue
        return v() if n.startswith('get') and callable(v) else v
    return ABSENT


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def as_int(x):
    v = num(x)
    return int(v) if v is not None and v == int(v) else None


def slc_files(W, d):
    """(name, size, mtime_ns) of the files of SLC/<d>/ that the unpacker writes (<d>.slc, .slc.xml, .slc.vrt, the shelve's
    files), in name order: the identity of what this phase verified. F21 (v0.5): a file written beside them later
    (MintPy's data.rsc, a GDAL .aux.xml) changes nothing."""
    sd = os.path.join(W, 'SLC', d)
    if not os.path.isdir(sd):
        return []
    names = set(SLC_NAMES + (d + '.slc', d + '.slc.xml', d + '.slc.vrt', d + '.slc.prefilter'))   # v0.13: the .prefilter
    out = []
    for n in sorted(os.listdir(sd)):
        if n in names:
            s = os.stat(os.path.join(sd, n))
            out.append((n, s.st_size, s.st_mtime_ns))
    return out


def shelf_md5(W, d):
    """md5 of each of the shelve's files in SLC/<d>/, as lp_rwin.py records them."""
    sd = os.path.join(W, 'SLC', d)
    return {n: C.md5_file(os.path.join(sd, n)) for n in SLC_NAMES if os.path.isfile(os.path.join(sd, n))}


def xml_int(path, name):
    try:
        m = re.search(r'name="%s".*?<value>\s*(\d+)' % name, open(path, errors='replace').read(), re.S)
    except OSError:
        return None
    return int(m.group(1)) if m else None


def read_date(W, d):
    """What the gates read for one date; 'error' set when the shelve cannot be read."""
    import shelve
    r = dict(date=d)
    try:
        with shelve.open(os.path.join(W, 'SLC', d, 'data'), 'r') as db:
            r['keys'] = sorted(db.keys())
            f = db['frame']
    except Exception as e:  # noqa: BLE001
        r['error'] = 'shelve unreadable: %s: %s' % (type(e).__name__, str(e)[:120])
        return r
    try:
        read_frame(f, r)
    except Exception as e:  # noqa: BLE001
        r['error'] = 'frame unreadable: %s: %s' % (type(e).__name__, str(e)[:120])
    return r


def read_frame(f, r):
    r['samples'] = as_int(g(f, 'numberOfSamples', 'getNumberOfSamples'))
    r['lines'] = as_int(g(f, 'numberOfLines', 'getNumberOfLines'))
    r['r0'] = num(g(f, 'startingRange', 'getStartingRange'))
    ss, se = g(f, 'sensingStart', 'getSensingStart'), g(f, 'sensingStop', 'getSensingStop')
    r['sensing_start'] = ss if ss is not ABSENT else None
    ins = g(f, 'instrument', 'getInstrument')
    r['prf'] = num(g(ins, 'PRF', 'getPulseRepetitionFrequency'))
    # v0.13, G1c.8: the attribute names RA1 read on felix's 276 shelves (ascending record 1.7, 2.2)
    r['wavelength'] = num(g(ins, 'radarWavelength', 'getRadarWavelength'))
    r['fs_hz'] = num(g(ins, 'rangeSamplingRate', 'getRangeSamplingRate'))
    r['slr_m'] = num(g(ins, 'rangePixelSize', 'getRangePixelSize'))
    pl, cs = num(g(ins, 'pulseLength', 'getPulseLength')), num(g(ins, 'chirpSlope', 'getChirpSlope'))
    r['bw_mhz'] = abs(cs) * pl / 1e6 if pl is not None and cs is not None else None
    look = g(g(ins, 'platform', 'getPlatform'), 'pointingDirection', 'getPointingDirection')
    r['look'] = None if look is ABSENT else look
    img = g(f, 'image', 'getImage')
    fn = g(img, 'filename', 'getFilename')
    r['image'] = None if fn is ABSENT else fn
    pd = g(f, 'passDirection', 'getPassDirection')
    r['pass_direction'] = 'absent' if pd is ABSENT else pd
    r['vz'] = r['sv_time'] = None
    try:
        mid = ss + (se - ss) / 2
        orb = g(f, 'orbit', 'getOrbit')
        sv = g(orb, 'stateVectors', '_stateVectors', 'getStateVectors')
        sv = list(orb) if sv is ABSENT else list(sv)
        near = min(sv, key=lambda m: abs((g(m, 'time', 'getTime') - mid).total_seconds()))
        r['vz'] = float(list(g(near, 'velocity', 'getVelocity'))[2])
        r['sv_time'], r['sensing_mid'], r['n_sv'] = g(near, 'time', 'getTime'), mid, len(sv)
    except Exception as e:  # noqa: BLE001
        r['orbit_error'] = '%s: %s' % (type(e).__name__, str(e)[:120])


def pol_means(W, d, stem, width, lines):
    """G4 (v0.13): linog_pol_gate.py's means, ported: (|SLC| over the window, IMG-HH's, IMG-HV's, first line, lines) with
    the window 200 lines from line 9000, or the middle 200 on a frame without them; IMG members as big-endian float32 pairs
    after the 720 B file descriptor and each record's 412 B prefix; None for a member that is absent or short."""
    import glob
    import numpy as np
    nl = min(POL_NL, lines)
    l0 = POL_L0 if lines >= POL_L0 + POL_NL else max(0, (lines - nl) // 2)
    slc = os.path.join(W, 'SLC', d, d + '.slc')
    a = np.fromfile(slc, dtype=np.complex64, count=width * nl, offset=width * l0 * 8)
    s = float(np.abs(a).mean()) if a.size == width * nl else None

    def ceos(pol):
        f = sorted(glob.glob(os.path.join(W, 'unzipped', stem or '?', 'IMG-%s-*' % pol)))
        if not f:
            return None
        rec, o = 412 + width * 8, []
        with open(f[0], 'rb') as fh:
            for i in range(nl):
                fh.seek(720 + (l0 + i) * rec + 412)
                b = fh.read(width * 8)
                if len(b) < width * 8:
                    return None
                v = np.frombuffer(b, dtype='>f4').reshape(-1, 2)
                o.append(np.abs(v[:, 0] + 1j * v[:, 1]).mean())
        return float(np.mean(o)) if o else None
    return s, ceos('HH'), ceos('HV'), l0, nl


def run_kit(W, kit, name, env_md5, pattern, n):
    """Run one kit check from the frame folder with this Python; (verdict, value, note)."""
    f = os.path.join(kit, name)
    got = C.md5_file(f) if os.path.isfile(f) else None
    if got != env_md5:
        return 'FAIL', '%s md5 %s' % (name, got), 'pinned %s in linog_env.cfg' % env_md5
    lg = P1.new_log(os.path.join(W, 'logs', 'verify', name + '.log'))
    with open(lg, 'w') as fh:
        rc = subprocess.call([sys.executable, f], cwd=W, stdout=fh, stderr=subprocess.STDOUT)
    txt = open(lg, errors='replace').read()
    m = re.search(pattern, txt)
    cnt, bad = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    ok = rc == 0 and cnt == n and bad == 0
    tail = '' if ok else '\n'.join(txt.strip().splitlines()[-6:])
    return ('PASS' if ok else 'FAIL'), '%s rc %d, %s' % (name, rc, m.group(0) if m else 'no count line'), \
        'log %s%s' % (lg, ('\n' + tail) if tail else '')


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 1c: verify')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env = P1.load_env()
    kit_md5 = dict((n, C.md5_file(os.path.join(env['KIT'], n)) if os.path.isfile(os.path.join(env['KIT'], n))
                    else None) for n, _, _ in KIT_CHECKS)
    rj = os.path.join(recdir, 'recon', 'RECON.json')
    rj_md5 = C.md5_file(rj) if os.path.exists(rj) else None
    r_unp = P1.record(recdir, '1b', 'unpack')
    r_bl = P1.record(recdir, '1bs', 'bandlimit')   # v0.13
    dates = (r_unp or {}).get('outputs', {}).get('dates', [])
    mj = os.path.join(W, 'recon', 'modes.json')
    fp = C.md5_obj(dict(unpack_fp=(r_unp or {}).get('fingerprint'),
                        dates_md5=(r_unp or {}).get('outputs', {}).get('dates_md5'), recon_json=rj_md5,
                        kit=kit_md5, env_cfg=env['env_cfg_md5'], tools=C.tool_md5s(*TOOLS),
                        bandlimit_fp=(r_bl or {}).get('fingerprint'),
                        slc=[(d['date'], slc_files(W, d['date'])) for d in dates] if not a.dryrun else None))
    if a.state:
        def missing(r):
            want = (r or {}).get('outputs', {}).get('modes_json_md5')
            return [] if os.path.exists(mj) and C.md5_file(mj) == want else [mj]
        print(P1.state_with_outputs(recdir, 'verify', '1c', fp, missing))
        return 0

    st = LiveStatus(recdir, 'verify', '1c', path, frame)
    P1.begin(st)
    st.rec['version'] = VERSION1C
    st.rec.update(fingerprint=fp, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(dates_md5=(r_unp or {}).get('outputs', {}).get('dates_md5'), recon_json=rj,
                              recon_json_md5=rj_md5, kit=env['KIT'], kit_md5=kit_md5, env_cfg=env['env_cfg_file'],
                              env_cfg_md5=env['env_cfg_md5']))
    st.write()
    print('%s  Phase 1c verify  p%s f%s  %s' % (VERSION1C, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: plan only)' if a.dryrun else ''))
    r_rec = P1.record(recdir, '0a', 'recon')
    r_rw = P1.record(recdir, '1br', 'rwin')
    why = []
    if not r_unp or r_unp.get('verdict') != 'PASS':
        why.append('unpack %s' % ((r_unp or {}).get('verdict') or 'has no record'))
    if not r_rw or r_rw.get('verdict') != 'PASS':
        why.append('rwin %s' % ((r_rw or {}).get('verdict') or 'has no record'))
    elif r_unp and ((r_rw.get('inputs') or {}).get('unpack_fingerprint') != r_unp.get('fingerprint') or
                    (r_rw.get('inputs') or {}).get('dates_md5') != (r_unp.get('outputs') or {}).get('dates_md5')):
        why.append('rwin ran on another unpack record (run rwin again)')
    elif not a.dryrun:
        rwd = (r_rw.get('outputs') or {}).get('dates') or []
        moved = [x.get('date') for x in rwd if shelf_md5(W, x.get('date')) != x.get('shelf_md5_after')]
        if moved or len(rwd) != len(dates):
            why.append('the shelves are not as rwin left them (%s; run rwin again)' % (
                ' '.join(moved) if moved else 'rwin recorded %d dates, unpack %d' % (len(rwd), len(dates))))
    # v0.13: bandlimit (P1bs) PASS, made from this unpack and rwin record, its files as it left them
    if not r_bl or r_bl.get('verdict') != 'PASS':
        why.append('bandlimit %s' % ((r_bl or {}).get('verdict') or 'has no record'))
    else:
        bi, bo = r_bl.get('inputs') or {}, r_bl.get('outputs') or {}
        if (r_unp and (bi.get('unpack_fingerprint') != r_unp.get('fingerprint') or
                       bi.get('dates_md5') != (r_unp.get('outputs') or {}).get('dates_md5'))) or \
                (r_rw and bi.get('rwin_fingerprint') != r_rw.get('fingerprint')):
            why.append('bandlimit ran on another unpack or rwin record (run bandlimit again)')
        elif not a.dryrun and not bo.get('dryrun'):
            import lp_bandlimit as BL
            moved = BL.missing_files(W, r_bl)
            if moved:
                why.append('the band-limited files are not as bandlimit left them (%s; run bandlimit again)' % ' '.join(moved))
    if not r_rec or r_rec.get('outputs', {}).get('recon_json_md5') != rj_md5:
        why.append('RECON.json changed since recon wrote it, or no recon record')
    if why:
        st.gate('G1c.1', 'unpack, rwin and bandlimit PASS on record', 'FAIL', '; '.join(why))
        return st.finish()
    R, _ = P1.recon_json(recdir)
    orw = r_rw.get('outputs') or {}
    obl = r_bl.get('outputs') or {}
    st.gate('G1c.1', 'unpack, rwin and bandlimit PASS on record', 'PASS', '%d dates, branch %s, direction %s; rwin %s; bandlimit %s' % (
        len(dates), R['branch'], R['direction'], 'a plan (dry run)' if orw.get('dryrun') else
        'changed %d, already %d' % (len(orw.get('change') or []), len(orw.get('already') or [])),
        'a plan (dry run)' if obl.get('dryrun') else ('N/A' if obl.get('na') else '%d FBS dates, %d FBD dates as it left them' % (
            len(obl.get('fbs') or []), len(obl.get('fbd') or [])))))
    try:
        import isce  # noqa: F401  (puts ISCE's components on sys.path, as the kit's tools expect)
        ok, ev, note = P1.env_check(env)
        st.gate('G1c.2', 'environment', 'PASS' if ok else 'ERROR', '%s, isce %s, python %s %s' % (
            ev, getattr(isce, '__version__', '?'), sys.executable, sys.version.split()[0]),
            '%s at ENV_PREFIX' % env['CONDA_ENV'], note)
    except Exception as e:  # noqa: BLE001
        st.gate('G1c.2', 'environment', 'ERROR', 'import isce failed: %s' % e, env['CONDA_ENV'])
    st.rec['inputs'].update(pythonpath=os.environ.get('PYTHONPATH', ''), conda_env=os.environ.get('CONDA_DEFAULT_ENV'))
    if any(x['verdict'] == 'ERROR' for x in st.rec['gates']):
        return st.finish()

    if a.dryrun:
        bad = ['%s md5 %s, pinned %s' % (n, kit_md5[n], env[k]) for n, k, _ in KIT_CHECKS if kit_md5[n] != env[k]]
        st.gate('G1c.6', 'kit checks at their pins', 'FAIL' if bad else 'PASS', '%d of %d' % (
            len(KIT_CHECKS) - len(bad), len(KIT_CHECKS)), 'all', '\n'.join(bad) + ('\nin %s' % env['KIT'] if bad else ''))
        if bad:
            return st.finish()
        print('   would verify %d dates (G3, G6, G1c.3, G3b, G5, G1c.4, G1c.5, G4 %s, G1c.8, the kit checks) and write %s' % (
            len(dates), 'N/A' if R['branch'] == 'FBS-only' else 'on %d FBD dates' % sum(d['mode'] == 'FBD' for d in dates), mj))
        st.rec['outputs'] = dict(planned=len(dates), dryrun=True)
        return st.finish('plan only (dry run)')

    want_vz = -1 if R['direction'] == 'D' else 1
    bw_want = dict(FBS=float(env['BW_FBS_MHZ']), FBD=float(env['BW_FBD_MHZ']))
    grid, r0ref = float(env['GATE_GRID_M']), float(env['GATE_R0REF_M'])
    rows, fails = [], collections.defaultdict(list)
    for d in dates:
        r = read_date(W, d['date'])
        dd, tag = d['date'], d['date'] + ': '
        if 'error' in r:
            fails['G3'].append(tag + r['error'])
            rows.append(dict(date=dd, mode=d['mode'], error=r['error']))
            continue
        if r['keys'] != ['doppler', 'fmrate', 'frame']:
            fails['G3'].append(tag + 'keys %s' % r['keys'])
        slc = os.path.join(W, 'SLC', dd, dd + '.slc')
        xw, xl = xml_int(slc + '.xml', 'width'), xml_int(slc + '.xml', 'length')
        ns, nl = r['samples'], r['lines']
        size = os.path.getsize(slc) if os.path.isfile(slc) else None
        w6 = []
        if ns != d['width'] or xw != ns:
            w6.append('samples %s, recon width %s, xml width %s' % (ns, d['width'], xw))
        if nl != d['lines'] or (xl is not None and xl != nl):
            w6.append('lines %s, summary.txt %s, xml length %s' % (nl, d['lines'], xl))
        if ns is None or nl is None or size != ns * nl * 8:
            w6.append('%s.slc %s B, want samples x lines x 8 = %s' % (dd, size, ns * nl * 8 if ns and nl else '?'))
        if w6:
            fails['G6'].append(tag + '; '.join(w6))
        ss = r['sensing_start']
        sday = ss.strftime('%Y%m%d') if hasattr(ss, 'strftime') else None
        if r['image'] != 'SLC/%s/%s.slc' % (dd, dd) or sday != dd:
            fails['G1c.3'].append(tag + 'image %s, sensing start %s' % (r['image'], ss))
        vz = r['vz']
        if vz is None or vz * want_vz <= 0:
            fails['G3b'].append(tag + 'vz %s at %s (%s)' % (vz, r['sv_time'], r.get('orbit_error', 'wrong sign')))
        bw = r['bw_mhz']
        if bw is None or d['mode'] not in bw_want or abs(bw - bw_want[d['mode']]) > BW_TOL_MHZ:
            fails['G5'].append(tag + '%s MHz for %s' % (None if bw is None else round(bw, 3), d['mode']))
        pos = off = None
        if r['r0'] is not None:
            k = (r['r0'] - r0ref) / grid
            pos, off = int(round(k)), abs(round(k) - k) * grid
        if off is None or off > GRID_TOL_M:
            fails['G1c.4'].append(tag + 'r0 %s, %s m off the grid' % (r['r0'], None if off is None else round(off, 3)))
        q = 100000.0 / r['prf'] if r['prf'] else None
        if q is None or abs(q - round(q)) < 1e-6:
            fails['G1c.5'].append(tag + 'PRF %s' % r['prf'])
        row = dict(date=dd, mode=d['mode'], width=ns, lines=nl, slc='SLC/%s/%s.slc' % (dd, dd),
                   bw_mhz=None if bw is None else round(bw, 3), prf=r['prf'], r0=r['r0'], grid_pos=pos,
                   grid_off_m=None if off is None else round(off, 4), vz=None if vz is None else round(vz, 1),
                   sv_time=str(r['sv_time']), sensing_start=str(ss), sensing_mid=str(r.get('sensing_mid')),
                   pass_direction=str(r['pass_direction']), look=r['look'],
                   fs_hz=r['fs_hz'], wavelength_m=r['wavelength'], slr_m=r['slr_m'])   # v0.13 (G1c.8)
        # v0.13, G4: an FBD date's polarisation from the data (the kit's linog_pol_gate.py's method)
        if d['mode'] == 'FBD':
            try:
                sm, hh, hv, l0, npl = pol_means(W, dd, d.get('stem'), d['width'], d['lines'])
            except Exception as e:  # noqa: BLE001
                sm = hh = hv = None
                l0, npl = None, None
                fails['G4'].append(tag + 'unreadable: %s: %s' % (type(e).__name__, str(e)[:120]))
            row['pol'] = dict(slc=sm, hh=hh, hv=hv, line0=l0, lines=npl, ratio=(hh / hv if hh and hv else None))
            if sm is None or hh is None or hv is None:
                if not any(x.startswith(tag) for x in fails['G4']):
                    fails['G4'].append(tag + 'means SLC %s, IMG-HH %s, IMG-HV %s' % (sm, hh, hv))
            elif not (abs(sm - hh) < abs(sm - hv) and abs(sm - hh) <= POL_TOL * abs(hh)):
                fails['G4'].append(tag + 'SLC %.1f, IMG-HH %.1f, IMG-HV %.1f: %s' % (
                    sm, hh, hv, 'nearer IMG-HV' if abs(sm - hv) <= abs(sm - hh) else 'off IMG-HH by %.2g' % (abs(sm - hh) / abs(hh))))
        rows.append(row)
    n = len(dates)
    good = [x for x in rows if 'error' not in x]

    def census(key):
        return dict(sorted(collections.Counter(str(x.get(key)) for x in good).items()))

    def gate(gid, name, value, thr):
        st.gate(gid, name, 'FAIL' if fails[gid] else 'PASS', value, thr, '\n'.join(fails[gid]))
    gate('G3', 'shelve readable, keys', '%d of %d doppler, fmrate, frame' % (n - len(fails['G3']), n), 'all')
    gate('G6', 'widths and sizes', '%d of %d; widths %s' % (n - len(fails['G6']), n, census('width')),
         'samples = recon = xml; size = samples x lines x 8')
    gate('G1c.3', 'shelve names its date', '%d of %d' % (n - len(fails['G1c.3']), n), 'image SLC/<d>/<d>.slc, sensing on <d>')
    gate('G3b', 'pass direction (orbit vz)', '%d of %d %s; passDirection read as %s' % (
        n - len(fails['G3b']), n, 'DESCENDING' if want_vz < 0 else 'ASCENDING', census('pass_direction')),
        'vz %s 0 at the state vector nearest the scene centre' % ('<' if want_vz < 0 else '>'))
    gate('G5', 'chirp bandwidth', '%d of %d; MHz %s' % (n - len(fails['G5']), n, census('bw_mhz')),
         'FBS %s, FBD %s +/- %s' % (env['BW_FBS_MHZ'], env['BW_FBD_MHZ'], BW_TOL_MHZ))
    gate('G1c.4', 'r0 on the gate grid', '%d of %d; positions %s' % (n - len(fails['G1c.4']), n, census('grid_pos')),
         '<= %.0f m off' % GRID_TOL_M)
    gate('G1c.5', 'PRF not synthetic', '%d of %d; PRF %s' % (n - len(fails['G1c.5']), n, census('prf')),
         '100000/PRF not an integer')
    nfbd = sum(d['mode'] == 'FBD' for d in dates)
    if R['branch'] == 'FBS-only' and not nfbd:
        st.gate('G4', 'polarisation (HV lottery)', 'N/A', 'FBS-only: no IMG-HV member in %d granules (G1a.4)' % n)
    else:
        rat = [x['pol']['ratio'] for x in good if x.get('pol') and x['pol'].get('ratio')]
        gate('G4', 'polarisation (HV lottery)', '%d of %d FBD dates from IMG-HH; HH/HV %s' % (
            nfbd - len(fails['G4']), nfbd, '%.2f to %.2f' % (min(rat), max(rat)) if rat else '-'),
            'SLC nearer IMG-HH than IMG-HV, within %g of IMG-HH (relative)' % POL_TOL)
    # v0.13, G1c.8: DA1's shelve check (ascending record 4.5)
    lams = sorted(x['wavelength_m'] for x in good if x.get('wavelength_m'))
    lam_med = lams[len(lams) // 2] if len(lams) % 2 else (0.5 * (lams[len(lams) // 2 - 1] + lams[len(lams) // 2]) if lams else None)
    slr = {'FBS': [], 'FBD': []}
    for x in rows:
        tag = x['date'] + ': '
        if 'error' in x:
            continue
        lam, fs, sl = x.get('wavelength_m'), x.get('fs_hz'), x.get('slr_m')
        if lam is None or not lam_med or abs(lam / lam_med - 1.0) > LAM_TOL:
            fails['G1c.8'].append(tag + 'wavelength %s m, the frame\'s median %s' % (lam, lam_med))
        mfs = [m for m, v in FS_HZ.items() if fs is not None and abs(fs - v) <= FS_TOL_HZ]
        if not mfs:
            fails['G1c.8'].append(tag + 'sampling rate %s Hz: neither 32 nor 16 MHz' % fs)
        elif mfs[0] != x['mode']:
            fails['G1c.8'].append(tag + 'sampling rate %s Hz is %s, the date is %s by recon\'s IMG-HV witness' % (fs, mfs[0], x['mode']))
        if not fs or sl is None or abs(sl - CLIGHT / (2.0 * fs)) > SLR_TOL_M:   # a zero rate too (P2-17)
            fails['G1c.8'].append(tag + 'pixel %s m, c / (2 fs) %s m' % (sl, CLIGHT / (2.0 * fs) if fs else None))
        elif x['mode'] in slr:
            slr[x['mode']].append(sl)
    ratio = None
    if slr['FBS'] and slr['FBD']:
        ratio = sorted(slr['FBD'])[len(slr['FBD']) // 2] / sorted(slr['FBS'])[len(slr['FBS']) // 2]
        if abs(ratio - 2.0) > RATIO_TOL:
            fails['G1c.8'].append('SLR(FBD) / SLR(FBS) = %.12f, want 2 within %g' % (ratio, RATIO_TOL))
    gate('G1c.8', 'the shelves\' instruments (DA1)', '%d of %d; wavelength %s m; fs %s; SLR(FBD) / SLR(FBS) %s' % (
        n - len(set(x.split(':')[0] for x in fails['G1c.8'])), n, lam_med, census('fs_hz'),
        '%.12f' % ratio if ratio is not None else 'n/a (one mode)'),
        'one wavelength (%g); 32 or 16 MHz (1 Hz), its mode the date\'s; c / (2 fs) (%g m); FBD pixel = 2 x FBS (%g)' % (
            LAM_TOL, SLR_TOL_M, RATIO_TOL))
    for i, (name, key, pattern) in enumerate(KIT_CHECKS):
        v, val, note = run_kit(W, env['KIT'], name, env[key], pattern, n)
        st.gate('G1c.6', 'kit check %d of %d' % (i + 1, len(KIT_CHECKS)), v, val, 'rc 0, %d counted, 0 flagged' % n, note)
    out = dict(version=VERSION1C, created=C.utc(), path=path, frame=frame, direction=R['direction'],
               branch=R['branch'], recon_json_md5=rj_md5, unpack_fingerprint=r_unp.get('fingerprint'),
               verdict='PASS' if not any(fails.values()) else 'FAIL', dates=rows,
               census=dict(mode=census('mode'), width=census('width'), bw_mhz=census('bw_mhz'), prf=census('prf'),
                           grid_pos=census('grid_pos'), look=census('look'), fs_hz=census('fs_hz')))
    tmp = mj + '.tmp%d' % os.getpid()
    with open(tmp, 'w') as fh:
        json.dump(out, fh, indent=1, default=str)
        fh.write('\n')
    os.replace(tmp, mj)
    m5 = C.md5_file(mj)
    st.gate('G1c.7', 'recon/modes.json', 'PASS' if len(rows) == n and n else 'FAIL', '%d rows, md5 %s' % (len(rows), m5),
            'one row per date', '' if not any(fails.values()) else 'it records verdict FAIL; later phases read it only after a PASS')
    st.rec['outputs'] = dict(dates=n, modes_json=mj, modes_json_md5=m5, census=out['census'])
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_verify', main)
