#!/usr/bin/env python3
"""lp_selftest12.py -- the v0.12 cases of the linog_auto self-test (item 1: the phase drop1, record 124.7; Ariel's word on
its four choices, 125.0), called by lp_selftest.py after the v0.11 cases, on the Phase 5 cases' frame (root p3, frame 3320:
4 dates, 6 pairs, 658 lines x 83 columns), put back to its copy after bgrid (S4e: the cases plant a flagged pair at igram)
or after sbas (S5d).

The mock: LINOG_MOCK_BADPAIR gives a pair random phase (R1 flags it over land and over the grid); LINOG_MOCK_D1BAD
(linog_mock3.d1_plant) lowers the temporal coherence on a block of land cells while a pair is kept, in sbas's inversion and
in drop1's alike, so dropping it gains that block; the other drops gain nothing (the mock's temporal coherence is the kept
pairs' mean coherence + 0.2: 0.78 on land whichever pair is dropped). Pairs: A 20080830, B 20081130, C 20090302,
D 20090602; AB (coherence 0.55) and the five others (0.59; LINOG_MOCK_COHPAIR sets one). The frame's 6 pairs make one
cull 16.7 %: the cases read cfg/mintpy_cap20.cfg (ADMIT_CULL_MAX_FRAC 0.20) unless they test the cap.
v0.13 r2 (the ascending record 18.3, the split rule, balanced; lp_selftest13r2a.py lists these changes with their reasons):
v0.12 r2 tested AB against its 5 peers, all above it (0.59), which the split rule keeps untestable. So the plant P1 gives BC
coherence 0.50 and CD 0.53 (LINOG_MOCK_COHPAIR), and the cases' cfgs DROP1_PEERS_SIDE 2 (DROP1_PEERS 4; the pool of 5 holds no
5 a side): AB is tested against CD and BC below it and AC and AD above (ties to the earlier name; BD at 0.59 is not a peer),
their mean 0.5525, 0.0025 above its own, so 6 inversions where there were 7 (the zero test, AB and its 4 peers). The mock's
velocities move no cell by 1 mm/yr, so the guard (19.6) reads 0 at 0 and culls (at equality). T331, T331b, T332 and T338 read
the split rule's functions and settings in place of v0.12 r2's nearest peers and minimum; T339b keeps AB by
DROP1_PEERS_BALANCE 0 in place of DROP1_MIN_PEERS 6.

  T320  a flagged pair whose drop gains more than every peer's, --decide auto, a whole run: drop1 culls it, writes
        recon/drop1_decision.json, moves mintpy/ into _archive/mintpy_predrop1_<UTC>/ and asks a restart; the driver
        restarts from the top; admit takes the cull (D1d, D3 INFO), mcfg and sbas run again on 5 pairs, drop1 reads the
        cull as in place (no inversion), and the run goes on to rerun, rc 0; the tests' evidence (each inverted with
        avgSpatialCoh.h5 one folder above its stack copy and nothing else beside it, the frame having no waterMask.h5; each
        temporalCoherence.h5 kept, no copy or time series left); RUN_MANIFEST.json's decisions.d3.drop1 (the peers, the
        minimum); T320b a re-run skips all 30 phases.
  T333  on T320's frame, admit's D1d: an unreadable decision file FAIL; with the operator's file not applied (INFO); taken
        on another network or other interferograms not applied (WARN, 6 kept); as drop1 wrote it applied again (5 kept);
        drop1's threshold changed: admit reads the file again (its fingerprint), the basis differs (WARN, 6 kept), mcfg
        stops at G5c.4 (mintpy/ in the way); mintpy/ moved aside: sbas on 6 pairs, drop1 tests again in a new folder and
        takes the cull again (the earlier decision into _archive/), the restart, then deliver stops at G6a.5 (the first
        delivery in the way), rc 4.
  T321  a flagged pair inside its peers' range (a peer's drop gains more): kept, no restart, PASS; the zero test INFO; with
        a rate in sbas's series (LINOG_MOCK_TS) the |dv| figures are numbers.
  T322  two flagged pairs, each above its peers: the cull of 2 of 6 (33 %) over the 20 % cap: none culled, R2c WARN, PASS;
        T322b one, under the shipped 10 % cap (16.7 %): refused alike.
  T323  --decide ask: DECISION naming the pair, nothing moved, no restart asked; the operator's recon/admission.txt names it
        and mintpy/ is moved aside: admit takes the operator's (5 kept), and drop1 reads the cull as in place; T323b then
        DROP1_TCOH_MIN changed: the operator's cull rests on another basis, not read as in place (none flagged is left).
  T324  an operator's file whose exclusions keep every pair (excludeDate12 = auto: D3 the operator's): the test runs and its
        cull is recorded, not applied (Doc JD, 119.5): PASS, no decision file, no restart; T324b the file moved aside: drop1
        runs again (not skipped), takes the cull from the tests already made, the restart, the cull in place.
  T325  drop1's restart and then d9ab's (R5, LINOG_MOCK_B_GAIN) in one run: two RESTART lines, rc 0; the third pass reads
        both decisions.
  T326  dry runs of admit and drop1 into a folder: the tests under it, the cull it would take, the frame unchanged; T326b
        F3310's install path: the frame's stack keeps 5 pairs (an operator's cull, then moved aside), the dry run's admit 6:
        drop1 plans, tests nothing.
  T327  R1's land floor above the land: nothing flagged to drop1 (R2 PASS), drop1 PASS (D1f WARN), no inversion.
  T328  the clean frame (no pair flagged): drop1 PASS, nothing tested.
  T329  an inversion that fails (LINOG_MOCK_D1FAIL): drop1 FAIL at G5d1.7, nothing taken; T330 one stopped at the time limit
        (LINOG_MOCK_D1SLEEP, DROP1_TIMEOUT_S 3): FAIL, its copies removed, the mock process gone; T330b SIGKILL to drop1
        while an inversion runs: the test's job and the inversion end with it (SIGTERM on their parent's death), leaving
        exactly the stack copy, avgSpatialCoh.h5 and base.npz (r2); T329b the
        plants gone, --recover: the stopped run's scratch removed (G5d1.4c), the completed tests read again, the failed
        one run, DECISION under ask.
  T331  lp_drop1's functions alone: the peers' order by distance in mean land coherence (not by name, not signed), the
        rule's ties and a pair with no peer, the guards, testability, the zero test's check; T331b (r2) the minimum peer
        count in the rule (fewer peers kept, margin None; as many culled), the zero test with no margin left, the settings'
        checks (over DROP1_PEERS, 0, absent, not a whole number) and admit's basis (the minimum in it).
  T332  DROP1_PEERS 2, one pair's coherence 0.56 (LINOG_MOCK_COHPAIR): the flagged pair's peers are the 2 nearest it.
  T334  the cull taken, --decide auto, with <frame>/_archive a file: G5d1.10 FAIL, nothing moved or written.
  T335  the flagged pair not testable (the operator's file excludes another pair of its date): kept, nothing run.
  T336  --decide auto with --only drop1: the restart not allowed, so the cull is a DECISION.
  T337  admit changed after sbas and drop1 run alone: the stack keeps another network, G5d1.4 FAIL, nothing tested.
  T338  (r2) DROP1_MIN_PEERS 6 over the flagged pair's 5 peers: kept whatever its net, "no cull", PASS, no decision file;
        then 5: drop1 runs again (its settings changed), reads the 7 tests again (none run) and culls it (a DECISION under ask).
        v0.13 r2: DROP1_PEERS_SIDE 3 over the pair's 2 unflagged pairs below: kept, untestable, its 5 peers and itself
        inverted (7 tests); then 2: drop1 runs again, reads its 6 tests again (none run), names it (a DECISION under ask).
  T339  (r2) the frame with mintpy/waterMask.h5 (LINOG_MOCK_WATERMASK: the geometry's waterMask, written by modify_network):
        each test's inversion finds ../avgSpatialCoh.h5 and waterMask.h5 in its folder, neither left after; drop1.json holds
        both files' md5s; T339b the water mask then changed: drop1 STALE (the md5s in its fingerprint), all 7 tests (v0.13 r2:
        6) run again (the md5s in their keys).
"""
import glob
import json
import os
import re
import signal
import socket
import shutil
import subprocess
import time

ROOT, FRAME = 'p3', '3320'
A_, B_, C_, D_ = '20080830', '20081130', '20090302', '20090602'
AB, AC, AD, BC, BD, CD = (A_ + '_' + B_, A_ + '_' + C_, A_ + '_' + D_, B_ + '_' + C_, B_ + '_' + D_, C_ + '_' + D_)
SCRATCH = ('inputs/ifgramStack.h5', 'inputs/geometryRadar.h5', 'avgSpatialCoh.h5', 'maskConnComp.h5', 'waterMask.h5', 'timeseries.h5')
BES_NO_WATER = ('around the stack: ../avgSpatialCoh.h5 yes, waterMask.h5 (the working folder) no; not read by MintPy 1.6.2\'s inversion: '
                '../maskConnComp.h5 no, geometryRadar.h5 no')   # r2: the mock ifgram_inversion.py's line for drop1's placing
BES_WATER = BES_NO_WATER.replace('waterMask.h5 (the working folder) no', 'waterMask.h5 (the working folder) yes')


def proc_stat(pid):
    """(state, ppid) of a process from /proc, or None when it is gone."""
    try:
        txt = open('/proc/%d/stat' % int(pid)).read()
    except (OSError, ValueError, TypeError):
        return None
    f = txt.rsplit(')', 1)[1].split()
    return f[0], int(f[1])


def alive(pid):
    """A process that still runs (a zombie has ended)."""
    s = proc_stat(pid)
    return bool(s) and s[0] not in ('Z', 'X')


