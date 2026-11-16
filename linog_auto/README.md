# linog_auto v0.13 r3 (2026-10-16; packaged 2026-10-18; r1 the same day; r2 2026-10-19; r3 2026-10-30)

Automated ALOS-1 PALSAR processing for LInOG: one entry point that takes a path and a frame, and (v0.10) a runner that
takes a path and its frames.
v0.13 holds Phase 0 (recon, stage), Phase 1 (extract, unpack, rwin, bandlimit, verify) for FBS-only, FBS+FBD and (R6-d)
FBD-only frames, Phase 2 (stack1, reference, stack2: the stack configuration), Phases 3 and 4 (topo, coarse, refine,
invert, datum, fine, bgrid, igram: the eight run files, to the interferograms of the network), Phase 4.5 (report: the
interferogram report, north up), Phase 5 (admit, prep, mcfg, sbas: MintPy from the admission of the pairs to the
geocoded time series and velocity in `mintpy/`; drop1 (v0.12): the drop-one peer test of the flagged pairs; d9ab: D9's
A/B), Phase 5e (wmask: the water and swath-edge masks), Phase 5f (dfit: the screened dates on the velocity fit) and
Phase 6 (deliver, accept, package, rerun: the 16 files of the v1.2 standard, their acceptance by the verifier, the review
package, and (v0.11) the package checked against an earlier one of the frame): 31 phases. Every version is installed on
felix into its own folder `insar/pipeline/vX.Y/`; nothing in `insar/scripts/` is changed.

