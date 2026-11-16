# selftest_kit (linog_auto self-test only)

Used by `lp_selftest.py` to run Phases 1 and 2 on mock data. Nothing here is used by a real run.

- `unpackFrame_ALOS.py`, `linog_unpack_verify.py`, `linog_shelve_gate.py`: byte copies of the LInOG kit's files
  (md5 c037bd4e..., ee37fbfd..., ac1a8275..., the pins in `linog_env.cfg`), so the self-test runs the same code as
  felix. The self-test checks these md5s against `linog_env.cfg` before it uses them.
- `mock_isce/`: a mock `isce` package whose ALOS_SLC sensor writes a sparse SLC and a Frame with the attribute
  names and values RD2 read on felix (26 Sept 2026), and a `sitecustomize.py` that makes shelves in dbm.dumb, as
  felix writes them. The self-test builds a mock conda env around it, activated as felix's `conda activate` does:
  no PYTHONPATH and no stripmapStack on the PATH.
- `mock_isce/isce/components/isceobj/Sensor/CEOS.py` and `db/alos_slc/{image_file,image_record,leader_file,scene_record}.xml`:
  byte copies of isce2 2.6.3's CEOS parser and four of its ALOS SLC record definitions (Apache License 2.0; md5
  e7f25f21..., 54efd830..., 6378e734..., c40135b6..., 823265c7...). v0.5: the mock sensor takes r0 from the leader's
  range gate delay through them, as ISCE's ALOS_SLC does, the self-test writes its granules' file descriptors,
  image-record prefixes and scene records from the same definitions, and rwin reads them with the same parser.
- `linog_net_table.py`: a byte copy of the kit's network table (md5 40bf01de..., the pin in `linog_stack.cfg`).
- `mock_stack/`: the real `stackStripMap.py` and `Stack.py` of the isce2 package felix runs (see its README).
- `mock_isce/isce/components/mroipac/`: a mock Baseline that returns felix's measured baselines of P084 F3320, so
  the self-test's network is the real one (157 pairs); the mock Frame writes its `.slc.vrt` in ISCE's layout.
