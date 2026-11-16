#!/usr/bin/env python3
"""lp_deliver.py -- linog_auto Phase 6a: the delivery, the kit's linog_phase6.sh (the 16 files of the v1.2 standard); v0.13 r3:
the pipeline's linog_phase6_r3.sh, the kit's script with chain A's DEM-error fit without the velocity fit's dates.

Runs inside lp_env.sh, after wmask (the masks the products are cut with): `bash $S/linog_phase6.sh <PATH> <FRAME>
<REF>` (43d6c15b), unchanged (design D-B; v0.13 r3: linog_phase6_r3.sh, below), with LINOG_ROOT set to the path table's root. From mintpy/ the script keeps
the ramp-first diagnostics (demErr_rampfirst.h5, timeseriesResidual_rampfirst.h5), runs chain A (dem_error.py without
deramp) and chain B (remove_ramp.py after it), three velocities, geocodes them with `python -m mintpy.cli.geocode`
(geocode.py is ISCE's on the env's PATH, G13), projects the two geocoded LOS velocities to vertical and horizontal
(the kit's linog_los2hv.py), and writes into mintpy/geo/LInOG_Upload_<TAG>/ two velocity KMZ and six hillshade PNG at
-10 to 10 cm/yr (G14), six GeoTIFF (NoData nan, N44; statistics embedded, the kit's linog_embed_stats.py) and two
time-series KMZ (the kit's linog_gen_interactive_kmz.py). Then this phase:
  D5  hard-links the report's pages into LInOG_Upload_<TAG>/reports/ (the top level stays at 16 files);
  D7  writes the four H/V files' labels from the frame (linog_los2hv.py writes 'look azimuth ~78 deg' and 'Single
      ascending track', both wrong for a descending path: F37): the look direction from geom_reference/los.rdr;
  F55 writes RUN_MANIFEST.json at the frame root: the run's parameters, decisions and conventions, and both headings
      (MintPy's HEADING from the orbit, and the one los.rdr gives), each with its source.
  v0.8 (record 69.7, 73.2 to 73.4) adds to RUN_MANIFEST.json: the reference's latitude and longitude as numbers, the
      geocoded cell that holds it (the floor of its fractional index from the grid's corner) beside MintPy's REF_Y,
      REF_X (the rounded index); D9's A/B (d9ab's record); the lead product (LEAD_PRODUCT, LEAD_REASON); and readings
      of the delivered GeoTIFFs (not gates): the value in the reference's cell, rings around the reference, and for each
      GNSS station of GNSS_STATIONS its discs minus the reference's.
  v0.9 (record 81) adds `fftw`: the wisdom refine's and igram's jobs ran with (file, md5s, the library's version, the
      modules, the jobs whose logs show the import), from their records; null for a step run before v0.9. LOGIC 3.
  v0.10 (record 108.3): dfit (R4) runs between wmask and this phase, and its exclusions (mintpy/exclude_date.txt, which
      linog_phase6.sh's three velocities read) are in the fingerprint; RUN_MANIFEST.json adds `velocity_fit` (the dates
      out of the velocity fit, MintPy's and R4's, with R4's A/B), `decisions.d3.rules` (R1's land, R3's dates, R2's cull)
      and, for a bridging run R5 took, `decisions.d9.r5` (the A/B that read bridging). LOGIC 4.
  v0.11 (item 4, record 122.4 and 122.6): after N6, G6a.10 sets every entry of the four KMZs to one fixed time,
      1980-01-01 00:00:00 (lp_kmz.py; Ariel's word, 122.8): MintPy's save_kmz.py stamps the velocity KMZs' entries with
      their files' mtimes and the kit's linog_gen_interactive_kmz.py the time-series KMZ's with the clock, so a rerun on the
      same data made other bytes (115.4). Each KMZ is made new in logs/p6/deliver/kmz/ and checked (only the time fields
      changed, zipfile's CRC test, every other field as written); only when all four pass are they moved over the
      originals. RUN_MANIFEST.json's delivery adds `kmz_times` (the fixed time, and the entries' times as written). LOGIC 5.
  v0.12 (item 1, record 124.7): drop1 tests the pairs R1 flags against their peers after sbas; its decision's digest is
      in the fingerprint, and RUN_MANIFEST.json adds `decisions.d3.drop1` (what drop1 decided: the pairs tested, each
      one's net against its peers' highest, the cull, the zero test, the decision file when the cull was taken). LOGIC 6.
  v0.13 r2 (the ascending record 15.2 with DB1-a to DB1-d as approved, 16.1, 16.2; 22.2's deliver row): after G6a.9, G6a.11
      reads the mode step (DB1, lp_modestep.py: RA1's Part B ported) from the chains' series and velocities and wmask's
      mask, a reading, not a gate (INFO, N/A or WARN; never FAIL or DECISION); deliver's record (outputs.mode_step) and
      RUN_MANIFEST.json's `mode_step` hold it, with one row per date at full precision. RUN_MANIFEST.json also adds
      `dates.dropped` (11.7: each granule recon dropped, with its date, mode, reason and the gate or file that dropped it:
      G0.4, G0.9, G1, G0.16, recon/exclude.txt, R7 with its loop; the decision files' md5s), `branch` and `looks` (18.5:
      recon's branch, the range and azimuth looks and the multilooked grid), and its label names v0.13 r2. LOGIC stays 6
      (DB1-b, approved: the reading and the new fields change no product, so a v0.12 delivery stays CURRENT and simply lacks
      them; 22.2's item 6: M64 keeps deliver CURRENT); lp_modestep.py's md5 is in the record's tools, not the fingerprint.
  v0.13 r3 (the ascending record 96.3): runs the pipeline's own linog_phase6_r3.sh (pinned here, PHASE6_R3_MD5; in the
      fingerprint) instead of the kit's linog_phase6.sh: the kit's script with three lines changed (S, the folder of the
      kit's helper tools, from LINOG_KIT_DIR, which this phase sets to the kit's folder; exclude_date.txt no longer held
      aside around chains A and B). Chain A's dem_error.py then reads mintpy/exclude_date.txt (dfit's E: MintPy's, R4's
      and the DEM-error loop's dates) through the template's topographicResidual.excludeDate, and fits the DEM error
      without them; G6a.6e checks its log names exactly E. The kit's four tools keep their pins (G6a.3); the kit's
      linog_phase6.sh is pinned and read (r3's script is it with three lines changed) but not run. RUN_MANIFEST.json's
      velocity_fit adds `dem_error_excluded` and `demfit` (the loop's passes). LOGIC 7: every earlier delivery is STALE
      (its demErr chains fitted the DEM error on every date) and its re-run a G6a.5 DECISION until its outputs are moved
      into the frame's _archive/.

Gates
  G6a.1  wmask PASS on record, its files as it recorded them; report PASS, its pages as it recorded them  FAIL
  G6a.1f dfit PASS on record (v0.10; v0.13 r3: r3's record, its DEM-error loop), mintpy/exclude_date.txt as it left it FAIL
  G6a.1d drop1 PASS on record (v0.12), not a cull taken and waiting for its restart                       FAIL
  G6a.2  environment; MintPy at its pin                                                        ERROR / FAIL
  G6a.3  the kit's linog_phase6.sh, linog_los2hv.py, linog_embed_stats.py, linog_gen_interactive_kmz.py FAIL
  G6a.3r v0.13 r3: the pipeline's linog_phase6_r3.sh at its pin                                       FAIL
  G6a.3c the script's commands on the PATH resolve into the pinned env's bin                           FAIL
  G6a.4  the coregistration reference (recon/reference.json = the reference record), SLC/<REF>/ there FAIL
  G6a.5  nothing in the way: the delivery folder and every file of the script's steps 2 to 10 absent DECISION
  D7l    the look direction from los.rdr, and MintPy's HEADING                                           INFO
  D7c    los.rdr's heading within LOS_HEADING_TOL_DEG of the stack's HEADING, its incidence within
         LOS_INCIDENCE_TOL_DEG of inputs/geometryRadar.h5's; los.rdr's scheme BSQ                        FAIL
  G6a.5r the ramp-first copies the script keeps, when there, whole HDF5 files                            FAIL
  G6a.6  linog_phase6_r3.sh (v0.13 r3; the kit's linog_phase6.sh before): rc 0; its steps 1 to 11;
         'PHASE 6 COMPLETE for <TAG>'                                                                   FAIL
  G6a.6e v0.13 r3: chain A's dem_error.py named exactly dfit's dates out of the fit (its log), once       FAIL
  G6a.8  the two masks as wmask recorded them (geocode --update skipped geo_maskTempCoh.h5), sbas's files FAIL
  N6     the delivery: the 16 names, nothing else at its top, no .aux.xml                               FAIL
  G6a.10 v0.11: the four KMZs' entries at 1980-01-01 00:00:00, nothing else changed (all four or none)  FAIL
  N44    the six GeoTIFF: NoData nan; statistics embedded (STATISTICS_MEAN)                              FAIL
  G22d   the demErr GeoTIFF's valid pixels = geo_maskTempCoh.h5's (delivered from the water mask)      FAIL
  G14    the renders' range: one range in the pinned script's save_kmz.py and view.py lines             FAIL
  D5     the report's pages in reports/ (hard links: the same inodes); the top level still 16           FAIL
  D7     the four H/V files carry the frame's direction and look azimuth                                FAIL
  G6a.9  the readings of the delivered GeoTIFFs (v0.8): the reference's cell, the rings, the GNSS discs  INFO / WARN
  G6a.11 v0.13 r2: the mode step (DB1; lp_modestep.py), a reading, not a gate: BOUNDED or UNBOUNDED INFO, one mode N/A,
         FLAG, NOT JUDGED or a reading that raised WARN                                           INFO / N/A / WARN
  G6a.7  RUN_MANIFEST.json written                                                                       FAIL
The script runs in a session of its own: a stop of this phase ends it and the MintPy steps under it before the record
says ERROR. --state: STALE also when a file of the delivery, the chains or RUN_MANIFEST.json changed since, and when the
report was made again or D9's decision changed (the report's digest and d9ab's decision are in the fingerprint). --dryrun
DIR: a plan (the command, the 16 names, the pages to link, the look direction and both headings read from the frame, and
RUN_MANIFEST.json as it would be, written into DIR, with the readings of the frame's own GeoTIFFs when it has been
delivered), or a plan only when the frame's sbas has not run; the frame is only read. v0.13 r2: a dry run reads G6a.11
from the frame's own products when they are there, marked as a dry run's, and before the frame's first delivery INFO "not
read: no products yet". Exit 0 PASS, 2 FAIL, 3 ERROR, 4 DECISION.
"""
import argparse
import collections
import glob
import json
import math
import os
import re