v0.13 runs the ascending frames (the ascending automation record v0.1, sections 3 to 23; its build plan 22.2 and 22-d:
parts 1 to 5 and part 6's accept under R9 and the package prefix; drop1's split rule and guard, deliver's G6a.11 and
RUN_MANIFEST.json's new fields follow as v0.13 r2; the DEM-error fit without the velocity fit's dates as v0.13 r3):
- **v0.13 r3 (30 Oct; the ascending record 95.3, 95.5, 96.3, 96.4):** a date out of the velocity fit still bent the velocity
  through the DEM-error fit, which read every date until r2 (P448 F0290: 2.9 mm/yr at the 95th percentile, 95.3). The rule:
  a date is out of both fits or of neither. **dfit** (LOGIC 2): from MintPy's dates E, a loop in `dfit/<UTC>/demfit/pass<k>/`: `dem_error.py
  mintpy/timeseries_ramp.h5` with the frame's template and geometry and an `exclude_date.txt` holding E in the pass's folder
  (the template's `mintpy.topographicResidual.excludeDate = auto` reads it; the log must name exactly E), then
  `timeseries_rms.py` on that pass's residual with the template's residualRMS cutoff and deramp (auto: 3, quadratic) and
  sbas's mask (`mintpy/watermask/maskTempCoh.orig.h5`); a date over the cutoff not in E joins E and the loop runs again, at
  most 4 passes (G5f.9 a pass; G5f.10 PASS when a pass names no new date, else DECISION). R4 then tests each candidate on
  that loop's series with the date out of both fits (`r4/<date>/`: dem_error.py and the velocity fit; A1, G5f.11, is the
  velocity on the loop's series), and a date it takes starts the loop again (`demfit2/`). `mintpy/exclude_date.txt` then
  holds E (G5f.7). The limit is linog_mintpy.cfg's `DFIT_DEMFIT_MAX_PASSES` (4); after a G5f.10 DECISION a person writes the dates
  to take out of both fits into `recon/demfit.txt` (MintPy's own among them; G5f.5o checks it), and dfit runs one pass on that
  set (both in dfit's fingerprint). **deliver** (LOGIC 7): runs the pipeline's own `linog_phase6_r3.sh` (pinned in lp_deliver.py,
  `PHASE6_R3_MD5`, and in the fingerprint; G6a.3r), the kit's `linog_phase6.sh` with three lines changed: `S` from
  `LINOG_KIT_DIR` (the kit's folder, set by deliver; the kit's four tools keep their pins, G6a.3), and `exclude_date.txt` no
  longer held aside around chains A and B, so chain A's `dem_error.py timeseries.h5` fits the DEM error without E; G6a.6e
  checks its log names exactly E. `RUN_MANIFEST.json`'s `velocity_fit` adds `dem_error_excluded` and `demfit`. The network
  is not touched. Not changed: sbas's ramp-first chain (`timeseries_ramp_demErr.h5`, `velocity.h5`, every date in its
  DEM-error fit), which d9ab's A/B and dfit's mirror read; the kit's own `scripts/linog_phase6.sh` (the v1.x deliveries use
  it); every phase before dfit, so a frame r2 ran keeps them CURRENT, and reads dfit and deliver STALE (LOGIC up; accept,
  package and rerun chain on deliver's); its re-run of deliver is a G6a.5 DECISION until the r2 delivery is moved into the
  frame's `_archive/`. **lp_modestep.py** (G6a.11): deliver passes it the date set chain A's dem_error ran over (G6a.6e), which
  it takes for the dem_error-aware form whenever the data agree (|partial r| within MODESTEP_PARTIAL_R_MAX), naming any
  other set the data take instead; with no set given (an r2 delivery) its choice is r2's. r3 installs into `insar/pipeline/v0.13r3/`, beside r2's
  `pipeline/v0.13r2/`, which stays installed and is only read. The self-test adds the suite 13r3 (`lp_selftest13r3.py`,
  run inside suite 10 on its 6-date frame: R3F1 to R3F5, R301 to R312); the mock MintPy's `dem_error.py` reads the
  exclusions and carries a residual plant, and a mock `timeseries_rms.py` joins it; T167, T209, T210, T300, M61 and M64 read
  r3's labels, LOGIC and states. install.sh compares the 65 files r3 keeps byte for byte
  from r2 against r2's install, and hashes the listings of `pipeline/v0.13r2/` and `pipeline/v0.13/` before and after.
- **v0.13 r2 (19 Oct, after S43 to S45; the ascending record 26.2, 28):** part 6's rest. **drop1** (LOGIC 2): the split rule,
  balanced (18.3): a flagged pair is tested only against the `DROP1_PEERS_SIDE` (5) nearest unflagged pairs at or below its
  mean land coherence and as many above, their mean coherence within `DROP1_PEERS_BALANCE` (0.005) of its own, and is kept
  untestable otherwise; the two keys join `linog_mintpy.cfg` and admit's drop1 basis, so a decision file made under v0.12
  r2's rule is not applied (D1d); the guard (19.6): under `--decide auto` a named pair is culled only when its `n_dv_gt1` is
  at most its peers' highest, and kept with a WARN otherwise (D1g). **deliver** (LOGIC 6, as DB1-b keeps it): G6a.11, the
  mode step (15.2 to 16.4; `lp_modestep.py`, the `MODESTEP_*` keys of `linog_phase6.cfg`, B95 at 0.0039), and
  RUN_MANIFEST.json's `mode_step`, `dates.dropped`, `branch`, `looks`, and drop1's rule and guard. **accept** (LOGIC 3) and
  the verifier copy: the part 6 review's P6R-01 to 04, 08, 10 and 13 (NaN read as off, the R9 plan only from a PASS record
  read right after the zero test, the dates missing on each side named, R9's arithmetic, the datum record in accept's
  inputs); **package** (LOGIC 2): G6c.0 refuses a direction neither A nor D (P6R-09), G6c.2 reads any prefix (P6R-11);
  **datum**'s G16 and G4c.8 read NaN as off (P6R-01; LOGIC and fingerprint unchanged); **25-b:** `lp_xmlwidth.py`, one
  `.xml` width as isce2 2.6.3 loads it, at reference's G17, topo's G3a.14 and igram's G17 (verify's G6 waits: its module's
  md5 is in Phase 1's fingerprints), and `coreg_ref`'s fallback (P6R-14); **25-c:** install.sh removes its self-test's mock
  data after a PASS, keeping `selftest/selftest_console.txt`. The self-test adds suites 13r2a, 13r2b and 13r2c (M49 to M65,
  M75 to M78, M84b to M84f, M86, M87, M100 to M114) and moves every mock time base to decimal years (16.4).
  `lp_common.py`, `lp_p1.py`, `lp_p2.py` and the Phase 0 and 1 modules are byte for byte r1's (Phases 0 and 1 put their
  md5s in their fingerprints), so a frame made under r1 keeps its phases to report CURRENT. Under r2 such a frame reruns drop1
  (LOGIC 2) and, once its delivery and package are moved into its `_archive/` (the ascending record 26.2), deliver, accept
  (LOGIC 3), package (LOGIC 2) and rerun; admit, prep, mcfg, sbas, d9ab, wmask and dfit stay CURRENT, since their
  fingerprints read nothing r2 changes (the r2 review's R2R-01). `lp_common.VERSION` stays r1's label for that reason; each changed phase names r2 in its own label.
  r2 installs into its own folder, `insar/pipeline/v0.13r2/`, beside r1's `pipeline/v0.13/`, which stays installed and is
  only read: install.sh compares the 49 files r2 keeps byte for byte from r1 against r1's install, and hashes the listings of
  `pipeline/v0.13/` and `pipeline/v0.12/` before and after. `linog_env.cfg` is r1's (its md5 is in unpack's fingerprint), so its
  `UNPACKER` names r1's copy of the unpacker, byte for byte r2's.
- **v0.13 r1 (18 Oct, after S42):** v0.13's package carried three files at mode 0444 (`selftest_kit/linog_fbs_bandlimit.py`,
  `selftest_kit/linog_fbs_downsample.py`, `unpackFrame_ALOS.py`); the self-test copied the two band-limit tools with their
  modes, and M8f's append to its copy of `linog_fbs_bandlimit.py` stopped the Phase 1 cases under felix's account, so
  install.sh installed nothing (S42, rc 6). r1: every file at git's mode (0644, or 0755 where git records the execute bit);
  the self-test's copies in `kit/` and `bin/` writable by its account whatever the package's modes; case T40b reads every
  file's mode bits, so a pipeline folder made read-only fails its own self-test there. No phase's file changed: every file
  but `lp_selftest.py`, this README and MANIFEST.md5 is byte for byte v0.13's.
- **recon (R8, G0.16):** any path, from the path table's entry or, for a path the table lacks, a derived entry (the residue
  by the path formula, the direction by the frame rule; `recon/path_entry.cfg`); the table holds P447 to P450 (3.6);
  G0.16 drops a granule framed off the frame's along-track anchor (9.3); G0.17, G0.18 (`recon/beam.txt`), G0.14 on the
  derived corners; a root the caller does not own is refused unless `LINOG_ROOT` names it (12.3, item 2); the driver checks
  its own `python3` (item 3); G0.4d reads coarse's `recon/d2_decision.json` (R7).
- **Phase 1 (R6, R6-d):** extract takes an FBS+FBD frame and an FBD-only one; unpack runs the package's own unpacker
  (`unpackFrame_ALOS.py`, the course kit's copy, at a path any account reads: 14.2, item 1) and its env gate checks the
  env's prefix as well as its name (12.3, item 4); rwin corrects every date's range window, FBD dates too (18.4); the new
  phase **bandlimit** (P1bs) band-limits the FBS dates of an FBS+FBD frame in place by the course kit's
  `linog_fbs_bandlimit.py` at its pins (`linog_mixed.cfg`; N/A on FBS-only and FBD-only frames); verify adds G4 (the
  polarisation, the kit's `linog_pol_gate.py` ported), G1c.8 and writes each date's mode in `recon/modes.json`.
- **Phase 2:** D1 picks the reference among the FBS dates of an FBS+FBD frame (D1c, D1f, 4.7); an FBD-only frame takes 6
  range looks (`STACK_RLKS_FBD`, 18.5); the reference's sources in R7's order (11.7).
- **topo:** G3a.14 (Gap 2b): the reference against topo's simulated amplitude, PASS within a quarter of a range gate, FAIL
  from half a gate, a window counted at a peak ratio of 1.25 (17.7, 20.10; `lp_reg3.py`).
- **coarse (R7):** a date G21 or G7 names leaves the stack by coarse's D2 take (MOVES.txt, `recon/d2_decision.json`, a
  restart), within the limits L0 to L8; the products are reused by 11.5's rule (G3b.6); `recon/d2.txt` is the operator's
  take or keep (11.6); G3b.11, G3b.12 and G21e.
- **datum (R9):** on an FBS+FBD frame the per-date misregistration is solved again in each date's own units with the
  reference pinned (17.2, 17.3), since run_04 doubles every pair's range offset from an FBD date; an FBS-only or FBD-only
  frame keeps G16, with R9 as a reading (G4c.10).
- **fine, igram:** G10 v3 and G10m as readings beside the kit's G10 v2 (17.4); G11's classes from `recon/modes.json`, G11m,
  G17's FILE_NAME (21.4).
- **admit:** R3 counts R7's dates in its share (R7-e). **accept** (LOGIC 2): the verifier copy's N22 and G16 check
  `dates/` against R9's plan on a frame datum ran R9 on (18.6), and N22's range factor is spacing(the reference's mode) /
  spacing(the date's) elsewhere, 1 on an FBD-only frame (18.5). **package:** the prefix by the path's direction,
  `LINOG_DESC` on a descending path and `LINOG_ASC` on an ascending one (11.13, 22-b).
- **On a frame v0.12 delivered** (path 84's four), as `--state` reads it: recon, stage, extract, unpack and verify STALE
  (their fingerprints hold the md5s of their own files, and `lp_common.py` changed; unpack's also `linog_env.cfg`'s, whose
  `UNPACKER` line changed), bandlimit NONE, accept STALE (its LOGIC and the copy's md5), and rwin and every phase from
  stack1 to deliver, package and rerun as v0.12 read them: their fingerprints hash their inputs and a LOGIC number (rwin's
  since v0.5: its LOGIC and unpack's recorded fingerprint), and package and rerun chain on accept's and package's records,
  which stay until accept runs again. A run from recon then runs Phases 0 and 1 again, and rwin with them through
  unpack's new fingerprint (the ascending record 4.2). S42 reads the four frames so.

v0.12 tests the pairs R1 flags before culling any (item 1: Doc JD's drop-one test, record 119.5; the rule, 120.5; the plan,
124.7; Ariel's word on its four choices, 125.0). admit (LOGIC 4) no longer culls by R2 alone: every pair R1 flags, over
land or over the whole grid, goes to the new phase **drop1** (5d1) after sbas. drop1 drops each flagged pair from a copy of
the stack and inverts the network again (MintPy's `ifgram_inversion.py`, 8 at a time), and does the same for the 10
unflagged pairs nearest it in mean land coherence (its peers) and once with no pair dropped (the zero test). A test's net
is the coherent land (temporal coherence 0.70 or more on R1's land) it gains minus what it loses against sbas's own; a
flagged pair is culled when its net exceeds every one of its peers' and it was tested against 10 peers or more (r2), and
R2's guards (10 % of the pairs at most, one component, every date in 2 pairs or more) bound the cull as a whole. Under
`--decide auto` drop1 takes the cull as d9ab's R5 takes bridging (`recon/drop1_decision.json`, `mintpy/` moved into `_archive/mintpy_predrop1_<UTC>/`, a restart from
admit); under `ask` it is a DECISION; with `recon/admission.txt` naming the exclusions the test runs and its cull is
recorded, not applied. The driver allows one restart per asking phase (drop1, then d9ab: at most 2 a run).
`RUN_MANIFEST.json` gains `decisions.d3.drop1` (deliver's LOGIC is 6), and deliver asks drop1 PASS on record (G6a.1d).
The driver prints the run summary in phase order (`lp_common.py` and `lp_p1.py` are unchanged: they are in the
fingerprints of Phases 0 and 1). On a frame v0.11 delivered, admit and deliver read STALE (their LOGIC is 4 and 6), drop1
NONE, and the others as v0.11 read them; deliver, STALE, stops at G6a.5 on any frame whose delivery is still in it,
until its outputs are moved into `_archive/` (as S37 did for v0.11's on F3310). On F3320 (no land flag, 157 kept) admit
decides as before and drop1 tests its one whole-grid flag against 10 peers. On F3310 (v0.10's R2 cut 2 land-flagged
pairs, 151 kept) admit keeps 153, so a v0.12 run stops first at mcfg's G5c.4 (`mintpy/` in the way) and later at
deliver's G6a.5: move each into `_archive/` as the DECISION says, or run the frame in a fresh tree; drop1 then tests the
46 to 48 flagged pairs after sbas runs again on 153.
v0.12 r2 (record 127, before install; the package `linog_auto_v0.12_20261009_r2.tar.gz`, installed as `pipeline/v0.12`):
the minimum peer count `DROP1_MIN_PEERS` (10), in the rule, admit's basis and fingerprint and drop1's fingerprint (and so
in deliver's, through drop1's decision digest); drop1 copies only what MintPy 1.6.2's inversion reads around a stack
(`avgSpatialCoh.h5` one folder above the stack copy, and `waterMask.h5` in the test's folder when the frame has one),
with their md5s in drop1's fingerprint and the tests' keys; install.sh compares felix's `ifgram_inversion.py` and its cli
with the published 1.6.2's md5s.

v0.11 makes a rerun checkable (record 122.6; Ariel's word on 122.8). **deliver** sets every entry of the four KMZs to
one fixed time, 1980-01-01 00:00:00 (G6a.10, `lp_kmz.py`): MintPy's `save_kmz.py` stamps the velocity KMZs' entries with
their files' mtimes and the kit's `linog_gen_interactive_kmz.py` the time-series KMZ's with the clock, so F3310's v0.10
rerun made v0.9's products byte for byte but for those four files and `RUN_MANIFEST.json` (record 115.4); with the
fixed times, v0.9's and v0.10's KMZs of F3310 match by md5 (122.4). The new phase **rerun** (6d) compares the package
with an earlier one of the frame: the one `recon/rerun_reference.txt` names, else the package of the frame's newest
archived tree (`p<path>/_archive/f<frame>_*_<UTC>`), else none (a first run). Every file equal but `RUN_MANIFEST.json`
(the KMZs by their entries, so a v0.10 package compares with a v0.11 one) is a PASS; files that differ on another network
are read (median, p01 and p99 of the difference, the shares beyond 1 and 5 mm/yr, the cells gained and lost, the maximum
beside them) and the phase PASSes with INFO; files that differ on the same network stop the run with DECISION, in either
`--decide` mode, until `recon/rerun.txt` takes them. `lp_compare.py`, beside the pipeline and not a phase, holds that
comparison and the trace's three others (the shelves without object ids, the unwrapped phases' whole cycles, the
velocity split between the network and the rest: record 119). The default `--to` is now `rerun`. Every file of Phases
0 to 5f, accept, package, `lp_p6.py`, the verifier copy and the seven settings files are byte-identical to v0.10; on a
frame v0.10 delivered, deliver reads STALE (its LOGIC is 5), rerun NONE, and the other 27 phases CURRENT (accept and
package until deliver runs again).

v0.10 decides what v0.9 asked the operator (record 108.3, the rules approved in 109.0), so a frame can run from its path
and frame alone. admit decides D3 by three rules: **R1** reads the kit's own statistics (`linog_admit.py`'s per-pair
coherence, R, spectral peak and LARGEST, and its own thresholds) over the land, not over the whole grid: the land is
`geom_reference/hgt.rdr` off the water tool's `flat_masks()` (F3310's sea is 56.5 % of its grid, and over the whole grid
the kit flagged 46 of its 153 pairs, over land 2: RD10, record 97); **R3** takes dead dates (more than half their pairs
flagged) and thin dates (fewer than 2 pairs) out of the network, within limits (min_dates, one component, at most 25 %
of the dates, D1's reference kept); **R2** culls the flagged pairs when they are 10 % of the network or fewer and the
network stays whole. A date the kit's screen proposes stays in the network for the new phase **dfit** (R4), which tests
it on the velocity fit after wmask. Under `--decide auto` the rules' exclusions are taken; under `ask` they are asked;
`recon/admission.txt` still takes their place, and the rules' result is recorded beside it. d9ab's bridging verdict
under `--decide auto` (**R5**) is taken too: the frame is run again from the top with bridging, once. The path table
gains paths 83, 86 and 87 (record 109.3, RD4's census), and `linog_path.sh` runs a path's frames one after another.
Every Phase 0 to 4 file, report, prep, mcfg, sbas, wmask, accept, package, `lp_p6.py`, the verifier copy and five
settings files are byte-identical to v0.9; on a frame v0.9 delivered, admit, d9ab and deliver read STALE (their LOGIC
is 3, 2 and 4), dfit NONE, and the other 24 phases CURRENT.

v0.9 pins the FFT plans of refine and igram (record 80 and 81). ISCE2's cfft1d_jpl, from which ampcor (refine), crossmul
and icu (igram) take their FFTs, plans each size with FFTW_MEASURE: the planner times its candidates, so the plan, and
the last bits of the result, changed from run to run. That is why I4, the second run of P084 F3320 from scratch, failed
78.5 although every choice was v1.0's (record 80); S25 then ran ampcor 46 times at once on one pair: 9 distinct results
without wisdom, 1 with a wisdom file made on felix (crossmul: 9 of 12, then 1). v0.9 carries that file
(`fftw/wisdom_felix.wis`) and `linog_fftw.cfg`, which pins it, the env's libfftw3f (md5 and version) and ISCE2's three
modules. refine and igram check them before any job (G4a.4w, G4f.4w: the pins, ldd, and in a fresh process the file's
coverage of all 512 problems cfft1d_jpl can plan, none without it), give the file to their jobs alone as `WISDOM_FILE`,
and read every job's log after the step (G4a.7w, G4f.8w: the wisdom line naming the file, the import's 1, no STOP; a
failed import STOPs with exit status 0, so rc 0 is not enough). Their LOGIC is 2 and their fingerprints carry the pins;
deliver's LOGIC is 3 and `RUN_MANIFEST.json` gains `fftw`. `lp_fftw.py` holds the checks (`facts`, `check`, `gen`,
`logs`). topo's G3a.13 and coarse's notes say that topozero's and geo2rdr's counts come from a race (F61, F65). Every
Phase 0 to 2 file, invert, datum, fine, bgrid, Phases 4.5 to 6 but deliver and the six settings files are byte-identical
to v0.8; on a frame v0.8 processed, refine, igram and deliver read STALE and the other 24 CURRENT.

v0.8 settles D9 (MintPy's unwrapError) by a test of the products instead of a threshold (record 62.0 and 63.8). admit
takes `no`, MintPy's default, unless `recon/admission.txt` names the method; the mean component fraction it used to
threshold stays in its record as evidence (9 of the 12 v1.2 frames, and F3320, fell between v0.6's two anchors, so v0.7
stopped for the operator on most frames). The new phase **d9ab** (5dab), after sbas, runs MintPy with bridging on a
copy of `mintpy/`'s inputs and applies the rule registered before RD8: bridging if MintPy on the copy ends rc 0 with its
products, the copy's mask keeps at least MintPy's smallest component more pixels (1,536 on F3320's grid), and the
velocity's spread over the pixels both masks keep is no larger; otherwise no. A bridging verdict under the default is
a DECISION (the operator's `recon/admission.txt`), in either `--decide` mode. `RUN_MANIFEST.json` gains the reference's
latitude and longitude as numbers, the geocoded cell that holds it beside MintPy's rounded REF_Y, REF_X, D9's A/B, the
lead product (`Velocity_demErr_ramp`, record 73.2) and readings of the delivered GeoTIFFs (the reference's cell, rings
around it, and the GNSS stations' discs minus the reference's: PIMO). Every Phase 0 to 4 file, report, prep, mcfg, sbas,
accept, package and four settings files are byte-identical to v0.7; on a frame v0.7 processed, admit and deliver read
STALE (their LOGIC is 2) and d9ab NONE.

v0.7 adds the four phases of 5e and 6 (below), `linog_phase6.cfg` (their settings and pins) and
`linog_verify_frame_d6.py` (the pipeline's copy of the kit's verifier, D6). Every file of Phases 0 to 5 and the five
settings files are byte-identical to v0.6.1, so a frame processed by v0.6.1 keeps its 22 records CURRENT and v0.7
starts at wmask. The default `--to` is now `package`, and the run's header names both Pythons: the driver's (the
`--state` checks and the standard-library phases) and the env's (every phase in `lp_env.sh`).

v0.6 adds the five phases of Phase 4.5 and Phase 5 (below) and `linog_mintpy.cfg`, their settings and pins. The 26
files of Phases 0 to 4 (every `lp_*.py` of v0.5 but the self-test, `lp_env.sh` and the four cfgs) are byte-identical
to v0.5, so a frame processed by v0.5 keeps its 17 records CURRENT and v0.6 starts at the report. The default `--to`
is now `sbas`.

v0.6.1 fixes the report after S14, v0.6's dry run on felix, where 19 of 157 combined images failed (F49): the pair
arrays now get imshow's own first steps before `imsave` (the HSV image clipped to 0..1, NaN masked in the phase). It
also quiets the libraries' start-up lines that ISCE's logging.conf prints and writes into isce.log after `import isce`
(matplotlib's in the report, h5py's in prep, mcfg and sbas: F50), and install.sh runs its steps 4 to 6 from the record
folder. The report's LOGIC is 2. The other 31 files a frame's records depend on are byte-identical to v0.6: the 26 of
Phases 0 to 4 (with `lp_env.sh` and the four settings files), `lp_admit.py`, `lp_prep.py`, `lp_mcfg.py`, `lp_sbas.py`
and `linog_mintpy.cfg`.

## Use (on felix)

    linog_auto.sh <PATH> <FRAME> [--to PHASE] [--only PHASE] [--force PHASE] [--recover] [--decide ask|auto] [--dry-run DIR]
    linog_auto.sh --selftest DIR

Frame folder: `<root>/p<PATH, 3 digits>/f<FRAME, 4 digits>`, e.g. `insar/p084/f3320`. Default `--to rerun`
(v0.7 to v0.10: `package`; v0.6: `sbas`; v0.5: `igram`; v0.3: `stack2`), `--decide ask`. v0.13: the record folder for an ascending
frame is the same (`insar/p447/f0310`); a test root by `LINOG_ROOT` (the root's owner must be the caller unless
`LINOG_ROOT` names it).

| phase | index | what it does | writes |
|:--|:--|:--|:--|
| recon | 0a | reads the archive (zip directory, summary.txt, 732 B of IMG-HH), gates G0.1-G0.15 and G1; v0.13: any path (R8: the table's entry or a derived one), G0.16 (the along-track framing), G0.17, G0.18, G0.4d (R7's decision), the root's owner | recon/RECON.json, recon/RECON.md; v0.13: recon/path_entry.cfg |
| stage | 0b | frame skeleton, DEM links, raw/ links of the kept granules | p<PATH>/LINEAGE.txt, raw/, DEM/, data -> raw |
| extract | 1a | each kept zip, flat by member name, CRC checked (Python zipfile; felix has no unzip); v0.13: the FBS+FBD and FBD-only branches (R6, R6-d) | unzipped/<zip stem>/ |
| unpack | 1b | the LInOG unpacker by absolute path (md5 pinned, G2), straight into SLC/<date>/; v0.13: the package's own copy, the env gate on its prefix too | SLC/<date>/, status/P1b_unpack.progress |
| rwin | 1br | each shelve's r0 = column 0 by its CEOS image records, where they differ from the leader by whole gates (F26); v0.13: FBD dates too, each date's sampling rate recorded (18.4) | SLC/<date>/data.* of those dates; _archive/rwin_<UTC>/ |
| bandlimit | 1bs | v0.13 (R6-a): the FBS dates of an FBS+FBD frame band-limited in place by the course kit's linog_fbs_bandlimit.py at its pins (linog_mixed.cfg), each date's spectrum read before and after; N/A on FBS-only and FBD-only frames | SLC/<date>/<date>.slc (the .prefilter kept beside it), status/P1bs_bandlimit.progress |
| verify | 1c | every shelve: G3, G6, G3b (orbit vz), G5, r0 grid, PRF; v0.13: G4 (the polarisation of an FBD date, linog_pol_gate.py ported), G1c.8; the kit's two checks | recon/modes.json (each date's mode) |
| stack1 | 2a | stackStripMap.py pass 1 (no reference) in a folder of its own; the kit's net table on it; thin nodes | stack/pass1.vN/, logs/stack/ |
| reference | 2b | D1, the reference rule, and two other rules on record; the operator's choice or D1's pick; G17; v0.13: D1 among the FBS dates of an FBS+FBD frame (D1c, D1f), R7's kept reference | recon/reference.json |
| stack2 | 2c | stackStripMap.py pass 2 with `-m <reference>`: a trial, checked, then in the frame; the water-mask strip; v0.13: 6 range looks on an FBD-only frame (18.5) | stack/pass2.vN/, configs/, run_files/, baselines/, pairs.pdf |
| topo | 3a | run_01: topo on the reference; the geometry's sizes; hgt.rdr fill (E62); v0.13: G3a.14, the reference against simamp.rdr (Gap 2b) | merged/geom_reference/, geom_reference/ |
| coarse | 3b | run_02 and run_03 (geo2rdr, coarse resampling); the kit's G21 and G7 v4; v0.13: R7's D2 take of the dates they name (limits L0 to L8, a restart), the products reused by 11.5's rule (G3b.6), G3b.11, G3b.12, G21e | offsets/, coregSLC/Coarse/; v0.13: recon/d2_decision.json, _archive/d2_<UTC>/ (MOVES.txt) |
| refine | 4a | run_04: the pairs' offsets; F15; G8 from the shelves (and the kit's census) | refineSecondaryTiming/pairs/ |
| invert | 4b | run_05: invertMisreg; "Design matrix is full rank."; the earliest date at 0 and 0 | refineSecondaryTiming/dates/ |
| datum | 4c | G16: the kit's rebase onto the reference (dry run, own plan, backup, --apply, check); G9; v0.13: R9 on an FBS+FBD frame (each date in its own units, the reference pinned), a reading elsewhere | dates/ rewritten, dates_predatum_bak_<UTC>/ |
| fine | 4d | run_06: the reference copy and fine resampling; the copy's size (A16); the kit's G10 v2; v0.13: G10 v3 and G10m as readings | merged/SLC/ |
| bgrid | 4e | run_07: the baseline grid of every date | merged/baselines/ |
| igram | 4f | G17 again (v0.13: the .xml's FILE_NAME); run_08: crossmul, filter, unwrap per pair; the six products' sizes; G11 and the per-date view; v0.13: G11's classes from recon/modes.json, G11m | Igrams/ |
| report | 4g | the interferogram report, the kit's rendering, north up from the frame's lat.rdr and lon.rdr (D4, F36) | Igrams/reports/ |
| admit | 5a | the kit's G18 and G20 (linog_admit.py); v0.10: D3 by the rules R1 to R3 over land; D9, unwrapError no unless the operator or R5 names it; v0.13: R3 counts R7's dates (G5a.8) | recon/admission.json |
| prep | 5b | MintPy's prep_isce.py from the frame, the metadata file named with .dat (F40); G12, N13, N20; F21 | the .rsc files |
| mcfg | 5c | the template from MintPy's own defaults file, the values of linog_mintpy.cfg and admit's; the bootstrap load_data; SNWE | mintpy/smallbaselineApp.cfg |
| sbas | 5d | load_data to modify_network; the kit's G19 pick into reference.yx; reference_point to geocode; G15, G24, N14 | mintpy/ |
| drop1 | 5d1 | v0.12: each flagged pair of the network against its 10 nearest unflagged peers in mean land coherence: ifgram_inversion.py on a copy of the stack without the pair; culled when it gains more coherent land than every peer, with 10 peers or more (r2); R2's guards on the cull; under --decide auto the cull taken (the frame restarted from admit) | drop1/<UTC>/ (drop1.json, drop1.tsv, tests/<pair>/); when the cull is taken, recon/drop1_decision.json, status/restart.json and mintpy/ moved into _archive/mintpy_predrop1_<UTC>/ |
| d9ab | 5dab | D9's A/B (v0.8): MintPy with bridging on a copy B of mintpy/'s inputs, compared with sbas's products by the rule of record 62.0; v0.10, R5: a bridging verdict taken under --decide auto (the frame restarted once) | d9ab/<UTC>/ (ab.json, ab_pairs.tsv, ab_velocity.png, B/); R5: recon/d9ab_decision.json, status/restart.json, mintpy/ moved into _archive/mintpy_nobridging_<UTC>/ |
| wmask | 5e | the kit's linog_watermask.py --apply: the SRTM-flat water bodies (G22) and the swath-edge strips (G23) out of both masks | mintpy/watermask/, the two masks in place |
| dfit | 5f | v0.10, R4: each screened date on the velocity fit, MintPy's fit A against B without the date, over the water-masked maskTempCoh; v0.13 r3: the DEM-error loop (the fit's dates out of dem_error, MintPy's residual RMS rule again until it stops), then R4 with each candidate out of both fits | dfit/<UTC>/ (fit.json, the fits, demfit/pass<k>/, r4/<date>/, demfit2/pass<k>/), mintpy/exclude_date.txt when a date leaves the fit |
| deliver | 6a | the kit's linog_phase6.sh (v0.13 r3: the pipeline's linog_phase6_r3.sh, chain A's DEM-error fit without the fit's dates): the two demErr chains, the geocoded velocities, H/V, the 16 files; D5, D7, F55; v0.8's manifest fields and readings; v0.11: the KMZs' entries at 1980-01-01 00:00:00 (G6a.10) | mintpy/geo/LInOG_Upload_<TAG>/, RUN_MANIFEST.json |
| accept | 6b | the pipeline's copy of the kit's verifier on the frame (D6): FAIL 0 to pass; its WARN lines listed; v0.13 (LOGIC 2): N22 and G16 by R9's plan where datum ran R9, N22's factor by the modes' spacings | (its log and record only) |
| package | 6c | the review package by hard links, laid out as the 12 frames' staging, with its manifest (D8); v0.13: the prefix by the path's direction (LINOG_DESC, LINOG_ASC) | _xfer/<PREFIX>_<TAG>_<VERSION>_<date>_review/ |
| rerun | 6d | v0.11: the package against an earlier one of the frame (lp_compare.py's comparison): equal but RUN_MANIFEST.json PASS; another network INFO with the readings; the same network DECISION | (its log and record only) |

unpack, rwin, bandlimit, verify, Phases 2 to 6b and 6d run inside `lp_env.sh`: `env -i`, `conda.sh`, `conda activate linog_isce2`, then the
PYTHONPATH the operator's shell carries (`<isce>/components`, `<env>/share/isce2`, `<isce>`), because the
activation alone sets none of it and a shelve cannot be unpickled without it (RD2, 26 Sept 2026). The env, the
unpacker and the kit checks are pinned in `linog_env.cfg`.

## The range window, rwin (v0.5)

ISCE's ALOS_SLC reader, which the kit's unpacker uses, gives each shelve the leader's range gate delay as its
starting range, r0 = c/2 x delay, and reads the image records' "Slant range to 1st data sample" only when the delay is
missing; the SLC holds every sample of every record, left fill included. On some granules the records put column 0
one gate (1 us, 149.896229 m, 32 FBS samples) nearer or farther than the delay says: RD4 read 51 of the 779 archive
granules so, 8 of P084 F3320's 24 dates (the eight that G7 flagged), and RD5 showed that with r0 from the records
run_03 and G7 pass all 23 secondaries (record sections 38 to 40). The width does not show it (F27): the records do.
For every unpacked date rwin reads the IMG-HH file descriptor, its first, middle and last image records and the
leader with ISCE's own CEOS parser and record definitions (`isceobj/Sensor/CEOS.py`, `db/alos_slc/`), and:

    column 0 = (slant range to 1st data sample) - (left fill) x c / (2 x sampling rate)
    k = round((column 0 - r0_leader) / 149.896229 m);  column 0 - r0_leader - k x gate within 1 m
    r0 = r0_leader + k x gate      (k = 0: nothing to change)

- Only what RD4 measured is corrected: records without fill (none of the 779 granules has any, so the fill term is
  the CEOS reading, never seen on felix) and one gate (all 51 that differ). It FAILs, and writes nothing, on fill,
  on |k| > 1, on a file descriptor that disagrees with unpack's lines and width, on first, middle and last records
  that disagree (G1br.3, G1br.5), on a shelve r0 that is neither the leader's nor already the target (G1br.4: the
  shelve was made some other way), and on a difference that is not whole gates (G1br.5).
- Before a shelve is written, its files are copied into `<frame>/_archive/rwin_<UTC>/SLC/<date>/` with a
  `backup.md5` (G1br.6, md5s compared). Only the r0 in the `frame` key changes; the other keys are compared byte for
  byte (G1br.7). The write, its read-back and the record that names the date run with SIGINT, SIGTERM and SIGHUP
  deferred: their Python handlers are swapped for a recorder as well as blocked, because once ISCE's objects are
  unpickled numpy's OpenBLAS threads can take a signal sent to the process (the same holds for Phase 3's job starts
  and the datum's --apply, `lp_p3.Deferred`). The record names the date being written before the write, for a SIGKILL.
- G1br.8 reads every date back: r0 = the target within 1e-6 m and column 0 within 1 m. A date already at the records'
  r0 is left alone, so a re-run, or a run after a stop, writes nothing twice; its other keys are compared with the
  newest copy an earlier run made (WARN when there is none). rwin is STALE when a shelve differs from what it
  recorded (a date unpacked again, a shelve put back from its copy) and then corrects that date again.
- `--dry-run`: when the frame's unpack is PASS on record, rwin reads the frame's records and shelves (read-only) and
  prints the table and what it would change; otherwise it prints the plan only.
- verify needs rwin PASS on record, made from the same unpack record, with the shelves as rwin left them (G1c.1:
  `--only verify` after a shelve changed FAILs there), and checks r0 on the kit's gate grid as before (G1c.4): the
  corrected dates sit one grid step away from the others.
- On P084 F3320 the eight corrected shelves make verify, stack1, reference and stack2 re-run, and coarse; stack2 and
  coarse then find the v0.4 run's `configs/`, `run_files/`, `baselines/`, `pairs.pdf`, `offsets/` and `coregSLC/` in
  the way (DECISION) until they are moved into the frame's `_archive/`: a human step (S12, after Ariel confirms it).

## Phase 2 (v0.3)

`linog_stack.cfg` holds the pinned env's prefix (`ENV_PREFIX`), the md5s of `stackStripMap.py`, `Stack.py` and the
kit's `linog_net_table.py`, the 12 frames' stackStripMap settings (`-t 730 -b 1500 -a 28 -r 12 -u snaphu`) and the
D1 settings. `stackStripMap.py` is not on the clean env's PATH, so it is called by absolute path,
`<ENV_PREFIX>/share/isce2/stripmapStack/stackStripMap.py`, with its md5 checked first (F13).

- stack1 runs pass 1 without a reference into `stack/pass1.vN/` (a new folder each run), checks its log and folder
  (configs 2P + 4S + 2, 16 run files, S baseline files that agree with the log), runs the kit's net table on it
  (dates from a `phase1_dates.json` written from `recon/modes.json`, F11) and lists thin nodes (degree <= 3, F15).
  A network that stackStripMap reports as not connected stops with DECISION: wider thresholds or excluded dates
  are a human choice.
- reference applies D1 (record 7.4 with Q3): dates of degree >= max degree - 1, the earliest date excluded
  (invertMisreg pins it, N23), the modal width first, then the date nearest the temporal midpoint. The midpoint
  alone and the kit list's first entry are recorded beside it (D1b WARN when the three differ, F14). With
  `--decide ask` (the default) the phase stops with DECISION NEEDED and the candidate table until the operator
  writes `recon/reference.txt`; `--decide auto` takes D1's pick. G17 checks the reference SLC's width and lines in
  modes.json, the file size, `.slc.xml`, `.slc.vrt` and the shelve.
- stack2 runs pass 2 with `-m <reference>` first as a trial into `stack/pass2.vN/` and checks it there: the dates,
  the network, the counts, the baselines named `<reference>_*`, the fineResamp configs naming `SLC/<reference>`,
  and `config_reference_<reference>` (21 lines, topo at line 4, createWaterMask at line 15). Pass 2 computes the
  baselines against the reference and pass 1 against the first date, so their |dB| differ slightly (up to 0.343 m
  on P084 F3320): a pair within `PAIR_FLIP_M` (1 m) of `-b` may be in one network and not the other, which is
  listed with WARN; pass 2's network is the stack's. Any other difference FAILs, and the frame is not touched.
  Then the same command runs from the frame folder, and its files must be the trial's with the folder name
  changed; `config_reference_<reference>` is copied to `.bak_watermask` and keeps its first 14 lines (record 7.2).
  ISCE appends to `isce.log` in the frame (F16).

`recon/reference.txt`, one line that is not a comment:

    YYYYMMDD  <why>

It must be a date of the stack and not the earliest date. Changing it re-runs reference; stack2 then finds its
earlier `configs/`, `run_files/`, `baselines/` and `pairs.pdf` in the frame and stops with DECISION until they
are moved into the frame's `_archive/`. A reference phase that re-runs and names the same date leaves stack2
CURRENT. Files added beside stack2's (Phase 3's logs) leave it CURRENT; a file it wrote that changes makes it STALE.

## Phases 3 and 4 (v0.4)

Each phase runs its run files' lines as the kit's `parallel -j` does, from the frame folder (A30: the shelves and
`.xml` files carry relative names), with `<ENV_PREFIX>/share/isce2/stripmapStack` first on the PATH (F13) and
`OMP_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS` set together. Its own job pool starts each line as
`bash -c` in a session of its own, waits for it with `wait4` (exit code and peak memory per line), keeps each
line's log under `logs/p3/<phase>.vN/<run file>/` and writes `joblog.tsv` there (line, tag, rc, seconds, peak kB,
log bytes). A stopped run ends every line's process group; a phase killed outright (SIGKILL, the OOM killer) takes
its lines with it (each gets SIGTERM from the kernel, PR_SET_PDEATHSIG). Jobs at once = min(J, lines, MemAvailable / PEAK_KB)
(`linog_run.cfg`: run_08's crossmul holds about 7 GB per job, A25); a step that memory holds to fewer jobs than J
says so with WARN, and to none, with FAIL.

`linog_run.cfg` holds the md5s of the 11 isce2 scripts the run files name or `stripmapWrapper.py` imports, the md5s
of the kit's 9 Phase 3 and 4 scripts, J, OMP and PEAK_KB per run file, and the gate settings (G7's retry depth, G8's
thresholds, G11's coherence mark, topo's fill level). A script not at its pin FAILs the phase before anything runs.

- An exit code of 0 is not a result: every phase checks what its step wrote (sizes from the reference geometry,
  `.xml`, shelves readable), and the kit gates' verdict lines are read anchored at line start (B55).
- coarse stops with DECISION (D2) when G21 or G7 flags a date, in either decide mode: excluding a date, archiving it
  and regenerating the configuration is a human step in v0.4. When G7 finds fewer textured windows than its
  quorum, its survey runs once more at depth `G7_NCAND_RETRY` (depth only, no threshold changed); fewer again is a
  DECISION.
- datum rewrites `refineSecondaryTiming/dates/` in place, and the kit's tool is not idempotent. The phase checks that
  `recon/reference.json`, the fineResamp configs (where the kit reads the reference) and refine name the same date,
  applies only to `dates/` exactly as invert recorded it (md5s), computes the plan itself from invert's values and the
  modes in `recon/modes.json` (passed as `--fbs-dates`), FAILs before anything is rewritten when the plan's azimuth or
  range spread is above 5 px (G9p, the kit's G9 threshold), checks the tool's dry run against the plan, copies
  `dates/` into `dates_predatum_bak_<UTC>/` (md5s checked) and writes the copy's name into the record, then applies:
  the tool runs in a session of its own while the phase holds SIGINT, SIGTERM and SIGHUP, and the md5s of the
  rewritten `dates/` are on record before a held stop ends the phase. It checks every date against the plan within
  1e-6 and the reference at 0 and 0. A later run that finds `dates/` equal to its own complete apply, with the copy
  intact, checks it again and never applies twice; any other `dates/` that no longer matches invert's record (rebased
  by hand, or cut off by a SIGKILL) is a DECISION that names the copy to restore.
- igram lists a date none of whose pairs reaches `COH_MARK` with WARN, and FAILs when that date is the reference
  (the datum bug's signature).
- In the way: a phase whose outputs are already in the frame without a PASS record for them stops with DECISION and
  lists them, with the later phases' outputs; move them into the frame's `_archive/` and re-run.
- A phase is STALE when a file it recorded is gone or changed; files added beside them (MintPy's `.rsc` sidecars, a
  report under `Igrams/`) change nothing. The SLC identity covers only the files the unpacker writes and the ISCE
  steps read (`<date>.slc`, `.xml`, `.vrt`, the shelve's `data`, `data.dat`, `.dir`, `.bak`, `.db`): in Phases 3 and 4
  since v0.4, in Phase 2 and verify since v0.5 (F21), so MintPy's `SLC/<REF>/data.rsc` or a GDAL `.aux.xml` changes
  nothing; for today's folders the values are the ones v0.4 computed.
- The kit's gates run with their output written straight into their logs (the log exists even when a phase is
  killed); `LINOG_REG_NCAND` reaches G7 and G10 only on their retry.

v0.9: refine's and igram's jobs, and no others, get `WISDOM_FILE` = the pinned `fftw/wisdom_felix.wis` (`job_env`); an
operator's exported `WISDOM_FILE` never reaches them (`lp_env.sh` passes `LINOG_*` only). Before the jobs, G4a.4w and
G4f.4w FAIL when the file, the env's `lib/libfftw3f.so.3` (resolving to `FFTW_LIB_REL`), its version or a module is not
as `linog_fftw.cfg` pins it, when a module loads another libfftw3f, when the file does not import or leaves a problem
uncovered, or when a check without it covers one (it could not fail). After them, G4a.7w and G4f.8w FAIL on any job
whose log lacks the import (1 line for refine: ampcor's; 2 for igram: crossmul's and icu's), shows `length = 0`, another
file, a return value other than 1, or a STOP line, and when the wisdom file's md5 is no longer the one found before the
jobs (it is read again after them). A new FFTW build or another CPU asks for a new wisdom file:
`lp_fftw.py gen OUT.wis` on felix, then its md5 into `linog_fftw.cfg` (a new pipeline version).

The disk gates use the path table's `disk_gib_margin`. For P084 F3320 (24 dates, 157 pairs) Phases 3 and 4 write
about 139 GB (topo 7.75, run_03 95.1, run_06 33.1, Igrams about 3), from the rehearsal's sizes.

## Phases 4.5 and 5 (v0.6)

- **report (4g).** The kit's rendering (`linog_save_insar_images.py` 402141d9, `linog_create_grid.py` 025340aa): each
  pair's `filt_<pair>.int` at full resolution, the phase in jet and the phase with the magnitude (stretched between its
  1st and 99th percentiles) in HSV, one pixel per pixel at 600 dpi, then pages of 12 pairs, US Letter landscape at
  300 dpi, named as the kit names them. The kit flips every frame up-down, north up for the ascending frames it was
  written for and 180 degrees off for a descending one (F36). This phase takes the flip from the frame's own
  `geom_reference/lat.rdr` and `lon.rdr` (up-down when line 0 is south, left-right when column 0 is east) and FAILs
  when that disagrees with the path table's direction (D4). The pair images are written with matplotlib's `imsave`:
  identical to the kit's JPEGs where the kit's figure comes out at the grid's size, and exact where it loses a column
  or a line (about 5 % of sizes; 778 x 658 is exact either way, F45). Before `imsave`, each pair's two arrays get
  what imshow does to them first: the HSV image clipped to 0..1 and NaN masked in the phase (F49; with felix's numpy
  1.26 the stretch's top can come out one float32 step above 1, which imshow clips and `imsave` refuses). hsv_to_rgb
  gives a NaN hue no colour (in the kit's image too), so those pixels are set to NaN: white in the JPEG. After `import
  isce`, the root logger goes to WARNING in the report and in prep, mcfg and sbas (F50; the kit's `stackStripMap.py`
  sets matplotlib's logger to WARNING for the same lines).
- **admit (5a).** The kit's `linog_admit.py` (8cff02ed) from the frame, parsed (G20). D3: v0.10's rules decide it (the
  section below); v0.9 took the kit's whole-grid pair proposal under `--decide auto`, asked it under `ask` and always
  asked a proposed date. D9 (v0.8): `mintpy.unwrapError.method` is no,
  MintPy's default, unless `recon/admission.txt` names it (bridging takes a linear ramp); d9ab tests bridging after
  sbas. The mean component fraction of the kept pairs over the kit's G19 valid area (20 px in from each edge, the
  statistic `linog_refpix.py` prints, computed from the pairs' files) is recorded as evidence; v0.6's anchors on it
  (0.34 and 0.90) are gone. The decisions go into `recon/admission.json`.
- **prep (5b).** `prep_isce.py -m SLC/<REF>/data.dat -g geom_reference -b baselines -f "Igrams/*/filt_*.unw"
  --geom-files hgt.rdr lat.rdr lon.rdr los.rdr shadowMask.rdr incLocal.rdr` from the frame (the kit's ph_prep); one
  `.unw.rsc` per pair (N20), the six geometry `.rsc` (N13), `data.rsc` with STARTING_RANGE, HEADING and POLARIZATION HH
  (G12); rwin, verify and stack2 still CURRENT beside the new `data.rsc` (F21).
- **mcfg (5c).** The template is written from MintPy's own defaults file (pinned by md5: 350 lines, 119 keys, every
  comment kept), with the values of `linog_mintpy.cfg` (the keys the 12 delivered cfgs set alike, F40 to F44 applied;
  paths as `{W}` and `{REF}`), admit's decisions, `reference.yx` auto and, in a marked block at the end,
  `ORBIT_DIRECTION` from the path table (load_data writes MACRO_CASE template keys into the stack: G24). Checked: each
  key once, each value on its line, every path under the frame and there (the three globs one file per pair), no
  other frame named, `mintpy.load.autoPath` auto or no. Then the kit's bootstrap `smallbaselineApp.py
  smallbaselineApp.cfg --dostep load_data` from `mintpy/`, the stack's HEADING and ORBIT_DIRECTION (G24c), and SNWE
  from `inputs/geometryRadar.h5`, snapped outward on the 1/1200 deg lattice with a 2 px margin (the kit's ph_pin).
- **sbas (5d).** `--dostep load_data`, then `--dostep modify_network` (one step a call, so MintPy plots nothing yet;
  updateMode no: the stack rewritten, G15), the stack's direction (G24) and pairs (kept = admit's), the kit's
  `linog_refpix.py` (cf7e059d, `--edge 20`) and its pick on `mintpy.reference.yx` (G19), then `--start reference_point
  --end geocode`, after which MintPy plots into `pic/` as the kit's second pass did: one inversion, where the kit's
  driver inverts twice. `recon/refpix.txt` takes the place of the kit's pick. The pixel must be unwrapped in every
  kept pair (MintPy's `maskConnComp.h5`; its reference_point refuses any other): when the kit's is not, G19 asks
  (DECISION), and says so when no pixel is unwrapped in every kept pair (then pairs have to go, in
  `recon/admission.txt`). An error in MintPy's plots after the last step is a WARN. The products: `timeseries.h5` with REF_Y and REF_X the pick, `temporalCoherence.h5`,
  `maskTempCoh.h5`, `timeseries_ramp_demErr.h5`, `velocity.h5`, and in `geo/` `geo_velocity.h5`,
  `geo_temporalCoherence.h5`, `geo_maskTempCoh.h5` and `geo_geometryRadar.h5` (N14); `unwrapPhase_bridging` in the
  stack exactly when bridging is set. MintPy's log lines "No input metadata file found" and "prep_isce.py failed"
  FAIL the phase (F40).

Each MintPy call and each kit tool writes its output straight into a log under `logs/p5/<phase>/`, with the command
first and the exit code last. mcfg owns the template only: its record keeps a digest of the template that leaves
`reference.yx` out (the one line sbas sets), so a hand edit of any other line makes mcfg and sbas STALE, and a hand
edit of `reference.yx` makes sbas STALE (`recon/refpix.txt` is the way to choose the pixel). mcfg and sbas take what
they read from admit and prep by content (admit's decisions, the `.rsc` files' bytes), so a re-run of either that
comes to the same leaves them CURRENT; a new MintPy version or defaults file makes prep, mcfg and sbas STALE. sbas's listing leaves out the files the water-mask phase and Phase 6 rewrite (v0.7).
A dry run renders the report, runs admit and writes the template (no load) under the dry-run folder, and prints the
plans of prep and sbas; on a frame whose igram has not run, each of them is a plan only.

## admit's rules, R5 and dfit (v0.10)

Record 108.3, approved in 109.0; `linog_mintpy.cfg` holds the settings.
- **R1, the kit over land (admit, G5a.6, G5a.7, R1).** The water: `flat_masks()` of the kit's `linog_watermask.py` (at its
  pin in `linog_phase6.cfg`) on `geom_reference/hgt.rdr` (|h| over 1e5 m read as no height): a 5 x 5 standard deviation
  under 1 cm, dilated, then a 3 x 3 opening; water = its two masks; land = the finite heights off the water. The kit's
  `conc()` and `flat_masks()` are taken from the pinned files' own source text, and its thresholds (LARGEST under 0.20 or
  R under 0.25 flags a pair; the date screen at 3.0x the frame's median peak) from its argparse defaults. admit first
  computes every pair over the whole grid and must print the kit's own lines, line for line (G5a.7: else FAIL), then
  computes them over land: coherence and LARGEST over the land's pixels, R and the spectral peak with the phasors off the
  land set to 0. With fewer than `ADMIT_LAND_MIN_PX` (50,000) land pixels no pair is flagged and no date screened (WARN).
- **R3, dead and thin dates (R3).** A date with fewer than 2 pairs in the network as it stands leaves (all such at once);
  a date with more than `ADMIT_DEAD_SHARE` (0.5) of its pairs flagged leaves, one at a time (the highest share, then the
  most flagged, then the earliest), the network read again after each, until none is left. It holds when the rest keeps
  min_dates (the path table) in one component, every date in 2 pairs or more, at most `ADMIT_EXCL_MAX_FRAC` (25 %) of the
  dates excluded, and D1's reference date; otherwise a DECISION in either `--decide` mode.
- **R2, the cull cap (R2).** On the network R3 leaves, the flagged pairs are culled whole when they are
  `ADMIT_CULL_MAX_FRAC` (10 %) of its pairs or fewer and the network left is one component with every date in 2 pairs or
  more; otherwise none is culled (WARN: MintPy's per-pixel masks stand in for it). v0.12: R2 culls nothing by itself; the
  flagged pairs (land and grid) go to drop1, whose cull these guards bound (below).
- **D3.** `--decide auto` takes the rules' excludeDate and excludeDate12 (INFO), `ask` asks them (DECISION) when there are
  any; `recon/admission.txt` takes their place (INFO), with the rules' result recorded beside it, "agree" or "DIFFER".
  On F3310, RD10's land flags give 2 of 153 pairs (1.3 %), the two S31's `recon/admission.txt` names; on F3320, none.
- **R4, the phase dfit (5f, after wmask).** The dates the screen proposes over land stay in the network. dfit runs
  `timeseries2velocity.py` on `mintpy/timeseries_ramp_demErr.h5` with MintPy's own exclusions (A; it must equal
  `mintpy/velocity.h5`, G5f.6, else WARN) and, for each candidate, with the date excluded too (B); the date leaves the fit
  when B's velocity std over the water-masked `maskTempCoh.h5` is lower than A's (R4.N). Then `mintpy/exclude_date.txt`
  is made to hold the fit's dates, the union of MintPy's and the dates taken (G5f.7): left when it does, written when it
  does not (the earlier file kept in `dfit/<UTC>/` as `exclude_date_before.txt`), and, when no date is out of the fit and
  an earlier run of dfit wrote it, moved there. dfit tells MintPy's dates from its own by its record (the file's md5 as
  it last left or found it). `linog_phase6.sh` fits the three velocities without them and keeps them away from the demErr
  chains (v0.13 r3: `linog_phase6_r3.sh` fits chain A's DEM error without them too; the kit's script, until r2, by its lines 13 and 18, which move the file to `mintpy/_exclude_date.hold` and back: a held file left by a stopped
  deliver is a DECISION in dfit, G5f.4h, and a FAIL in deliver, G6a.1f, until it is put back). A runs on every frame, so the
  fit's machinery is checked on each. R4 applies under both `--decide` modes: it changes the fit's dates only, not the
  network, the time series or the demErr. deliver asks for dfit's PASS and the file as dfit left it (G6a.1f);
  `RUN_MANIFEST.json` gains `velocity_fit` and `decisions.d3.rules`.
- **R5, d9ab's bridging under auto.** When the A/B reads bridging and the operator named no method, d9ab under
  `--decide auto`, in a run of the driver without `--only` (`LINOG_RESTART=allowed`), writes `recon/d9ab_decision.json`
  (the method, the A/B, the network admit kept), moves `mintpy/` into `_archive/mintpy_nobridging_<UTC>/` (a rename) and
  asks a restart (`status/restart.json`). The driver runs the frame again from the top once: admit takes bridging from
  the decision file, mcfg and sbas run again, d9ab reads bridging as chosen. After the restart the driver sets
  `LINOG_RESTART=no` for d9ab (v0.12: for the phase that asked; each asking phase may restart the run once), so a second
  bridging verdict in the same run is a DECISION (and a second request all the same stops the run, rc 4); under `ask`, or
  with `--only`, the verdict stays a DECISION. `recon/admission.txt` naming a method
  overrides it. The move takes `mintpy/` as it is: on a frame d9ab runs again after wmask, dfit or deliver, their files in
  `mintpy/` go with it (nothing is deleted).

## drop1, the peer test (v0.12)

Record 124.7 (the plan), Ariel's word on its four choices in 125.0; `linog_mintpy.cfg` holds `DROP1_PEERS` (10),
`DROP1_MIN_PEERS` (10; r2, record 127), `DROP1_TCOH_MIN` (0.70), `DROP1_WORKERS` (8), `DROP1_TIMEOUT_S` (1800) and
`DROP1_FREE_GIB` (10) [CONFIRM WITH PL: the 10 peers and the minimum of 10].
- **The pairs tested.** admit's handoff (`recon/admission.json`, `decisions.drop1`): every pair R1 flags over land or over
  the whole grid; under R1's land floor, none (drop1 D1f WARN: the measure needs land). Those in the network sbas inverted
  are tested, each one whose drop alone keeps the network one component with every date in 2 pairs or more; the others
  are recorded as not testable, and kept.
- **The peers.** For each, the 10 unflagged pairs of the network nearest it in mean coherence over R1's land (the stack's
  coherence; ties to the earlier name), each one whose drop alone keeps the network as above. Peers are shared, and each
  pair is inverted once.
- **The inversions.** For each test, `drop1/<UTC>/tests/<pair>/`: a copy of `mintpy/inputs/ifgramStack.h5` with that
  pair's `dropIfgram` off, with copies of the files MintPy 1.6.2's inversion reads around a stack placed as sbas's
  inversion had them (r2, record 127, from the published source): `avgSpatialCoh.h5` one folder above the stack copy
  (`../avgSpatialCoh.h5`; a cell at 0 there is not inverted) and, when the frame has one, `mintpy/waterMask.h5` in the
  test's folder (the template's `waterMaskFile` auto reads `waterMask.h5` in the working folder; MintPy's
  modify_network writes it when `geometryRadar.h5` holds a waterMask). The inversion opens neither `geometryRadar.h5`
  nor `maskConnComp.h5`, so r2 copies neither (r1 did). Then
  `ifgram_inversion.py <copy> -t <a copy of the frame's template>` run there (E1's form), `DROP1_WORKERS` at a time with
  the cores shared among them, each stopped after `DROP1_TIMEOUT_S` (and sent SIGTERM if its job dies). The copies are
  removed when the inversion ends and `timeseries.h5` once read; `temporalCoherence.h5`, `numInvIfgram.h5`, the log and
  `result.json` stay. A stopped run's scratch (copies, time series, `base.npz`) is removed by the next run (G5d1.4c). The
  zero test runs the same with no pair dropped: this phase's inversion against sbas's, the measure's noise floor (D1z WARN
  when the cells it changes reach the closest decision's margin). A test completed on the same inputs (sbas's files, the
  template, the network, the pair, the threshold, R1's land, MintPy's pins, the files copied beside the stack) is read
  again, not run again, so a run stopped or failed part way loses only its unfinished tests.
