# linog_auto v0.13 r3

The pipeline that made every run of the LInOG letter "Assessing the Impact of National and Global Digital Elevation Models in Regional ALOS InSAR Deformation Time-Series Analysis" (IEEE GRSL, in preparation): ALOS-1 PALSAR Level 1.1 FBS and FBD frames to SBAS velocities with ISCE2 stripmapStack and MintPy, in 31 phases. Its own documentation is `linog_auto/README.md`.

## The same files that ran

`linog_auto/` holds the 166 files of the installed pipeline and its `MANIFEST.md5` (md5 dd4113b3ab2814b3d7f50b917c8bf5aa), unchanged. The manifest also lists `install.sh`, the installer for the authors' server, which is not published. To check:

```
cd linog_auto && grep -v ' install.sh$' MANIFEST.md5 | md5sum -c --quiet && echo "166 of 166 OK"
```

## What it was run with

ISCE2 from conda-forge, build 2.6.4 (it reports 2.6.3); MintPy 1.6.2; Python 3.11.15, NumPy 1.26.4, h5py 3.16.0, SciPy 1.17.1, Matplotlib 3.10.8.

## Before running elsewhere

`linog_paths.cfg`, `linog_env.cfg` and `linog_stack.cfg` carry the authors' server paths; set them for your machine. `fftw/wisdom_felix.wis` is an FFTW plan for that server.

## Data

None is included. ALOS-1 PALSAR data are copyright JAXA/METI. The national IfSAR DTM belongs to NAMRIA and is not distributed.

## Licence

GNU General Public License v3 or later (`LICENSE`); third-party files and their licences are listed in `NOTICE`.