import lp_common as C
import lp_kmz as K
import lp_modestep as MS   # v0.13 r2: G6a.11 (standard library at import; numpy, h5py and scipy inside its functions)
import lp_p1 as P1
import lp_p2 as P2
import lp_p3 as P3
import lp_p5 as P5
import lp_p6 as P6

# LOGIC 6 since v0.12 (drop1's decision; v0.11: 5, the KMZs' fixed entry times; v0.10: 4). v0.13 r2 keeps it (DB1-b, the
# ascending record 15.2 and 16.1, as Ariel approved it; 22.2's item 6): G6a.11's reading and RUN_MANIFEST.json's mode_step,
# dates.dropped, branch and looks change what the manifest holds but no product, so a v0.12 or v0.13 r1 delivery stays CURRENT
# and simply lacks them (M64); LOGIC 7 would make every earlier delivery STALE and its re-run a G6a.5 DECISION (15.2). A frame
# whose earlier phases run again (the test root's rerun from admit) gets a new delivery, with them, through its fingerprint.
# v0.13 r3: LOGIC 7 (the ascending record 96.3): chain A's DEM-error fit leaves the velocity fit's dates out, so the demErr
# products change; every earlier delivery is STALE, and its re-run a G6a.5 DECISION until its outputs are archived.
PHASE, IDX, LOGIC = 'deliver', '6a', 7
VERSION_DELIVER = 'linog_auto v0.13 r3 (2026-10-30)'   # the release that last changed this phase (RUN_MANIFEST.json's label)
# v0.13's first install changed one line here (G6a.5's package glob by the path's direction) and kept v0.12's label; v0.13 r2
# names itself with G6a.11's reading (the ascending record 15.2's build note: a reader knows which manifests carry it)
KIT = ('linog_phase6.sh', 'linog_los2hv.py', 'linog_embed_stats.py', 'linog_gen_interactive_kmz.py')
# v0.13 r3: the script this phase runs, the pipeline's own (the kit's linog_phase6.sh with three lines changed), and its pin
PHASE6_R3, PHASE6_R3_MD5 = 'linog_phase6_r3.sh', '0adc02ba3af60f0b602bec04a35451d0'
DEMMSG = 'exclude the following dates for DEM error estimation'   # dem_error.py's line (MintPy 1.6.2), G6a.6e
CMDS = ('dem_error.py', 'remove_ramp.py', 'timeseries2velocity.py', 'save_kmz.py', 'save_gdal.py', 'gdal_edit.py', 'view.py', 'python')
STEPS = ('1', '2', '3', '4', '5', '6', '7', '8', '8b', '9', '10', '11')
BANNER = re.compile(r'^===== (\d+b?) ', re.M)


def reference_date(W, recdir):
    """recon/reference.json's date, and the reference record's."""
    rj = os.path.join(W, 'recon', 'reference.json')
    j = json.load(open(rj)) if os.path.isfile(rj) else {}
    r = P1.record(W, '2b', 'reference') or {}
    return j.get('reference'), r.get('outputs', {}).get('reference'), j.get('decided_by')


def stack_heading(W):
    ih = os.path.join(W, 'mintpy', 'inputs', 'ifgramStack.h5')
    try:
        return float(P5.h5_attrs(ih).get('HEADING'))
    except (OSError, TypeError, ValueError):
        return None


def records(W):
    out = {}
    for f in sorted(glob.glob(os.path.join(W, 'status', 'P*.json'))):
        try:
            r = json.load(open(f))
        except ValueError:
            continue
        out[r.get('phase')] = dict(index=r.get('index'), verdict=r.get('verdict'), end=r.get('end'), version=r.get('version'),
                                   fingerprint=r.get('fingerprint'))
    return out


def run_manifest(W, path, frame, cfg, q, m, los, head_stack, wsum, delivery, reports, tmd5, rng, d9ab=None, reads=None, rfit=None,
                 adm_dir=None, kmz=None, drop1=None, mode_step=None):
    """RUN_MANIFEST.json: what made the delivery (design 7.3), the conventions of its files (D7) and both headings
    (F55). adm_dir (v0.10, a dry run's folder): its recon/admission.json, when there, in place of the frame's (the decisions
    a run would make: admit runs again before deliver). v0.13 r2: mode_step (G6a.11's reading), dates.dropped, branch and
    looks."""
    rec = lambda i, p: P1.record(W, i, p) or {}   # noqa: E731
    rs, r1, rv = rec('5d', 'sbas'), rec('2a', 'stack1'), rec('1c', 'verify')
    ref, ref_rec, by = reference_date(W, W)
    adm = {}
    aj = os.path.join(W, 'recon', 'admission.json')
    if adm_dir and os.path.isfile(os.path.join(adm_dir, 'recon', 'admission.json')):
        aj = os.path.join(adm_dir, 'recon', 'admission.json')
    if os.path.isfile(aj):
        adm = json.load(open(aj))
    tf = os.path.join(W, 'mintpy', 'smallbaselineApp.cfg')
    vals = P5.cfg_dict(open(tf).read()) if os.path.isfile(tf) else {}   # the template as MintPy ran it (sbas set reference.yx)
    keep = ('mintpy.geocode.SNWE', 'mintpy.geocode.laloStep', 'mintpy.unwrapError.method', 'mintpy.unwrapError.ramp',
            'mintpy.network.excludeDate', 'mintpy.network.excludeDate12', 'mintpy.deramp', 'mintpy.topographicResidual',
            'mintpy.troposphericDelay.method', 'mintpy.networkInversion.maskDataset', 'mintpy.networkInversion.maskThreshold',
            'mintpy.reference.yx', 'ORBIT_DIRECTION')
    ts = {}
    try:
        ts = P5.h5_attrs(os.path.join(W, 'mintpy', 'timeseries.h5'))
    except OSError:
        pass
    gv, gsrc = geo_ref(W)
    tb = los['toward_satellite_bearing']
    dirn = 'descending' if cfg['direction'] == 'D' else 'ascending'
    return dict(
        manifest='RUN_MANIFEST.json (%s deliver)' % VERSION_DELIVER, created=C.utc(), pipeline=P6.HERE,
        frame=dict(path=path, frame=frame, tag=P6.tag(path, frame), folder=W, direction=dirn),
        dates=dict(modes=(rv.get('outputs', {}).get('census') or {}).get('mode'), dates=rv.get('outputs', {}).get('dates'),
                   pairs=adm.get('pairs'), kept=adm.get('kept'), network_pairs=r1.get('outputs', {}).get('pairs'),
                   dropped=dropped_entry(W)),
        branch=branch_entry(W), looks=looks_entry(W),
        mode_step=mode_step,
        decisions=dict(
            reference_date=dict(value=ref, decided_by=by, record=ref_rec),
            d3=dict(excludeDate=(adm.get('cfg') or {}).get('mintpy.network.excludeDate'),
                    excludeDate12=(adm.get('cfg') or {}).get('mintpy.network.excludeDate12'),
                    source=((adm.get('decisions') or {}).get('d3') or {}).get('source'),
                    rules=rules_entry(adm), drop1=drop1_entry(W, drop1)),
            d9=dict(unwrapError=(adm.get('cfg') or {}).get('mintpy.unwrapError.method'),
                    source=((adm.get('decisions') or {}).get('d9') or {}).get('source'),
                    statistic=(((adm.get('decisions') or {}).get('d9') or {}).get('statistic') or {}).get('mean'),
                    ab=d9ab_entry(d9ab), r5=r5_entry(W, adm)),
            operator_files=operator_files(W),
            reference_pixel=dict(dict(yx=(rs.get('outputs', {}).get('refpix') or {}).get('yx'),
                                      source=(rs.get('outputs', {}).get('refpix') or {}).get('source')), **ref_cell(gv, gsrc)),
            reference_date_mintpy=ts.get('REF_DATE')),
        velocity_fit=fit_entry(rfit),
        lead_product=lead(P6.tag(path, frame), q, [x[0] for x in delivery]),
        readings=reads,
        dem=dict(path=(r1.get('inputs') or {}).get('dem') or cfg.get('dem')),
        mintpy=dict(version=m['MINTPY_VERSION'], template='mintpy/smallbaselineApp.cfg',
                    template_md5=C.md5_file(tf) if os.path.isfile(tf) else None,
                    values=dict((k, vals.get(k)) for k in keep if k in vals), heading=head_stack),
        water_mask=wsum,
        fftw=fftw_entry(W),
        headings=dict(
            mintpy=dict(deg=head_stack, source='the stack\'s HEADING attribute (MintPy 1.6.2 stripmap metadata: '
                                               'orbit.getENUHeading at the scene\'s mid time); G24 checks it'),
            los=dict(deg=round(los['heading'], 4), source=los['source']),
            difference_deg=None if head_stack is None else round(los['heading'] - head_stack, 3),
            note='F55: two headings for one frame; the H/V labels use the line of sight (los.rdr), pixel by pixel as the '
                 'projection does'),
        look=dict(incidence_median_deg=round(los['incidence_median'], 3), incidence_range_deg=[round(los['incidence_min'], 3),
                                                                                          round(los['incidence_max'], 3)],
                  toward_satellite_bearing_deg=round(tb, 2), toward_satellite_compass=P6.compass(tb),
                  look_azimuth_deg=round(los['look_azimuth'], 2)),
        conventions=dict(
            units='GeoTIFF in m/yr; the PNG and KMZ renders in cm/yr, at %s cm/yr (the script\'s save_kmz.py and view.py lines)' % (
                ' and '.join('%g to %g' % r for r in sorted(set((a_, b_) for _, a_, b_ in rng))) or 'no range read'),
            los='positive toward the satellite (MintPy)',
            vertical='_Vertical = LOS/cos(inc): assumes no horizontal motion',
            horizontal='_Horizontal = LOS/sin(inc): assumes no vertical motion; positive toward the satellite along ground range, '
                       'bearing %.1f deg from north (%s) on this %s track' % (tb, P6.compass(tb), dirn),
            note='one %s track: projections, NOT a decomposition' % dirn, nodata='nan in every GeoTIFF (N44)',
            ramp='_ramp: a linear ramp removed after the DEM error (chain B); without it, chain A'),
        delivery=dict(folder=P6.upload_rel(path, frame), files=delivery, reports=reports, kmz_times=kmz),
        tools=tmd5, records=dict((k, v) for k, v in records(W).items() if k not in ('deliver', 'accept', 'package', 'rerun')),
        records_note='the records of Phases 0 to 5e when this manifest was written (deliver\'s own is its caller\'s)')