- **The measure (E1's).** Coherent land: temporal coherence of `DROP1_TCOH_MIN` or more on R1's land. A test's net is the
  coherent land cells it gains minus those it loses against sbas's `mintpy/temporalCoherence.h5`; p99 and max of |dv| (a
  line through each `timeseries.h5`, mm/yr) on land coherent in both, and the cells beyond 1 mm/yr, are recorded, not used.
- **The rule.** A flagged pair is culled when its net exceeds every one of its peers' and it was tested against
  `DROP1_MIN_PEERS` peers or more (r2). With n peers an ordinary pair exceeds all of them one time in n + 1, so the
  minimum of 10 holds the false cull at the 1 in 11 the 10 peers give (record 120.5); a small network gives fewer testable
  peers, and its flagged pairs are then kept (D1r "n peers, under the 10"). A pair with no peer is kept. The cull is
  taken whole when it is `ADMIT_CULL_MAX_FRAC` (10 %) of the network's pairs or fewer and leaves one component with every
  date in 2 pairs or more; otherwise none is culled (R2c WARN). F3320's dry run gives its flagged pair 10 peers, and
  F3310's network of 153 pairs should give each of its flagged pairs 10 as well, so the minimum should change nothing on
  either.
- **The decision.** The cull in place (D1c): admit applied `recon/drop1_decision.json` and the file's network after the
  cull, interferograms and basis are this run's; or, `recon/admission.txt` deciding D3, a completed run of drop1 took a
  cull on this basis and these interferograms that leaves this network (the operator wrote it in): PASS, nothing run
  again. `recon/admission.txt` naming the exclusions otherwise: the test runs, its cull recorded, not applied (Doc JD). A
  cull under `--decide auto` in a run of the driver without `--only`: `recon/drop1_decision.json` (the cull; the network,
  interferograms' digest and basis it was taken on, and the network after it; the table, the zero test, the guards; an
  earlier one moved into `_archive/`), `mintpy/` moved into `_archive/mintpy_predrop1_<UTC>/` (a rename) and
  `status/restart.json`, with the stop signals held until all three are done; the driver runs the frame again from the
  top, admit takes the cull from the file (D1d INFO; in its fingerprint), mcfg and sbas run again, and drop1 reads the
  cull as in place. Otherwise (`ask`, or `auto` with `--only`) a DECISION: write the cull into `recon/admission.txt`
  (`mintpy.network.excludeDate12`, and `excludeDate` as admit decided it), move `mintpy/` into `_archive/`, and run again.
  A dry run says what a run would do: under `auto` INFO naming the cull, under `ask` the DECISION.