- v0.7, Phases 5e and 6: `kit3/` holds byte copies of the kit's `linog_watermask.py`, `linog_phase6.sh`,
  `linog_los2hv.py`, `linog_embed_stats.py`, `linog_gen_interactive_kmz.py` and `linog_verify_frame.py` (md5 907cf856,
  43d6c15b, ada17e14, c35e935a, 45dc2d01, 7f2b53cf: the pins in `linog_phase6.cfg`), which the self-test runs as felix
  pins them. The mock MintPy adds `mintpy.utils.readfile` and `writefile`, `mintpy.cli.geocode` (nearest neighbour
  through the geometry, `--update` as MintPy 1.6.2's run_or_skip decides it) and, in the env's bin, `dem_error.py`,
  `remove_ramp.py`, `timeseries2velocity.py`, `save_kmz.py`, `save_gdal.py` (a mock GeoTIFF), `gdal_edit.py`, `view.py`
  and `gdalinfo`; the mock `osgeo.gdal` reads, edits and computes the statistics of those GeoTIFFs
  (`mock_isce/linog_mock6.py`). `linog_mock3.scene()` is the frame's ground: a sea flat at 44 m in the south-east
  corner (half of it decorrelated), a bright pier, a dark strip along the near-range edge; the mock crossmul writes each
  pair's `.amp` from it and the mock smallbaselineApp its heights and temporal coherence. The env's bin has `python`.
- v0.10, admit's rules and dfit: the mock topo's `hgt.rdr` rises 0.02 m a line over the land (a 5 x 5 standard
  deviation of 3 cm: land to the water tool's `flat_masks()`) and holds the scene's sea flat at 44 m (water); the mock
  FilterAndCoherence takes LINOG_MOCK_BADDATE (every pair of a date random phase) and LINOG_MOCK_RAMPDATE (a date's pairs
  at 12 fringes: the kit's date screen); the mock smallbaselineApp's invert_network keeps the kept pairs' dates and takes
  LINOG_MOCK_TS (a rate, and a date with a ramp), its residual_RMS writes `exclude_date.txt` with LINOG_MOCK_RMSOUT (and
  removes one it finds otherwise, as MintPy 1.6.2 does), and its velocity step and the mock `timeseries2velocity.py` fit
  alike (`linog_mock6.fit_velocity`), honouring `--ex` and the template's `mintpy.timeFunc.excludeDate`.
- v0.11, the rerun check: the env's bin has a mock `ifgram_inversion.py` (`STACK -t CFG`, as lp_compare.py's split runs
  it): `timeseries.h5` and `temporalCoherence.h5` from the stack's kept pairs, in the folder it runs in.
- v0.12, drop1's peer test: that mock also writes `numInvIfgram.h5`, and `linog_mock3.d1_plant()` (applied alike by it
  and by the mock smallbaselineApp's invert_network) takes LINOG_MOCK_D1BAD=<pair>:<cells> (the temporal coherence falls
  to 0.55 on a block of land while that pair is kept, so dropping it gains the block); LINOG_MOCK_D1FAIL=<pair> (the
  inversion without that pair exits 1) and LINOG_MOCK_D1SLEEP=<pair>:<s> (it sleeps first, writing its pid into
  LINOG_MOCK_MARK when set). The mock FilterAndCoherence takes LINOG_MOCK_COHPAIR=<pair>:<c> (that pair's coherence), so
  the peers nearest a flagged pair in mean land coherence can be chosen.
- v0.13, FBS+FBD and FBD-only frames (the ascending record 4.11, 18.5): `linog_fbs_bandlimit.py` and
  `linog_fbs_downsample.py` are byte copies of the course kit's (md5 5befb0bd..., 69323fe8..., the pins in
  `linog_mixed.cfg`), which bandlimit (P1bs) runs as felix pins them. The mock ALOS_SLC sensor takes the sampling rate,
  the wavelength, the pulse length and the chirp from the leader's scene record by mode, as ISCE2's ALOS_SLC does (an FBD
  shelve reads 16 MHz, a 14 MHz chirp and a 9.37 m pixel), and on a short frame whose IMG-HH records carry samples it
  writes them into the SLC as ISCE's writeRawData does; LINOG_MOCK_HV=<date>[:log] reads IMG-HV instead (logged or not),
  LINOG_MOCK_WAVELENGTH=<date>:<factor> and LINOG_MOCK_FS16=<date> plant the shelve's instrument. The self-test's
  granules carry those fields in their leaders, and the mixed frame 3350 (12 dates, 4 FBD) and the FBD-only frame 3360
  band-limited noise in every record (FBS 28 of 32 MHz, FBD 14 of 16 MHz, IMG-HV at half IMG-HH's amplitude), 512 lines
  of 1000 to 1048 samples.
- v0.13 r2, deliver's G6a.11 (the mode step, DB1; the ascending record 15.3 D, 15.4, 16.2 and 16.4): every mock time base
  is MintPy's decimal years, `linog_mock6.yyyymmdd2years` (year + (day of year - 1) / 365.25, from the first date): the
  velocity fit (`linog_mock6.fit_velocity`), the mock `dem_error.py`'s bowl and the LINOG_MOCK_TS plant. The mock
  `remove_ramp.py` takes out, per date, the plane MintPy 1.6.2's deramp fits (over the mask's nonzero finite pixels,
  [y, x, 1], referenced to REF_Y, REF_X, 0 kept 0) in place of its fixed ramp. The mock `dem_error.py` writes a 1-D
  `bperp` (0 on every date, the mock stack's) and MintPy 1.6.2's four `mintpy.topographicResidual.*` attributes as
  strings; with LINOG_MOCK_DB1=<case> and LINOG_MOCK_DB1_TABLE=`db1/mock3350_table.json` it plants the table: each date's
  range plane from the case's c into dem_error, 1 mm x the date's index, no bowl, then each pixel's part on bperp given
  [1, t, t^2] taken out, and the table's bperp written. `db1/mock3350_table.json` is the desk's table (`db1_desk.py` v2 at
  the line 0.0039, its `D`: dates, modes, bperp, and per case c into and out of dem_error with the desk's reading);
  `db1/ra1_dates.tsv` and `ra1_frames.tsv` are RA1's own (md5 1bf7aee1..., d6bedb39...), and `ra1_frames.json` holds
  from `ra1.json` and `expect_ra1.json` what M50 reads of them. The mock `view.py` takes LINOG_MOCK_H5BREAK=<file> (it
  writes over that file, which only G6a.11 reads after step 9).