def fftw_entry(W):
    """v0.9 (record 81): the FFTW wisdom refine's and igram's jobs ran with, from their records (inputs.fftw: the files as
    the gate found them, at their pins; outputs.fftw: the jobs' logs read). None for a step run before v0.9, whose jobs
    planned their FFTs by timing them (FFTW_MEASURE, no wisdom)."""
    out = {}
    for i, ph in (('4a', 'refine'), ('4f', 'igram')):
        r = P1.record(W, i, ph) or {}
        fi, fo = (r.get('inputs') or {}).get('fftw'), (r.get('outputs') or {}).get('fftw') or {}
        if not fi:
            out[ph] = None
            continue
        out[ph] = dict(wisdom=fi.get('wisdom'), wisdom_md5=fi.get('wisdom_md5'), lib=fi.get('lib'), lib_md5=fi.get('lib_md5'),
                       version=(fi.get('with_file') or {}).get('version'), problems=(fi.get('with_file') or {}).get('total'),
                       covered=(fi.get('with_file') or {}).get('covered'),
                       modules=dict((m, (v or {}).get('md5')) for m, v in sorted((fi.get('modules') or {}).items())),
                       jobs=fo.get('jobs'), jobs_imported=fo.get('good'))
    out['note'] = ('ISCE2\'s cfft1d_jpl plans the FFTs of ampcor (refine), crossmul and icu (igram); from v0.9 with the pinned '
                   'wisdom (linog_fftw.cfg), before it by timing them (FFTW_MEASURE), so their results could change from run '
                   'to run (record 80, 81); null: that step ran before v0.9')
    return out


# v0.13 r2 (the ascending record 11.7): the gate or file behind each reason recon writes for a granule it drops (lp_recon.py)
DROP_BY = (('excluded in recon/exclude.txt', 'recon/exclude.txt'), ('R7 (D2), loop', 'R7'), ('unreadable:', 'G0.4'),
           ('product ', 'G0.9'), ('off-beam:', 'G1'), ('G0.16 framing', 'G0.16'))


def dropped_entry(W):
    """v0.13 r2 (the ascending record 11.7): each granule recon dropped, from recon/RECON.json's granule table (recon's own
    record of each: v0.12 r2's manifest listed none), with its date, mode, reason and the gate or file that dropped it (G0.4,
    G0.9, G1, G0.16, recon/exclude.txt, R7 with its loop), and the decision files' md5s as recon read them (its record's
    inputs). None when the frame has no RECON.json (a frame recon never ran on)."""
    rj = os.path.join(W, 'recon', 'RECON.json')
    if not os.path.isfile(rj):
        return None
    try:
        J = json.load(open(rj))
    except ValueError as e:
        return dict(granules=None, note='recon/RECON.json unreadable: %s' % e)
    rows = []
    for g in J.get('granules') or []:
        if g.get('status') != 'DROPPED':
            continue
        why = str(g.get('reason') or '')
        by = next((b for p, b in DROP_BY if why.startswith(p)), None)
        lm = re.match(r'R7 \(D2\), loop (\d+)', why)
        rows.append(dict(date=g.get('date_summary'), mode=g.get('mode'), product=g.get('product'), scene=g.get('scene'), zip=g.get('zip'), by=by,
                         loop=int(lm.group(1)) if lm else None, reason=why))
    rows.sort(key=lambda x: (str(x['date'] or ''), str(x['scene'] or '')))
    inp = (P1.record(W, '0a', 'recon') or {}).get('inputs') or {}
    return dict(granules=rows, count=len(rows), by=dict(collections.Counter(str(x['by']) for x in rows)),
                decision_files={'recon/exclude.txt': J.get('exclusions_md5') or inp.get('exclusions_md5'),
                                'recon/d2_decision.json': inp.get('d2_decision_md5')},
                recon_json_md5=C.md5_file(rj), source='recon/RECON.json (recon, P0a: its granule table; the decision files\' md5s '
                                                      'as recon read them, null for a file it did not read)')


def branch_entry(W):
    """v0.13 r2 (the ascending record 18.5): the frame's branch as recon read it (G0.10: FBS-only, FBS+FBD or FBD-only), and
    verify's (recon/modes.json)."""
    out = dict(recon=None, verify=None, source='recon/RECON.json (G0.10) and recon/modes.json (verify)')
    for k, rel in (('recon', 'RECON.json'), ('verify', 'modes.json')):
        try:
            out[k] = json.load(open(os.path.join(W, 'recon', rel))).get('branch')
        except (OSError, ValueError):
            pass
    out['value'] = out['verify'] or out['recon']
    return out


def looks_entry(W):
    """v0.13 r2 (the ascending record 18.5): the range and azimuth looks the stack ran with and the multilooked grid (Rule 4:
    int(width / range looks) x int(lines / azimuth looks)), from recon/reference.json's geometry; on an FBD-only frame
    linog_mixed.cfg's STACK_RLKS_FBD in place of STACK_RLKS (the reference's record names it)."""
    try:
        geo = json.load(open(os.path.join(W, 'recon', 'reference.json'))).get('geometry') or {}
    except (OSError, ValueError):
        return None
    note = ((P1.record(W, '2b', 'reference') or {}).get('outputs') or {}).get('looks')
    return dict(range=geo.get('rlks'), azimuth=geo.get('alks'), grid_columns=geo.get('width'), grid_lines=geo.get('length'),
                source='recon/reference.json\'s geometry (Rule 4)',
                note=note or 'linog_stack.cfg\'s STACK_RLKS and STACK_ALKS (on an FBD-only frame R6-d puts linog_mixed.cfg\'s '
                             'STACK_RLKS_FBD in place of STACK_RLKS)')


def mode_step_of(W, q, dry=False, dem_excl=None):
    """v0.13 r2: G6a.11's reading of the frame's products (lp_modestep.read, which names its own failures; this guard names a
    failure of the call itself), and its gate line (verdict, value, note). v0.13 r3: dem_excl, the dates chain A's dem_error
    left out (G6a.6e), passed on."""
    try:
        ms = MS.read(W, q, dry=dry, dem_excl=dem_excl)
    except Exception as e:  # noqa: BLE001  a reading, not a gate: the delivery stands
        ms = dict(reader='lp_modestep.py', state='NOT JUDGED', error='%s: %s' % (type(e).__name__, str(e)[:200]), dry_run=bool(dry),
                  why=['the reading raised %s: %s' % (type(e).__name__, str(e)[:200])], notes=[])
    return ms, MS.gate(ms)


def operator_files(W):
    """The operator's files the run read (recon/reference.txt, admission.txt, refpix.txt): md5 and their # lines, where
    the operator records why (S15's admission.txt names the rule and the reading behind D3 and D9)."""
    out = {}
    for n in ('reference.txt', 'admission.txt', 'refpix.txt'):
        f = os.path.join(W, 'recon', n)
        if os.path.isfile(f):
            out['recon/' + n] = dict(md5=C.md5_file(f), notes=[ln.strip().lstrip('#').strip() for ln in open(f, errors='replace')
                                                                if ln.strip().startswith('#')])
    return out


def geo_ref(W):
    """The attributes of the geocoded velocity that carries the reference (MintPy writes REF_LAT, REF_LON, REF_Y, REF_X and
    the grid): geo_velocity_demErr.h5 (the delivery's), else sbas's geo_velocity.h5. (attributes, the file's name)."""
    for n in ('geo_velocity_demErr.h5', 'geo_velocity.h5'):
        try:
            return P5.h5_attrs(os.path.join(W, 'mintpy', 'geo', n)), 'mintpy/geo/' + n
        except OSError:
            continue
    return {}, None


def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def ref_cell(gv, src):
    """The reference's latitude and longitude as numbers, and the geocoded cell that holds it: the floor of its fractional
    index counted from the grid's corner (Y_FIRST, X_FIRST the north and west edges); MintPy's geocoded REF_Y, REF_X round
    that index (69.3: on F3320 the zero sits in (582, 97), MintPy names (583, 98), whose centre is 78 m from the point).
    Distances to the two cells' centres in m (equirectangular, 111.32 km per degree)."""
    lat, lon = num(gv.get('REF_LAT')), num(gv.get('REF_LON'))
    y0, x0, dy, dx = (num(gv.get(k)) for k in ('Y_FIRST', 'X_FIRST', 'Y_STEP', 'X_STEP'))
    out = dict(lat=lat, lon=lon, attributes_from=src)
    if None in (lat, lon, y0, x0, dy, dx) or not dy or not dx:
        return dict(out, geo_cell=None, note='no geocoded grid or reference to read')
    fy, fx = (lat - y0) / dy, (lon - x0) / dx
    cell = [int(math.floor(fy)), int(math.floor(fx))]
    my, mx = num(gv.get('REF_Y')), num(gv.get('REF_X'))

    def metres(cy, cx):
        return round(math.hypot((cy + 0.5 - fy) * dy * 111320.0, (cx + 0.5 - fx) * dx * 111320.0 * math.cos(math.radians(lat))), 1)
    mc = [int(my), int(mx)] if my is not None and mx is not None else None
    return dict(out, geo_cell=cell, geo_cell_fractional=[round(fy, 3), round(fx, 3)], geo_cell_centre_m=metres(*cell),
                geo_cell_mintpy=mc, geo_cell_mintpy_centre_m=metres(*mc) if mc else None,
                geo_cell_note='geo_cell holds the reference (the floor of the fractional index from the grid\'s corner); '
                              'geo_cell_mintpy is MintPy\'s geocoded REF_Y, REF_X (the rounded index)')