- **A decision not applied.** admit applies the file only when it was taken on the network the rules leave now, on the
  same interferograms and on the same basis (the flagged pairs, R1's land floor, `DROP1_PEERS`, `DROP1_MIN_PEERS`,
  `DROP1_TCOH_MIN`, `ADMIT_CULL_MAX_FRAC`; admit reads the file again when drop1's settings change). Otherwise D1d WARN (INFO when the
  operator's file or R3's limits decide; FAIL when the file is unreadable): the network goes back to the rules', mcfg stops
  at G5c.4 until `mintpy/` is moved into `_archive/`, and drop1 tests again; a new cull replaces the file (the old one into
  `_archive/`).
- **deliver** asks drop1 PASS on record (G6a.1d): a DECISION or FAIL holds the delivery, and so does a cull taken whose
  restart has not run.
- **drop1 before d9ab.** In one run drop1 decides first, on sbas's products under the unwrapError method admit decided,
  then d9ab's A/B runs on the network drop1 leaves. A cull taken after bridging changes the network, so R5's decision no
  longer applies (D9 WARN) and d9ab tests again (a second run may be needed). A cull in place is not tested again when
  the method changes later: its basis does not hold the method.
- **drop1's own fingerprint** holds sbas's files, admit's decisions and network, the handoff, igram's digest, the
  settings, MintPy's pins, the decision file, whether the operator's file decides D3 and (r2) the md5s of
  `mintpy/avgSpatialCoh.h5` and `mintpy/waterMask.h5`, which sbas's listing leaves out; a change to any of them runs it
  again, and its tests are read again where their inputs are the same.
