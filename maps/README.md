# linog_map

LInOG velocity maps on a satellite base, made from a settings file. Version 1.0, 26 Nov 2026.

The map style follows the 2026 LInOG reports:
- a Sentinel-2 cloudless 2024 base (EOX);
- grid coordinates and province lines (GADM 4.1);
- labelled places;
- one velocity scale for every map: RdYlBu_r, -5 to +5 cm/yr LOS. Blue is away from the satellite (sinking); red is toward it (uplift);
- sinking areas traced by a line drawn just outside them, never a dot on top.

## Install once

1. Install Miniforge: https://conda-forge.org/download/
2. In a Miniforge Prompt (Windows) or Terminal (macOS), from this folder, run:

       conda env create -f environment.yml

## Make a map

    conda activate linog_map
    python linog_map.py examples/coverage_12_frames.yaml --check    (quick preview and label check)
    python linog_map.py examples/coverage_12_frames.yaml            (the final map)

The examples expect the v1.2 delivery folder `LINOG_DELIVERY_v1.2_20260924_final` to sit next to this folder. Otherwise, change the `frames:` lines.

To make a new map, copy an example, change it, and run it. The guide (LINOG_MAP_GUIDE_*.docx) explains every setting.

To add a place: `python linog_map.py --find "Gapan City, Nueva Ecija"`. This saves the place in data/my_places.json.

## Files

| File | What it is |
|---|---|
| linog_map.py | The program; it should not need editing |
| examples/*.yaml | Three settings files: 12-frame coverage, a Cabanatuan zoom with the sinking area traced, one frame |
| data/places.json | 68 places (OpenStreetMap Nominatim) |
| data/my_places.json | Places you add with --find |
| environment.yml | The Python packages |

Downloads are kept in ~/.linog_map_cache: the EOX tiles and GADM's province file.
- The base tiles are licensed CC BY-NC-SA 4.0 (non-commercial use).
- GADM is free for academic use and is not redistributed here.

Do not map NAMRIA IfSAR heights with this tool (the NAMRIA data agreement).

Licence: GPL-3.0-or-later.