def lead(tag, q, names):
    """RUN_MANIFEST.json's lead product (record 73.2): LEAD_PRODUCT (Velocity_demErr or Velocity_demErr_ramp) and its
    Vertical and Horizontal projections, which carry _ramp when it does (the kit's names), as they are in the delivery."""
    p = q['LEAD_PRODUCT']
    r = '_ramp' if p.endswith('_ramp') else ''
    want = ['%s_%s.tif' % (tag, x) for x in (p, 'Velocity_Vertical' + r, 'Velocity_Horizontal' + r)]
    other = 'Velocity_demErr' if r else 'Velocity_demErr_ramp'
    return dict(product=p, files=[n for n in want if n in names], missing=[n for n in want if n not in names] or None,
                reason=q['LEAD_REASON'], also='%s_%s.tif and its projections: the other chain (the v1.2 layout ships both)' % (tag, other))


def d9ab_entry(r):
    """D9's A/B as d9ab recorded it, for the manifest."""
    if not r:
        return None
    o = r.get('outputs') or {}
    res = o.get('result') or {}
    ids = set(g.get('id') for g in r.get('gates') or [])
    note = None if res else 'not run: unwrapError bridging (%s)' % (o.get('source') or 'the operator\'s') if 'D9m' in ids else \
        'd9ab %s: no A/B on record' % r.get('verdict')
    return dict(verdict=r.get('verdict'), rule=res.get('verdict'), compared=res.get('compared'), why=res.get('why'),
                min_gain_px=res.get('min_gain'), gain_px=res.get('gain'), mask_a_px=res.get('mask_a'), mask_b_px=res.get('mask_b'),
                std_common_mm_yr=[res.get('std_common_a'), res.get('std_common_b')], pairs_changed=res.get('pairs_changed'),
                moved_px=res.get('moved_px'), folder=o.get('folder'), reused=o.get('reused'), note=note)


def rules_entry(adm):
    """v0.10: what admit's rules read and decided (record 108.3), from recon/admission.json; None for an admit before v0.10."""
    d = adm.get('decisions') or {}
    r1, r3, r2 = d.get('r1'), d.get('r3'), d.get('r2')
    if not r1:
        return None
    rr = ((d.get('d3') or {}).get('rules')) or {}
    return dict(r1=dict(land_px=(r1.get('land') or {}).get('land'), water_px=(r1.get('land') or {}).get('water'), grid_px=(r1.get('land') or {}).get('grid'),
                        floor_px=r1.get('floor'), under_floor=r1.get('under_floor'), flagged_over_land=r1.get('flagged'),
                        flagged_over_whole_grid=len(r1.get('whole_flagged') or []), screened_over_land=r1.get('screened'), kit=r1.get('kit')),
                r3=dict(excluded=[dict(date=x.get('date'), why=x.get('why')) for x in (r3 or {}).get('excluded') or []], ok=(r3 or {}).get('ok')),
                r2=dict(cull=(r2 or {}).get('cull'), taken=(r2 or {}).get('taken'), why=(r2 or {}).get('why')),
                r4_candidates=(d.get('r4') or {}).get('dates'), rules_agree_with_d3=rr.get('agree'),
                note='record 108.3: R1 the kit over land, R3 dead and thin dates, R2 the cull cap; the operator\'s file, when there, decides D3 '
                     'and the rules are recorded beside it')


def drop1_entry(W, r):
    """v0.12: what drop1 decided (its record): the state, the pairs tested with each one's net against its peers' highest, the
    cull and whether it was taken, the zero test, the evidence folder and the decision file. None without a drop1 record.
    v0.13 r2: a record of r2's drop1 adds its rule (rule_id, side, balance), each tested pair's split, its peers' coherence range
    and mean and whether it was testable, and the guard's reading; a v0.12 r2 record keeps v0.12's entry."""
    if not r:
        return None
    o = r.get('outputs') or {}
    f = os.path.join(W, 'recon', 'drop1_decision.json')
    split = o.get('rule_id') is not None   # v0.13 r2's drop1 record (the split rule, balanced, and the guard); v0.12 r2's has none
    tested = []
    for x in o.get('table') or []:
        e = dict(pair=x.get('pair'), net_px=x.get('net'), peers_max_px=x.get('peers_max'), peers=len(x.get('peers') or []),
                 culled=x.get('culled'), why=x.get('why'))
        if split:   # v0.13 r2 (18.3): the split, the peers' coherence range and their mean, and whether the pair was testable
            e.update(coh=x.get('coh'), below=len(x.get('below') or []), above=len(x.get('above') or []), peers_lo=x.get('peers_lo'),
                     peers_hi=x.get('peers_hi'), peers_mean=x.get('peers_mean'), offset=x.get('offset'), testable=x.get('testable'))
        tested.append(e)
    d = dict(verdict=r.get('verdict'), state=o.get('state'), flagged=len(o.get('flagged') or []), in_network=o.get('in_network'),
             tested=tested, peers_n=o.get('peers_n'), min_peers=o.get('min_peers'),
             cull=o.get('cull'), taken=o.get('taken'), zero=o.get('zero'), folder=o.get('folder') or o.get('in_place'),
             decision_file=dict(file='recon/drop1_decision.json', md5=C.md5_file(f)) if o.get('decision_file') and os.path.isfile(f) else None)
    if split:
        d.update(rule_id=o.get('rule_id'), side=o.get('side'), balance=o.get('balance'),
                 guard=[dict(pair=g.get('pair'), n_dv_gt1=g.get('n_dv_gt1'), peers_max=g.get('peers_max'), over=g.get('over'))
                        if isinstance(g, dict) else dict(zip(('pair', 'n_dv_gt1', 'peers_max', 'over'), list(g)[:4]))
                        for g in o.get('guard') or []],   # a row of the record, or [pair, n, peers' highest, over] of the decision file
                 note='record 18.3 and 19.6 (v0.13 r2): each pair R1 flags, over land or the whole grid, tested against the '
                      'DROP1_PEERS_SIDE nearest unflagged pairs at or below its mean land coherence and as many above, their mean '
                      'coherence within DROP1_PEERS_BALANCE of its own (untestable and kept otherwise); named when dropping it gains '
                      'more coherent land (temporal coherence of DROP1_TCOH_MIN or more) than dropping any peer; under --decide auto a '
                      'named pair is culled only when its n_dv_gt1 is at most its peers\' highest (the guard, kept with a WARN '
                      'otherwise); R2\'s guards on the cull')
    else:
        d['note'] = ('record 124.7: each pair R1 flags, over land or the whole grid, against its nearest unflagged peers in mean land '
                     'coherence; culled when dropping it gains more coherent land (temporal coherence of DROP1_TCOH_MIN or more) than '
                     'dropping any peer, and it was tested against DROP1_MIN_PEERS peers or more (r2, record 127); R2\'s guards on the cull')
    return d


def r5_entry(W, adm):
    """v0.10: the A/B R5 took bridging on (recon/d9ab_decision.json), when the method's source is R5's; else None."""
    src = str(((adm.get('decisions') or {}).get('d9') or {}).get('source') or '')
    f = os.path.join(W, 'recon', 'd9ab_decision.json')
    if not src.startswith('R5') or not os.path.isfile(f):
        return None
    try:
        j = json.load(open(f))
    except ValueError:
        return dict(file='recon/d9ab_decision.json', note='unreadable')
    res = j.get('result') or {}
    return dict(file='recon/d9ab_decision.json', md5=C.md5_file(f), folder=j.get('folder'), taken=j.get('taken'), moved_to=j.get('moved_to'),
                rule=res.get('verdict'), why=res.get('why'), min_gain_px=res.get('min_gain'), gain_px=res.get('gain'),
                std_common_mm_yr=[res.get('std_common_a'), res.get('std_common_b')])


def fit_entry(r):
    """v0.10: the velocity fit's dates (dfit's record): MintPy's own exclusions, R4's A/B and the dates it took."""
    if not r:
        return None
    o = r.get('outputs') or {}
    return dict(dates_out_of_fit=o.get('final'), mintpy_exclusions=o.get('base'), mintpy_source=o.get('base_source'), r4_candidates=o.get('candidates'),
                r4_taken=o.get('taken'), r4_tests=o.get('tests'), a_mirror=o.get('a_mirror'), folder=o.get('folder'),
                file='mintpy/exclude_date.txt' if o.get('final') else None,
                # v0.13 r3: dfit's DEM-error loop (LOGIC 2) and chain A's DEM-error fit without the same dates
                dem_error_excluded=o.get('final') if 'demfit' in o else [], demfit=o.get('demfit'),
                note='the ascending record 96.3 (v0.13 r3): linog_phase6_r3.sh fits chain A\'s DEM error and the three velocities '
                     'without dates_out_of_fit (MintPy\'s, R4\'s and dfit\'s DEM-error loop\'s); the ramp-first chain '
                     '(timeseries_ramp_demErr.h5, velocity_ramp_demErr.h5) is sbas\'s, every date in its DEM-error fit'
                if 'demfit' in o else
                'record 108.3, R4: the demErr chains on every date; linog_phase6.sh\'s three velocities without dates_out_of_fit '
                '(lines 13, 18 and 20 to 22)')


def read_tifs(up, tag, products):
    """{product: (values in mm/yr as float64, geotransform)} of the delivery's <TAG>_Velocity_<product>.tif, read with GDAL's
    PAM off (no .aux.xml)."""
    from osgeo import gdal
    gdal.UseExceptions()
    gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')
    out = {}
    for pr in products:
        ds = gdal.Open(os.path.join(up, '%s_Velocity_%s.tif' % (tag, pr)))
        out[pr] = (ds.GetRasterBand(1).ReadAsArray().astype('f8') * 1e3, [float(v) for v in ds.GetGeoTransform()])
        ds = None
    return out