def cmdline(pid):
    try:
        return open('/proc/%d/cmdline' % int(pid), 'rb').read().replace(b'\0', b' ').decode('utf-8', 'replace')
    except (OSError, ValueError, TypeError):
        return ''


def phase12(T, case, S):
    import lp_drop1 as D1
    W = S.fdir(T, FRAME, ROOT)
    MC = os.path.join(T, 'cfg', 'mintpy_mock.cfg')

    def mcopy(name, **kv):
        """cfg/mintpy_mock.cfg with keys set (each present once)."""
        dst = os.path.join(T, 'cfg', name)
        n = dict((k, 0) for k in kv)
        with open(dst, 'w') as fh:
            for ln in open(MC):
                k = ln.split('=', 1)[0]
                if k in kv:
                    ln, n[k] = '%s=%s\n' % (k, kv[k]), n[k] + 1
                fh.write(ln)
        assert all(v == 1 for v in n.values()), n
        return dst
    SIDE2 = dict(DROP1_PEERS_SIDE='2', DROP1_PEERS='4')   # v0.13 r2: the split rule's 2 a side on the 6-pair frame
    CAP20 = mcopy('mintpy_cap20.cfg', ADMIT_CULL_MAX_FRAC='0.20', **SIDE2)

    def run(args, extra=None, decide='auto', mcfg=CAP20):
        e = {'LINOG_ROOT': os.path.join(T, ROOT), 'LINOG_MINTPY_CFG': mcfg}
        e.update(extra or {})
        return S.run(T, ['084', FRAME, '--decide', decide] + args, cfg='paths_p3.cfg', env_extra=e, keep_default=True)

    def killed(args, extra, mark, decide='ask', mcfg=CAP20):
        """A run started in a session of its own; once the planted mock inversion has written mark ('pid N'), SIGKILL to
        drop1's own process (the parent of the test's job, checked by its command line); wait for the run. Returns rc, the
        console, and dict(mock, job, phase pids; whether the job and the mock were still running 15 s after)."""
        env = {k: v for k, v in os.environ.items() if k not in ('LINOG_ROOT', 'LINOG_ARCHIVE', 'LINOG_DEM', 'LINOG_MINTPY_CFG')
               and not k.startswith('LINOG_MOCK_')}
        env.update(LINOG_AUTO_CFG=os.path.join(T, 'cfg', 'paths_p3.cfg'), LINOG_AUTO_HOST=socket.gethostname(),
                   LINOG_ENV_CFG=os.path.join(T, 'cfg', 'env_mock.cfg'), LINOG_STACK_CFG=os.path.join(T, 'cfg', 'stack_mock.cfg'),
                   LINOG_RUN_CFG=os.path.join(T, 'cfg', 'run_mock.cfg'), LINOG_FFTW_CFG=os.path.join(T, 'cfg', 'fftw_mock.cfg'),
                   LINOG_ROOT=os.path.join(T, ROOT), LINOG_MINTPY_CFG=mcfg, LINOG_MOCK_MARK=mark, **extra)
        if os.path.exists(mark):   # r2: a mark left by an earlier run of the same tree would name a process long gone
            os.remove(mark)
        p = subprocess.Popen(['bash', S.ENTRY, '084', FRAME, '--decide', decide] + args, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.time()
        while not os.path.exists(mark) and p.poll() is None and time.time() - t0 < 120:
            time.sleep(0.2)
        time.sleep(1.0)
        info = {}
        if os.path.exists(mark) and p.poll() is None:
            m = re.search(r'pid (\d+)', open(mark).read())
            mpid = int(m.group(1)) if m else 0
            jpid = (proc_stat(mpid) or (None, 0))[1]
            fpid = (proc_stat(jpid) or (None, 0))[1]
            info = dict(mock=mpid, job=jpid, phase=fpid, job_cmd=cmdline(jpid)[-60:], phase_cmd=cmdline(fpid)[-60:])
            if fpid and 'lp_drop1.py' in cmdline(fpid) and '--job' not in cmdline(fpid) and '--job' in cmdline(jpid):
                os.kill(fpid, signal.SIGKILL)
                t1 = time.time()
                while (alive(mpid) or alive(jpid)) and time.time() - t1 < 15:
                    time.sleep(0.2)
                info.update(killed=True, mock_alive=alive(mpid), job_alive=alive(jpid), seconds=round(time.time() - t1, 1))
        out = p.communicate(timeout=300)[0].decode('utf-8', 'replace')
        with open(os.path.join(T, 'selftest_console.txt'), 'a') as fh:
            fh.write('\n\n######## linog_auto.sh 084 %s --decide %s %s  (%s; SIGKILL to drop1: %s)  rc %d\n%s' % (
                FRAME, decide, ' '.join(args), ' '.join('%s=%s' % kv for kv in sorted(extra.items())), info, p.returncode, out))
        return p.returncode, out, info

    def rec(idx, ph):
        return S.rec(T, FRAME, idx, ph, ROOT)

    def gates(r):
        return dict((x['id'], x['verdict']) for x in r.get('gates', []))

    def gl(r, gid):
        return [x for x in r.get('gates', []) if x['id'] == gid]

    def val(r, gid):
        return dict((x['id'], x.get('value', '')) for x in r.get('gates', [])).get(gid, '')

    def out(r):
        return r.get('outputs') or {}

    def jload(p):
        try:
            return json.load(open(p))
        except (OSError, ValueError):
            return {}

    def restore(snap, tag):
        S.aside(T, W, 'p12_%s' % tag)
        shutil.copytree(os.path.join(T, 'snap_p3', snap), W, symlinks=True, copy_function=copy_fn)

    def copy_fn(src, dst):   # as lp_selftest6: mintpy/'s files always copied (the mock and the kit write some in place)
        if os.path.getsize(src) > (1 << 20) and '%smintpy%s' % (os.sep, os.sep) not in src:
            os.link(src, dst)
        else:
            shutil.copy2(src, dst)

    def ledger():
        p = os.path.join(W, 'logs', 'STATUS.txt')
        return open(p).read() if os.path.isfile(p) else ''

    def last_run(led):
        ids = [x.split('id=')[1].split()[0] for x in led.splitlines() if 'auto_run START id=' in x]
        return ids[-1] if ids else '-'

    def listing(d, skip=()):
        res = []
        for dp, dn, fn in os.walk(d):
            dn[:] = sorted(x for x in dn if os.path.relpath(os.path.join(dp, x), d) not in skip)
            for n in sorted(fn):
                q = os.path.join(dp, n)
                st = os.lstat(q)
                res.append((os.path.relpath(q, d), st.st_size, st.st_mtime_ns))
        return res

    def tests_of(folder):
        """{test: (result.json, names in its folder)} under a drop1 evidence folder."""
        res = {}
        for t in sorted(glob.glob(os.path.join(folder, 'tests', '*'))):
            names = sorted(os.listdir(t)) + sorted('inputs/' + x for x in (os.listdir(os.path.join(t, 'inputs')) if os.path.isdir(
                os.path.join(t, 'inputs')) else []))
            res[os.path.basename(t)] = (jload(os.path.join(t, 'result.json')), names)
        return res

    def no_scratch(names):
        return not any(x in names for x in SCRATCH)

    def scratch_under(d):
        """This phase's scratch anywhere under d's drop1/ (lp_drop1.leftovers)."""
        return D1.leftovers(d)

    def put_archive(src, tag):
        os.makedirs(os.path.join(W, '_archive'), exist_ok=True)
        dst = os.path.join(W, '_archive', '%s_%s' % (tag, os.path.basename(src)))
        os.rename(src, dst)
        return dst

    print('-- v0.12 (item 1): the phase drop1 (the drop-one peer test, record 124.7), admit\'s handoff, the driver\'s restarts')
    if not os.path.isdir(os.path.join(T, 'snap_p3', 'S4e')) or not os.path.isdir(os.path.join(T, 'snap_p3', 'S5d')):
        case('T320-T339 not run: no copy of the frame after bgrid or sbas (the Phase 3 to 5 cases stopped early)', False)
        return
    COH2 = '%s:0.50,%s:0.53' % (BC, CD)   # v0.13 r2: AB's 2 peers below it (18.3's split rule)
    P1 = {'LINOG_MOCK_BADPAIR': AB, 'LINOG_MOCK_D1BAD': '%s:300' % AB, 'LINOG_MOCK_COHPAIR': COH2}
    TESTED = sorted(['zero', AB, AC, AD, BC, CD])   # v0.13 r2: the zero test, AB and its 4 peers (CD, BC below; AC, AD above)

    # ------------------------------------------------------------------ T320: the cull taken, the restart, a whole run
    restore('S4e', 'T320')
    rc, txt = run([], P1)
    led = ledger()
    rid = last_run(led)
    rd, ra, rs, r9 = rec('5d1', 'drop1'), rec('5a', 'admit'), rec('5d', 'sbas'), rec('5dab', 'd9ab')
    dec = jload(os.path.join(W, 'recon', 'drop1_decision.json'))
    rk = jload(os.path.join(W, 'status', 'restart_%s_1.json' % rid))
    adm = jload(os.path.join(W, 'recon', 'admission.json'))
    hist = sorted(glob.glob(os.path.join(W, 'status', 'history', 'P5d1_drop1.*.json')))
    h1 = jload(hist[-1]) if hist else {}
    ev = os.path.join(W, dec.get('folder') or '-')
    tt = tests_of(ev)
    j1 = jload(os.path.join(ev, 'drop1.json'))
    moved = os.path.join(W, dec.get('moved_to') or '-', 'mintpy')
    man = jload(os.path.join(W, 'RUN_MANIFEST.json'))
    md1 = ((man.get('decisions') or {}).get('d3') or {}).get('drop1') or {}
    ok_ev = sorted(tt) == TESTED and all(
        r.get('complete') is True and 'temporalCoherence.h5' in nm and 'numInvIfgram.h5' in nm and no_scratch(nm) for r, nm in tt.values())
    mt = md1.get('tested') or [{}]
    logs = [os.path.join(ev, 'tests', t, 'inv.log') for t in tt]
    ok_bes = len(logs) == 6 and all(os.path.isfile(x) and BES_NO_WATER in open(x).read() for x in logs)
    case('T320 a flagged pair whose drop gains 300 land cells, its 4 peers\' 0 (v0.13 r2: 2 below its coherence, 2 above; the cap at '
         '20 %), --decide auto, a whole run: drop1 culls it (D1r named, the guard and R2c INFO, G5d1.10 PASS): recon/drop1_decision.json '
         '(the basis, the table, the zero test), mintpy/ moved into '
         '_archive/mintpy_predrop1_<UTC>/, a restart asked by drop1; the ledger "auto_run RESTART ... after=drop1"; admit takes the cull '
         '(D1d INFO, D3 INFO naming drop1, 5 kept); sbas on 5 pairs; drop1 reads the cull as in place (D1c, no inversion); rerun PASS, '
         'rc 0; 6 tests, each inverted with ../avgSpatialCoh.h5 placed above its stack copy and no other file beside it (r2: the frame has no '
         'waterMask.h5; the mock\'s log), each with its temporalCoherence.h5 and numInvIfgram.h5 kept, no copy or time series left; '
         'RUN_MANIFEST.json\'s decisions.d3.drop1 with the pair tested against its 4 peers (DROP1_PEERS 4, 1 at least in the mock\'s cfg) '
         'and the zero test',
         rc == 0 and dec.get('cull') == [AB] and dec.get('igram') and dec.get('network') and dec.get('after') and dec.get('basis')
         and len(dec.get('table') or []) == 1 and (dec.get('zero') or {}).get('churn') == 0 and (dec.get('guards') or {}).get('taken') is True
         and os.path.isdir(moved) and rk.get('by') == 'drop1' and led.count('auto_run RESTART id=%s after=drop1' % rid) == 1
         and led.count('auto_run RESTART') == 1 and led.count('auto_run END id=%s rc=0' % rid) == 1
         and out(h1).get('state') == 'cull taken' and gates(h1).get('G5d1.10') == 'PASS' and gates(h1).get('R2c') == 'INFO'
         and gates(h1).get('D1z') == 'INFO' and any(x['verdict'] == 'INFO' and x['value'].startswith('named') for x in gl(h1, 'D1r'))
         and gates(h1).get('D1g') == 'PASS'
         and gates(ra).get('D1d') == 'INFO' and gates(ra).get('D3') == 'INFO' and 'drop1' in val(ra, 'D3') and adm.get('kept') == 5
         and AB not in (adm.get('kept_pairs') or []) and out(rs).get('kept') == 5
         and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'cull in place' and gates(rd).get('D1c') == 'INFO' and 'G5d1.7' not in gates(rd)
         and rec('6d', 'rerun').get('verdict') == 'PASS' and gates(rec('6a', 'deliver')).get('G6a.1d') == 'PASS'
         and ok_ev and ok_bes and j1.get('complete') is True and j1.get('cull') == [AB] and j1.get('basis') == dec.get('basis')
         and md1.get('state') == 'cull in place' and md1.get('cull') == [AB] and md1.get('taken') is True
         and len(md1.get('tested') or []) == 1 and mt[0].get('pair') == AB and mt[0].get('peers') == 4 and mt[0].get('culled') is True
         and md1.get('peers_n') == 4 and md1.get('min_peers') == 1 and (j1.get('beside') or {}).keys() == {'avgSpatialCoh.h5'}
         and isinstance(md1.get('zero'), dict) and not os.path.exists(os.path.join(ev, 'base.npz')),
         'rc %d; decision %s; restart %s; ledger restarts %d; pass 1 %s (G5d1.10 %s); admit D1d %s D3 %s, kept %s; drop1 %s; tests %s; '
         'evidence %s, beside %s; manifest drop1 %s %s' % (rc, dec.get('cull'), rk.get('by'), led.count('auto_run RESTART'), out(h1).get('state'),
                                                            gates(h1).get('G5d1.10'), gates(ra).get('D1d'), gates(ra).get('D3'), adm.get('kept'),
                                                            out(rd).get('state'), sorted(tt), ok_ev, ok_bes, md1.get('state'), mt))
    rc2, txt2 = run([], P1)
    case('T320b a re-run with no --to: all 31 phases skipped (v0.13: bandlimit among them), rc 0',
         rc2 == 0 and txt2.count('skip: PASS on record, inputs unchanged') == 31, 'rc %d; %d skipped' % (
             rc2, txt2.count('skip: PASS on record, inputs unchanged')))

    # ------------------------------------------------------------------ T333: admit's D1d paths, then the cull re-tested
    df = os.path.join(W, 'recon', 'drop1_decision.json')
    D0 = open(df).read() if os.path.isfile(df) else '{}'
    d0 = json.loads(D0)

    def put(x):
        with open(df, 'w') as fh:
            fh.write(x if isinstance(x, str) else json.dumps(x))

    def admit_only(mcfg=CAP20):
        rc_, _ = run(['--only', 'admit'], P1, mcfg=mcfg)
        return rc_, rec('5a', 'admit'), jload(os.path.join(W, 'recon', 'admission.json'))
    got = []
    put('{')
    rc, ra, adm = admit_only()
    got.append(('unreadable', rc == 2 and gates(ra).get('D1d') == 'FAIL', 'rc %d D1d %s' % (rc, gates(ra).get('D1d'))))
    put(D0)
    opf = os.path.join(W, 'recon', 'admission.txt')
    with open(opf, 'w') as fh:
        fh.write('# the operator decides D3 (self-test T333)\nmintpy.network.excludeDate12 = auto\n')
    rc, ra, adm = admit_only()
    got.append(('operator', rc == 0 and gates(ra).get('D1d') == 'INFO' and 'the operator' in val(ra, 'D1d') and adm.get('kept') == 6,
                'rc %d D1d %s kept %s' % (rc, gates(ra).get('D1d'), adm.get('kept'))))
    put_archive(opf, 'T333')
    for tag, key in (('network', 'network'), ('igram', 'igram')):
        put(dict(d0, **{key: '0' * 32}))
        rc, ra, adm = admit_only()
        got.append((tag, rc == 0 and gates(ra).get('D1d') == 'WARN' and adm.get('kept') == 6 and gates(ra).get('D3') == 'PASS',
                    'rc %d D1d %s %s kept %s D3 %s' % (rc, gates(ra).get('D1d'), val(ra, 'D1d')[:60], adm.get('kept'), gates(ra).get('D3'))))
    put(D0)
    rc, ra, adm = admit_only()
    got.append(('applied', rc == 0 and gates(ra).get('D1d') == 'INFO' and adm.get('kept') == 5,
                'rc %d D1d %s kept %s' % (rc, gates(ra).get('D1d'), adm.get('kept'))))
    TH69 = mcopy('mintpy_thr69.cfg', ADMIT_CULL_MAX_FRAC='0.20', DROP1_TCOH_MIN='0.69', **SIDE2)
    rc, txt = run([], P1, mcfg=TH69)
    ra, rm, adm = rec('5a', 'admit'), rec('5c', 'mcfg'), jload(os.path.join(W, 'recon', 'admission.json'))
    got.append(('basis', rc == 4 and gates(ra).get('D1d') == 'WARN' and 'basis' in val(ra, 'D1d') and adm.get('kept') == 6
                and rm.get('verdict') == 'DECISION' and gates(rm).get('G5c.4') == 'DECISION',
                'rc %d D1d %s kept %s mcfg %s G5c.4 %s' % (rc, gates(ra).get('D1d'), adm.get('kept'), rm.get('verdict'), gates(rm).get('G5c.4'))))
    put_archive(os.path.join(W, 'mintpy'), 'T333')
    rc, txt = run([], P1, mcfg=TH69)
    led = ledger()
    rid = last_run(led)
    dec = jload(df)
    rd, adm = rec('5d1', 'drop1'), jload(os.path.join(W, 'recon', 'admission.json'))
    runs = sorted(glob.glob(os.path.join(W, 'drop1', '*', 'drop1.json')))
    ear = os.path.join(W, dec.get('earlier') or '-')
    rv = rec('6a', 'deliver')
    got.append(('again', rc == 4 and dec.get('cull') == [AB] and dec.get('basis') and dec.get('basis') != d0.get('basis')
                and dec.get('folder') != d0.get('folder') and os.path.isfile(ear) and jload(ear).get('basis') == d0.get('basis')
                and led.count('auto_run RESTART id=%s after=drop1' % rid) == 1 and adm.get('kept') == 5 and len(runs) == 2
                and out(rd).get('state') == 'cull in place' and gates(rec('5a', 'admit')).get('D1d') == 'INFO'
                and all(rec(i, n).get('verdict') == 'PASS' for i, n in (('5dab', 'd9ab'), ('5e', 'wmask'), ('5f', 'dfit')))
                and rv.get('verdict') == 'DECISION' and gates(rv).get('G6a.5') == 'DECISION',
                'rc %d cull %s basis %s/%s earlier %s restarts %d kept %s runs %d drop1 %s deliver %s G6a.5 %s' % (
                    rc, dec.get('cull'), str(dec.get('basis'))[:8], str(d0.get('basis'))[:8], dec.get('earlier'),
                    led.count('auto_run RESTART id=%s' % rid), adm.get('kept'), len(runs), out(rd).get('state'), rv.get('verdict'),
                    gates(rv).get('G6a.5'))))
    case('T333 admit\'s D1d on T320\'s frame: an unreadable recon/drop1_decision.json FAIL (rc 2); with the operator\'s file not applied '
         '(INFO, 6 kept); taken on another network, or on other interferograms: not applied (WARN, 6 kept, D3 PASS); as drop1 wrote it: '
         'applied (5 kept); DROP1_TCOH_MIN 0.69: admit reads it again, another basis (WARN, 6 kept), mcfg G5c.4 DECISION (rc 4); mintpy/ '
         'moved aside: sbas on 6, drop1 tests again in a new folder, takes the cull (the earlier decision in _archive/), one restart, '
         'admit applies it, drop1 in place, d9ab, wmask and dfit PASS, deliver stops at G6a.5 (T320\'s delivery in the way: rc 4, as '
         'on F3310 under v0.12)', all(ok for _, ok, _ in got),
         '; '.join('%s %s (%s)' % (t, 'ok' if ok else 'NO', d) for t, ok, d in got))

    # ------------------------------------------------------------------ T321: inside its peers' range
    restore('S4e', 'T321')
    rc, txt = run(['--to', 'drop1'], {'LINOG_MOCK_BADPAIR': AB, 'LINOG_MOCK_D1BAD': '%s:100,%s:300' % (AB, CD), 'LINOG_MOCK_TS': '2',
                                      'LINOG_MOCK_COHPAIR': COH2})
    rd = rec('5d1', 'drop1')
    tb = dict((x['pair'], x) for x in out(rd).get('table') or [])
    jt = (jload(os.path.join(W, out(rd).get('folder') or '-', 'drop1.json')).get('tests') or {})
    p99 = [(jt.get(k) or {}).get('p99_dv') for k in ('zero', AB, CD)]
    case('T321 the flagged pair\'s drop gains 100 cells, a peer\'s (%s) 300: kept (D1r "kept", +100 against +300), no cull, no restart, '
         'drop1 PASS, rc 0; the zero test INFO (0 changed); with a 2 mm/yr rate in sbas\'s series, p99 |dv| a number in each test' % CD,
         rc == 0 and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'no cull' and (tb.get(AB) or {}).get('net') == 100
         and (tb.get(AB) or {}).get('peers_max') == 300 and (tb.get(AB) or {}).get('culled') is False and 'RESTART' not in ledger()
         and gates(rd).get('D1z') == 'INFO' and (out(rd).get('zero') or {}).get('churn') == 0
         and all(isinstance(x, float) and x == x for x in p99)
         and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')) and os.path.isdir(os.path.join(W, 'mintpy')),
         'rc %d; drop1 %s %s; %s; D1z %s; p99 %s' % (rc, rd.get('verdict'), out(rd).get('state'), tb.get(AB), gates(rd).get('D1z'), p99))

    # ------------------------------------------------------------------ T322, T322b: the cap
    restore('S4e', 'T322')
    rc, txt = run(['--to', 'drop1'], {'LINOG_MOCK_BADPAIR': '%s,%s' % (AB, CD), 'LINOG_MOCK_D1BAD': '%s:300,%s:300' % (AB, CD),
                                      'LINOG_MOCK_COHPAIR': '%s:0.50,%s:0.52,%s:0.55' % (BC, BD, CD)})
    rd, ra = rec('5d1', 'drop1'), rec('5a', 'admit')
    case('T322 two flagged pairs (%s, %s), each above its 4 peers (v0.13 r2: both at 0.55, BC 0.50 and BD 0.52 below, AC and AD 0.59 '
         'above): the cull of 2 of 6 (33.3 %%) over the 20 %% cap: R2c WARN, none culled '
         '(state "cull refused"), no restart, drop1 PASS, rc 0; admit handed both (R2 INFO)' % (AB, CD),
         rc == 0 and rd.get('verdict') == 'PASS' and gates(rd).get('R2c') == 'WARN' and out(rd).get('state') == 'cull refused'
         and out(rd).get('cull') == [AB, CD] and out(rd).get('taken') is False and 'RESTART' not in ledger()
         and gates(ra).get('R2') == 'INFO' and sorted(((out(ra).get('decisions') or {}).get('drop1') or {}).get('in_network') or []) == [AB, CD]
         and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')),
         'rc %d; R2c %s: %s; state %s' % (rc, gates(rd).get('R2c'), val(rd, 'R2c')[:100], out(rd).get('state')))
    restore('S4e', 'T322b')
    rc, txt = run(['--to', 'drop1'], P1, mcfg=mcopy('mintpy_side2.cfg', **SIDE2))
    rd = rec('5d1', 'drop1')
    case('T322b one flagged pair above its 4 peers under the shipped cap (ADMIT_CULL_MAX_FRAC 0.10): 1 of 6 (16.7 %) over it: R2c WARN, '
         'state "cull refused", no decision file, no restart, drop1 PASS, rc 0',
         rc == 0 and rd.get('verdict') == 'PASS' and gates(rd).get('R2c') == 'WARN' and 'over 10 %' in val(rd, 'R2c')
         and out(rd).get('state') == 'cull refused' and out(rd).get('cull') == [AB] and 'RESTART' not in ledger()
         and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')),
         'rc %d; R2c %s: %s; state %s' % (rc, gates(rd).get('R2c'), val(rd, 'R2c')[:100], out(rd).get('state')))

    # ------------------------------------------------------------------ T323: ask, then the operator's file
    restore('S4e', 'T323')
    rc, txt = run(['--to', 'drop1'], P1, decide='ask')
    rd = rec('5d1', 'drop1')
    noa = (not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')) and os.path.isdir(os.path.join(W, 'mintpy'))
           and not os.path.exists(os.path.join(W, 'status', 'restart.json')) and not glob.glob(os.path.join(W, 'status', 'restart_*.json')))
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# the operator takes drop1\'s cull (self-test T323)\nmintpy.network.excludeDate12 = %s\n' % AB)
    os.makedirs(os.path.join(W, '_archive'), exist_ok=True)
    os.rename(os.path.join(W, 'mintpy'), os.path.join(W, '_archive', 'T323_mintpy'))
    nt0 = len(glob.glob(os.path.join(W, 'drop1', '*', 'tests', '*', 'result.json')))
    rc2, txt2 = run(['--to', 'drop1'], P1, decide='ask')
    rd2, ra2 = rec('5d1', 'drop1'), rec('5a', 'admit')
    adm = jload(os.path.join(W, 'recon', 'admission.json'))
    nt1 = len(glob.glob(os.path.join(W, 'drop1', '*', 'tests', '*', 'result.json')))
    case('T323 --decide ask: drop1 DECISION naming %s, rc 4, nothing moved, no decision file, no restart asked; then recon/admission.txt '
         'names it and mintpy/ is moved aside (the DECISION\'s instruction): admit D3 INFO (the operator\'s), 5 kept; drop1 PASS, the cull '
         'in place (D1c, no inversion), rc 0' % AB,
         rc == 4 and rd.get('verdict') == 'DECISION' and AB in val(rd, 'D1') and 'admission.txt' in val(rd, 'D1') and noa
         and rc2 == 0 and gates(ra2).get('D3') == 'INFO' and val(ra2, 'D3').find('the operator') >= 0 and adm.get('kept') == 5
         and rd2.get('verdict') == 'PASS' and out(rd2).get('state') == 'cull in place' and gates(rd2).get('D1c') == 'INFO' and nt1 == nt0,
         'rc %d %s; nothing moved %s; rc %d; D3 %s; kept %s; drop1 %s; tests %d -> %d' % (
             rc, rd.get('verdict'), noa, rc2, gates(ra2).get('D3'), adm.get('kept'), out(rd2).get('state'), nt0, nt1))
    rc3, txt3 = run(['--to', 'drop1'], P1, decide='ask', mcfg=TH69)
    rd3 = rec('5d1', 'drop1')
    case('T323b then DROP1_TCOH_MIN 0.69: the operator\'s cull rests on a test taken at 0.70 (another basis), so drop1 does not read it as '
         'in place; with %s excluded no flagged pair is left in the network: drop1 PASS (state "none flagged", no D1c), rc 0' % AB,
         rc3 == 0 and rd3.get('verdict') == 'PASS' and out(rd3).get('state') == 'none flagged' and 'D1c' not in gates(rd3),
         'rc %d; drop1 %s %s' % (rc3, rd3.get('verdict'), out(rd3).get('state')))

    # ------------------------------------------------------------------ T324: an operator's file (D3 the operator's)
    restore('S4e', 'T324')
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# the operator excludes no pair (self-test T324)\nmintpy.network.excludeDate12 = auto\n')
    rc, txt = run(['--to', 'drop1'], P1)
    rd, ra = rec('5d1', 'drop1'), rec('5a', 'admit')
    case('T324 recon/admission.txt says excludeDate12 = auto (D3 the operator\'s, 6 kept): drop1 tests %s against its 4 peers and its cull '
         'is recorded, not applied (state "recorded, not applied"): PASS, rc 0, no decision file, no restart, mintpy/ in place' % AB,
         rc == 0 and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'recorded, not applied' and out(rd).get('cull') == [AB]
         and out(rd).get('taken') is False and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json'))
         and 'RESTART' not in ledger() and os.path.isdir(os.path.join(W, 'mintpy')) and len(out(rd).get('table') or []) == 1
         and len(((out(rd).get('table') or [{}])[0]).get('peers') or []) == 4 and 'the operator' in val(ra, 'D3'),
         'rc %d; drop1 %s %s; cull %s' % (rc, rd.get('verdict'), out(rd).get('state'), out(rd).get('cull')))
    put_archive(os.path.join(W, 'recon', 'admission.txt'), 'T324b')
    rc2, txt2 = run(['--to', 'drop1'], P1)
    led = ledger()
    rid = last_run(led)
    hist = sorted(glob.glob(os.path.join(W, 'status', 'history', 'P5d1_drop1.*.json')))
    h1 = jload(hist[-1]) if hist else {}
    rd2 = rec('5d1', 'drop1')
    dec = jload(os.path.join(W, 'recon', 'drop1_decision.json'))
    case('T324b the operator\'s file then moved aside (D3 back to the rules, the same 6 pairs): drop1 runs again (its fingerprint holds '
         'whether the operator decides D3), takes the cull under auto from the tests already made (6 read again, none run), one restart, '
         'then the cull in place, rc 0',
         rc2 == 0 and out(h1).get('state') == 'cull taken' and out(h1).get('reused') == 6 and out(h1).get('ran') == 0
         and led.count('auto_run RESTART id=%s after=drop1' % rid) == 1 and out(rd2).get('state') == 'cull in place' and dec.get('cull') == [AB],
         'rc %d; pass 1 %s (read again %s, ran %s); restarts %d; drop1 %s; decision %s' % (
             rc2, out(h1).get('state'), out(h1).get('reused'), out(h1).get('ran'), led.count('auto_run RESTART id=%s' % rid),
             out(rd2).get('state'), dec.get('cull')))

    # ------------------------------------------------------------------ T325: drop1's restart, then d9ab's
    restore('S4e', 'T325')
    rc, txt = run(['--to', 'd9ab'], dict(P1, LINOG_MOCK_B_GAIN='1'))
    led = ledger()
    rid = last_run(led)
    rd, r9, ra = rec('5d1', 'drop1'), rec('5dab', 'd9ab'), rec('5a', 'admit')
    adm = jload(os.path.join(W, 'recon', 'admission.json'))
    case('T325 drop1 culls %s and asks a restart, then d9ab\'s A/B reads bridging and asks one (R5): two RESTART lines (after=drop1, '
         'after=d9ab), rc 0; the third pass: admit takes both (5 kept, unwrapError bridging), drop1 the cull in place, d9ab D9m (not '
         'run: bridging)' % AB,
         rc == 0 and led.count('auto_run RESTART id=%s after=drop1' % rid) == 1 and led.count('auto_run RESTART id=%s after=d9ab' % rid) == 1
         and led.count('auto_run RESTART') == 2 and 'REFUSED' not in led and adm.get('kept') == 5
         and (adm.get('cfg') or {}).get('mintpy.unwrapError.method') == 'bridging' and out(rd).get('state') == 'cull in place'
         and gates(r9).get('D9m') == 'INFO' and os.path.isfile(os.path.join(W, 'recon', 'd9ab_decision.json')),
         'rc %d; restarts %s; kept %s; method %s; drop1 %s; d9ab %s' % (
             rc, [x.split('after=')[1].split()[0] for x in led.splitlines() if 'auto_run RESTART' in x], adm.get('kept'),
             (adm.get('cfg') or {}).get('mintpy.unwrapError.method'), out(rd).get('state'), sorted(gates(r9))[-3:]))

    # ------------------------------------------------------------------ T326, T326b: dry runs of admit and drop1
    restore('S4e', 'T326')
    rc0, _ = run(['--to', 'sbas'], P1)
    DRY = os.path.join(T, 'dry_p12')
    before = listing(W, skip=('logs',))
    rc1, t1 = run(['--only', 'admit', '--dry-run', DRY], P1)
    rc2, t2 = run(['--only', 'drop1', '--dry-run', DRY], P1)
    after = listing(W, skip=('logs',))
    dd = jload(os.path.join(DRY, 'status', 'P5d1_drop1.json'))
    case('T326 dry runs of admit and then drop1 into one folder, the frame after sbas: drop1 INFO "dry run", the cull it would take '
         '(%s), its tests under the folder\'s drop1/ (no scratch left); the frame unchanged (no decision file, no restart, mintpy/ in '
         'place), rc 0 each' % AB,
         rc0 == 0 and rc1 == 0 and rc2 == 0 and dd.get('verdict') == 'PASS' and out(dd).get('state') == 'dry run' and out(dd).get('cull') == [AB]
         and 'without --only' in val(dd, 'D1') and len(glob.glob(os.path.join(DRY, 'drop1', '*', 'tests', '*', 'temporalCoherence.h5'))) == 6
         and not scratch_under(DRY) and before == after
         and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')) and not os.path.exists(os.path.join(W, 'drop1')),
         'rc %d %d %d; drop1 %s %s %s; frame unchanged %s; scratch %s' % (rc0, rc1, rc2, dd.get('verdict'), out(dd).get('state'),
                                                                        out(dd).get('cull'), before == after, scratch_under(DRY)[:2]))
    restore('S4e', 'T326b')
    opf = os.path.join(W, 'recon', 'admission.txt')
    with open(opf, 'w') as fh:
        fh.write('# R2\'s cull as v0.11 took it on F3310 (self-test T326b)\nmintpy.network.excludeDate12 = %s\n' % AB)
    rc0, _ = run(['--to', 'sbas'], P1)
    put_archive(opf, 'T326b')
    DRY2 = os.path.join(T, 'dry_p12b')
    rc1, _ = run(['--only', 'admit', '--dry-run', DRY2], P1)
    rc2, _ = run(['--only', 'drop1', '--dry-run', DRY2], P1)
    dd, da = jload(os.path.join(DRY2, 'status', 'P5d1_drop1.json')), jload(os.path.join(DRY2, 'recon', 'admission.json'))
    case('T326b F3310\'s install path: the frame\'s stack keeps 5 pairs (an operator\'s cull of %s, then the file moved aside), the dry run\'s '
         'admit 6 (D3 PASS, %s handed to drop1): drop1\'s dry run plans ("keeps 6 pairs, the frame\'s stack 5"), PASS, nothing tested, '
         'rc 0 each' % (AB, AB),
         rc0 == 0 and rc1 == 0 and rc2 == 0 and da.get('kept') == 6 and dd.get('verdict') == 'PASS' and out(dd).get('planned') is True
         and 'keeps 6 pairs, the frame\'s stack 5' in (out(dd).get('note') or '') and not os.path.exists(os.path.join(DRY2, 'drop1')),
         'rc %d %d %d; dry admit kept %s; drop1 %s planned %s: %s' % (rc0, rc1, rc2, da.get('kept'), dd.get('verdict'), out(dd).get('planned'),
                                                                     (out(dd).get('note') or '')[:90]))

    # ------------------------------------------------------------------ T327, T328: the land floor; no pair flagged
    restore('S4e', 'T327')
    floor = mcopy('mintpy_floor_d1.cfg', ADMIT_CULL_MAX_FRAC='0.20', ADMIT_LAND_MIN_PX='60000')
    rc, txt = run(['--to', 'drop1'], P1, mcfg=floor)
    rd, ra = rec('5d1', 'drop1'), rec('5a', 'admit')
    case('T327 R1\'s land floor (60,000 px) above the mock\'s land: admit hands nothing to drop1 (R2 PASS, under_floor), drop1 PASS with '
         'D1f WARN and no test (no drop1/ folder), rc 0',
         rc == 0 and gates(ra).get('R2') == 'PASS' and ((out(ra).get('decisions') or {}).get('drop1') or {}).get('under_floor') is True
         and rd.get('verdict') == 'PASS' and gates(rd).get('D1f') == 'WARN' and out(rd).get('state') == 'under the land floor'
         and not os.path.exists(os.path.join(W, 'drop1')), 'rc %d; R2 %s; drop1 %s %s' % (rc, gates(ra).get('R2'), rd.get('verdict'), gates(rd).get('D1f')))
    restore('S5d', 'T328')
    rc, txt = run(['--to', 'drop1'])
    rd = rec('5d1', 'drop1')
    case('T328 the clean frame after sbas: no pair flagged, drop1 PASS (state "none flagged"), nothing tested, rc 0',
         rc == 0 and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'none flagged' and not os.path.exists(os.path.join(W, 'drop1')),
         'rc %d; drop1 %s %s' % (rc, rd.get('verdict'), out(rd).get('state')))

    # ------------------------------------------------------------------ T329, T330, T330b, T329b: failed, stopped and killed inversions
    restore('S4e', 'T329')
    rc, txt = run(['--to', 'drop1'], dict(P1, LINOG_MOCK_D1FAIL=AC), decide='ask')
    rd = rec('5d1', 'drop1')
    fold = os.path.join(W, out(rd).get('folder') or '-')
    tt = tests_of(fold)
    case('T329 the inversion without %s fails (LINOG_MOCK_D1FAIL): drop1 FAIL at G5d1.7 naming it, rc 2; nothing taken; its copies '
         'removed; the 5 others complete' % AC,
         rc == 2 and rd.get('verdict') == 'FAIL' and gates(rd).get('G5d1.7') == 'FAIL' and AC in val(rd, 'G5d1.7') + json.dumps(gl(rd, 'G5d1.7'))
         and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')) and (tt.get(AC) or ({}, []))[0].get('complete') is False
         and no_scratch((tt.get(AC) or ({}, ['-']))[1]) and sum(1 for r, _ in tt.values() if r.get('complete')) == 5,
         'rc %d; drop1 %s; G5d1.7 %s' % (rc, rd.get('verdict'), val(rd, 'G5d1.7')[:100]))
    slow = mcopy('mintpy_d1slow.cfg', ADMIT_CULL_MAX_FRAC='0.20', DROP1_TIMEOUT_S='3', **SIDE2)
    mk = os.path.join(T, 'mark_T330')
    t0 = time.time()
    rc, txt = run(['--to', 'drop1'], dict(P1, LINOG_MOCK_D1SLEEP='%s:30' % AC, LINOG_MOCK_MARK=mk), decide='ask', mcfg=slow)
    secs = time.time() - t0
    rd = rec('5d1', 'drop1')
    fold = os.path.join(W, out(rd).get('folder') or '-')
    tt = tests_of(fold)
    r_ac = (tt.get(AC) or ({}, []))[0]
    mpid = re.search(r'pid (\d+)', open(mk).read()).group(1) if os.path.isfile(mk) else None
    case('T330 the inversion without %s sleeps 30 s, the time limit 3 s: stopped (late), drop1 FAIL at G5d1.7, rc 2, in well under 30 s; '
         'the 5 complete tests read again (not run), the stopped one\'s copies removed, the mock process gone' % AC,
         rc == 2 and gates(rd).get('G5d1.7') == 'FAIL' and r_ac.get('late') is True and r_ac.get('complete') is False and secs < 25
         and no_scratch((tt.get(AC) or ({}, ['-']))[1]) and sorted(tt) == [AC] and bool(mpid) and not alive(mpid),
         'rc %d; %.0f s; %s late %s; tests in the folder %s; the mock pid %s alive %s' % (
             rc, secs, AC, r_ac.get('late'), sorted(tt), mpid, alive(mpid) if mpid else '-'))
    mk = os.path.join(T, 'mark_T330b')
    rc, txt, kinfo = killed(['--to', 'drop1'], dict(P1, LINOG_MOCK_D1SLEEP='%s:60' % AC), mk)
    rd = rec('5d1', 'drop1')
    left = scratch_under(W)
    lrel = sorted(os.path.relpath(x, os.path.join(W, out(rd).get('folder') or '-')) for x in left)
    lwant = sorted(['base.npz', os.path.join('tests', AC, 'avgSpatialCoh.h5'), os.path.join('tests', AC, 'inputs', 'ifgramStack.h5')])
    case('T330b SIGKILL to drop1 while the inversion without %s sleeps (60 s): the run stops (rc not 0), drop1\'s record RUNNING; the test\'s '
         'job and the mock inversion end within 15 s (each sent SIGTERM when its parent dies); left in the killed run\'s folder exactly the '
         'stopped test\'s stack copy and avgSpatialCoh.h5 (r2: nothing else is copied beside it) and base.npz' % AC,
         rc != 0 and kinfo.get('killed') is True and kinfo.get('job_alive') is False and kinfo.get('mock_alive') is False
         and rd.get('verdict') == 'RUNNING' and lrel == lwant,
         'rc %d; %s; drop1 %s; scratch %d: %s' % (rc, kinfo, rd.get('verdict'), len(left), [os.path.relpath(x, W) for x in left[:6]]))
    rc, txt = run(['--to', 'drop1', '--recover'], P1, decide='ask')
    rd = rec('5d1', 'drop1')
    case('T329b the plants gone, --recover, --decide ask: the killed run\'s scratch removed (G5d1.4c INFO), the 5 complete tests read again, '
         '%s run (1), its cull asked: DECISION, rc 4; no scratch left' % AC,
         rc == 4 and rd.get('verdict') == 'DECISION' and gates(rd).get('G5d1.4c') == 'INFO' and out(rd).get('reused') == 5
         and out(rd).get('ran') == 1 and out(rd).get('cull') == [AB] and not scratch_under(W),
         'rc %d; drop1 %s; G5d1.4c %s; reused %s, ran %s; cull %s; scratch %s' % (
             rc, rd.get('verdict'), val(rd, 'G5d1.4c')[:80], out(rd).get('reused'), out(rd).get('ran'), out(rd).get('cull'), scratch_under(W)[:2]))

    # ------------------------------------------------------------------ T331: lp_drop1's functions alone
    k4 = [AB, AC, AD, BC, BD, CD]
    # v0.13 r2 (18.3): the split's peers, nearest first on each side, ties to the earlier name
    mc = {AB: 0.55, AC: 0.59, AD: 0.59, BC: 0.50, BD: 0.59, CD: 0.53}
    pk = D1.pick_peers(AB, mc, [AC, AD, BC, BD, CD], 2)
    mc2 = {AB: 0.55, AC: 0.59, AD: 0.60, BC: 0.55, BD: 0.30, CD: 0.56}
    pk2 = D1.pick_peers(AB, mc2, [AC, AD, BC, BD, CD], 2)
    tb = D1.rule([AB, BC], {AB: 5, BC: 5, AC: 5, AD: 0, CD: 0}, {AB: ([CD], [AC]), BC: ([], [AD])}, mc, 1, 0.5)
    g1 = D1.guards(k4, [AB, CD], 0.2)
    g2 = D1.guards(k4, [AB], 0.2)
    g3 = D1.guards(k4, [AB, AC], 0.5)
    five = [AC, AD, BC, BD, CD]
    zt = [dict(pair=AB, margin=-4), dict(pair=CD, margin=None)]
    z1 = D1.zero_check(dict(gained=3, lost=2, net=1, p99_dv=None), zt, 'zero/inv.log')
    z2 = D1.zero_check(dict(gained=0, lost=0, net=0, p99_dv=0.25), zt, 'zero/inv.log')
    z3 = D1.zero_check(dict(gained=1, lost=1, net=0, p99_dv=None), zt[1:], 'zero/inv.log')
    case('T331 lp_drop1 alone (v0.13 r2: the split rule, 18.3): the peers nearest at or below and nearest above the pair\'s mean land '
         'coherence, nearest first, ties to the earlier name (%s; with BC equal to AB\'s 0.55 and BD far below, CD and AC above: %s, not '
         'by name nor across the sides); a net equal to its peers\' highest is kept, a pair with none below kept untestable; the guards: '
         '2 of 6 over 20 %% refused, 1 of 6 taken, two pairs of one date refused (the date left with 1 pair); testable: every pair of K4, '
         'in K4 without AB not AC (A left in 1 pair) but CD; the zero test WARN when its 5 cells changed reach the closest margin (4), '
         'INFO at 0, INFO with no margin' % (pk, pk2),
         pk == ([CD, BC], [AC, AD]) and pk2 == ([BC, BD], [CD, AC]) and tb[0]['culled'] is False and tb[0]['peers_max'] == 5
         and tb[0]['testable'] is True and tb[1]['culled'] is False
         and tb[1]['why'] == 'untestable: 0 unflagged pairs below its coherence 0.5000, 1 asked: kept'
         and g1['taken'] is False and 'over 20 %' in g1['why'] and g2['taken'] is True
         and g3['taken'] is False and A_ in g3['why'] and all(D1.testable(k4, p)[0] for p in k4)
         and D1.testable(five, AC)[0] is False and D1.testable(five, CD)[0] is True and D1.network_md5([AC, AB]) == D1.network_md5([AB, AC])
         and z1[0] == 'WARN' and z1[4]['churn'] == 5 and z1[4]['closest_pair'] == AB and 'zero/inv.log' in z1[3]
         and z2[0] == 'INFO' and z2[4]['noisy'] is False and z3[0] == 'INFO' and z3[4]['closest_margin'] is None,
         'peers %s / %s; rule %s; guards %s / %s / %s; zero %s %s %s' % (
             pk, pk2, [(x['pair'], x['culled'], x['why']) for x in tb], g1['why'], g2['why'], g3['why'], z1[0], z2[0], z3[0]))

    # ------------------------------------------------------------------ T331b (r2): the minimum peer count, the settings, the basis
    # v0.13 r2: through the split rule (18.3): each tested pair's split given, its peers' mean at its coherence
    import lp_admit as AM
    nets = {AB: 9, BC: 9, CD: 9, AC: 1, AD: 2, BD: 3}
    mq = {AB: 0.55, BC: 0.545, CD: 0.52, AC: 0.56, AD: 0.53, BD: 0.56}
    sq = {AB: ([AD], [AC, BD]), BC: ([AD], [AC]), CD: ([], [AD])}
    tm = D1.rule([AB, BC, CD], nets, sq, mq, 1, 0.005, 3)
    t1 = D1.rule([BC], nets, sq, mq, 1, 0.005)   # the default minimum, 1 (v0.12 r1's rule)
    zm = D1.zero_check(dict(gained=50, lost=50, net=0, p99_dv=None), tm[1:], 'zero/inv.log')
    m0 = dict(DROP1_PEERS='10', DROP1_MIN_PEERS='10', DROP1_PEERS_SIDE='5', DROP1_PEERS_BALANCE='0.005', DROP1_TCOH_MIN='0.70',
              DROP1_WORKERS='8', DROP1_TIMEOUT_S='1800', DROP1_FREE_GIB='10', ADMIT_CULL_MAX_FRAC='0.10', mintpy_cfg_file='linog_mintpy.cfg')
    sv0, sb0 = D1.read_settings(m0)
    sbad = dict((tag, D1.read_settings(mm)[1]) for tag, mm in (
        ('over', dict(m0, DROP1_MIN_PEERS='11')), ('zero', dict(m0, DROP1_MIN_PEERS='0')), ('frac', dict(m0, DROP1_MIN_PEERS='2.5')),
        ('absent', dict((k, v) for k, v in m0.items() if k != 'DROP1_MIN_PEERS')), ('peers', dict(m0, DROP1_PEERS='12')),
        ('side', dict((k, v) for k, v in m0.items() if k != 'DROP1_PEERS_SIDE'))))
    b10, b9 = AM.drop1_basis([AB], False, m0), AM.drop1_basis([AB], False, dict(m0, DROP1_MIN_PEERS='9'))
    bs4, bb4 = AM.drop1_basis([AB], False, dict(m0, DROP1_PEERS_SIDE='4')), AM.drop1_basis([AB], False, dict(m0, DROP1_PEERS_BALANCE='0.004'))
    lo = os.path.join(T, 'leftovers_T331b')
    lt = os.path.join(lo, 'drop1', '20261009T000000Z', 'tests', AB)
    os.makedirs(os.path.join(lt, 'inputs'), exist_ok=True)
    for n in ('inputs/ifgramStack.h5', 'avgSpatialCoh.h5', 'waterMask.h5', 'timeseries.h5', 'temporalCoherence.h5', 'numInvIfgram.h5',
              'result.json', 'inv.log', '../../base.npz', '../../drop1.json'):
        open(os.path.join(lt, n), 'w').close()
    lo_got = sorted(os.path.relpath(x, os.path.join(lo, 'drop1', '20261009T000000Z')) for x in D1.leftovers(lo))
    lo_want = sorted(['base.npz'] + [os.path.join('tests', AB, n) for n in ('inputs/ifgramStack.h5', 'avgSpatialCoh.h5', 'waterMask.h5',
                                                                          'timeseries.h5')])
    case('T331b (r2) the minimum peer count (v0.13 r2: through the split rule, each pair\'s peers balanced at its coherence): with 3 '
         'asked, a pair above its 3 peers named (margin +6), one above its 2 peers kept (margin None, "2 peers, under the 3"), one '
         'with none below kept untestable; the default 1 names the 2-peer pair (r1\'s rule); the zero test with no margin left INFO ("no '
         'flagged pair testable"); the settings: 10 of 10 read, 11 over DROP1_PEERS, 0, 2.5 and absent refused, and (v0.13 r2) '
         'DROP1_PEERS 12 not 2 x DROP1_PEERS_SIDE, the side absent; admit\'s basis differs between 10 and 9, and by the side and the '
         'balance; leftovers() lists a stopped test\'s stack copy, avgSpatialCoh.h5, waterMask.h5, time series and base.npz, and not '
         'its evidence',
         [x['culled'] for x in tm] == [True, False, False] and tm[0]['margin'] == 6 and tm[1]['margin'] is None
         and tm[1]['why'].startswith('2 peers, under the 3 the rule asks (') and tm[1]['peers_max'] == 2
         and tm[2]['why'] == 'untestable: 0 unflagged pairs below its coherence 0.5200, 1 asked: kept'
         and t1[0]['culled'] is True and zm[0] == 'INFO' and zm[4]['closest_margin'] is None and 'no flagged pair testable' in zm[1]
         and not sb0 and sv0.get('DROP1_MIN_PEERS') == 10 and 'DROP1_MIN_PEERS = 11, over DROP1_PEERS = 10' in sbad['over']
         and any('under 1' in x for x in sbad['zero']) and any('not a whole number' in x for x in sbad['frac'])
         and any('DROP1_MIN_PEERS absent' in x for x in sbad['absent']) and any('not 2 x DROP1_PEERS_SIDE' in x for x in sbad['peers'])
         and any('DROP1_PEERS_SIDE absent' in x for x in sbad['side']) and b10 != b9 and len(set([b10, bs4, bb4])) == 3
         and lo_got == lo_want,
         'rule %s; default %s; zero %s %s; settings %s %s; basis %s %s; leftovers %s' % (
             [(x['pair'], x['culled'], x['margin'], x['why']) for x in tm], t1[0]['culled'], zm[0], zm[1][-60:], sb0, sbad, b10[:8], b9[:8], lo_got))

    # ------------------------------------------------------------------ T332: the peers chosen by coherence
    restore('S4e', 'T332')
    # v0.13 r2: the split rule's 1 a side (v0.12 r2: DROP1_PEERS 2, the 2 nearest on either side)
    two = mcopy('mintpy_peers2.cfg', ADMIT_CULL_MAX_FRAC='0.20', DROP1_PEERS='2', DROP1_PEERS_SIDE='1')
    rc, txt = run(['--to', 'drop1'], dict(P1, LINOG_MOCK_COHPAIR='%s:0.54,%s:0.56' % (CD, BC)), decide='ask', mcfg=two)
    rd = rec('5d1', 'drop1')
    tb = dict((x['pair'], x) for x in out(rd).get('table') or [])
    jm = jload(os.path.join(W, out(rd).get('folder') or '-', 'drop1.json')).get('mean_coh_land') or {}
    case('T332 (v0.13 r2) DROP1_PEERS_SIDE 1 (DROP1_PEERS 2), %s\'s coherence 0.54 and %s\'s 0.56 (the flagged %s 0.55, the others '
         '0.59): its peers are %s (the nearest at or below it) and %s (the nearest above; %s, %s and %s at 0.59 farther), their mean '
         'at its coherence, 3 inversions and the zero test; the cull asked under ask, rc 4' % (CD, BC, AB, CD, BC, AC, AD, BD),
         rc == 4 and rd.get('verdict') == 'DECISION' and (tb.get(AB) or {}).get('peers') == [CD, BC] and out(rd).get('tests') == 4
         and (tb.get(AB) or {}).get('below') == [CD] and (tb.get(AB) or {}).get('above') == [BC]
         and abs((jm.get(BC) or 0) - 0.56) < 1e-4 and abs((jm.get(AB) or 0) - 0.55) < 1e-4 and abs((jm.get(CD) or 0) - 0.54) < 1e-4,
         'rc %d; drop1 %s; peers %s; tests %s; mean coherence %s' % (rc, rd.get('verdict'), (tb.get(AB) or {}).get('peers'), out(rd).get('tests'),
                                                                  dict((k, round(v, 3)) for k, v in jm.items())))

    # ------------------------------------------------------------------ T334: the cull taken with _archive a file
    restore('S4e', 'T334')
    arch = os.path.join(W, '_archive')
    if os.path.isdir(arch):
        os.rename(arch, os.path.join(W, '_archive_T334'))
    with open(arch, 'w') as fh:
        fh.write('a file where the folder _archive/ belongs (self-test T334)\n')
    rc, txt = run(['--to', 'drop1'], P1)
    rd = rec('5d1', 'drop1')
    case('T334 the cull taken under --decide auto with <frame>/_archive a file: G5d1.10 FAIL, drop1 FAIL, rc 2; mintpy/ in place, no '
         'decision file, no restart asked',
         rc == 2 and rd.get('verdict') == 'FAIL' and gates(rd).get('G5d1.10') == 'FAIL' and os.path.isdir(os.path.join(W, 'mintpy'))
         and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')) and not os.path.exists(os.path.join(W, 'status', 'restart.json'))
         and 'RESTART' not in ledger(),
         'rc %d; drop1 %s; G5d1.10 %s' % (rc, rd.get('verdict'), val(rd, 'G5d1.10')[:100]))

    # ------------------------------------------------------------------ T335: a flagged pair not testable
    restore('S4e', 'T335')
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# the operator excludes %s (self-test T335): %s is left in %s and %s only\nmintpy.network.excludeDate12 = %s\n' % (
            AC, A_, AB, AD, AC))
    rc, txt = run(['--to', 'drop1'], P1)
    rd = rec('5d1', 'drop1')
    un = out(rd).get('untestable') or []
    case('T335 the operator excludes %s, so dropping the flagged %s would leave %s in 1 pair: not testable, kept; drop1 PASS (state "no '
         'cull"), nothing run (no drop1/ folder), rc 0' % (AC, AB, A_),
         rc == 0 and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'no cull' and len(un) == 1 and un[0][0] == AB and A_ in un[0][1]
         and 'not testable' in val(rd, 'D1t') and not os.path.exists(os.path.join(W, 'drop1')),
         'rc %d; drop1 %s %s; untestable %s' % (rc, rd.get('verdict'), out(rd).get('state'), un))

    # ------------------------------------------------------------------ T336: --only drop1 under auto
    restore('S4e', 'T336')
    rc0, _ = run(['--to', 'sbas'], P1)
    rc, txt = run(['--only', 'drop1'], P1)
    rd = rec('5d1', 'drop1')
    case('T336 --decide auto with --only drop1 (LINOG_RESTART no): the cull is a DECISION ("without --only"), rc 4; nothing moved, no '
         'decision file, no restart asked',
         rc0 == 0 and rc == 4 and rd.get('verdict') == 'DECISION' and out(rd).get('state') == 'cull asked' and 'without --only' in val(rd, 'D1')
         and os.path.isdir(os.path.join(W, 'mintpy')) and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json'))
         and not os.path.exists(os.path.join(W, 'status', 'restart.json')),
         'rc %d %d; drop1 %s %s' % (rc0, rc, rd.get('verdict'), out(rd).get('state')))

    # ------------------------------------------------------------------ T337: admit changed after sbas, drop1 run alone
    restore('S4e', 'T337')
    rc0, _ = run(['--to', 'sbas'], P1)
    with open(os.path.join(W, 'recon', 'admission.txt'), 'w') as fh:
        fh.write('# the operator excludes %s after sbas (self-test T337)\nmintpy.network.excludeDate12 = %s\n' % (AB, AB))
    rc1, _ = run(['--only', 'admit'], P1)
    rc, txt = run(['--only', 'drop1'], P1)
    rd = rec('5d1', 'drop1')
    case('T337 admit changed after sbas (the operator excludes %s; --only admit: 5 kept) and drop1 run alone: the frame\'s stack keeps 6, '
         'so G5d1.4 FAIL ("mcfg and sbas are to run again"), rc 2, nothing tested, no decision file' % AB,
         rc0 == 0 and rc1 == 0 and rc == 2 and rd.get('verdict') == 'FAIL' and gates(rd).get('G5d1.4') == 'FAIL'
         and 'keeps 5 pairs, the frame\'s stack 6' in val(rd, 'G5d1.4') and not os.path.exists(os.path.join(W, 'drop1'))
         and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')),
         'rc %d %d %d; drop1 %s; G5d1.4 %s' % (rc0, rc1, rc, rd.get('verdict'), val(rd, 'G5d1.4')[:120]))

    # ------------------------------------------------------------------ T338 (r2): the minimum peer count in a run
    # v0.13 r2: the split rule's settings in a run (v0.12 r2 read DROP1_MIN_PEERS 6 and then 5 here; at the settings drop1 takes,
    # the minimum no longer keeps a tested pair, 18.3)
    restore('S4e', 'T338')
    three = mcopy('mintpy_side3.cfg', ADMIT_CULL_MAX_FRAC='0.20', DROP1_PEERS_SIDE='3', DROP1_PEERS='6')
    rc, txt = run(['--to', 'drop1'], P1, decide='ask', mcfg=three)
    rd = rec('5d1', 'drop1')
    tb = out(rd).get('table') or [{}]
    ev = os.path.join(W, out(rd).get('folder') or '-')
    j3 = jload(os.path.join(ev, 'drop1.json'))
    ok3 = (rc == 0 and rd.get('verdict') == 'PASS' and out(rd).get('state') == 'no cull' and out(rd).get('ran') == 7 and len(tb) == 1
           and tb[0].get('pair') == AB and tb[0].get('culled') is False and tb[0].get('margin') is None and tb[0].get('net') == 300
           and tb[0].get('peers_max') == 0 and tb[0].get('below') == [CD, BC] and tb[0].get('above') == [AC, AD, BD]
           and any(x['verdict'] == 'INFO' and x['value'].startswith('untestable: 2 unflagged pairs below its coherence 0.5500, 3 asked: '
                                                                    'kept') for x in gl(rd, 'D1r'))
           and 'each pair\'s 3 nearest at or below its coherence and 3 nearest above' in val(rd, 'D1t') and gates(rd).get('R2c') == 'PASS'
           and gates(rd).get('D1z') == 'INFO' and gates(rd).get('D1g') == 'N/A'
           and 'kept: 1 with fewer than 3 unflagged pairs on a side (%s)' % AB in val(rd, 'D1') and out(rd).get('side') == 3
           and j3.get('side') == 3 and j3.get('cull') == [] and j3.get('cull_proposed') == []
           and not os.path.exists(os.path.join(W, 'recon', 'drop1_decision.json')) and not os.path.exists(os.path.join(W, 'status', 'restart.json')))
    d3 = dict(rc=rc, verdict=rd.get('verdict'), state=out(rd).get('state'), ran=out(rd).get('ran'), d1r=val(rd, 'D1r')[:90], d1=val(rd, 'D1')[:90])
    before = [rec(i, ph) for i, ph in (('5a', 'admit'), ('5c', 'mcfg'), ('5d', 'sbas'))]
    rc5, txt5 = run(['--to', 'drop1'], P1, decide='ask', mcfg=CAP20)
    r5 = rec('5d1', 'drop1')
    same = before == [rec(i, ph) for i, ph in (('5a', 'admit'), ('5c', 'mcfg'), ('5d', 'sbas'))]
    t5 = out(r5).get('table') or [{}]
    case('T338 (r2; v0.13 r2) DROP1_PEERS_SIDE 3 (DROP1_PEERS 6) over %s\'s 2 unflagged pairs below it (its drop gains 300 land cells, '
         'theirs 0): kept, D1r "untestable: 2 unflagged pairs below its coherence 0.5500, 3 asked", its 2 below and 3 above inverted '
         '(7 tests), state "no cull", PASS, rc 0, no decision file nor restart; then 2 (DROP1_PEERS 4): drop1 runs again (its settings in '
         'its fingerprint, admit\'s record unchanged), reads its 6 tests again (none run: the peers it lacks, none), names it (margin '
         '+300), a DECISION under ask, rc 4' % AB,
         ok3 and rc5 == 4 and r5.get('verdict') == 'DECISION' and out(r5).get('state') == 'cull asked' and out(r5).get('reused') == 6
         and out(r5).get('ran') == 0 and t5[0].get('culled') is True and t5[0].get('margin') == 300 and out(r5).get('side') == 2
         and same and all(x.get('verdict') == 'PASS' for x in before) and gates(r5).get('G5d1.7') == 'PASS',
         'side 3: %s; side 2: rc %d %s %s, reused %s, ran %s, culled %s, margin %s; admit, mcfg, sbas records unchanged %s' % (
             d3, rc5, r5.get('verdict'), out(r5).get('state'), out(r5).get('reused'), out(r5).get('ran'), t5[0].get('culled'), t5[0].get('margin'),
             same))

    # ------------------------------------------------------------------ T339 (r2): the frame with mintpy/waterMask.h5
    restore('S4e', 'T339')
    rc, txt = run(['--to', 'drop1'], dict(P1, LINOG_MOCK_WATERMASK='1'), decide='ask')
    rd = rec('5d1', 'drop1')
    ev = os.path.join(W, out(rd).get('folder') or '-')
    tt = tests_of(ev)
    jw = jload(os.path.join(ev, 'drop1.json'))
    wmf = os.path.join(W, 'mintpy', 'waterMask.h5')
    logs = [os.path.join(ev, 'tests', t, 'inv.log') for t in tt]
    side = jw.get('beside') or {}
    keys = set((x or {}).get('key') for x, _ in tt.values())
    case('T339 (r2) the frame with mintpy/waterMask.h5 (the geometry\'s waterMask, written by the mock modify_network as MintPy 1.6.2 '
         'does): each of the 6 inversions finds ../avgSpatialCoh.h5 and waterMask.h5 in its own folder (the mock\'s log), and neither '
         'maskConnComp.h5 nor geometryRadar.h5; no copy left in any test folder; D1t names both; drop1.json\'s beside holds both '
         'files\' md5s; the 6 keys distinct; the cull asked under ask, rc 4',
         rc == 4 and rd.get('verdict') == 'DECISION' and os.path.isfile(wmf) and len(logs) == 6
         and all(os.path.isfile(x) and BES_WATER in open(x).read() for x in logs)
         and all(no_scratch(nm) and 'temporalCoherence.h5' in nm for _, nm in tt.values())
         and 'beside each stack copy: avgSpatialCoh.h5, waterMask.h5' in val(rd, 'D1t')
         and side.get('waterMask.h5') == S.md5(wmf) and side.get('avgSpatialCoh.h5') == S.md5(os.path.join(W, 'mintpy', 'avgSpatialCoh.h5'))
         and len(keys) == 6 and None not in keys,
         'rc %d; drop1 %s; waterMask.h5 %s; logs %d, the water line in %d; D1t %s; beside %s' % (
             rc, rd.get('verdict'), os.path.isfile(wmf), len(logs), sum(1 for x in logs if os.path.isfile(x) and BES_WATER in open(x).read()),
             val(rd, 'D1t')[-120:], sorted(side)))
    # T339b (r2): the water mask changed after drop1 PASSed: drop1 STALE (the beside files' md5s are in its fingerprint, sbas's
    # listing leaves them out), every test runs again (their keys hold the md5s). First a PASS on record: v0.13 r2,
    # DROP1_PEERS_BALANCE 0 keeps the pair (its peers' mean 0.0025 off; v0.12 r2: DROP1_MIN_PEERS 6), its tests read again.
    bal0 = mcopy('mintpy_bal0.cfg', ADMIT_CULL_MAX_FRAC='0.20', DROP1_PEERS_BALANCE='0', **SIDE2)
    rc0, txt0 = run(['--to', 'drop1'], dict(P1, LINOG_MOCK_WATERMASK='1'), decide='ask', mcfg=bal0)
    r0 = rec('5d1', 'drop1')
    s0 = (r0.get('started'), out(r0).get('folder'))
    with open(wmf, 'ab') as fh:   # one byte more: another md5 (no phase of this run opens the file again)
        fh.write(b'\0')
    rc, txt = run(['--to', 'drop1'], dict(P1, LINOG_MOCK_WATERMASK='1'), decide='ask', mcfg=bal0)
    rb = rec('5d1', 'drop1')
    jb = jload(os.path.join(W, out(rb).get('folder') or '-', 'drop1.json'))
    case('T339b (r2) on T339\'s frame, DROP1_PEERS_BALANCE 0 (v0.13 r2; v0.12 r2: DROP1_MIN_PEERS 6): drop1 PASS (no cull: the '
         'pair\'s peers\' mean 0.0025 off its coherence), its 6 tests read again; then mintpy/waterMask.h5 changed '
         '(one byte more): drop1 STALE (its fingerprint holds the beside files\' md5s; sbas\'s listing leaves them out), none of the 6 '
         'tests read again (their keys hold the md5s), all 6 run in a new folder, drop1.json\'s beside naming the new md5; PASS, rc 0',
         rc0 == 0 and r0.get('verdict') == 'PASS' and out(r0).get('state') == 'no cull' and out(r0).get('reused') == 6 and out(r0).get('ran') == 0
         and rc == 0 and rb.get('verdict') == 'PASS' and 'P5d1 drop1: record STALE' in txt and (rb.get('started'), out(rb).get('folder')) != s0
         and out(rb).get('reused') == 0 and out(rb).get('ran') == 6 and (jb.get('beside') or {}).get('waterMask.h5') == S.md5(wmf) != side.get('waterMask.h5'),
         'first rc %d %s reused %s ran %s; then rc %d; drop1 %s; STALE line %s; reused %s, ran %s; beside %s (before %s)' % (
             rc0, r0.get('verdict'), out(r0).get('reused'), out(r0).get('ran'), rc, rb.get('verdict'), 'P5d1 drop1: record STALE' in txt,
             out(rb).get('reused'), out(rb).get('ran'), (jb.get('beside') or {}).get('waterMask.h5'), side.get('waterMask.h5')))
