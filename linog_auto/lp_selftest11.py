#!/usr/bin/env python3
"""lp_selftest11.py -- the v0.11 cases of the linog_auto self-test (record 122.6, items 3 to 5), called by lp_selftest.py after
the v0.10 cases, on the Phase 5 cases' frame (root p3, frame 3320) put back to its copy after sbas (S5d), as lp_selftest6 does.

  T300 to T302  item 4: deliver's G6a.10 on the mock delivery (the kit's own linog_gen_interactive_kmz.py and the mock
                save_kmz.py, every entry at 1980-01-01 00:00:00, RUN_MANIFEST.json's kmz_times, LOGIC 5); a second delivery of
                the same frame made after the first was moved into <frame>/_archive/ (G6a.5's own instruction: the acceptance
                planned on F3310, 122.8) gives the same bytes in all 16 files, and rerun, named the moved package, PASSes;
                a KMZ with an extra field (LINOG_MOCK_KMZ_EXTRA) FAILs G6a.10 with every KMZ left as written.
  T303 to T309  item 3: rerun's first run; a reference whose KMZs carry other times (as v0.10's: equal by their entries);
                a GeoTIFF changed on the same network (DECISION under --decide auto, its readings; taken by recon/rerun.txt,
                whose accept line is matched word by word); another network, and a key one manifest does not record whole
                (INFO, the readings); a KMZ whose entries differ and a name only in the reference, on the same network
                (DECISION); a broken reference, another frame's package and a reference file naming nothing (FAIL); the
                newest archived tree with a package (a newer one without a package, and one whose rerun record reads
                DECISION, passed over); 29 phases (v0.12: 30), all skipped on a re-run; its dry run. v0.12: T300 reads deliver's
                LOGIC 6 and v0.12's label; v0.13 r2 (the ascending record 15.4's M61): v0.13 r2's label, LOGIC 6.
  T310 to T314  item 5: lp_compare.py's packages (as rerun's), shelves, cycles and split (its plan, a --run with the mock
                ifgram_inversion.py, a --cf made before), nothing written outside --out and --scratch, an --out inside an
                input refused.
  T315          lp_kmz.py alone: a zip written with data descriptors fixed; its refusals (bytes after the archive, an extra
                field, a ZIP64 locator, no entry), nothing written for a refusal; a zip comment kept.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import time

ROOT, FRAME, TAG = 'p3', '3320', 'P084F3320'
FIXED = (1980, 1, 1, 0, 0, 0)
PROBE = r'''
import json, sys, pickle, dbm
what, args = sys.argv[1], sys.argv[2:]
if what == 'tif_shift':   # add args[1] m/yr to one cell and make another NaN in a mock GeoTIFF, in place
    import numpy as np, linog_mock6 as M6
    h, a = M6.read_tiff(args[0])
    a = a.astype(np.float32)
    ok = np.argwhere(np.isfinite(a))
    y, x = ok[len(ok) // 2]
    a[y, x] += float(args[1])
    y2, x2 = ok[len(ok) // 3]
    a[y2, x2] = np.nan
    M6.write_tiff(args[0], h, a)
    print(json.dumps(dict(cell=[int(y), int(x)], nan=[int(y2), int(x2)], finite=int(np.isfinite(a).sum()))))
elif what == 'shelf_bump':   # one float attribute of a date's frame shelve + 1.0, re-pickled (the copy only)
    db = dbm.open(args[0], 'w')
    o = pickle.loads(bytes(db[b'frame']))
    name = None
    for k, v in sorted(vars(o).items()):
        if isinstance(v, float):
            setattr(o, k, v + 1.0)
            name = k
            break
    if name is None:   # no float attribute on the mock frame: one added (one leaf on one side only)
        name = 'selftestBump'
        setattr(o, name, 1.0)
    db[b'frame'] = pickle.dumps(o)
    db.close()
    print(json.dumps(dict(attribute=name)))
elif what == 'unw_field':   # every pair's unwrapPhase a smooth field (the mock's are 0, which the comparison skips)
    import h5py, numpy as np
    with h5py.File(args[0], 'r+') as f:
        n, L, W = f['unwrapPhase'].shape
        yy, xx = np.mgrid[0:L, 0:W].astype(np.float32)
        for i in range(n):
            f['unwrapPhase'][i] = (yy / L + 2.0 * xx / W + 0.1 * i + 0.5).astype(np.float32)
    print(json.dumps(dict(pairs=int(n))))
elif what == 'unw_jump':   # pair 0's unwrapPhase + 2 pi on a block, pair 1's dropIfgram flipped (the copy only)
    import h5py, numpy as np
    with h5py.File(args[0], 'r+') as f:
        u = f['unwrapPhase'][0]
        L, W = u.shape
        u[L // 4:L // 2, W // 4:W // 2] += 2 * np.pi
        f['unwrapPhase'][0] = u
        d = f['dropIfgram'][()]
        d[1] = not d[1]
        f['dropIfgram'][...] = d
        names = ['%s_%s' % (x[0].decode(), x[1].decode()) for x in f['date'][()]]
    print(json.dumps(dict(pair0=names[0], pair1=names[1], block=(L // 4) * (W // 4))))
elif what == 'drop_one':   # the copy's dropIfgram: the last kept pair dropped; then the mock inversion's two files there
    import h5py, numpy as np
    with h5py.File(args[0], 'r+') as f:
        d = f['dropIfgram'][()]
        i = int(np.where(d)[0][-1])
        d[i] = False
        f['dropIfgram'][...] = d
        names = ['%s_%s' % (x[0].decode(), x[1].decode()) for x in f['date'][()]]
    print(json.dumps(dict(dropped=names[i], kept=int(d.sum()))))
'''


def phase11(T, case, S):
    import lp_kmz as K
    import lp_p6 as P6
    W = S.fdir(T, FRAME, ROOT)
    E = {'LINOG_ROOT': os.path.join(T, ROOT), 'LINOG_MINTPY_CFG': os.path.join(T, 'cfg', 'mintpy_mock.cfg')}
    q6 = S.real_pins('linog_phase6.cfg')
    py = S.MOCKPY[0]
    site = os.path.join(T, 'mockconda', 'envs', 'linog_isce2', 'lib', 'site-packages')
    UP = os.path.join(W, 'mintpy', 'geo', 'LInOG_Upload_%s' % TAG)

    def run(args, extra=None, decide='auto'):
        return S.run(T, ['084', FRAME, '--decide', decide] + args, cfg='paths_p3.cfg', env_extra=dict(E, **(extra or {})), keep_default=True)

    def rec(idx, ph, root=None):
        return S.rec(T, FRAME, idx, ph, root or ROOT)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in r.get('gates', []))

    def val(r, gid):
        return dict((x['id'], x.get('value', '')) for x in r.get('gates', [])).get(gid, '')

    def note(r, gid):
        return dict((x['id'], x.get('note', '')) for x in r.get('gates', [])).get(gid, '')

    def copy_fn(src, dst):   # as lp_selftest6: mintpy/'s files always copies (the kit's tools write some in place)
        if os.path.getsize(src) > (1 << 20) and '%smintpy%s' % (os.sep, os.sep) not in src:
            os.link(src, dst)
        else:
            shutil.copy2(src, dst)

    def restore(tag):
        S.aside(T, W, 'p11_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_p3', 'S5d'), W, symlinks=True, copy_function=copy_fn)

    def probe(*args):
        # the mock site-packages and, as lp_env.sh adds them, ISCE's components (isceobj: the shelves' frames unpickle with it)
        env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', T), 'PYTHONDONTWRITEBYTECODE': '1',
               'PYTHONPATH': '%s:%s' % (os.path.join(site, 'isce', 'components'), site), 'MPLCONFIGDIR': os.path.join(T, 'mplconfig_probe')}
        p = subprocess.run([py, '-B', '-c', PROBE] + [str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, cwd=T)
        try:
            return json.loads(p.stdout.decode('utf-8', 'replace').strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {'_error': p.stdout.decode('utf-8', 'replace')[-400:]}

    def compare(args):
        """lp_compare.py in the mock env, as the operator runs it on felix with the env's python3: (rc, output)."""
        env = dict((k, v) for k, v in os.environ.items() if not k.startswith('LINOG_'))
        env.update(LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), MPLCONFIGDIR=os.path.join(T, 'mplconfig_probe'))
        p = subprocess.run(['bash', os.path.join(S.HERE, 'lp_env.sh'), 'python3', '-B', os.path.join(S.HERE, 'lp_compare.py')] + args,
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=T)
        out = p.stdout.decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## lp_compare.py %s  rc %d\n%s' % (' '.join(args), p.returncode, out))
        return p.returncode, out

    def md5(p):
        return S.md5(p) if os.path.isfile(p) else None

    def tree_md5s(d):
        out = {}
        for dp, dn, fn in os.walk(d):
            dn.sort()
            for n in sorted(fn):
                out[os.path.relpath(os.path.join(dp, n), d)] = S.md5(os.path.join(dp, n))
        return out

    def listing(d):
        out = []
        for dp, dn, fn in os.walk(d):
            dn.sort()
            for n in sorted(fn):
                qq = os.path.join(dp, n)
                st = os.lstat(qq)
                out.append((os.path.relpath(qq, d), st.st_size, st.st_mtime_ns))
        return out

    def package():
        return os.path.join(W, (rec('6c', 'package').get('outputs') or {}).get('package') or '-')

    def remanifest(pkg):
        """The package copy's TRANSFER_MANIFEST_<TAG>.txt written again from its files (as lp_package does)."""
        mname = 'TRANSFER_MANIFEST_%s.txt' % TAG
        lines = P6.manifest_lines(pkg, mname)
        with open(os.path.join(pkg, mname), 'w') as fh:
            fh.write(''.join(ln + '\n' for ln in lines))
        return len(lines)

    def copy_pkg(dst):
        """A copy (not links) of the frame's package, outside the frame's package folder."""
        if os.path.exists(dst):
            S.aside(T, dst, 'p11_old')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(package(), dst)
        return dst

    def retime(pkg, dt):
        """Every KMZ of a package copy with its entries at dt (lp_kmz), as a v0.10 package's carry the run's times."""
        n = 0
        for k in sorted(glob.glob(os.path.join(pkg, 'LInOG_Upload_%s' % TAG, '*.kmz'))):
            K.fix_times(k, k + '.tmp', dt)
            os.replace(k + '.tmp', k)
            n += 1
        return n

    def name_ref(path):
        with open(os.path.join(W, 'recon', 'rerun_reference.txt'), 'w') as fh:
            fh.write('# linog_auto self-test (v0.11): the package rerun compares with\n%s\n' % path)

    def unname(tag):
        for n in ('rerun_reference.txt', 'rerun.txt'):
            p = os.path.join(W, 'recon', n)
            if os.path.isfile(p):
                os.makedirs(os.path.join(W, '_archive', tag), exist_ok=True)
                os.rename(p, os.path.join(W, '_archive', tag, n))

    def move_out(tag):
        """deliver's outputs, RUN_MANIFEST.json and the package into <frame>/_archive/<tag>/ (G6a.5's and G6c.2's instruction)."""
        dst = os.path.join(W, '_archive', tag)
        moved = []
        for rel in tuple(P6.deliver_way('084', FRAME)) + (P6.package_glob('084', FRAME, q6, 'D'),):
            for p in sorted(glob.glob(os.path.join(W, rel))):
                d = os.path.join(dst, os.path.relpath(p, W))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                os.rename(p, d)
                moved.append(os.path.relpath(p, W))
        return dst, moved

    def entries(p):
        return K.members(p) if os.path.isfile(p) else []

    print('-- v0.11 (items 3 to 5): the KMZs\' fixed entry times (G6a.10), the rerun check (P6d) and lp_compare.py, on the Phase 5 '
          'frame after sbas')
    if not os.path.isdir(os.path.join(T, 'snap_p3', 'S5d')):
        case('T300-T314 not run: no copy of the frame after sbas (the Phase 4.5 and 5 cases stopped early)', False)
        return

    # ------------------------------------------------------------------ item 4
    restore('T300')
    rc, out = run([])
    rd, rr = rec('6a', 'deliver'), rec('6d', 'rerun')
    kz = sorted(glob.glob(os.path.join(UP, '*.kmz')))
    ents = [e for k in kz for e in entries(k)]
    man = json.load(open(os.path.join(W, 'RUN_MANIFEST.json'))) if os.path.isfile(os.path.join(W, 'RUN_MANIFEST.json')) else {}
    kt = (man.get('delivery') or {}).get('kmz_times') or {}
    od = (rd.get('outputs') or {}).get('kmz') or {}
    case('T300 clean run from sbas (no --to: v0.11\'s default, rerun): rc 0; deliver PASS, LOGIC 7, v0.13 r3 (v0.11: 5; v0.12: 6; '
         'v0.13 r2\'s label with G6a.11; v0.13 r3: chain A\'s DEM-error fit); G6a.10 PASS: the 4 KMZs '
         '(2 by the mock save_kmz.py, 2 by the kit\'s own linog_gen_interactive_kmz.py), every entry at 1980-01-01 00:00:00, zipfile\'s '
         'CRC test passing; RUN_MANIFEST.json\'s delivery.kmz_times names the 4 with their entries\' times as written; rerun PASS, a '
         'first run (G6d.2 INFO, no reference)',
         rc == 0 and rd.get('verdict') == 'PASS' and rd.get('logic') == 7 and rd.get('version') == 'linog_auto v0.13 r3 (2026-10-30)'
         and gates(rd).get('G6a.10') == 'PASS' and len(kz) == 4 and ents and all(e['date_time'] == FIXED for e in ents)
         and all(K.zipfile.ZipFile(k).testzip() is None for k in kz) and kt.get('fixed') == K.FIXED_TEXT
         and sorted((kt.get('files') or {})) == sorted(os.path.basename(k) for k in kz) and len(od) == 4
         and all(0 < r.get('bytes_changed', 0) <= 8 * r.get('entries', 0) for r in od.values())
         and rr.get('verdict') == 'PASS' and gates(rr).get('G6d.2') == 'INFO' and (rr.get('outputs') or {}).get('first_run') is True
         and (man.get('manifest') or '').startswith('RUN_MANIFEST.json (linog_auto v0.13 r3'),
         'rc %d; deliver %s LOGIC %s %s; G6a.10 %s: %s; %d KMZs, %d entries, at %s; kmz_times %s; rerun %s %s' % (
             rc, rd.get('verdict'), rd.get('logic'), rd.get('version'), gates(rd).get('G6a.10'), val(rd, 'G6a.10')[:150], len(kz), len(ents),
             sorted(set(e['date_time'] for e in ents)), sorted(kt.get('files') or {}), rr.get('verdict'), val(rr, 'G6d.2')[:100]))

    d0 = tree_md5s(UP)
    pk0 = os.path.basename(package())
    dst, moved = move_out('T301')
    time.sleep(2.2)   # the zip format keeps times to 2 s: without G6a.10 a second delivery's entries would differ
    name_ref('_archive/T301/%s/%s' % (q6['XFER'], pk0))
    rc, out = run([])
    rd, rr = rec('6a', 'deliver'), rec('6d', 'rerun')
    d1 = tree_md5s(UP)
    orr = rr.get('outputs') or {}
    case('T301 the planned acceptance (122.8, choice 3) on the mock: deliver\'s outputs, RUN_MANIFEST.json and the package moved into '
         '<frame>/_archive/T301/ (G6a.5\'s instruction), recon/rerun_reference.txt naming the moved package, the chain run again from '
         'deliver: rc 0; the 16 files and the reports\' pages byte for byte the first delivery\'s, the 4 KMZs among them (made 2 s '
         'later); rerun PASS: every file equal but RUN_MANIFEST.json, the network key complete and equal',
         rc == 0 and len(moved) >= 3 and rd.get('verdict') == 'PASS' and d0 and d1 == d0
         and rr.get('verdict') == 'PASS' and gates(rr).get('G6d.9') == 'PASS' and orr.get('same_files') is True
         and (orr.get('network') or {}).get('equal') is True and orr.get('other_differ') == [] and gates(rr).get('G6d.3') == 'PASS'
         and [os.path.basename(x) for x in orr.get('differ') or []] == ['RUN_MANIFEST.json'],
         'rc %d; moved %d paths; deliveries equal %s (%d files); rerun %s, G6d.9 %s: %s; differ %s; network %s' % (
             rc, len(moved), d1 == d0, len(d1), rr.get('verdict'), gates(rr).get('G6d.9'), val(rr, 'G6d.9')[:120], orr.get('differ'),
             (orr.get('network') or {}).get('fields')))

    # ------------------------------------------------------------------ item 3
    R2 = copy_pkg(os.path.join(W, '_archive', 'T303', 'ref_times', pk0))
    nk = retime(R2, (2026, 10, 8, 9, 22, 6))
    remanifest(R2)
    name_ref(R2)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    orr = rr.get('outputs') or {}
    case('T303 a reference whose 4 KMZs carry other entry times (as a v0.10 package\'s): rerun PASS, rc 0; G6d.5 counts the 4 KMZs '
         'equal by their entries, times differing; G6d.9 PASS',
         nk == 4 and rc == 0 and rr.get('verdict') == 'PASS' and len(orr.get('kmz_equal_by_entries') or []) == 4
         and all((v or {}).get('times_differ') for v in (orr.get('kmz') or {}).values()) and gates(rr).get('G6d.9') == 'PASS'
         and 'KMZs equal by their entries (times differ)' in val(rr, 'G6d.5'),
         'rc %d; G6d.5 %s; G6d.9 %s' % (rc, val(rr, 'G6d.5')[:160], gates(rr).get('G6d.9')))

    R3 = copy_pkg(os.path.join(W, '_archive', 'T304', 'ref_tif', pk0))
    tif = os.path.join(R3, 'LInOG_Upload_%s' % TAG, '%s_Velocity_demErr.tif' % TAG)
    pr = probe('tif_shift', tif, '0.010')
    remanifest(R3)
    name_ref(R3)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    orr = rr.get('outputs') or {}
    rdg = (orr.get('readings') or {}).get('demErr') or {}
    nt = note(rr, 'G6d.9')
    mm = re.search(r'accept (\S+) ([0-9a-f]{32}) ([0-9a-f]{32})', nt)
    case('T304 the reference\'s demErr GeoTIFF moved by 10 mm/yr in one cell and NaN in another, its manifest made again (the same '
         'network): rerun DECISION under --decide auto, rc 4; G6d.7 complete and equal; G6d.8\'s demErr readings: max 10.00 mm/yr, '
         'one cell beyond 5, one cell gained; G6d.9\'s note gives the accept line',
         '_error' not in pr and rc == 4 and rr.get('verdict') == 'DECISION' and gates(rr).get('G6d.9') == 'DECISION'
         and val(rr, 'G6d.7') == 'complete and equal' and abs(rdg.get('max_abs', 0) - 10.0) < 1e-3 and rdg.get('gained') == 1
         and rdg.get('lost') == 0 and rdg.get('cells_both', 0) > 0 and abs(rdg.get('share_gt5', 0) * rdg.get('cells_both', 0) - 1) < 1e-6
         and mm is not None and mm.group(1) == pk0,
         'rc %d; %s; G6d.7 %s; demErr %s; accept line %s; probe %s' % (rc, rr.get('verdict'), val(rr, 'G6d.7'), dict(
             (k, rdg.get(k)) for k in ('max_abs', 'gained', 'lost', 'cells_both', 'share_gt5')), mm.group(0) if mm else None, pr))
    if mm:
        with open(os.path.join(W, 'recon', 'rerun.txt'), 'w') as fh:   # the words as the note gives them, a tab and two spaces between
            fh.write('accept\t%s  %s %s \n# self-test T304b: the reference\'s GeoTIFF was changed on purpose\n' % mm.groups())
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    case('T304b recon/rerun.txt with that accept line (a tab and two spaces between its words) and a # reason: rerun PASS, rc 0; '
         'G6d.9 INFO naming the operator\'s line, the reason in its note',
         rc == 0 and rr.get('verdict') == 'PASS' and gates(rr).get('G6d.9') == 'INFO' and 'taken by the operator' in val(rr, 'G6d.9')
         and 'changed on purpose' in note(rr, 'G6d.9') and (rr.get('outputs') or {}).get('accepted') == (mm.group(0) if mm else '-'),
         'rc %d; %s; G6d.9 %s' % (rc, rr.get('verdict'), val(rr, 'G6d.9')[:140]))
    unname('T304b')

    R4 = copy_pkg(os.path.join(W, '_archive', 'T305', 'ref_net', pk0))
    probe('tif_shift', os.path.join(R4, 'LInOG_Upload_%s' % TAG, '%s_Velocity_demErr.tif' % TAG), '0.010')
    mj = json.load(open(os.path.join(R4, 'RUN_MANIFEST.json')))
    mj['decisions']['d3']['excludeDate12'] = '20080830_20081130'
    mj['dates']['kept'] = (mj['dates'].get('kept') or 6) - 1
    with open(os.path.join(R4, 'RUN_MANIFEST.json'), 'w') as fh:
        json.dump(mj, fh, indent=1)
    remanifest(R4)
    name_ref(R4)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    case('T305 a reference on another network (its RUN_MANIFEST.json: excludeDate12 a pair, one pair fewer kept) whose demErr '
         'GeoTIFF differs: rerun PASS, rc 0; G6d.7 names the two fields; G6d.9 INFO (another network), the readings in G6d.8',
         rc == 0 and rr.get('verdict') == 'PASS' and gates(rr).get('G6d.9') == 'INFO' and 'another network' in val(rr, 'G6d.9')
         and 'excludeDate12' in val(rr, 'G6d.7') and 'kept' in val(rr, 'G6d.7') and 'demErr median' in val(rr, 'G6d.8'),
         'rc %d; G6d.7 %s; G6d.9 %s' % (rc, val(rr, 'G6d.7')[:140], val(rr, 'G6d.9')[:100]))

    R4b = copy_pkg(os.path.join(W, '_archive', 'T305b', 'ref_nofit', pk0))
    probe('tif_shift', os.path.join(R4b, 'LInOG_Upload_%s' % TAG, '%s_Velocity_demErr.tif' % TAG), '0.010')
    mj = json.load(open(os.path.join(R4b, 'RUN_MANIFEST.json')))
    mj.pop('velocity_fit', None)   # as a v0.9 manifest: no velocity_fit
    with open(os.path.join(R4b, 'RUN_MANIFEST.json'), 'w') as fh:
        json.dump(mj, fh, indent=1)
    remanifest(R4b)
    name_ref(R4b)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    case('T305b a reference whose RUN_MANIFEST.json has no velocity_fit (as v0.9\'s), its demErr GeoTIFF changed, the other fields of the '
         'key equal (the path F3320 takes against v1.0): rerun PASS, rc 0; G6d.7 "not recorded whole: dates_out_of_fit"; G6d.9 INFO',
         rc == 0 and rr.get('verdict') == 'PASS' and gates(rr).get('G6d.9') == 'INFO' and 'not recorded whole: dates_out_of_fit' in val(rr, 'G6d.7')
         and 'do not record whole' in val(rr, 'G6d.9'),
         'rc %d; G6d.7 %s; G6d.9 %s' % (rc, val(rr, 'G6d.7')[:120], val(rr, 'G6d.9')[:120]))

    R4c = copy_pkg(os.path.join(W, '_archive', 'T305c', 'ref_kmz', pk0))
    kc = sorted(glob.glob(os.path.join(R4c, 'LInOG_Upload_%s' % TAG, '*_TimeSeries_demErr.kmz')))[0]
    with K.zipfile.ZipFile(kc) as z:
        kml = z.read('doc.kml')
    zi = K.zipfile.ZipInfo('doc.kml', FIXED)
    zi.compress_type = K.zipfile.ZIP_DEFLATED
    with K.zipfile.ZipFile(kc + '.new', 'w') as z:
        z.writestr(zi, kml + b'<!-- T305c -->')
    os.replace(kc + '.new', kc)
    remanifest(R4c)
    name_ref(R4c)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    okc = ((rr.get('outputs') or {}).get('kmz') or {}).get('./LInOG_Upload_%s/%s' % (TAG, os.path.basename(kc))) or {}
    case('T305c the reference\'s time-series KMZ with other content in its entry (the same network): rerun DECISION, rc 4; the KMZ among '
         'the files that differ, its entries compared (content not equal)',
         rc == 4 and rr.get('verdict') == 'DECISION' and okc.get('content_equal') is False
         and any(x.endswith(os.path.basename(kc)) for x in (rr.get('outputs') or {}).get('other_differ') or []),
         'rc %d; %s; KMZ %s' % (rc, rr.get('verdict'), okc))

    R4d = copy_pkg(os.path.join(W, '_archive', 'T305d', 'ref_name', pk0))
    with open(os.path.join(R4d, 'Igrams', 'reports', 'extra_page.jpg'), 'wb') as fh:
        fh.write(b'T305d')
    remanifest(R4d)
    name_ref(R4d)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    case('T305d a name only in the reference (the same network, every shared file equal): G6d.4 INFO naming it; rerun DECISION, rc 4',
         rc == 4 and rr.get('verdict') == 'DECISION' and gates(rr).get('G6d.4') == 'INFO' and 'only in the reference 1' in val(rr, 'G6d.4')
         and 'extra_page.jpg' in note(rr, 'G6d.4') and (rr.get('outputs') or {}).get('other_differ') == [],
         'rc %d; %s; G6d.4 %s | %s' % (rc, rr.get('verdict'), val(rr, 'G6d.4'), note(rr, 'G6d.4')[:100]))

    R5 = copy_pkg(os.path.join(W, '_archive', 'T306', 'ref_broken', pk0))
    with open(os.path.join(R5, 'Igrams', sorted(os.listdir(os.path.join(R5, 'Igrams')))[0]), 'ab') as fh:
        fh.write(b'x')   # a payload file changed after its manifest was written
    name_ref(R5)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    case('T306 a broken reference (a payload file changed after its manifest): rerun FAIL at G6d.3 naming the line, rc 2',
         rc == 2 and rr.get('verdict') == 'FAIL' and gates(rr).get('G6d.3') == 'FAIL' and 'the reference: 1 lines not OK' in note(rr, 'G6d.3'),
         'rc %d; G6d.3 %s | %s' % (rc, gates(rr).get('G6d.3'), note(rr, 'G6d.3')[:120]))

    R6 = copy_pkg(os.path.join(W, '_archive', 'T306b', 'ref_other', pk0))
    os.rename(os.path.join(R6, 'TRANSFER_MANIFEST_%s.txt' % TAG), os.path.join(R6, 'TRANSFER_MANIFEST_P084F3310.txt'))
    name_ref(R6)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    with open(os.path.join(W, 'recon', 'rerun_reference.txt'), 'w') as fh:
        fh.write('# linog_auto self-test T306c: a reference file that names no folder\n')
    rc2, out2 = run(['--only', 'rerun'])
    rr2 = rec('6d', 'rerun')
    case('T306b another frame\'s package named (its manifest TRANSFER_MANIFEST_P084F3310.txt): rerun FAIL at G6d.2, rc 2; T306c a '
         'recon/rerun_reference.txt naming no folder: FAIL at G6d.2, rc 2',
         rc == 2 and gates(rr).get('G6d.2') == 'FAIL' and 'not this frame' in val(rr, 'G6d.2') and rc2 == 2
         and gates(rr2).get('G6d.2') == 'FAIL' and 'names no folder' in val(rr2, 'G6d.2'),
         'rc %d: %s | rc %d: %s' % (rc, val(rr, 'G6d.2')[:100], rc2, val(rr2, 'G6d.2')[:80]))

    unname('T307')
    AR = os.path.join(T, ROOT, 'p084', '_archive')
    t_new, t_dec, t_mid, t_old = (os.path.join(AR, 'f%s_%s' % (FRAME, x)) for x in ('v0.11_20261009T050000Z', 'v0.11_20261009T040000Z',
                                                                                    'v0.10_20261008T082537Z', 'v0.9_20261001T000000Z'))
    os.makedirs(os.path.join(t_new, 'status'))   # a newer tree without a package: passed over
    copy_pkg(os.path.join(t_dec, q6['XFER'], pk0))   # then one whose rerun ended in DECISION: passed over too
    os.makedirs(os.path.join(t_dec, 'status'))
    with open(os.path.join(t_dec, 'status', 'P6d_rerun.json'), 'w') as fh:
        json.dump(dict(phase='rerun', index='6d', verdict='DECISION'), fh)
    pm = copy_pkg(os.path.join(t_mid, q6['XFER'], pk0))
    retime(pm, (2026, 10, 8, 9, 22, 6))
    remanifest(pm)
    os.makedirs(os.path.join(t_mid, 'status'))
    with open(os.path.join(t_mid, 'status', 'P6c_package.json'), 'w') as fh:
        json.dump(dict(phase='package', index='6c', verdict='PASS', outputs=dict(package='%s/%s' % (q6['XFER'], pk0))), fh)
    po = copy_pkg(os.path.join(t_old, q6['XFER'], pk0))
    probe('tif_shift', os.path.join(po, 'LInOG_Upload_%s' % TAG, '%s_Velocity_demErr.tif' % TAG), '0.010')
    remanifest(po)
    rc, out = run(['--only', 'rerun'])
    rr = rec('6d', 'rerun')
    case('T307 no recon/rerun_reference.txt; under p084/_archive/ four trees of the frame: the newest (v0.11_20261009T050000Z) without '
         'a package, then v0.11_20261009T040000Z whose rerun record reads DECISION, then v0.10_20261008T082537Z whose '
         'status/P6c_package.json names its package, then an older one: rerun takes v0.10\'s (the two newer passed over, each named '
         'with why), PASS, rc 0',
         rc == 0 and rr.get('verdict') == 'PASS' and (rr.get('outputs') or {}).get('reference', {}).get('path') == pm
         and 'passed over' in val(rr, 'G6d.2') and 'v0.11_20261009T050000Z' in val(rr, 'G6d.2')
         and 'v0.11_20261009T040000Z (its rerun record reads DECISION)' in val(rr, 'G6d.2') and gates(rr).get('G6d.9') == 'PASS',
         'rc %d; G6d.2 %s' % (rc, val(rr, 'G6d.2')[:220]))

    m0 = dict((p, md5(p)) for p in glob.glob(os.path.join(W, 'status', 'P*.json')))
    rc, out = run([])
    phases = re.search(r'^PHASES="([^"]*)"', open(os.path.join(S.HERE, 'linog_auto.sh')).read(), re.M).group(1).split()
    case('T308 a re-run with no --to: all 31 phases skipped (v0.13: bandlimit; v0.12: drop1 among them; PASS on record, inputs unchanged), rc 0, every '
         'record unchanged; the driver\'s phases end with package, rerun',
         rc == 0 and out.count('skip: PASS on record') == 31 and len(phases) == 31 and phases[-2:] == ['package', 'rerun']
         and all(md5(p) == h for p, h in m0.items()),
         'rc %d; %d skipped; %d phases, last %s' % (rc, out.count('skip: PASS on record'), len(phases), phases[-2:]))

    D = os.path.join(T, 'dry_p11')
    l0, g0 = listing(W), md5(os.path.join(W, 'logs', 'STATUS.txt'))
    rc, out = run(['--dry-run', D, '--only', 'rerun'])
    dr = json.load(open(os.path.join(D, 'status', 'P6d_rerun.json'))) if os.path.isfile(os.path.join(D, 'status', 'P6d_rerun.json')) else {}
    case('T309 rerun\'s dry run (--only rerun): rc 0; its record in DIR, PASS, the same reference and verdict as the run\'s; the frame '
         'unchanged (listing and ledger)',
         rc == 0 and dr.get('verdict') == 'PASS' and (dr.get('outputs') or {}).get('reference', {}).get('path') == pm
         and gates(dr).get('G6d.9') == 'PASS' and listing(W) == l0 and md5(os.path.join(W, 'logs', 'STATUS.txt')) == g0,
         'rc %d; %s; G6d.9 %s; frame unchanged %s' % (rc, dr.get('verdict'), gates(dr).get('G6d.9'), listing(W) == l0))

    # ------------------------------------------------------------------ item 5
    l0 = listing(W)
    O1 = os.path.join(T, 'cmp_out', 'packages')
    rc, out = compare(['packages', package(), R3, '--out', O1])
    cj = json.load(open(os.path.join(O1, 'compare_packages.json'))).get('result', {}) if os.path.isfile(os.path.join(O1, 'compare_packages.json')) else {}
    rdg = (cj.get('readings') or {}).get('demErr') or {}
    case('T310 lp_compare.py packages, the frame\'s package against T304\'s reference (the env\'s python3, as on felix): rc 0; its JSON '
         'under --out: the network complete and equal, the demErr GeoTIFF among the files that differ, max 10.00 mm/yr; the report '
         'lines in compare_packages.txt',
         rc == 0 and (cj.get('network') or {}).get('equal') is True and any(x.endswith('_Velocity_demErr.tif') for x in cj.get('other_differ') or [])
         and abs(rdg.get('max_abs', 0) - 10.0) < 1e-3 and os.path.isfile(os.path.join(O1, 'compare_packages.txt')),
         'rc %d; other_differ %s; demErr %s' % (rc, cj.get('other_differ'), dict((k, rdg.get(k)) for k in ('max_abs', 'gained', 'lost'))))

    C2 = os.path.join(T, 'cmp_trees', 'shelves')
    for d in sorted(x for x in os.listdir(os.path.join(W, 'SLC')) if x.isdigit()):   # the shelves alone, not the SLC images
        os.makedirs(os.path.join(C2, 'SLC', d))
        for n in os.listdir(os.path.join(W, 'SLC', d)):
            if n.startswith('data'):
                shutil.copy2(os.path.join(W, 'SLC', d, n), os.path.join(C2, 'SLC', d, n))
    d1 = sorted(d for d in os.listdir(os.path.join(C2, 'SLC')) if d.isdigit())[0]
    pb = probe('shelf_bump', os.path.join(C2, 'SLC', d1, 'data'))
    O2 = os.path.join(T, 'cmp_out', 'shelves')
    rc, out = compare(['shelves', W, C2, '--out', O2])
    sj = json.load(open(os.path.join(O2, 'compare_shelves.json'))).get('result', {}) if os.path.isfile(os.path.join(O2, 'compare_shelves.json')) else {}
    rows = sj.get('rows') or []
    dif = [r for r in rows if r.get('differ')]
    case('T311 lp_compare.py shelves, the frame against a copy of its SLC/ with one float attribute of %s\'s frame + 1.0: rc 0; that '
         'shelve key alone differs, by 1 leaf (object ids left out), every other key bytes identical; no isce.log where it was run' % d1,
         rc == 0 and '_error' not in pb and len(dif) == 1 and dif[0].get('date') == d1 and dif[0].get('key') == 'frame'
         and dif[0].get('differ') == 1 and all(r.get('state') == 'bytes identical' for r in rows if r is not dif[0])
         and not os.path.exists(os.path.join(T, 'isce.log')),
         'rc %d; %d rows; differing %s; probe %s' % (rc, len(rows), [(r.get('date'), r.get('key'), r.get('differ')) for r in dif], pb))

    C3, C3n = os.path.join(T, 'cmp_trees', 'cycles_ref'), os.path.join(T, 'cmp_trees', 'cycles_new')
    for c3 in (C3n, C3):
        os.makedirs(os.path.join(c3, 'mintpy', 'inputs'))
        shutil.copy2(os.path.join(W, 'mintpy', 'inputs', 'ifgramStack.h5'), os.path.join(c3, 'mintpy', 'inputs', 'ifgramStack.h5'))
        probe('unw_field', os.path.join(c3, 'mintpy', 'inputs', 'ifgramStack.h5'))
    pu = probe('unw_jump', os.path.join(C3, 'mintpy', 'inputs', 'ifgramStack.h5'))
    O3 = os.path.join(T, 'cmp_out', 'cycles')
    rc, out = compare(['cycles', C3n, C3, '--out', O3])
    yj = json.load(open(os.path.join(O3, 'compare_cycles.json'))).get('result', {}) if os.path.isfile(os.path.join(O3, 'compare_cycles.json')) else {}
    yr = dict((r.get('pair'), r) for r in yj.get('rows') or [])
    p0 = yr.get(pu.get('pair0')) or {}
    case('T312 lp_compare.py cycles on two copies of the frame\'s stack, their unwrapPhase a smooth field (the mock\'s are 0), one '
         'with pair 0\'s + 2 pi on a block and pair 1\'s dropIfgram flipped: rc 0; dropIfgram differs on that pair alone; pair 0 the only pair with cells beyond pi, every other pair '
         'byte-equal',
         rc == 0 and '_error' not in pu and [x.get('pair') for x in (yj.get('kept') or {}).get('differ') or []] == [pu.get('pair1')]
         and p0.get('beyond_pi', 0) > 0 and all(r.get('byte_equal') for k, r in yr.items() if k != pu.get('pair0'))
         and not p0.get('byte_equal'),
         'rc %d; kept differ %s; pair 0 %s; probe %s' % (rc, (yj.get('kept') or {}).get('differ'),
                                                        dict((k, p0.get(k)) for k in ('beyond_pi', 'offset', 'cells')), pu))

    C4, C5 = os.path.join(T, 'cmp_trees', 'split_ref'), os.path.join(T, 'cmp_trees', 'split_new')
    ienv = dict((k, v) for k, v in os.environ.items() if not k.startswith('LINOG_'))
    ienv['LINOG_ENV_CFG'] = os.path.join(T, 'cfg', 'env_mock.cfg')
    pd = {}
    for c in (C5, C4):   # NEW: the frame's stack and network; REF: the same stack, one pair dropped; each inverted by the mock
        os.makedirs(os.path.join(c, 'mintpy', 'inputs'))
        for n in ('inputs/ifgramStack.h5', 'inputs/geometryRadar.h5', 'smallbaselineApp.cfg', 'maskTempCoh.h5'):
            shutil.copy2(os.path.join(W, 'mintpy', n), os.path.join(c, 'mintpy', n))
        if c == C4:
            pd = probe('drop_one', os.path.join(c, 'mintpy', 'inputs', 'ifgramStack.h5'))
        subprocess.run(['bash', os.path.join(S.HERE, 'lp_env.sh'), 'ifgram_inversion.py', 'inputs/ifgramStack.h5', '-t', 'smallbaselineApp.cfg'],
                       cwd=os.path.join(c, 'mintpy'), env=ienv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    SC = os.path.join(T, 'cmp_scratch')
    rc0, out0 = compare(['split', C5, C4, '--scratch', SC])
    plan_only = rc0 == 0 and 'plan only' in out0 and not os.path.exists(os.path.join(SC, 'cf'))
    O4 = os.path.join(T, 'cmp_out', 'split')
    rc, out = compare(['split', C5, C4, '--scratch', SC, '--run', '--out', O4])
    pj = json.load(open(os.path.join(O4, 'compare_split.json'))).get('result', {}) if os.path.isfile(os.path.join(O4, 'compare_split.json')) else {}
    stt = open(os.path.join(SC, 'cf', 'split.status')).read() if os.path.isfile(os.path.join(SC, 'cf', 'split.status')) else ''
    vv = pj.get('velocity') or {}
    rc2, out2 = compare(['split', C5, C4, '--cf', os.path.join(SC, 'cf'), '--out', os.path.join(T, 'cmp_out', 'split_cf')])
    pj2 = json.load(open(os.path.join(T, 'cmp_out', 'split_cf', 'compare_split.json'))).get('result', {}) \
        if os.path.isfile(os.path.join(T, 'cmp_out', 'split_cf', 'compare_split.json')) else {}
    rc3, out3 = compare(['split', C5, C4, '--scratch', SC, '--run'])
    rest = (vv.get('the rest: CF - REF') or {}).get('all') or {}
    case('T313 lp_compare.py split on two copies of the frame\'s stack inverted by the mock ifgram_inversion.py, NEW with its network, '
         'REF without %s: without --run the plan only (the pair named, nothing written); with --run NEW\'s copy under --scratch/cf with '
         'REF\'s network (split.status exit=0, one pair fewer kept), then the three differences on every cell and in both masks: the '
         'rest exactly 0 (CF is REF\'s inversion), the network equal to the total; --cf on that folder gives the same; a second --run '
         'into the same --scratch refused (rc 2)' % pd.get('dropped'),
         plan_only and pd.get('dropped', '-') in out0 and rc == 0 and stt.startswith('exit=0 ') and ('kept=%d' % pd.get('kept', -1)) in stt
         and sorted(vv) == ['network: NEW - CF', 'the rest: CF - REF', 'total: NEW - REF']
         and all((vv[k].get('all') or {}).get('n', 0) > 0 and (vv[k].get('both_masks') or {}).get('n', 0) > 0 for k in vv)
         and (pj.get('tempcoh') or {}).get('threshold') == 0.7
         and rest.get('max_abs') == 0.0 and vv['network: NEW - CF'] == vv['total: NEW - REF']
         and (vv['network: NEW - CF'].get('all') or {}).get('max_abs', 0) > 0
         and rc2 == 0 and pj2.get('velocity') == pj.get('velocity') and rc3 == 2 and 'not empty' in out3,
         'plan %s (rc %d); rc %d, status %r; velocity keys %s; --cf rc %d equal %s; again rc %d' % (
             plan_only, rc0, rc, stt.strip(), sorted(vv), rc2, pj2.get('velocity') == pj.get('velocity'), rc3))

    rc4, out4 = compare(['packages', package(), R3, '--out', os.path.join(package(), 'cmp')])
    case('T314 lp_compare.py wrote nothing in what it compared: the frame\'s listing as before T310; an --out inside a compared '
         'package refused, rc 2, nothing written there',
         listing(W) == l0 and rc4 == 2 and 'only reads' in out4 and not os.path.exists(os.path.join(package(), 'cmp')),
         'frame unchanged %s; rc %d: %s' % (listing(W) == l0, rc4, out4.strip().splitlines()[-1][:120] if out4.strip() else ''))

    # ------------------------------------------------------------------ item 4: a KMZ refused
    restore('T302')
    rc, out = run([], extra=dict(LINOG_MOCK_KMZ_EXTRA='1'))
    rd = rec('6a', 'deliver')
    kz = sorted(glob.glob(os.path.join(UP, '*.kmz')))
    ents = [e for k in kz for e in entries(k)]
    case('T302 a velocity KMZ with an extra field (LINOG_MOCK_KMZ_EXTRA, as Info-ZIP\'s timestamp): deliver FAIL at G6a.10 naming '
         'it, rc 2; all 4 KMZs left as written (none at the fixed time); no RUN_MANIFEST.json',
         rc == 2 and rd.get('verdict') == 'FAIL' and gates(rd).get('G6a.10') == 'FAIL' and 'extra field' in note(rd, 'G6a.10')
         and 'no KMZ replaced' in note(rd, 'G6a.10') and len(kz) == 4 and ents and not any(e['date_time'] == FIXED for e in ents)
         and not os.path.isfile(os.path.join(W, 'RUN_MANIFEST.json')),
         'rc %d; G6a.10 %s | %s; %d KMZs, times %s' % (rc, gates(rd).get('G6a.10'), note(rd, 'G6a.10').replace('\n', ' | ')[:200], len(kz),
                                                      sorted(set(e['date_time'] for e in ents))[:3]))

    # ------------------------------------------------------------------ lp_kmz.py alone
    import io
    import struct
    KT = os.path.join(T, 'kmz_unit')
    os.makedirs(KT)

    class Stream(io.RawIOBase):   # a write-only stream that cannot seek: zipfile writes data descriptors (flag bit 3) to it
        def __init__(self, fh):
            self.fh = fh

        def writable(self):
            return True

        def write(self, b):
            return self.fh.write(b)

    with open(os.path.join(KT, 'dd.kmz'), 'wb') as fh:
        with K.zipfile.ZipFile(Stream(fh), 'w', K.zipfile.ZIP_DEFLATED) as z:
            z.writestr('doc.kml', '<kml>T315</kml>' * 50)
            z.writestr('b.png', b'PNG' * 10)
    with K.zipfile.ZipFile(os.path.join(KT, 'dd.kmz')) as z:
        dflag = all(i.flag_bits & 8 for i in z.infolist())
    r = K.fix_times(os.path.join(KT, 'dd.kmz'), os.path.join(KT, 'dd_fixed.kmz'))
    okdd = dflag and r['entries'] == 2 and all(e['date_time'] == FIXED for e in entries(os.path.join(KT, 'dd_fixed.kmz')))
    with K.zipfile.ZipFile(os.path.join(KT, 'c.kmz'), 'w') as z:
        z.writestr('doc.kml', '<kml/>')
        z.comment = b'T315 comment'
    K.fix_times(os.path.join(KT, 'c.kmz'), os.path.join(KT, 'c_fixed.kmz'))
    with K.zipfile.ZipFile(os.path.join(KT, 'c_fixed.kmz')) as z:
        okc = z.comment == b'T315 comment'
    good = open(os.path.join(KT, 'c.kmz'), 'rb').read()
    e = good.rfind(b'PK\x05\x06')
    bads = dict(trail=good + b'xx', zip64=good[:e] + b'PK\x06\x07' + b'\0' * 16 + good[e:],
                empty=b'PK\x05\x06' + b'\0' * 18)
    zi = K.zipfile.ZipInfo('doc.kml', (2026, 10, 9, 1, 2, 4))
    zi.extra = b'UT\x05\x00\x01' + struct.pack('<I', 1791500000)
    with K.zipfile.ZipFile(os.path.join(KT, 'extra.kmz'), 'w') as z:
        z.writestr(zi, '<kml/>')
    bads['extra'] = open(os.path.join(KT, 'extra.kmz'), 'rb').read()
    refused = {}
    for n, b in sorted(bads.items()):
        with open(os.path.join(KT, n + '.kmz'), 'wb') as fh:
            fh.write(b)
        try:
            K.fix_times(os.path.join(KT, n + '.kmz'), os.path.join(KT, n + '_fixed.kmz'))
            refused[n] = 'NOT refused'
        except K.KmzError as x:
            refused[n] = str(x) if not os.path.exists(os.path.join(KT, n + '_fixed.kmz')) else 'refused, but wrote its output'
    case('T315 lp_kmz.py alone: a zip written with data descriptors (flag bit 3) fixed, 2 entries at 1980-01-01; a zip comment kept; '
         'refused, nothing written: bytes after the archive, an extra field, a ZIP64 locator, no entry',
         okdd and okc and 'bytes after' in refused.get('trail', '') and 'extra field' in refused.get('extra', '')
         and refused.get('zip64') == 'ZIP64' and refused.get('empty') == 'no entries',
         'data descriptors %s fixed %s; comment kept %s; %s' % (dflag, okdd, okc, refused))