def readings(prods, lat0, lon0, rings, discs, ring_products, disc_products, stations):
    """The delivered velocity around the reference and at the GNSS stations (record 71.3 and 73.3), in mm/yr: the value
    in the cell that holds the reference; per ring between the edges rings (km), then the whole frame, the valid cells and
    their median, mean, 10th and 90th percentiles; per station (name, lat, lon) and disc radius r (km) in discs, the
    median of the valid cells within r of the station minus that within r of the reference. Distances between cell centres,
    equirectangular at 111.32 km per degree, the cosine at the centre point's latitude (S20's around20.py, pimo35)."""
    import numpy as np
    grids = set((a.shape, tuple(g)) for a, g in prods.values())
    if len(grids) != 1:
        raise ValueError('the GeoTIFFs are not on one grid: %s' % sorted(grids))
    (H, Wd), gt = grids.pop()
    rr, cc = np.mgrid[0:H, 0:Wd]
    latc = gt[3] + (rr + 0.5) * gt[5]
    lonc = gt[0] + (cc + 0.5) * gt[1]

    def dist(pt):
        return np.hypot((latc - pt[0]) * 111.32, (lonc - pt[1]) * 111.32 * math.cos(math.radians(pt[0])))

    def cell(pt):
        return int(math.floor((pt[0] - gt[3]) / gt[5])), int(math.floor((pt[1] - gt[0]) / gt[1]))

    def med(a, sel):
        v = a[sel & np.isfinite(a)]
        return int(v.size), (float(np.median(v)) if v.size else None)
    cy, cx = cell((lat0, lon0))
    inside = 0 <= cy < H and 0 <= cx < Wd
    d0 = dist((lat0, lon0))
    out = dict(units='mm/yr', grid=[int(H), int(Wd)], geotransform=list(gt),
               method='distances between cell centres, equirectangular at 111.32 km per degree, the cosine at the centre point\'s '
                      'latitude; medians over the valid (finite) cells',
               reference=dict(lat=lat0, lon=lon0, cell=[cy, cx], inside=inside,
                              value=dict((p, float(prods[p][0][cy, cx]) if inside and math.isfinite(prods[p][0][cy, cx]) else None)
                                         for p in sorted(set(ring_products) | set(disc_products)))))
    rows = []
    for lo, hi in zip(rings[:-1], rings[1:]):
        rows.append(('%g-%g km' % (lo, hi), (d0 >= lo) & (d0 < hi)))
    rows.append(('frame', np.ones((H, Wd), bool)))
    out['rings'] = []
    for name, sel in rows:
        rec = dict(ring=name)
        for p in ring_products:
            a = prods[p][0]
            v = a[sel & np.isfinite(a)]
            rec[p] = dict(cells=int(v.size), median=float(np.median(v)) if v.size else None, mean=float(v.mean()) if v.size else None,
                          p10=float(np.percentile(v, 10)) if v.size else None, p90=float(np.percentile(v, 90)) if v.size else None)
        out['rings'].append(rec)
    out['gnss'] = []
    for name, la, lo in stations:
        sy, sx = cell((la, lo))
        g = dict(station=name, lat=la, lon=lo, cell=[sy, sx], inside=0 <= sy < H and 0 <= sx < Wd,
                 km_from_reference=round(math.hypot((la - lat0) * 111.32, (lo - lon0) * 111.32 * math.cos(math.radians(la))), 3),
                 discs=[])
        ds, dr = dist((la, lo)), d0
        for r in discs:
            row = dict(r_km=r)
            for p in disc_products:
                a = prods[p][0]
                ns, ms = med(a, ds < r)
                nr, mr = med(a, dr < r)
                row[p] = dict(station_cells=ns, reference_cells=nr, station_median=ms, reference_median=mr,
                              difference=(ms - mr) if ms is not None and mr is not None else None)
            g['discs'].append(row)
        out['gnss'].append(g)
    return out


def stations_of(q):
    """[(name, lat, lon)] of GNSS_STATIONS (NAME:lat:lon, comma-separated)."""
    out = []
    for x in q['GNSS_STATIONS'].split(','):
        x = x.strip()
        if x:
            n, la, lo = x.split(':')
            out.append((n.strip(), float(la), float(lo)))
    return out


def km_list(v):
    return [float(x) for x in v.split(',') if x.strip()]


def try_readings(W, path, frame, q, gv):
    """(readings or None, a line for the gate, a problem or None): the readings of the delivery's GeoTIFFs, when they and the
    reference's latitude and longitude are there."""
    lat, lon = num(gv.get('REF_LAT')), num(gv.get('REF_LON'))
    up = os.path.join(W, P6.upload_rel(path, frame))
    rp = [x.strip() for x in q['READ_RING_PRODUCTS'].split(',') if x.strip()]
    dp = [x.strip() for x in q['READ_DISC_PRODUCTS'].split(',') if x.strip()]
    need = sorted(set(rp) | set(dp))
    miss = [p for p in need if not os.path.isfile(os.path.join(up, '%s_Velocity_%s.tif' % (P6.tag(path, frame), p)))]
    if lat is None or lon is None:
        return None, 'not read: no REF_LAT, REF_LON in the geocoded velocity', None
    if miss:
        return None, 'not read: the delivery holds no %s' % ', '.join(miss), None
    try:
        r = readings(read_tifs(up, P6.tag(path, frame), need), lat, lon, km_list(q['READ_RINGS_KM']), km_list(q['READ_DISCS_KM']),
                     rp, dp, stations_of(q))
    except Exception as e:  # noqa: BLE001  the readings are not a gate: a failure is named, the delivery stands
        return None, 'not read', '%s: %s' % (type(e).__name__, str(e)[:200])
    ref = r['reference']
    first = r['rings'][0]
    line = 'the reference\'s cell (%d, %d): %s; ring %s: %s' % (
        ref['cell'][0], ref['cell'][1], ', '.join('%s %s' % (p, '%+.3f' % v if v is not None else 'none') for p, v in sorted(ref['value'].items())),
        first['ring'], ', '.join('%s median %s over %d cells' % (p, '%+.3f' % first[p]['median'] if first[p]['median'] is not None else 'none',
                                                                 first[p]['cells']) for p in rp))
    for g in r['gnss']:
        dd = [x for x in g['discs'] if x.get(dp[0], {}).get('difference') is not None] if dp else []
        line += '; %s %.2f km from the reference, %s%s' % (
            g['station'], g['km_from_reference'], 'inside the grid' if g['inside'] else 'outside the grid',
            (': %s minus the reference %s' % (dp[0], ', '.join('%+.2f (%g km)' % (x[dp[0]]['difference'], x['r_km']) for x in dd))) if dd else '')
    return r, line, None


def fix_kmzs(W, upd, kmzs):
    """v0.11 (item 4, record 122.6): each KMZ of the delivery made new with every entry at K.FIXED (lp_kmz.fix_times) in
    logs/p6/deliver/kmz/ (the frame's filesystem, so a stop leaves nothing in the delivery) and checked there; only when
    all of them pass are they moved over the originals (os.replace, the original's mode kept), so a refusal or a failed
    check leaves every original as MintPy and the kit wrote it. Returns ({name: what fix_times found, with the md5 of the
    file delivered}, [problems])."""
    import shutil
    tmpd = os.path.join(W, 'logs', 'p6', 'deliver', 'kmz')
    os.makedirs(tmpd, exist_ok=True)
    if os.stat(tmpd).st_dev != os.stat(upd).st_dev:
        return {}, ['logs/p6/deliver/kmz/ and the delivery are on two filesystems: a fixed KMZ cannot be moved over its original']
    done, bad = [], []
    for n in kmzs:
        tmp = os.path.join(tmpd, '%s.%s.%d' % (n, C.utc().replace(':', ''), os.getpid()))
        try:
            r = K.fix_times(os.path.join(upd, n), tmp)
            shutil.copymode(os.path.join(upd, n), tmp)
            done.append((n, tmp, dict(r, md5=C.md5_file(tmp))))
        except Exception as e:  # noqa: BLE001  a refusal, a failed check or an unreadable zip: the original stays
            bad.append('%s: %s: %s' % (n, type(e).__name__, e))
    if bad:
        return {}, bad + ['no KMZ replaced: every original kept as written']
    out = {}
    for n, tmp, r in done:
        os.replace(tmp, os.path.join(upd, n))
        if C.md5_file(os.path.join(upd, n)) != r['md5']:
            bad.append('%s: after the move its md5 is not the checked file\'s' % n)
        out[n] = r
    return out, bad


def kmz_entry(fixed):
    """RUN_MANIFEST.json's delivery.kmz_times (v0.11): the fixed time and, per KMZ, the entries' times as written."""
    if fixed is None:
        return dict(fixed=K.FIXED_TEXT, files=None, note='a dry run: a run sets every entry of the four KMZs to the fixed time (G6a.10)')
    return dict(fixed=K.FIXED_TEXT, files=dict((n, dict(entries=r['entries'], written=[min(r['written']), max(r['written'])],
                                                        bytes_changed=r['bytes_changed'])) for n, r in sorted(fixed.items())),
                note='v0.11 (record 122.6): every entry of the four KMZs set to the fixed time, so a rerun on the same data makes '
                     'the same bytes; written: the entries\' times as MintPy\'s save_kmz.py and the kit\'s linog_gen_interactive_kmz.py '
                     'wrote them (the run\'s times)')


def hv_label(p, comp, los, dirn, head_stack):
    """D7: the H/V file's labels from the frame, replacing linog_los2hv.py's ascending text (F37)."""
    import h5py
    tb = los['toward_satellite_bearing']
    assumption = ('pure vertical motion, no horizontal' if comp == 'Vertical' else
                  'pure ground-range motion, no vertical; positive toward the satellite along ground range, bearing %.1f deg from N '
                  '(%s); look azimuth %.1f deg from N' % (tb, P6.compass(tb), los['look_azimuth']))
    with h5py.File(p, 'r+') as f:
        f.attrs['PROJECTION_ASSUMPTION'] = assumption
        f.attrs['PROJECTION_NOTE'] = 'Single %s track: projection, NOT a decomposition.' % dirn
        f.attrs['LOOK_AZIMUTH_DEG'] = '%.2f' % los['look_azimuth']
        f.attrs['GROUND_RANGE_TOWARD_SATELLITE_DEG'] = '%.2f' % tb
        f.attrs['INCIDENCE_MEDIAN_DEG'] = '%.3f' % los['incidence_median']
        f.attrs['HEADING_LOS_DEG'] = '%.3f' % los['heading']
        f.attrs['HEADING_MINTPY_DEG'] = 'none' if head_stack is None else '%.6f' % head_stack
        f.attrs['LINOG_D7'] = ('%s deliver: the labels from the frame (geom_reference/los.rdr), in place of linog_los2hv.py\'s '
                               '"look azimuth ~78 deg" and "Single ascending track" (F37)' % P6.VERSION_P6)
    return assumption