- **Cost.** E1 took 1 min 34 s for one inversion on F3320 (record 119.3). F3320: 12 inversions (its one flag, 10 peers, the
  zero test); F3310: its 46 to 48 flags and their peers' union [VERIFY on felix]. Free space: `DROP1_WORKERS` stack copies
  and time series at once, the tests' files, plus `DROP1_FREE_GIB`.

## The path runner, linog_path.sh (v0.10)

    linog_path.sh <PATH> [FRAME ...] [--decide ask|auto] [--to PHASE] [--dry-run DIR]

The frames of one path, one after another, each through `linog_auto.sh`; with no frame, the frames the path table
lists for the path (its `expect_<frame>` keys), a delivered one among them run again in place as `linog_auto.sh` runs it
(P084: F3290 to F3330, with F3310 and F3320 delivered): name the frames to run. With no `--decide`, `linog_auto.sh`'s
default, ask. A frame that stops does not stop the next: each keeps its tree for its own resume. `--to` and the frames
are checked before any frame starts, and a dry-run folder inside or around `<root>/p<PATH>/` is refused. Records: `runner.tsv` (frame, start, rc, seconds, the driver's last line) and `frame_<FRAME>.log` in
`<root>/p<PATH>/_path_runs/<UTC>_<pid>/`, or in DIR for a dry run (each frame's dry run under `DIR/p<PATH>_f<FRAME>/`).
Exit 0 when every frame ended rc 0, 5 when one did not, 130, 143 or 129 when a signal stopped it (no frame starts after
it), 3 for a usage error or the wrong host.

## D9's A/B, d9ab (v0.8)

After sbas and before wmask, from the frame's `mintpy/` (A, read only; its mask sbas's, `mintpy/watermask/maskTempCoh.orig.h5`
once wmask has written the water mask). When admit's method is bridging (the operator's), A is the bridging run and the
A/B is not run (D9m INFO). Otherwise:
- **the copy B**, `d9ab/<UTC>/B/mintpy/` (in a dry run under the dry-run folder): `inputs/ifgramStack.h5`,
  `inputs/geometryRadar.h5`, `smallbaselineApp.cfg`, `avgSpatialCoh.h5` and `maskConnComp.h5`, each checked by md5, and
  in B's template `mintpy.unwrapError.method = bridging`, `mintpy.unwrapError.ramp = linear`, `mintpy.plot = no`: three
  lines differ from A's (G5dab.6). A new A/B asks for twice the copy's size plus `D9AB_FREE_GIB` (2 GiB) free (G5dab.5);
  B was 1.299 GiB on F3320, twice its 0.646 GiB copy.
