#!/usr/bin/env python3
"""lp_unpack.py -- linog_auto Phase 1b: unpack every extracted granule straight into SLC/<date>/.

Runs inside lp_env.sh (a clean linog_isce2 environment). Calls the LInOG unpacker by its absolute path with
this Python, never by name (the env's stock copy comes first on the PATH: the unpacker PATH shadow), from the
frame folder, so each shelve records SLC/<date>/<date>.slc as the kit's frames do. The unpacker's exit code
is not trusted (N11): every date's outputs are sized and counted. A date finished in an earlier run is listed
in status/P1b_unpack.progress and not unpacked again. Nothing is overwritten, moved or deleted.

v0.13 (ascending record 12.3 item 4, 4.2): G1b.2 checks the env's prefix as well as its name (CONDA_PREFIX is
linog_stack.cfg's ENV_PREFIX); a log that names IMG-HV, or no IMG-HH, is G1b.5's FAIL, as this docstring always said (v0.12
reported it under G1b.4). FBD dates unpack as FBS dates do: IMG-HH by the pinned unpacker (R6, 18.5).

Gates
  G1b.1 extract PASS on record                                                       FAIL
  G1b.2 environment: CONDA_DEFAULT_ENV is the pinned env, CONDA_PREFIX its prefix, `import isce` works      ERROR
  G2    unpacker: the pinned md5, an absolute path                                   FAIL
  G1b.3 nothing in the way: SLC/<date> absent, or finished earlier from the same granule by the same unpacker
        (progress record, sizes match); nothing in SLC/ but the kept dates (a stale date would enter the stack
        at Phase 2)                                                                          DECISION
  G1b.6 free disk for the SLCs still to write, plus the path table's disk_gib_margin   FAIL
  G1b.4 per date: unpacker rc 0; <date>.slc = width x lines x 8 B, its .xml and the shelve present   FAIL
  G1b.5 per date: the unpacker's log names IMG-HH as its input, never IMG-HV          FAIL
--dryrun DIR: G1b.1, G1b.2, G2, G1b.3 and G1b.6 on the plan; writes only DIR/status/P1b_unpack.json
(its outputs carry the planned dates, so the verify dry run can plan from them).
Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import json
import os
import subprocess
import sys
import time

import lp_common as C
import lp_p1 as P1

TOOLS = ('lp_unpack.py', 'lp_p1.py', 'lp_common.py')


def slc_problems(W, date, width, lines):
    d = os.path.join(W, 'SLC', date)
    slc = os.path.join(d, date + '.slc')
    shelf = sorted(f for f in os.listdir(d) if f == 'data' or f.startswith('data.')) if os.path.isdir(d) else []
    probs = []
    if not os.path.isfile(slc):
        probs.append('no %s.slc' % date)
    elif os.path.getsize(slc) != width * lines * 8:
        probs.append('%s.slc is %d B, want %d x %d x 8 = %d' % (date, os.path.getsize(slc), width, lines,
                                                               width * lines * 8))
    if not os.path.isfile(slc + '.xml'):
        probs.append('no %s.slc.xml' % date)
    if not shelf:
        probs.append('no shelve')
    return probs, shelf


def progress(recdir):
    f = os.path.join(recdir, 'status', 'P1b_unpack.progress')
    done = {}
    if os.path.exists(f):
        for ln in open(f):
            try:
                r = json.loads(ln)
                done[r['date']] = r
            except (ValueError, KeyError):
                pass
    return f, done


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 1b: unpack')
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
    U = env['UNPACKER']
    u_md5 = C.md5_file(U) if os.path.isfile(U) else None
    r_ext = P1.record(recdir, '1a', 'extract')
    gran = (r_ext or {}).get('outputs', {}).get('granules', [])
    fp = C.md5_obj(dict(granules=(r_ext or {}).get('outputs', {}).get('granules_md5'),
                        extract_fp=(r_ext or {}).get('fingerprint'), unpacker=u_md5, env_cfg=env['env_cfg_md5'],
                        tools=C.tool_md5s(*TOOLS)))
    if a.state:
        def missing(r):
            ds = (r or {}).get('outputs', {}).get('dates', [])
            sd = os.path.join(W, 'SLC')
            extra = sorted(set(os.listdir(sd)) - set(d['date'] for d in ds)) if os.path.isdir(sd) else []
            return [d['date'] for d in ds if slc_problems(W, d['date'], d['width'], d['lines'])[0]] + extra
        print(P1.state_with_outputs(recdir, 'unpack', '1b', fp, missing))
        return 0

    st = C.Status(recdir, 'unpack', '1b', path, frame)
    P1.begin(st)
    st.rec['version'] = P1.VERSION1
    st.rec.update(fingerprint=fp, tools=C.tool_md5s(*TOOLS),
                  inputs=dict(granules_md5=(r_ext or {}).get('outputs', {}).get('granules_md5'), unpacker=U,
                              unpacker_md5=u_md5, env_cfg=env['env_cfg_file'], env_cfg_md5=env['env_cfg_md5']))
    st.write()
    print('%s  Phase 1b unpack  p%s f%s  %s' % (P1.VERSION1, path, frame, C.utc()))
    print('   frame folder %s%s' % (W, '   (DRY RUN: plan only)' if a.dryrun else ''))
    if P1.prior(st, 'G1b.1', recdir, [('1a', 'extract')]) is None:
        return st.finish()
    try:
        import isce  # noqa: F401
        iv = getattr(isce, '__version__', '?')
        ok, ev, note = P1.env_check(env)
        st.gate('G1b.2', 'environment', 'PASS' if ok else 'ERROR', '%s, isce %s, python %s %s' % (
            ev, iv, sys.executable, sys.version.split()[0]), '%s at ENV_PREFIX' % env['CONDA_ENV'], note)
    except Exception as e:  # noqa: BLE001
        st.gate('G1b.2', 'environment', 'ERROR', 'import isce failed: %s' % e, env['CONDA_ENV'])
    st.rec['inputs'].update(pythonpath=os.environ.get('PYTHONPATH', ''), conda_env=os.environ.get('CONDA_DEFAULT_ENV'))
    g2 = os.path.isabs(U) and u_md5 == env['UNPACKER_MD5']
    st.gate('G2', 'unpacker md5, absolute path', 'PASS' if g2 else 'FAIL', '%s %s' % (U, u_md5), env['UNPACKER_MD5'])
    pf, done = progress(W)
    plan, way = [], []
    for g in gran:
        d = g['date']
        probs, _ = slc_problems(W, d, g['width'], g['lines'])
        if os.path.lexists(os.path.join(W, 'SLC', d)):
            pr = done.get(d, {})
            if pr and not probs and pr.get('unpacker') == u_md5 and pr.get('stem') == g['stem']:
                act = 'done'
            else:
                why = probs or (['no progress line'] if not pr else [])
                if pr and pr.get('unpacker') != u_md5:
                    why.append('made by unpacker %s, pinned now %s' % (pr.get('unpacker'), u_md5))
                if pr and pr.get('stem') != g['stem']:
                    why.append('made from %s, kept granule now %s' % (pr.get('stem'), g['stem']))
                way.append('%s: exists, not finished by an earlier run of this plan (%s)' % (
                    os.path.join(W, 'SLC', d), '; '.join(why)))
                act = 'blocked'
        else:
            act = 'unpack'
        plan.append(dict(g, action=act))
    sd = os.path.join(W, 'SLC')
    kept_dates = set(g['date'] for g in gran)
    for e in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
        if e not in kept_dates:
            way.append('%s: in SLC/ but not a kept date' % os.path.join(sd, e))
    todo = [p for p in plan if p['action'] == 'unpack']
    margin = float(cfg.get('disk_gib_margin', 10))
    need = sum(p['width'] * p['lines'] * 8 for p in todo) / 2.0 ** 30 + margin
    free = P1.free_gib(W)
    st.gate('G1b.6', 'free disk', 'PASS' if free >= need else 'FAIL', '%.1f GiB free, %.1f GiB needed' % (free, need),
            '>= what is to write + disk_gib_margin %.0f GiB' % margin)
    st.gate('G1b.3', 'nothing in the way', 'DECISION' if way else 'PASS',
            '%d to unpack, %d done earlier, %d in the way' % (len(todo), sum(p['action'] == 'done' for p in plan), len(way)),
            '0 in the way', '\n'.join(way) + ('\nnothing was changed; move these into %s/ by hand, then re-run'
                                              % os.path.join(W, '_archive') if way else ''))
    if any(x['verdict'] in ('FAIL', 'DECISION', 'ERROR') for x in st.rec['gates']):
        return st.finish()
    if a.dryrun:
        print('   would unpack %d dates into %s/SLC/<date>/ (%.1f GB of SLC)' % (
            len(todo), W, sum(p['width'] * p['lines'] * 8 for p in todo) / 1e9))
        for p in todo[:3]:
            print('      unzipped/%s -> SLC/%s' % (p['stem'], p['date']))
        if len(todo) > 3:
            print('      ... %d more' % (len(todo) - 3))
        dates = [dict(date=p['date'], stem=p['stem'], mode=p['mode'], width=p['width'], lines=p['lines'],
                      slc=os.path.join(W, 'SLC', p['date'], p['date'] + '.slc')) for p in plan]
        st.rec['outputs'] = dict(planned=len(todo), dryrun=True, dates=dates, dates_md5=C.md5_obj(dates))
        return st.finish('plan only (dry run)')

    os.makedirs(os.path.join(W, 'SLC'), exist_ok=True)
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        d, t = p['date'], time.time()
        lg = P1.new_log(os.path.join(W, 'logs', 'unpack', d + '.log'))
        with open(lg, 'w') as fh:
            rc = subprocess.call([sys.executable, U, '-i', os.path.join('unzipped', p['stem']),
                                  '-o', os.path.join('SLC', d)], cwd=W, stdout=fh, stderr=subprocess.STDOUT)
        probs, shelf = slc_problems(W, d, p['width'], p['lines'])
        if rc != 0:
            probs.insert(0, 'unpacker rc %d' % rc)
        txt = open(lg, errors='replace').read()
        hv = []   # v0.13: G1b.5's own FAIL (v0.12 put it among G1b.4's problems)
        if 'IMG-HV-' in txt or 'IMG-HH-' not in txt:
            hv.append('the log does not name IMG-HH as the input%s' % (' (it names IMG-HV)' if 'IMG-HV-' in txt else ''))
        print('   [%2d/%d] %s  rc %d  %.0f MB  %.0f s%s' % (i, len(todo), d, rc,
                                                        p['width'] * p['lines'] * 8 / 1e6, time.time() - t,
                                                        ('  ' + '; '.join(probs + hv)) if probs or hv else ''))
        sys.stdout.flush()
        if probs or hv:
            tail = [x for x in txt.strip().splitlines() if x.strip()][-3:]
            note = 'SLC/%s is left as it is: move it into %s/ before the next run\nlog %s, last lines:\n%s' % (
                d, os.path.join(W, '_archive'), lg, '\n'.join('  ' + x for x in tail))
            if probs:
                st.gate('G1b.4', 'SLC, xml, shelve per date', 'FAIL', '%s: %s' % (d, '; '.join(probs)), 'all', note)
            if hv:
                st.gate('G1b.5', 'input IMG-HH per date', 'FAIL', '%s: %s' % (d, '; '.join(hv)), 'all', note)
            return st.finish()
        with open(pf, 'a') as fh:
            fh.write(json.dumps(dict(date=d, stem=p['stem'], unpacker=u_md5, rc=rc, shelve=shelf, log=lg,
                                     slc_bytes=p['width'] * p['lines'] * 8, end=C.utc())) + '\n')
    _, done = progress(W)
    dates, bad = [], []
    for p in plan:
        probs, shelf = slc_problems(W, p['date'], p['width'], p['lines'])
        if probs or p['date'] not in done:
            bad.append('%s: %s' % (p['date'], '; '.join(probs) or 'no progress line'))
        dates.append(dict(date=p['date'], stem=p['stem'], mode=p['mode'], width=p['width'], lines=p['lines'],
                          slc=os.path.join(W, 'SLC', p['date'], p['date'] + '.slc'), shelve=shelf,
                          log=done.get(p['date'], {}).get('log')))
    st.gate('G1b.4', 'SLC, xml, shelve per date', 'FAIL' if bad else 'PASS',
            '%d of %d dates, %.0f s' % (len(plan) - len(bad), len(plan), time.time() - t0), 'all', '\n'.join(bad))
    st.gate('G1b.5', 'input IMG-HH per date', 'PASS', '%d of %d logs name IMG-HH' % (len(todo), len(todo)),
            'all', 'dates done in an earlier run were checked then' if len(todo) < len(plan) else '')
    st.rec['outputs'] = dict(dates=dates, dates_md5=C.md5_obj(dates), unpacked=len(todo), done_before=len(plan) - len(todo))
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_unpack', main)