def main():
    ap = argparse.ArgumentParser(description='linog_auto Phase 6a: the delivery (the kit\'s linog_phase6.sh, D5, D7, F55)')
    ap.add_argument('--path', required=True)
    ap.add_argument('--frame', required=True)
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--dryrun', metavar='DIR')
    a = ap.parse_args()
    path, frame = C.norm_path(a.path), C.norm_frame(a.frame)
    cfg = C.load_cfg(path, frame)
    W = C.frame_dir(cfg, path, frame)
    recdir = os.path.abspath(a.dryrun) if a.dryrun else W
    env, s, m, q = P1.load_env(), P2.load_stack(), P5.load_mintpy(), P6.load_p6()
    tm = P6.tools(env, q, KIT)
    rw = P1.record(recdir, '5e', 'wmask') or {}
    rr = P1.record(recdir, '4g', 'report') or {}
    # v0.8: d9ab's record goes into RUN_MANIFEST.json (a dry run reads its own first, then the frame's)
    rd9 = (P1.record(recdir, '5dab', 'd9ab') if a.dryrun else None) or P1.record(W, '5dab', 'd9ab') or {}
    # v0.10: dfit's record (R4's exclusions), a dry run's own first, then the frame's
    rft = (P1.record(recdir, '5f', 'dfit') if a.dryrun else None) or P1.record(W, '5f', 'dfit') or {}
    # v0.12: drop1's record (its decision), a dry run's own first, then the frame's
    rd1 = (P1.record(recdir, '5d1', 'drop1') if a.dryrun else None) or P1.record(W, '5d1', 'drop1') or {}
    ref, _, _ = reference_date(W, recdir)
    r3p = os.path.join(P6.HERE, PHASE6_R3)   # v0.13 r3: the script this phase runs (G6a.3r)
    TAG, UP = P6.tag(path, frame), P6.upload_rel(path, frame)
    OUTS = P6.deliver_outs(path, frame)
    # the report's digest too: D5 links its pages into the delivery, so a report made again makes the delivery STALE; and
    # d9ab's decision (v0.8), which the manifest carries
    fp = C.md5_obj(dict(logic=LOGIC, wmask=rw.get('outputs', {}).get('digest'), report=rr.get('outputs', {}).get('digest'),
                        kit=dict((n, v[1]) for n, v in tm.items()), reference=ref, mintpy=m['MINTPY_VERSION'],
                        d9ab=(rd9.get('outputs') or {}).get('decision_md5'), dfit=(rft.get('outputs') or {}).get('decision_md5'),
                        drop1=(rd1.get('outputs') or {}).get('decision_md5'), phase6_r3=C.md5_file(r3p) if os.path.isfile(r3p) else None))
    if a.state:
        print(P6.state(recdir, W, PHASE, IDX, fp, OUTS))
        return 0

    st = P6.begin(recdir, PHASE, IDX, path, frame, fp, LOGIC, dict(p6_cfg=q['p6_cfg_file'], p6_cfg_md5=q['p6_cfg_md5'],
                                                                   tools=dict([(n, dict(path=v[0], md5=v[1])) for n, v in tm.items()] + [(
                                                                       PHASE6_R3, dict(path=r3p, md5=C.md5_file(r3p) if os.path.isfile(r3p) else None))])))
    st.rec['version'] = VERSION_DELIVER   # v0.9: this phase's release (the header line names lp_p6.py's)
    # v0.11: G6a.10's module; v0.13 r2: G6a.11's, recorded, not fingerprinted (the ascending record 15.2: a module added to the
    # fingerprint's kit would make every delivery STALE)
    st.rec['tools'].update(C.tool_md5s('lp_kmz.py', 'lp_modestep.py'))
    st.write()
    P6.header(PHASE, IDX, path, frame, W, a.dryrun)
    print('   deliver: %s, LOGIC %d' % (VERSION_DELIVER, LOGIC))
    rw, _ = P6.prior6(st, 'G6a.1', recdir, W, '5e', 'wmask', P6.WMASK_OUTS, bool(a.dryrun))
    if not rw:
        return st.finish()
    if a.dryrun and (P1.record(W, '5d', 'sbas') or {}).get('verdict') != 'PASS':
        return P5.plan_only(st, ['would run the kit\'s linog_phase6.sh from the frame after wmask, then D5, D7 and RUN_MANIFEST.json'],
                            'the frame\'s sbas has not run, so there are no MintPy products to plan the delivery from')
    rr, _ = P6.prior6(st, 'G6a.1r', recdir, W, '4g', 'report', P5.OUTS['report'], bool(a.dryrun))
    if not rr:
        return st.finish()
    # v0.10: dfit PASS on record and mintpy/exclude_date.txt as it left it (the fit's dates linog_phase6.sh reads)
    fo = rft.get('outputs') or {}
    ex5 = C.md5_file(os.path.join(W, 'mintpy', 'exclude_date.txt')) if os.path.isfile(os.path.join(W, 'mintpy', 'exclude_date.txt')) else None
    hold = os.path.lexists(os.path.join(W, 'mintpy', '_exclude_date.hold'))   # linog_phase6.sh's lines 13 to 18, left by a stop
    # v0.13 r3 (the review's item 1): dfit's record r3's (LOGIC 2: its DEM-error loop), not r2's; a dry run's plan-only dfit
    # record (the frame's wmask not run yet) has no loop to show and passes as before
    r3f = 'demfit' in fo or (bool(a.dryrun) and bool(fo.get('planned')))
    okf = rft.get('verdict') == 'PASS' and r3f and (a.dryrun or not fo.get('planned')) and not hold and (
        'excl_md5_after' not in fo or fo.get('excl_md5_after') == ex5 or (a.dryrun and fo.get('dryrun')))
    st.gate('G6a.1f', 'dfit PASS on record', 'PASS' if okf else 'FAIL', 'P5f dfit %s; the fit\'s dates out: %s; mintpy/exclude_date.txt %s%s' % (
        rft.get('verdict') or 'has no record', ', '.join(fo.get('final') or []) or 'none', 'as dfit left it' if fo.get('excl_md5_after') == ex5 else
        'NOT as dfit left it' if 'excl_md5_after' in fo else 'not recorded', '; mintpy/_exclude_date.hold EXISTS' if hold else '') + (
        '' if r3f or not rft else '; the record is not r3\'s (no DEM-error loop: LOGIC %s)' % rft.get('logic')),
        'PASS, by r3\'s dfit (its DEM-error loop on record); the file as dfit left it; no held file',
        '' if okf else 'run dfit first (after wmask: R4\'s fit; v0.13 r3: a frame dfit last ran under r2 runs it again, its '
        'DEM-error loop); a changed exclude_date.txt makes dfit STALE, and a held one '
        '(mintpy/_exclude_date.hold, left by a stopped deliver) stops dfit until it is put back')
    if not okf:
        return st.finish()
    # v0.12: drop1 PASS on record (a DECISION or FAIL of the peer test holds the delivery; a cull taken waits for its restart)
    o1 = rd1.get('outputs') or {}
    ok1 = rd1.get('verdict') == 'PASS' and (a.dryrun or not o1.get('planned')) and o1.get('state') != 'cull taken'
    st.gate('G6a.1d', 'drop1 PASS on record', 'PASS' if ok1 else 'FAIL', 'P5d1 drop1 %s%s' % (
        rd1.get('verdict') or 'has no record', ': %s' % (o1.get('state') or ('planned' if o1.get('planned') else 'no state')) if rd1 else ''),
        'PASS, and not a cull taken whose restart has not run (v0.12)',
        '' if ok1 else 'run drop1 first (after sbas; the driver runs it). A DECISION names the pairs to cull and how; a cull taken '
        '(--decide auto) waits for the driver\'s restart from admit')
    if not ok1:
        return st.finish()
    pages, _ = P6.pages_of(rr)
    if not P5.env_gate(st, 'G6a.2', env, s, m):
        return st.finish()
    if not P3.pins_gate(st, 'G6a.3', tm, 'the kit\'s Phase 6 tools') or \
            not P6.which_gate(st, 'G6a.3c', s, CMDS, 'the script\'s commands on the PATH'):
        return st.finish()
    # v0.13 r3: the pipeline's linog_phase6_r3.sh at its pin; the kit's helper tools from the kit's folder (LINOG_KIT_DIR)
    r3m = C.md5_file(r3p) if os.path.isfile(r3p) else None
    kdir = os.path.dirname(tm['linog_phase6.sh'][0])
    ok = r3m == PHASE6_R3_MD5 and all(os.path.dirname(v[0]) == kdir for v in tm.values())
    st.gate('G6a.3r', PHASE6_R3, 'PASS' if ok else 'FAIL', '%s md5 %s (pinned %s); the kit\'s helper tools from %s (LINOG_KIT_DIR)' % (
        r3p, r3m or 'ABSENT', PHASE6_R3_MD5, kdir), 'at its pin; the kit\'s four tools in one folder',
        '' if ok else 'the pipeline\'s copy is not as installed: check the package against its MANIFEST.md5')
    if not ok:
        return st.finish()
    ref, ref_rec, by = reference_date(W, recdir)
    ok = bool(ref) and ref == ref_rec and os.path.isdir(os.path.join(W, 'SLC', ref or '-'))
    st.gate('G6a.4', 'the coregistration reference', 'PASS' if ok else 'FAIL', '%s (recon/reference.json, decided by %s; the reference '
            'record %s); SLC/%s/ %s' % (ref, by, ref_rec, ref, 'present' if ref and os.path.isdir(os.path.join(W, 'SLC', ref)) else 'ABSENT'),
            'the same date in both; its SLC folder present (the kit\'s third argument)')
    if not ok:
        return st.finish()
    way = P6.deliver_way(path, frame)
    later = (P6.package_glob(path, frame, q, cfg['direction']),)   # accept writes no file in the frame; package's folder, whatever its date
    if not P6.way_gate(st, 'G6a.5', W, PHASE, way, later, bool(a.dryrun)):
        return st.finish()
    names = P6.delivery_names(path, frame)
    dirn = 'descending' if cfg['direction'] == 'D' else 'ascending'
    los = P6.los_direction(W)
    head = stack_heading(W)
    st.gate('D7l', 'the look direction (los.rdr)', 'INFO', 'incidence %.3f deg (median; %.3f to %.3f); heading %.2f deg (los.rdr), %s '
            '(MintPy\'s HEADING, the orbit): %s; toward the satellite along ground range %.1f deg (%s); look azimuth %.1f deg' % (
                los['incidence_median'], los['incidence_min'], los['incidence_max'], los['heading'],
                '%.3f' % head if head is not None else 'none', 'differ by %.2f deg (F55)' % (los['heading'] - head) if head is not None
                else '-', los['toward_satellite_bearing'], P6.compass(los['toward_satellite_bearing']), los['look_azimuth']),
            'a %s track: heading near %s deg' % (dirn, '-169' if cfg['direction'] == 'D' else '-11'))
    inc_stack = P6.stack_incidence(W)
    htol, itol = float(q['LOS_HEADING_TOL_DEG']), float(q['LOS_INCIDENCE_TOL_DEG'])
    dh = None if head is None else (los['heading'] - head + 180.0) % 360.0 - 180.0
    di = None if inc_stack is None else los['incidence_median'] - inc_stack
    ok = dh is not None and abs(dh) <= htol and di is not None and abs(di) <= itol
    st.gate('D7c', 'los.rdr against MintPy\'s geometry', 'PASS' if ok else 'FAIL', 'heading %+.3f deg from the stack\'s HEADING; incidence '
            'median %s deg from inputs/geometryRadar.h5\'s; los.rdr scheme %s' % (
                dh if dh is not None else float('nan'), '%+.4f' % di if di is not None else 'none (no incidenceAngle)', los['scheme']),
            'within %g deg and %g deg' % (htol, itol), '' if ok else 'the H/V labels and RUN_MANIFEST.json would carry a misread look '
            'direction; read geom_reference/los.rdr.xml and the stack\'s HEADING')
    if not ok:
        return st.finish()
    phase6 = r3p   # v0.13 r3: the pipeline's linog_phase6_r3.sh (G6a.3r), not the kit's linog_phase6.sh
    rng = P6.kit_ranges(phase6)
    tmd5 = dict((n, v[1]) for n, v in P6.tools(env, q).items())
    tmd5.update(dict((n, v[1]) for n, v in P5.tools(env, m).items()))
    tmd5[PHASE6_R3] = r3m   # v0.13 r3 (the review's item 2): the script that made the products; the kit's linog_phase6.sh is pinned, not run
    if a.dryrun:
        print('   would run from %s: bash %s %s %s %s  (LINOG_ROOT=%s, LINOG_KIT_DIR=%s)' % (W, phase6, path, frame, ref, cfg['root'], kdir))
        print('   would write %s/ with %d files: %s' % (UP, len(names), ', '.join(names)))
        print('   would set every entry of the four KMZs to %s (G6a.10, v0.11), hard-link the report\'s %d pages into %s/reports/ '
              '(D5), label the four H/V files from los.rdr (D7), and write RUN_MANIFEST.json at the frame root (its preview: '
              '%s/RUN_MANIFEST.json)' % (K.FIXED_TEXT, len(pages), UP, recdir))
        wsum = (rw.get('outputs') or {}).get('summary')
        reads, rline, rprob = try_readings(W, path, frame, q, geo_ref(W)[0])
        st.gate('G6a.9', 'the readings', 'WARN' if rprob else 'INFO', 'dry run, from the frame\'s delivery as it is: %s' % rline,
                'readings, not a gate (record 73.4)', rprob or '')
        if reads:
            reads['source'] = 'a dry run: the frame\'s own delivery as it is, not a new one'
        # v0.13 r2: G6a.11 from the frame's own products as they are (as G6a.9), marked as a dry run's; INFO "not read"
        # before the frame's first delivery
        # v0.13 r3: the frame's own delivery's G6a.6e when its record holds one (an r2 delivery: None, r2's choice)
        ms, (mv, mval, mnote) = mode_step_of(W, q, dry=True, dem_excl=((P1.record(W, IDX, PHASE) or {}).get('outputs') or {}).get(
            'dem_error_excluded'))
        st.gate('G6a.11', MS.GATE_NAME, mv, mval, MS.THRESHOLD, mnote)
        if ms.get('state') != 'not read':
            ms['source'] = 'a dry run: the frame\'s own products as they are, not a new delivery'
        man = run_manifest(W, path, frame, cfg, q, m, los, head, wsum, [[n, None, None] for n in names],
                           [[os.path.basename(p), None, None] for p in pages], tmd5, rng, rd9, reads, rft, adm_dir=recdir,
                           kmz=kmz_entry(None), drop1=rd1, mode_step=ms)
        man['dry_run'] = 'a preview: the frame is not delivered; sizes and md5s come with the run'
        P6.write_json(os.path.join(recdir, 'RUN_MANIFEST.json'), P6.jsonable(man))
        st.rec['outputs'] = dict(planned=True, dryrun=True, names=names, pages=len(pages), los=los, heading_mintpy=head,
                                 preview=os.path.join(recdir, 'RUN_MANIFEST.json'), readings=bool(reads), mode_step=ms)
        return st.finish('plan only (dry run)')

    # ---- the ramp-first copies the script keeps when they are there (step 1: [ -f X ] || cp): whole HDF5 files, not a
    # copy a stopped run cut short
    import h5py
    bad = []
    for n, ds in (('demErr_rampfirst.h5', 'dem'), ('timeseriesResidual_rampfirst.h5', 'timeseries')):
        f = os.path.join(W, 'mintpy', n)
        if os.path.isfile(f):
            try:
                with h5py.File(f, 'r') as h:
                    h[ds].shape
            except Exception as e:  # noqa: BLE001
                bad.append('%s: %s' % (n, e))
    kept = [n for n in ('demErr_rampfirst.h5', 'timeseriesResidual_rampfirst.h5') if os.path.isfile(os.path.join(W, 'mintpy', n))]
    st.gate('G6a.5r', 'the ramp-first copies', 'FAIL' if bad else 'PASS', '; '.join(bad) or ('%s there, whole (the script keeps them)' % ', '.join(kept)
                                                                                           if kept else 'absent (the script makes them)'),
            'absent, or whole HDF5 files', 'move the file into %s/_archive/ and run again: step 1 copies it again from sbas\'s' % W if bad else '')
    if bad:
        return st.finish()
    # ---- the kit's Phase 6, in a session of its own: a stop of this phase ends the script and the MintPy steps under it
    logd = os.path.join(W, 'logs', 'p6', 'deliver')
    lg = P1.new_log(os.path.join(logd, 'linog_phase6.log'))
    extra = dict(P5.mpl_env(W), LINOG_ROOT=cfg['root'], LINOG_KIT_DIR=kdir)
    rc, out = P6.run_group(['bash', phase6, path, frame, ref], W, lg, extra)
    seen = BANNER.findall(out)
    done = ('PHASE 6 COMPLETE for %s' % TAG) in out
    bad = rc != 0 or [x for x in STEPS if x not in seen] or not done
    st.gate('G6a.6', PHASE6_R3, 'FAIL' if bad else 'PASS', 'rc %d; steps %s; %s' % (rc, ' '.join(seen) or 'none',
                                                                                       'complete' if done else 'NOT complete'),
            'rc 0; steps %s; PHASE 6 COMPLETE for %s' % (' '.join(STEPS), TAG), 'log %s' % lg + ('' if not bad else '\n' + P3.tail(lg, 10)))
    st.rec['outputs'] = dict(log=lg)
    if bad:
        return st.finish()
    # v0.13 r3: chain A's dem_error.py named exactly dfit's dates out of the fit (MintPy prints none when it reads no date)
    import lp_dfit as DF
    want = sorted(fo.get('final') or [])
    k = out.count(DEMMSG)
    m_ = DF.EXMSG.search(out)
    named = (sorted(re.findall(r'\d{8}', m_.group(2))) if m_ and len(re.findall(r'\d{8}', m_.group(2))) == int(m_.group(1)) else None) \
        if k else []
    ok = k <= 1 and named == want
    st.gate('G6a.6e', 'chain A\'s DEM-error fit', 'PASS' if ok else 'FAIL', 'dem_error.py\'s log names %s (%d line%s); dfit\'s dates out of '
            'the fit %s' % (', '.join(named) if named else ('no date' if named == [] else 'NOT READ'), k, '' if k == 1 else 's',
                            ', '.join(want) or 'none'), 'the same dates, one line at most (v0.13 r3)',
            '' if ok else 'log %s: chain A did not fit the DEM error without the velocity fit\'s dates' % lg)
    st.rec['outputs'].update(dem_error_excluded=named)
    if not ok:
        return st.finish()
    # the script's geocode runs with --update: it must have skipped geo_maskTempCoh.h5, which wmask wrote 1 s after
    # maskTempCoh.h5 (a rewrite would drop the water mask from every product cut after it); and it writes none of sbas's
    ch = ['water mask: ' + x for x in P3.listing_changed(W, P6.WMASK_OUTS, rw.get('outputs', {}).get('files'))]
    ch += ['sbas: ' + x for x in P3.listing_changed(W, P5.OUTS['sbas'], (P1.record(W, '5d', 'sbas') or {}).get('outputs', {}).get('files'))]
    st.gate('G6a.8', 'the masks and sbas\'s files kept', 'FAIL' if ch else 'PASS', '; '.join(ch[:6]) or 'wmask\'s %d files and sbas\'s %d as '
            'they recorded them (geocode --update skipped geo_maskTempCoh.h5)' % (len(rw.get('outputs', {}).get('files') or []), len(
                (P1.record(W, '5d', 'sbas') or {}).get('outputs', {}).get('files') or [])), 'unchanged by linog_phase6.sh',
            'a mask rewritten after wmask drops the water mask from the delivery (G22); the delivery is to be made again after wmask'
            if ch else '')
    if ch:
        return st.finish()
    upd = os.path.join(W, UP)
    top = sorted(n for n in os.listdir(upd) if os.path.isfile(os.path.join(upd, n))) if os.path.isdir(upd) else []
    dirs = sorted(n for n in os.listdir(upd) if os.path.isdir(os.path.join(upd, n))) if os.path.isdir(upd) else []
    aux = [os.path.relpath(p, upd) for p in glob.glob(os.path.join(upd, '**', '*.aux.xml'), recursive=True)]
    bad = []
    if top != names:
        bad.append('missing: %s' % ', '.join(sorted(set(names) - set(top))) if set(names) - set(top) else '')
        bad.append('extra: %s' % ', '.join(sorted(set(top) - set(names))) if set(top) - set(names) else '')
    kinds = dict((k, len([n for n in top if n.endswith('.' + k)])) for k in ('tif', 'png', 'kmz'))
    want = dict(tif=int(q['DELIVERY_TIF']), png=int(q['DELIVERY_PNG']), kmz=int(q['DELIVERY_KMZ']))
    if kinds != want or len(top) != int(q['DELIVERY_FILES']):
        bad.append('counts %s, %d files; the standard %s, %s' % (kinds, len(top), want, q['DELIVERY_FILES']))
    if dirs:
        bad.append('folders: %s' % ', '.join(dirs))
    if aux:
        bad.append('.aux.xml: %s' % ', '.join(aux))
    bad = [x for x in bad if x]
    st.gate('N6', 'the delivery', 'FAIL' if bad else 'PASS', '%s: %d files (%d tif, %d png, %d kmz), %d .aux.xml' % (
        UP, len(top), len([n for n in top if n.endswith('.tif')]), len([n for n in top if n.endswith('.png')]),
        len([n for n in top if n.endswith('.kmz')]), len(aux)), '%s files: the 16 names; nothing else; no .aux.xml' % q['DELIVERY_FILES'],
        '\n'.join(bad))
    if bad:
        return st.finish()
    # ---- v0.11 (item 4): the KMZs' entries at one fixed time, all four or none
    kmzs = [n for n in names if n.endswith('.kmz')]
    fixed, bad = fix_kmzs(W, upd, kmzs)
    ne = sum(r['entries'] for r in fixed.values())
    wr = sorted(w for r in fixed.values() for w in r['written'])
    st.gate('G6a.10', 'the KMZs\' entry times', 'FAIL' if bad else 'PASS', '%d KMZs, %d entries at %s (as written: %s); %d bytes changed, only '
            'the time fields; zipfile\'s CRC test and every other field as written' % (
                len(fixed), ne, K.FIXED_TEXT, '%s to %s' % (wr[0], wr[-1]) if wr else 'none', sum(r['bytes_changed'] for r in fixed.values()))
            if not bad else 'not fixed', 'every entry of the %d at %s, nothing else changed' % (len(kmzs), K.FIXED_TEXT), '\n'.join(bad))
    if bad:
        return st.finish()
    tifs = [n for n in names if n.endswith('.tif')]
    facts, bad = {}, []
    import math
    for n in tifs:
        mean, nd, fin, xs, ys = P6.tif_facts(os.path.join(upd, n))
        facts[n] = dict(statistics_mean=mean, nodata=str(nd), finite=fin, width=xs, height=ys)   # str: a bare NaN is not JSON
        if mean is None:
            bad.append('%s: no STATISTICS_MEAN' % n)
        if nd is None or not math.isnan(nd):
            bad.append('%s: NoData %s' % (n, nd))
    st.gate('N44', 'the GeoTIFFs', 'FAIL' if bad else 'PASS', '%d of %d with NoData nan and STATISTICS_MEAN embedded; %d x %d cells' % (
        len(tifs) - len(set(x.split(':')[0] for x in bad)), len(tifs), facts[tifs[0]]['width'], facts[tifs[0]]['height']),
        'all six', '\n'.join(bad))
    if bad:
        return st.finish()
    import h5py
    import numpy as np
    with h5py.File(os.path.join(W, 'mintpy', 'geo', 'geo_maskTempCoh.h5'), 'r') as f:
        gm = int(np.count_nonzero(f['mask'][()]))
    t0 = '%s_Velocity_demErr.tif' % TAG
    ok = facts[t0]['finite'] == gm
    st.gate('G22d', 'delivered from the water mask', 'PASS' if ok else 'FAIL', '%s valid %d px, geo_maskTempCoh.h5 %d' % (
        t0, facts[t0]['finite'], gm), 'equal')
    if not ok:
        return st.finish()
    rs = sorted(set((a_, b_) for _, a_, b_ in rng))
    st.gate('G14', 'the renders\' range', 'PASS' if len(rs) == 1 and len(rng) == 2 else 'FAIL', '%s cm/yr in %s\'s %s lines (the '
            'script at its pin)' % (' and '.join('%g to %g' % r for r in rs) or 'no', PHASE6_R3, ' and '.join(c for c, _, _ in rng) or 'no'),
            'one range for save_kmz.py and view.py, fixed, not stretched per frame')
    # ---- D5: the report's pages, by hard link
    rdir = os.path.join(upd, 'reports')
    bad = []
    devs = set(os.stat(os.path.join(W, p)).st_dev for p in pages) | {os.stat(upd).st_dev}
    if len(devs) != 1:
        bad.append('the pages and the delivery are on %d devices: hard links impossible' % len(devs))
    if not pages:
        bad.append('the report records no pages')
    if not bad:
        os.makedirs(rdir)
        for p in pages:
            os.link(os.path.join(W, p), os.path.join(rdir, os.path.basename(p)))
        for p in pages:
            a_, b_ = os.stat(os.path.join(W, p)), os.stat(os.path.join(rdir, os.path.basename(p)))
            if (a_.st_ino, a_.st_dev) != (b_.st_ino, b_.st_dev):
                bad.append('%s is not a link of %s' % (os.path.basename(p), p))
    top2 = sorted(n for n in os.listdir(upd) if os.path.isfile(os.path.join(upd, n)))
    if top2 != names:
        bad.append('the top level changed: %d files' % len(top2))
    st.gate('D5', 'the report\'s pages in the delivery', 'FAIL' if bad else 'PASS', '%d pages hard-linked into %s/reports/; the top level '
            'still %d files' % (len(pages), UP, len(top2)), 'every page, the same inode; 16 files at the top', '\n'.join(bad))
    if bad:
        return st.finish()
    # ---- D7: the H/V labels
    bad, labels = [], {}
    for comp in P6.HV:
        p = os.path.join(W, 'mintpy', 'geo', 'geo_velocity_%s.h5' % comp)
        if not os.path.isfile(p):
            bad.append('%s absent' % os.path.basename(p))
            continue
        base = comp.split('_')[0]
        labels[comp] = hv_label(p, base, los, dirn, head)
        at = P5.h5_attrs(p)
        if dirn not in str(at.get('PROJECTION_NOTE', '')) or 'ascending' in str(at.get('PROJECTION_NOTE', '')) and dirn != 'ascending' \
                or at.get('PROJECTION_COMPONENT') != base:
            bad.append('%s: note %r, component %r' % (os.path.basename(p), at.get('PROJECTION_NOTE'), at.get('PROJECTION_COMPONENT')))
    st.gate('D7', 'the H/V labels', 'FAIL' if bad else 'PASS', '4 files: "Single %s track"; the horizontal positive toward the satellite at '
            '%.1f deg (%s), look azimuth %.1f deg' % (dirn, los['toward_satellite_bearing'], P6.compass(los['toward_satellite_bearing']),
                                                       los['look_azimuth']), 'the frame\'s direction and look azimuth in all four',
            '\n'.join(bad))
    if bad:
        return st.finish()
    # ---- v0.8: the readings of the delivered GeoTIFFs (not a gate: a failure to read them is a WARN)
    reads, rline, rprob = try_readings(W, path, frame, q, geo_ref(W)[0])
    st.gate('G6a.9', 'the readings', 'WARN' if rprob or not reads else 'INFO', rline, 'readings, not a gate (record 73.4)', rprob or '')
    # ---- v0.13 r2: G6a.11, the mode step (DB1), a reading, not a gate (INFO, N/A or WARN: the delivery stands)
    ms, (mv, mval, mnote) = mode_step_of(W, q, dem_excl=named)   # v0.13 r3: G6a.6e's
    st.gate('G6a.11', MS.GATE_NAME, mv, mval, MS.THRESHOLD, mnote)
    # ---- F55: RUN_MANIFEST.json
    deliv = [[n, os.path.getsize(os.path.join(upd, n)), C.md5_file(os.path.join(upd, n))] for n in names]
    reps = [[os.path.basename(p), os.path.getsize(os.path.join(W, p)), C.md5_file(os.path.join(W, p))] for p in pages]
    rwo = rw.get('outputs', {})
    man = run_manifest(W, path, frame, cfg, q, m, los, head, rwo.get('summary'), deliv, reps, tmd5, rng, rd9, reads, rft,
                       kmz=kmz_entry(fixed), drop1=rd1, mode_step=ms)
    mp = os.path.join(W, 'RUN_MANIFEST.json')
    P6.write_json(mp, P6.jsonable(man))
    ok = os.path.isfile(mp) and json.load(open(mp)).get('frame', {}).get('tag') == TAG
    st.gate('G6a.7', 'RUN_MANIFEST.json', 'PASS' if ok else 'FAIL', '%s, %d B, md5 %s; headings: MintPy %s, los.rdr %.3f deg' % (
        mp, os.path.getsize(mp) if os.path.isfile(mp) else 0, C.md5_file(mp) if os.path.isfile(mp) else '-',
        '%.3f' % head if head is not None else 'none', los['heading']), 'written at the frame root')
    lst = P3.listing(W, OUTS)
    st.rec['outputs'].update(files=lst, digest=P3.digest(lst), delivery=deliv, reports=len(reps), tif=facts, hv=labels, los=los, kmz=fixed,
                             heading_mintpy=head, manifest=mp, manifest_md5=C.md5_file(mp) if os.path.isfile(mp) else None,
                             mode_step=ms)
    return st.finish()


if __name__ == '__main__':
    P1.main_guard('lp_deliver', main)