- **MintPy on B**: `nice -n 10 smallbaselineApp.py smallbaselineApp.cfg --start correct_unwrap_error --end geocode` from
  B, in a session of its own (a stop of the phase ends it), stopped after `D9AB_TIMEOUT_S` (3600 s; RD8 took 160 s).
  Not rc 0 through its 12 steps: G5dab.7 WARN, and the rule reads no by its first condition.
- **the comparison**, RD8's `rd8_ab.py` in the phase: the pairs bridging changed and the pixels it moved; T_int
  (MintPy's arithmetic, RD7's function) before and after over the kit's valid area, inside and outside A's mask and
  over the moved pixels, and where T_int is high (the DEM there: F56's water); the masks, the temporal coherence, the
  velocity's spread in each run's mask and in both, its change B - A; `ab.json`, `ab_pairs.tsv` and `ab_velocity.png`
  (north up) in `d9ab/<UTC>/`. The frame's `mintpy/` is listed before and after: unchanged (G5dab.9).
- **the rule** (record 62.0): bridging if and only if MintPy on B ends rc 0 with `unwrapPhase_bridging` and its three
  products, B's mask keeps at least ceil(min(`D9AB_MIN_GAIN_CAP`, `D9AB_MIN_GAIN_FRAC` x length x width)) px more than
  A's (MintPy's smallest component on the grid, 2500 and 0.003: 1,536 px on 658 x 778), and the velocity std over the
  pixels both masks keep is no larger in B; otherwise no.
