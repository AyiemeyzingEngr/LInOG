# mock_stack (linog_auto self-test only)

`stackStripMap.py` (md5 30c0d85b6d4e11605ececef910cfbd5a) and `Stack.py` (md5 bad64ed9062c5a2870a4c9a42a8f2544) are
unmodified copies of the files in conda-forge `isce2-2.6.4-py311h916084f_2` (`share/isce2/stripmapStack/`), the build
felix's `linog_isce2` runs (RD3, 27 Sept 2026: the same md5s on felix). ISCE2, https://github.com/isce-framework/isce2,
Apache License 2.0: the licence text is in `LICENSE-Apache-2.0.txt` beside them (the package's about.json names the
licence; the package carries no copy of the text). The self-test puts the two files in its mock env's
`share/isce2/stripmapStack/`, so Phase 2 runs the real stack-configuration code with the mock `isce`, the mock
`mroipac` Baseline (felix's measured baselines) and mock SLCs. Nothing here is used by a real run.
