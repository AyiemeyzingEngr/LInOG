#!/usr/bin/env python3
"""lp_mcfg.py -- linog_auto Phase 5c: MintPy's template for the frame, mintpy/smallbaselineApp.cfg.

Runs inside lp_env.sh. The kit copies the frame's previous cfg (ph_pin) and dies without one; the 12 delivered
frames were first seeded by hand from a sibling, the trap of eleven absolute sibling paths. This phase writes the
template from MintPy's own defaults file (pinned by md5: every key and comment, as the 12 delivered cfgs carry
them), puts in place linog_mintpy.cfg's values (the keys the 12 cfgs set alike, with F40 to F44 applied), admit's
decisions (excludeDate, excludeDate12, unwrapError), reference.yx auto (sbas pins it with the kit's G19) and, in a
marked block at the end, ORBIT_DIRECTION from the path table (load_data writes MACRO_CASE template keys into the stack,
F38; G24). Then the kit's bootstrap: `smallbaselineApp.py smallbaselineApp.cfg --dostep load_data` from mintpy/
(Phase 5's second working folder), and SNWE from inputs/geometryRadar.h5's latitude and longitude, snapped outward on
the 1/1200 deg lattice with a 2 px margin (ph_pin's formula), put into the template.

Gates
  G5c.1  prep PASS on record, its files as it wrote them; admit PASS, recon/admission.json as it wrote it   FAIL
  G5c.2  environment; MintPy at its pin                                                     ERROR / FAIL
  G5c.3  smallbaselineApp.py on the PATH is the pinned env's                                              FAIL
  G5c.4  nothing in the way: mintpy/ absent                                                                DECISION
  G5c.5  the template: the defaults file's keys, each once; each value put on its one line; every path under
         the frame and there (the three globs: one file per pair); no other frame's folder named;
         ORBIT_DIRECTION; mintpy.load.autoPath auto or no (F44)                                           FAIL
  G5c.6  the bootstrap load_data: rc 0; the steps as asked; F40's two warnings absent; ifgramStack.h5 and
         geometryRadar.h5 written                                                                          FAIL
  G24c   the bootstrap stack: HEADING in the direction's band; ORBIT_DIRECTION as written                   FAIL
  G5c.7  SNWE: on the lattice, every valid latitude and longitude inside it; put on its line               FAIL
--dryrun DIR: the template (SNWE left auto) written to DIR/mintpy/ and checked; no load_data; a plan only when the
frame's igram has not run. Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import glob
import json
import os
import re

import lp_common as C
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5

PHASE, IDX, LOGIC = 'mcfg', '5c', 1
GLOBS = ('mintpy.load.unwFile', 'mintpy.load.corFile', 'mintpy.load.connCompFile')


def template(defaults_text, m, W, ref, adm, direction):
    """(text, values, extras, problems)."""
    vals = dict((k, v.replace('{W}', W).replace('{REF}', ref)) for k, v in m['cfg'].items())
    vals.update(adm.get('cfg', {}))
    vals['mintpy.reference.yx'] = 'auto'
    vals['mintpy.geocode.SNWE'] = 'auto'
    extras = [('ORBIT_DIRECTION', 'descending' if direction == 'D' else 'ascending')]
    text, bad = P5.set_values(defaults_text, vals, extras)
    return text, vals, extras, bad


def check_template(text, defaults_text, vals, extras, W, path, frame, npairs):
    """The problems of a written template (G5c.5), and what was read."""
    bad = []
    kv = P5.read_cfg(text, is_text=True)
    keys = [k for k, _, _ in kv]
    dkeys = [k for k, _, _ in P5.read_cfg(defaults_text, is_text=True)]
    dup = sorted(k for k in set(keys) if keys.count(k) > 1)
    if dup:
        bad.append('keys on more than one line: %s' % ', '.join(dup))
    miss = [k for k in dkeys if k not in keys]
    extra = sorted(set(keys) - set(dkeys) - set(k for k, _ in extras))
    if miss or extra:
        bad.append('keys missing %s, not in the defaults file %s' % (miss[:5], extra[:5]))
    d = dict((k, v) for k, v, _ in kv)
    for k, v in list(vals.items()) + list(extras):
        if d.get(k) != v:
            bad.append('%s reads %r, want %r' % (k, d.get(k), v))
    for k in sorted(vals):
        v = d.get(k, '')
        if not (k.startswith('mintpy.load.') and (k.endswith('File') or k.endswith('Dir'))) or v in ('auto', 'no', ''):
            continue
        if not v.startswith(W + '/'):
            bad.append('%s = %s is not under %s' % (k, v, W))
            continue
        n = len(glob.glob(v))
        if k in GLOBS:
            if n != npairs:
                bad.append('%s matches %d files, the frame has %d pairs' % (k, n, npairs))
        elif k.endswith('Dir'):
            if not os.path.isdir(v):
                bad.append('%s: no folder %s' % (k, v))
        elif not os.path.isfile(v):
            bad.append('%s: no file %s' % (k, v))
    others = sorted(set(x for x in re.findall(r'/p(\d{3})/f(\d{4})', text) if x != (path, frame)))
    if others:
        bad.append('other frames named: %s' % ', '.join('p%s/f%s' % x for x in others))
    ap = d.get('mintpy.load.autoPath', 'auto')
    if ap not in ('auto', 'no'):
        bad.append('mintpy.load.autoPath = %s: a load key left at auto would then load (F44)' % ap)
    return bad, d, len(keys)


def write_atomic(p, text):
    tmp = p + '.tmp%d' % os.getpid()
    with open(tmp, 'w') as fh:
        fh.write(text)
    os.replace(tmp, p)


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 5c: MintPy\'s template (and the bootstrap load, SNWE)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, m = P1.load_env(), P2.load_stack(), P5.load_mintpy()
    geo, _ = P3.geometry(W)
    ref = (geo or {}).get('ref')
    rp = P1.record(recdir, '5b', 'prep') or {}
    ra = P1.record(recdir, '5a', 'admit') or {}
    fp = C.md5_obj(dict(logic=LOGIC, prep=rp.get('outputs', {}).get('content_md5'), admit=ra.get('outputs', {}).get('decisions_md5'),
                        cfg=m['cfg'], defaults=m['MINTPY_DEFAULTS_MD5'], mintpy=m['MINTPY_VERSION'],
                        lattice=[m['SNWE_LATTICE'], m['SNWE_MARGIN_PX']],
                        direction=cfg['direction'], reference=ref))
    mdir = os.path.join(recdir, 'mintpy')
    tfile = os.path.join(mdir, 'smallbaselineApp.cfg')

    def digest_changed(rec):
        want = (rec or {}).get('outputs', {}).get('cfg_digest')
        if not os.path.isfile(tfile):
            return ['gone: mintpy/smallbaselineApp.cfg']
        return [] if P5.cfg_digest(open(tfile).read()) == want else ['changed: mintpy/smallbaselineApp.cfg (other than reference.yx)']
    if a.state:
        print(P5.state(recdir, W, PHASE, IDX, fp, extra=digest_changed))
        return 0

    st = P5.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(mintpy_cfg=m['mintpy_cfg_file'], mintpy_cfg_md5=m['mintpy_cfg_md5']))
    P5.header(PHASE, IDX, path, frame, W, a.dryrun)
    rp = P5.prior5(st, 'G5c.1', recdir, W, '5b', 'prep', outs=not a.dryrun, dry=bool(a.dryrun))
    if not rp:
        return st.finish()
    ra = P5.prior5(st, 'G5c.1a', recdir, recdir, '5a', 'admit', outs=True, dry=bool(a.dryrun))
    if not ra:
        return st.finish()
    mi = P5.env_gate(st, 'G5c.2', env, s, m)
    if not mi:
        return st.finish()
    if not P5.which_gate(st, 'G5c.3', s, ('smallbaselineApp.py',)):
        return st.finish()
    if a.dryrun and not P5.frame_igram(W):
        return P5.plan_only(st, ['would write mintpy/smallbaselineApp.cfg from %s, then run its load_data from mintpy/ and set SNWE'
                                 % mi['defaults']], 'the frame has no interferograms yet')
    adm = json.load(open(os.path.join(recdir, 'recon', 'admission.json')))
    dtext = open(mi['defaults']).read()
    text, vals, extras, bad = template(dtext, m, W, ref, adm, cfg['direction'])
    npairs = len(P5.pairs_of(W))
    if a.dryrun:
        P5.way_gate(st, 'G5c.4', W, PHASE, True)
        if os.path.exists(mdir):
            dst = P2.new_dir(os.path.join(recdir, '_archive', 'mintpy'))
            os.replace(mdir, os.path.join(dst, 'mintpy'))
    elif not P5.way_gate(st, 'G5c.4', W, PHASE, False):
        return st.finish()
    os.makedirs(mdir)
    write_atomic(tfile, text)
    bad2, d, nkeys = check_template(open(tfile).read(), dtext, vals, extras, W, path, frame, npairs)
    bad += bad2
    st.gate('G5c.5', 'the template', 'FAIL' if bad else 'PASS', '%s: %d keys (the defaults file\'s %s and %s); %d values put in place; '
            'excludeDate %s, excludeDate12 %s, unwrapError %s; every path under the frame' % (
                tfile, nkeys, m['MINTPY_DEFAULT_KEYS'], ', '.join(k for k, _ in extras), len(vals), d.get('mintpy.network.excludeDate'),
                d.get('mintpy.network.excludeDate12'), d.get('mintpy.unwrapError.method')),
            'each key once; the values as written; paths there; no other frame', '\n'.join(bad[:10]))
    st.rec['outputs'] = dict(cfg=tfile, values=vals, extras=extras, files=[])
    if bad:
        return st.finish()
    if a.dryrun:
        st.rec['outputs'].update(planned=True, dryrun=True, cfg_digest=P5.cfg_digest(open(tfile).read()), cfg_md5=C.md5_file(tfile))
        print('   the template is in %s (SNWE auto: the dry run does not load)' % tfile)
        return st.finish('plan only (dry run): the template written and checked; no load_data')
    lg = P1.new_log(os.path.join(W, 'logs', 'p5', 'mcfg', 'load_bootstrap.log'))
    rc, out = P5.run_logged(['smallbaselineApp.py', 'smallbaselineApp.cfg', '--dostep', 'load_data'], mdir, lg, P5.mpl_env(W))
    steps, warn = P5.steps_run(out), P5.f40_lines(out)
    ih = os.path.join(mdir, 'inputs', 'ifgramStack.h5')
    gh = os.path.join(mdir, 'inputs', 'geometryRadar.h5')
    miss = [os.path.basename(x) for x in (ih, gh) if not os.path.isfile(x)]
    bad = rc != 0 or steps != ['load_data'] or warn or miss
    st.gate('G5c.6', 'the bootstrap load_data', 'FAIL' if bad else 'PASS', 'rc %d; steps %s; F40 warnings %d; %s' % (
        rc, ' '.join(steps) or 'none', len(warn), 'missing %s' % ', '.join(miss) if miss else 'ifgramStack.h5 and geometryRadar.h5 written'),
        'rc 0; load_data; no "No input metadata file found" or "prep_isce.py failed"', ('log %s\n' % lg) + '\n'.join(warn[:3]) +
        ('' if not rc else '\n' + P3.tail(lg, 8)))
    if bad:
        return st.finish()
    at = P5.h5_attrs(ih)
    hok, hwant, hd = P5.heading_ok(at.get('HEADING', 'nan'), cfg['direction'], float(m['HEADING_TOL_DEG']))
    od = str(at.get('ORBIT_DIRECTION'))
    want_od = dict(extras)['ORBIT_DIRECTION']
    bad = not hok or od != want_od
    st.gate('G24c', 'the stack\'s direction (bootstrap)', 'FAIL' if bad else 'PASS', 'HEADING %s (%+.1f deg from %s), ORBIT_DIRECTION %s' % (
        at.get('HEADING'), hd, hwant, od), 'HEADING within %s deg of %s; ORBIT_DIRECTION %s' % (m['HEADING_TOL_DEG'], hwant, want_od))
    if bad:
        return st.finish()
    import h5py
    with h5py.File(gh, 'r') as f:
        lat, lon = f['latitude'][:], f['longitude'][:]
    txt, v = P5.snwe(lat, lon, int(m['SNWE_LATTICE']), int(m['SNWE_MARGIN_PX']))
    import numpy as np
    la, lo = lat[np.isfinite(lat) & (lat != 0)], lon[np.isfinite(lon) & (lon != 0)]
    inside = la.min() >= v[0] and la.max() <= v[1] and lo.min() >= v[2] and lo.max() <= v[3]
    text2, bad = P5.set_values(open(tfile).read(), {'mintpy.geocode.SNWE': txt})
    if not bad:
        write_atomic(tfile, text2)
    got = P5.cfg_dict(open(tfile).read()).get('mintpy.geocode.SNWE')
    ok = not bad and inside and P5.on_lattice(v, int(m['SNWE_LATTICE'])) and got == txt
    st.gate('G5c.7', 'SNWE', 'PASS' if ok else 'FAIL', '%s (latitude %.5f to %.5f, longitude %.5f to %.5f; %d x %d cells of 1/%s deg)' % (
        txt, la.min(), la.max(), lo.min(), lo.max(), int(round((v[1] - v[0]) * int(m['SNWE_LATTICE']))),
        int(round((v[3] - v[2]) * int(m['SNWE_LATTICE']))), m['SNWE_LATTICE']),
        'on the 1/%s deg lattice, %s px outward; every valid pixel inside' % (m['SNWE_LATTICE'], m['SNWE_MARGIN_PX']),
        '' if ok else 'template %s; inside %s; lattice %s; on its line %s' % (bad, inside, P5.on_lattice(v, int(m['SNWE_LATTICE'])), got))
    if not ok:
        return st.finish()
    final = open(tfile).read()
    st.rec['outputs'].update(snwe=txt, cfg_md5=C.md5_file(tfile), cfg_digest=P5.cfg_digest(final), log=lg, heading=at.get('HEADING'),
                             orbit_direction=od)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_mcfg', main)