- **the decision** (D9ab, record 63.8): no PASSes; bridging when the operator chose no in `recon/admission.txt` is INFO
  (the operator's no stands); bridging under MintPy's default is a DECISION under `--decide ask`, and (v0.10) R5's to take
  under `auto` in a run without `--only` (above), a DECISION otherwise. The note says
  what to do: `mintpy.unwrapError.method = no` in `recon/admission.txt` keeps the products (the next run reads the same
  A/B again and passes in seconds), `= bridging` makes admit take it and mcfg stop at G5c.4 until `mintpy/` is moved
  into `_archive/`, after which mcfg and sbas run again with bridging (prep's outputs do not depend on admit).
An A/B completed on the same inputs (its `ab.json`'s key: sbas's files as recorded, A's mask and template, the rule's
settings, MintPy's pins; not the time limit) is read again, not run again. Completed means A unchanged while MintPy ran
on B, and MintPy at rc 0 through its steps within the time limit: a failed or timed-out A/B is made again the next time
d9ab runs, and one during which the frame's `mintpy/` changed is void (G5dab.9 FAIL). B stays as evidence. The fingerprint holds sbas's digest, admit's
decisions and D9's source, so a changed choice in `recon/admission.txt` runs d9ab again (and reads its A/B again).
wmask asks for d9ab's PASS (G5e.1d), and deliver's fingerprint holds d9ab's decision, which `RUN_MANIFEST.json` carries.

## Phases 5e and 6 (v0.7)

The kit's tools run from `$S` unchanged (design D-B), at the md5s `linog_phase6.cfg` pins: `linog_watermask.py`
907cf856, `linog_phase6.sh` 43d6c15b, `linog_los2hv.py` ada17e14, `linog_embed_stats.py` c35e935a,
`linog_gen_interactive_kmz.py` 45dc2d01, and the verifier `linog_verify_frame.py` 7f2b53cf, of which the pipeline
runs its own copy.

- **wmask (5e).** `linog_watermask.py <frame> --apply`, after sbas (the last MintPy call that writes the masks) and
  before deliver. The tool masks the valid pixels on SRTM-flat water whose amplitude is within 6 dB of the water's own
  (G22: the Goldstein filter spreads land phase 2 to 3 km into water, N60) and the dark strips along the grid's edges
  (G23), backs both masks up to `mintpy/watermask/*.orig.h5`, writes `maskTempCoh.h5` and, 1 s later,
  `geo/geo_maskTempCoh.h5` (so deliver's geocode `--update` keeps it), and `summary.json` last. The phase parses every
  line the tool prints (v0.8: after d9ab's PASS, G5e.1d), checks the reference pixel kept and equal to sbas's, `summary.json` (rule v2, the tool's md5,
  both masks' md5), the attribute in both masks, and sbas's six files unchanged. The `--apply` runs in a session of its
  own with the stop signals held, as the datum's does: a stop lands after the tool has ended and the masks are whole. A
  dry run runs the tool's own dry run (`--outdir DIR/mintpy/watermask_dryrun`) when the frame's sbas is PASS. The masks
  carrying the attribute with no record of this phase, or `mintpy/watermask/` there, is a DECISION (the originals are
  beside them).
- **deliver (6a).** Before the script: los.rdr's heading within `LOS_HEADING_TOL_DEG` (3 deg) of the stack's HEADING and
  its incidence within `LOS_INCIDENCE_TOL_DEG` of `inputs/geometryRadar.h5`'s, los.rdr's scheme BSQ (D7c: a misread
  los.rdr would label the delivery wrongly), and the ramp-first copies the script keeps, when there, whole HDF5 files
  (G6a.5r). `bash $S/linog_phase6.sh <PATH> <FRAME> <REF>` (v0.13 r3: `bash <pipeline>/linog_phase6_r3.sh <PATH> <FRAME>
  <REF>` with `LINOG_KIT_DIR` the kit's folder) with `LINOG_ROOT` the path table's root, in a session of its
  own (a stop of the phase ends the script and the MintPy steps under it); REF is `recon/reference.json`'s date, equal
  to the reference record's. The script's 12 steps (1 to 11 and 8b), rc 0 and
  `PHASE 6 COMPLETE`; then the two masks and sbas's files as they were recorded (G6a.8: a geocode that rewrote
  `geo_maskTempCoh.h5` would drop the water mask from the delivery), the 16 names and nothing else at the top with no
  `.aux.xml` (N6), NoData nan and STATISTICS_MEAN in the six GeoTIFFs (N44), the demErr GeoTIFF's valid cells equal to
  `geo_maskTempCoh.h5`'s (G22d), one colour range in the script's save_kmz.py and view.py lines (G14). Then this phase: **D5** hard-links the report's pages into `reports/` (the top stays
  at 16); **D7** labels the four H/V files from `geom_reference/los.rdr` (the direction, the bearing toward the
  satellite along ground range, the look azimuth; `linog_los2hv.py` writes "look azimuth ~78 deg" and "Single
  ascending track": F37); **F55** writes `RUN_MANIFEST.json` at the frame root: the dates, the decisions (the reference,
  D3, D9, the reference pixel, the operator's files with their `#` notes), the template's values as MintPy ran them,
  the water mask's summary, both headings with their sources (MintPy's HEADING from the orbit, and los.rdr's), the look
  geometry, the conventions (m/yr in the GeoTIFFs, cm/yr in the renders; LOS positive toward the satellite; the H/V
  files projections, not a decomposition), the delivery's files with their sizes and md5s, the tools' md5s and every
  record's verdict. v0.8 adds: the reference's latitude and longitude as numbers, `geo_cell` (the cell that holds the
  reference: the floor of its fractional index from the grid's corner) beside `geo_cell_mintpy` (MintPy's geocoded
  REF_Y, REF_X, the rounded index; on F3320 (582, 97) and (583, 98)), each with its centre's distance; D9's A/B from
  d9ab's record; `lead_product` (`LEAD_PRODUCT`, its Vertical and Horizontal GeoTIFFs, `LEAD_REASON`); and `readings`
  of the delivered GeoTIFFs, in mm/yr (G6a.9, INFO: readings, not a gate): the value in the reference's cell, rings
  around the reference between the `READ_RINGS_KM` edges and the whole frame in the `READ_RING_PRODUCTS` (cells, median,
  mean, 10th and 90th percentiles), and for each station of `GNSS_STATIONS` the median of each `READ_DISCS_KM` disc
  around it minus that around the reference in the `READ_DISC_PRODUCTS` (distances between cell centres,
  equirectangular, S20's and the review's method). v0.9 adds `fftw`: for refine and igram, the wisdom file their jobs ran
  with, its md5, the library's md5 and version, the problems covered, the modules' md5s and the jobs whose logs show the
  import, from their records (null for a step run before v0.9, which planned its FFTs by timing them); deliver's LOGIC
  is 3. deliver's fingerprint holds the report's digest (D5 links its
  pages) and d9ab's decision: a report made again, or a changed D9, makes the delivery STALE. A dry run prints the plan
  and writes `DIR/RUN_MANIFEST.json` as it would be, with the readings of the frame's own delivery when it has one; on
  a frame whose sbas has not run, a plan only.
- **accept (6b).** `python3 -B linog_verify_frame_d6.py <frame>` from `logs/p6/accept/` (the verifier imports isce).
  The copy is the kit's verifier with one change (D6): N22 takes each date's mode from `recon/modes.json` and prints
  its source; on an FBS-only frame the kit's own rule (the folders of `raw_fbs_unpacked/`) classes every secondary FBD
  and FAILs N22 (F39). The phase checks the verifier's summary against its lines, N22's source and counts, no FAIL line,
  and the frame unchanged by the run; its WARN lines are listed (the kit: WARN does not fail). A dry run gives the
  verifier's baseline on the frame as it is. `lp_d6check.sh OUTDIR FRAME...` runs the kit's verifier and the copy on the
  same frames and compares their lines (v0.9's install.sh did so on the 12 delivered frames; v0.10's leaves it out, as
  the verifier copy and accept are unchanged).
- **package (6c).** `<frame>/_xfer/<PREFIX>_<TAG>_<VERSION>_<YYYYMMDD, UTC>_review/` (`LINOG_DESC`, `v0.1` in
  `linog_phase6.cfg`), laid out as the 12 frames' staging (chapter 9.4): `LInOG_Upload_<TAG>/` (the 16 files and
  `reports/`), `Igrams/` (the report's pair JPEGs, flat), `Igrams/reports/` (the pages), `RUN_MANIFEST.json`, and
  `TRANSFER_MANIFEST_<TAG>.txt` written last (`md5  ./path` for every other file, in byte order, not self-listed). Every
  payload file is a hard link of the file the records name (one filesystem; nothing copied); the package is checked
  with `md5sum -c` and its hash of hashes (`cut -c1-32 TRANSFER_MANIFEST_<TAG>.txt | LC_ALL=C sort | md5sum`) against
  the sources'. Each page in the delivery's `reports/` must be the report's own page (the same inode). A package of the
  same frame and version already under `_xfer/` is a DECISION.

A phase's outputs in the frame without a PASS record stop it with DECISION (move them into `<frame>/_archive/`). wmask,
deliver and package list their files; accept's fingerprint holds deliver's digest and package's holds deliver's, the
report's and accept's, and both read STALE when the delivery (or, for package, the report) is no longer as its phase
recorded it.

## The rerun check and lp_compare.py (v0.11)

- **The KMZs (deliver's G6a.10).** After N6, each of the four KMZs is made new in `logs/p6/deliver/kmz/` (the frame's
  filesystem, so a stop leaves nothing in the delivery) with every entry's DOS time and date at 1980-01-01 00:00:00,
  in the central directory and the local header (8 bytes an entry), and checked: only those bytes changed, zipfile's
  CRC test passes, every other field (name, order, compression, CRC-32, sizes, attributes, flags, extra field, comment,
  offset) as written. Only when all four pass are they moved over the originals (`os.replace`, the original's mode
  kept); a refusal (ZIP64, more than one disk, bytes after the archive, an extra field, which may carry another
  timestamp) or a failed check leaves all four as MintPy and the kit wrote them, and deliver FAILs. `RUN_MANIFEST.json`'s
  `delivery.kmz_times` holds the fixed time and, per KMZ, its entries' times as written (the run's). The kit's scripts
  and MintPy stay at their pins (`KIT_KMZ_MD5`, `KIT_PHASE6_MD5`, G6a.3).
- **rerun (6d).** After package, inside `lp_env.sh`. The reference: the package folder named on the first line of
  `recon/rerun_reference.txt` that is not a `#` comment (absolute, or relative to the frame folder); else the package
  of the frame's newest archived tree under `<root>/p<path>/_archive/f<frame>_*` (newest by the UTC stamp ending its
  name, as the run block names them: the one its `status/P6c_package.json` records, else its one `_xfer/*_review`; a
  tree with neither is passed over and named); else none, a first run (PASS, INFO). Then: both manifests by
  `md5sum -c` (G6d.3, FAIL when a line is not OK); the names both ways (G6d.4); the files by md5, the KMZs whose md5s
  differ by their entries (G6d.5); `RUN_MANIFEST.json`'s leaves that differ, listed, not judged (G6d.6); the network key
  of both `RUN_MANIFEST.json` (G6d.7: `dates.kept`, `decisions.d3.excludeDate12` and `excludeDate`, the reference date
  and pixel, D9's method, `velocity_fit.dates_out_of_fit`; `auto`, `no` and empty read as none; a field one manifest
  lacks is "not recorded", record 122.5); and for each GeoTIFF that differs, on the cells valid in both, NEW minus REF
  in mm/yr (G6d.8: the median, p01, p99, the shares beyond 1 and 5 mm/yr, the maximum, and the cells gained and lost).
  The verdict (G6d.9): every file equal but `RUN_MANIFEST.json`, PASS; files that differ on another network, or on one
  the two manifests do not record whole, INFO (PASS, the readings in the record); files that differ on the same
  network, DECISION, in either `--decide` mode: a product changed with nothing in the network to explain it. The
  DECISION's note gives the line that takes the change: `accept <the reference's folder name> <the new package's hash
  of hashes>`, written into `recon/rerun.txt` with a `#` line saying why; then `--only rerun`. The fingerprint holds
  the package's digest, the reference (its path and its manifest's md5), and both operator files' md5s. A dry run makes
  the same comparison on the frame's package as it is, its DECISION an INFO there.
- **lp_compare.py** (item 5; not a phase; run it with the env's python3: `bash lp_env.sh python3 -B lp_compare.py ...`).
  It only reads what it compares and writes only under `--out` (`compare_<command>.json` and `.txt`), and `split
  --run` also under `--scratch`; an `--out` inside a compared folder is refused. `packages NEW REF`: rerun's comparison
  of two packages. `shelves NEW_FRAME REF_FRAME [--dates ...]`: each date's `SLC/<date>/data` shelve key by key, byte
  for byte, then unpickled with the object ids left out (record 119.2, steps 3b and 3c-3; it needs `--out` and works there,
  since ISCE's classes may open isce.log in the working folder, and lp_env.sh's PYTHONPATH to unpickle them). `cycles NEW_FRAME REF_FRAME`: both
  `mintpy/inputs/ifgramStack.h5`, the pairs and dropIfgram, and per pair unwrapPhase NEW minus REF with its median offset
  removed: the median, p99 and share of cells beyond pi (a whole cycle). `split NEW_FRAME REF_FRAME (--cf DIR |
  --scratch DIR [--run])`: the velocity change split between the network and the rest (record 119.3): CF is NEW's stack
  inverted with REF's network, made by `ifgram_inversion.py` on a copy under `--scratch/cf/` (only with `--run`; the
  plan otherwise; `split.status` at the end) or made before (`--cf`); velocities by a linear fit to each
  `timeseries.h5`; network NEW - CF, the rest CF - REF, total NEW - REF, on every cell and on the cells both
  `maskTempCoh.orig.h5` (else `maskTempCoh.h5`) keep; temporal coherence at `minTempCoh` gained and lost, on land and
  water when `watermask/waterMask.h5` is there. Exit 0 when it ran, 2 when an input is missing or unreadable, 3 on an
  unexpected error.

## Records

- `status/P<index>_<phase>.json`: written at START (RUNNING) and at END (PASS, FAIL, DECISION, ERROR), with
  every gate's id, verdict, value and threshold, the input fingerprint and the tool md5s. rwin, verify and Phases 2
  to 4 write it again after every gate (F25), so a running phase's record shows the gates taken so far. A phase that
  raises ends its record ERROR with the traceback tail. Phases 3 and 4 first copy the previous record into
  `status/history/P<index>_<phase>.<its start>_<its pid>.json`.
- `logs/STATUS.txt`: `auto_run START id=...` and `auto_run END id=... rc=N` around each run (with
  `stopped in <phase>` when a signal stopped it); inside, `auto_<phase> START` and `auto_<phase> END rc=N`, as
  `linog_run.sh` writes them.
- `logs/auto_P<index>_<phase>.log.vN`: the phase's console, one version per run; `logs/unpack/<date>.log.vN`,
  `logs/verify/<check>.log.vN`, `logs/stack/stackcfg<1|2>.log.vN` and `logs/p3/<phase>.vN/`: the tools' own output.
- v0.10: `status/restart.json` (R5's request; the driver keeps it as `status/restart_<run>_<n>.json`, an earlier run's
  as `restart_stale_<run>.json`) and the ledger's `auto_run RESTART id=... after=<phase>` line;
  `recon/d9ab_decision.json`; `dfit/<UTC>/fit.json` with the fits' logs.
- v0.12: `drop1/<UTC>/` (`drop1.json`: the tests, the rule's table, the zero test, the cull, its guards, the network,
  interferograms and basis tested, the peers asked and the minimum, the files copied beside the stack with their md5s; `drop1.tsv`: one row a test, E1's columns; `tests/<pair>/`: `result.json`,
  `temporalCoherence.h5`, `numInvIfgram.h5`, `inv.log`, `job.json`); `recon/drop1_decision.json` when the cull is taken
  (the cull, what it was taken on, the network after it, the table, the zero test, the guards, where `mintpy/` went);
  `status/restart.json` may now be drop1's too (its `by`).
- v0.11: `status/P6d_rerun.json` (the reference, the counts, the files that differ, the KMZs' entries, the network key, the
  readings, the verdict); `logs/p6/deliver/kmz/` (the KMZs as checked before the move; when one fails, none is moved and the checked ones stay there).
- `recon/modes.json`: one row per date (mode, width, lines, bandwidth, PRF, r0 grid position, orbit vz, look
  side); every later phase reads modes from here, never from a folder name. `recon/reference.json`: the
  reference, who decided it, the three rules' picks, the candidate table, G17's values and the Rule 4 geometry.

A phase is skipped when its record is PASS, its inputs are unchanged (same fingerprint) and its outputs are
still there; otherwise it runs again. The fingerprints of recon, stage, extract, unpack and verify include the md5s of
the pipeline's own files (rwin's, since v0.5, its LOGIC and unpack's recorded fingerprint);
Phase 2 to 4 fingerprints hold what each phase reads (the shelves, modes.json's rows, pass 1's network, the reference
date, the previous phase's output digest, the run files' md5s), the settings it uses from `linog_stack.cfg` and
the gate settings from `linog_run.cfg` (not the files; J, OMP and PEAK_KB change no result and are only recorded),
the ISCE tools' md5s and the DEM, plus a LOGIC
number in each phase's file that a new version raises when what the phase writes or decides changes. So a code
change that leaves the result as it was does not ask for the stack configuration to be moved aside. A RUNNING record without an END means a run died: the next run stops and
asks for `--recover`. One run per frame at a time (flock on `status/.lock`).

## Exit codes

0 PASS · 2 FAIL (a gate) · 3 ERROR (tool, host, input, environment, or a frame this version cannot process) ·
4 DECISION NEEDED (a human choice; the record says which; v0.10: also a second restart in one run; v0.12: a second restart asked by one phase) · 130 or 143: the run was stopped (Ctrl-C, SIGTERM);
the phase's record then reads ERROR, and anything it left half-written is listed as a DECISION on the next run.
install.sh (v0.13): 0 installed, the env check rc 0, the unpacker readable by another account by its mode bits (an ACL on its
path is named, not judged), read-only yes · 5 installed, but the env check did not end rc 0 or the unpacker is not readable
by another account · 6 installed, but one of path 84's four frames or pipeline/v0.12 changed (read-only NO) · 7 not
installed, pipeline/v0.13 left incomplete · 2 not installed (the package damaged, pipeline/v0.13 there already, too little
free space, or the self-test failed) · 3 not installed (the host, or a folder). Its last line says which. Block S42 judges
its own predictions (expect_s42.json); they are not exit codes of install.sh.

## Human decisions

`recon/exclude.txt` in the frame folder, one granule per line with a reason:

    ALPSRP<orbit><frame>  <reason>

`recon/reference.txt` (above). `recon/admission.txt` (admit, D3 and D9; v0.8: the answer to d9ab's DECISION; v0.10: key by key, either D3 key takes the place of the rules R1 to R3's exclusions, a D3 key left out then excluding nothing, and `mintpy.unwrapError.method` takes the place of R5's decision; a file naming only D3 keys leaves D9 to R5): MintPy's own key = value lines, any of
`mintpy.network.excludeDate = no | YYYYMMDD[,...]`, `mintpy.network.excludeDate12 = no | auto | YYYYMMDD_YYYYMMDD[,...]`
and `mintpy.unwrapError.method = no | bridging`; each value is checked against the network, and a key left out
excludes nothing. `recon/refpix.txt` (sbas, G19): one line `mintpy.reference.yx = y,x`, the operator's reference pixel
in place of the kit's pick. v0.11: `recon/rerun_reference.txt` (rerun: the package to compare with, on its first line
that is not a `#` comment) and `recon/rerun.txt` (rerun: `accept <reference folder> <hash of hashes>` and `#` lines, which
take a change on the same network). The pipeline deletes nothing. It rewrites in place a shelve rwin corrects, after copying it
into `_archive/rwin_<UTC>/`, and (v0.10) `mintpy/exclude_date.txt` when dfit changes the fit's dates, after copying it
into `dfit/<UTC>/`; v0.11's deliver moves its four checked KMZs over the ones the kit wrote moments before (G6a.10); it moves
(renames) only what v0.10's R5 moves (`mintpy/` and an earlier `recon/d9ab_decision.json` into
`_archive/`), what v0.12's drop1 moves (`mintpy/` and an earlier `recon/drop1_decision.json` into `_archive/`; it removes
only its own scratch under `drop1/<UTC>/`: the stack copies and the files placed beside them, time series and `base.npz`,
also those a stopped run left), what dfit moves (its own earlier `exclude_date.txt` into `dfit/<UTC>/`) and the driver's
`status/restart.json` (kept as `status/restart_<run>_<n>.json`). An entry in its way (a raw/ link that is not
a kept granule, a `unzipped/.<stem>.part/` left by a killed extract, an `SLC/<date>/` not finished by an earlier
run, a folder in `SLC/` or `unzipped/` that is not a kept date or granule, an `SLC/<date>/` made by another
unpacker, an earlier stack configuration in the frame) stops the phase with DECISION and is listed; move it into
the frame's own `_archive/` (`<frame>/_archive/`, not a folder inside `SLC/`, `raw/` or `configs/`) and re-run.

## Path table and environment

`linog_paths.cfg`: root, archive, DEM, thresholds; per path the direction, orbit residue, date-law anchor,
expected granule counts and frame footprints (from ASF metadata), each with its source. v0.10 adds paths 83, 86 and 87
(descending; residue, anchor and counts from RD4's census of felix's archive; no footprint, so recon's G0.14 reads WARN).
`linog_env.cfg`: conda.sh, the env name, the unpacker and kit-check paths with their md5s, the gate grid,
and the chirp bandwidth per mode. `linog_stack.cfg`: Phase 2 (above). `linog_run.cfg`: Phases 3 and 4 (above).
`linog_fftw.cfg` (v0.9): the wisdom file and its md5, the env's libfftw3f (its path under ENV_PREFIX, md5 and version),
ISCE2's ampcor, crossmul and icu modules (paths under the isce package, md5s) and the problems the wisdom must cover
(`LINOG_FFTW_CFG` names another copy).
`linog_phase6.cfg`: Phases 5e and 6: the md5s of the kit's six tools, the verifier copy's name, the delivery's counts,
D7c's two tolerances, the package's folder, prefix and version, and (v0.8) `RUN_MANIFEST.json`'s lead product and its
reason, the readings' rings, discs and products, and the GNSS stations (PIMO).
`linog_mintpy.cfg`: Phases 4.5 and 5: MintPy's version and the md5 of its defaults file, the md5s of the kit's
`linog_admit.py` and `linog_refpix.py`, the report's settings, D9's A/B settings (v0.8, in place of v0.6's anchors), admit's rules and dfit's time limit (v0.10), G19's edge, SNWE's lattice and margin,
G24's heading tolerance, and the `CFG.` lines the template takes (`LINOG_MINTPY_CFG` names another copy).
`selftest_kit/` holds the mock environment the self-test uses, with byte copies of the kit's scripts (`kit3/`: the
nine Phase 3 and 4 gates) and of ISCE2's `stackStripMap.py`, `Stack.py`, `stripmapWrapper.py`, `invertMisreg.py` and
`referenceStackCopy.py` (Apache License 2.0, text in `selftest_kit/mock_stack/`); the ISCE steps those scripts call
(topo, geo2rdr, resampleSlc, refineSecondaryTiming, baselineGrid, crossmul, FilterAndCoherence, unwrap) and
`gdal_translate` are mocks (`mock_stack3/`, `mock_isce/linog_mock3.py`) that write the files the rehearsal measured,
sparse except the rows the kit's gates read, on a 4-date frame 1000 x 18432 (cases T63 to T83, T93). The mock ALOS
sensor takes r0 from the leader with ISCE's own `CEOS.py` and four of its `db/alos_slc/` record definitions (byte
copies, Apache License 2.0), and the mock granules carry CEOS file descriptors, image-record prefixes and a scene
record written from those definitions, so rwin reads them as it reads felix's (cases T84 to T91, T94, T95).
Phases 4.5 and 5 run the kit's `linog_admit.py` and `linog_refpix.py` (byte copies in `kit3/`) and a mock MintPy
(`mock_mintpy/`): the package with version 1.6.2 and MintPy 1.6.2's own `defaults/smallbaselineApp.cfg` (GPL-3.0),
and mock `prep_isce.py` and `smallbaselineApp.py` that write the files a stripmapStack frame gives, with 1.6.2's step
banners, on the Phase 3 frame's grid (cases T99 to T121). The kit's `linog_save_insar_images.py` (a byte copy in
`kit3/`, 402141d9) renders two planted pairs for a byte comparison with the report, and the mock `isce` reads ISCE2
2.6.3's own `defaults/logging/logging.conf` (a byte copy, 21a67de3, Apache License 2.0) with `fileConfig`, as
`isce/__init__.py` does (cases T122 and T123). v0.8: the mock `smallbaselineApp.py` writes `maskConnComp.h5` in
reference_point and runs on d9ab's copy (bridging copies unwrapPhase; planted: `LINOG_MOCK_B_GAIN`, `LINOG_MOCK_B_VSTD`,
a sleep for the stop case), and the mock geocode writes REF_Y, REF_X on the geo grid, rounded, as MintPy 1.6.2 does
(cases T104 to T104c, T125f, T125g, T146 to T150). v0.9: the mock env carries a real libfftw3f (a copy of the pinned
env's, read on felix, or of the host's system library), stand-ins of the three modules with a mock `ldd`, and a wisdom
file made with that library for 20 problems; the mock refineSecondaryTiming, crossmul and FilterAndCoherence print
cfft1d_jpl's wisdom lines and import the file through that library, STOP with status 0 on a failed import and crash on a
missing file (cases T154 to T171, and T64 and T93 with the new gates). v0.10 (`lp_selftest10.py`, T200 to T224): the mock
topo's `hgt.rdr` carries land (a gentle slope) and the scene's sea flat at 44 m; planted LINOG_MOCK_BADDATE (a date's
pairs random) and LINOG_MOCK_RAMPDATE (a date's pairs at 12 fringes: the screen) at igram, LINOG_MOCK_TS (a rate, and a
date with a ramp) and LINOG_MOCK_RMSOUT (MintPy's own outlier) in MintPy; the mock velocity step and
`timeseries2velocity.py` fit alike and honour `--ex` and the template's excludeDate. R3 and R2 run as functions (on
felix's F3310 and F3320 networks too), R1 on a synthetic frame beside the kit's tool, a 6-date frame is built through
Phases 0 to 4 for R3's thin date and dfit, the driver's restart runs on a stub pipeline, and the path runner and the tag
on mock granules at RD4's orbits. v0.11 (`lp_selftest11.py`, T300 to T315): G6a.10 on the mock delivery (the kit's own
`linog_gen_interactive_kmz.py` and the mock `save_kmz.py`, whose plant LINOG_MOCK_KMZ_EXTRA writes an extra field); a second
delivery of the frame, made after the first was moved into `_archive/` as G6a.5 says, byte for byte the first (the
acceptance planned on F3310); rerun against references with other KMZ times, a changed GeoTIFF (DECISION, then taken by
`recon/rerun.txt`), another network, a key not recorded whole, a KMZ with other content, a name on one side, a broken
reference, another frame's package and a reference file naming nothing, and the newest archived tree (two newer trees
passed over); 29 phases; rerun's dry run; `lp_compare.py`'s four commands (the mock MintPy's bin adds
`ifgram_inversion.py` for split); and `lp_kmz.py` alone (data descriptors, a comment, its refusals). v0.12
(`lp_selftest12.py`, T320 to T339 with T331b, and the stub driver's T212b and T213c): the mock's LINOG_MOCK_D1BAD lowers the
temporal coherence on a block of land while a pair is kept, in sbas's inversion and in drop1's alike (LINOG_MOCK_D1FAIL
and LINOG_MOCK_D1SLEEP fail or hold one test; LINOG_MOCK_COHPAIR sets a pair's coherence); a cull taken with its restart
through a whole run and a re-run of 30 phases skipped; admit's D1d on that frame (unreadable, the operator's file,
another network, other interferograms, applied, another basis after a settings change, then the cull tested and taken
again); a pair inside its peers' range (with the |dv| figures); a cull over the 20 % cap and one over the shipped 10 %;
ask, then the operator's file and the cull in place, then a changed threshold (not in place); an operator's file
(recorded, not applied), then the file moved aside (the cull taken from the tests already made); drop1's restart and then
d9ab's in one run; dry runs of admit and drop1, and F3310's plan; the land floor; no flag; a failed, a stopped and a
killed inversion (the job and the inversion end with drop1), then the scratch removed and the completed tests read again;
the peers chosen by coherence; the cull refused when `_archive` is a file; a flagged pair not testable; `--only drop1`
under auto; admit changed after sbas with drop1 run alone (G5d1.4 FAIL); and the functions alone. r2: the minimum peer
count (T331b alone; T338 in a run: 6 over the pair's 5 peers keeps it, then 5 culls it from the tests read again); a
frame with `mintpy/waterMask.h5` (T339: the mock's LINOG_MOCK_WATERMASK gives the geometry a waterMask, and its
modify_network writes `waterMask.h5`, as MintPy 1.6.2 does; T339b the mask changed: drop1 STALE, every test run again);
a killed run leaves exactly the stack copy, `avgSpatialCoh.h5` and `base.npz` (T330b); and SIGKILL to d9ab alone while
MintPy runs on B ends MintPy on B too (T149k, record 77.12). The mock inversion logs which of the files MintPy reads
around a stack it found, and the two it does not read (T320 and T339 check each test's).
