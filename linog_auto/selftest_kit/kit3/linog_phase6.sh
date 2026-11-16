#!/bin/bash
# LInOG Phase 6: demErr chains -> geocode -> H/V -> 16 deliverables
# Usage: linog_phase6.sh <PATH> <FRAME> <REF_DATE>    e.g. 448 0280 20091111
set -e
PN=$1; FR=$2; REF=$3
B=${LINOG_ROOT:-/eggraid/home/arieln/projects/linog/insar}/p${PN}/f${FR}
S=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)   # the directory this script lives in (= $LINOG_ROOT/scripts)
TAG=P${PN}F${FR}; M=$B/mintpy; G=$M/geo; OUT=$G/LInOG_Upload_$TAG
cd $M
echo "===== 1 preserve ramp-first diagnostics ===== $(date +%H:%M:%S)"
[ -f demErr_rampfirst.h5 ] || cp demErr.h5 demErr_rampfirst.h5
[ -f timeseriesResidual_rampfirst.h5 ] || cp timeseriesResidual.h5 timeseriesResidual_rampfirst.h5
[ -f exclude_date.txt ] && mv exclude_date.txt _exclude_date.hold
echo "===== 2 chain A: demErr without deramp ===== $(date +%H:%M:%S)"
dem_error.py timeseries.h5 -t smallbaselineApp.cfg -g inputs/geometryRadar.h5 -o timeseries_demErr.h5
echo "===== 3 chain B: deramp after demErr ===== $(date +%H:%M:%S)"
remove_ramp.py timeseries_demErr.h5 -s linear -m maskTempCoh.h5 -o timeseries_demErr_ramp.h5
[ -f _exclude_date.hold ] && mv _exclude_date.hold exclude_date.txt
echo "===== 4 velocities x3 ===== $(date +%H:%M:%S)"
timeseries2velocity.py timeseries_demErr.h5      -t smallbaselineApp.cfg -o velocity_demErr.h5
timeseries2velocity.py timeseries_demErr_ramp.h5 -t smallbaselineApp.cfg -o velocity_demErr_ramp.h5
timeseries2velocity.py timeseries_ramp_demErr.h5 -t smallbaselineApp.cfg -o velocity_ramp_demErr.h5
echo "===== 5 geocode (module form; geocode.py is shadowed by ISCE2) ===== $(date +%H:%M:%S)"
python -m mintpy.cli.geocode timeseries_demErr.h5 timeseries_demErr_ramp.h5 \
  velocity_demErr.h5 velocity_demErr_ramp.h5 \
  inputs/geometryRadar.h5 maskTempCoh.h5 \
  -l inputs/geometryRadar.h5 -t smallbaselineApp.cfg --outdir geo --update
echo "===== 6 H/V projections ===== $(date +%H:%M:%S)"
cd $G; mkdir -p $OUT
for src in demErr demErr_ramp; do
  sf=""; [ "$src" = "demErr_ramp" ] && sf="_ramp"
  python $S/linog_los2hv.py geo_velocity_$src.h5 geo_geometryRadar.h5 Vertical   geo_velocity_Vertical$sf.h5
  python $S/linog_los2hv.py geo_velocity_$src.h5 geo_geometryRadar.h5 Horizontal geo_velocity_Horizontal$sf.h5
done
echo "===== 7 Velocity KMZ x2 at SOP range -10..10 cm/yr ===== $(date +%H:%M:%S)"
for s in demErr demErr_ramp; do
  save_kmz.py geo_velocity_$s.h5 -m geo_maskTempCoh.h5 -v -10 10 -u cm/year -o $OUT/${TAG}_Velocity_$s.kmz
done
echo "===== 8 GeoTIFF x6 ===== $(date +%H:%M:%S)"
for s in demErr demErr_ramp Vertical Vertical_ramp Horizontal Horizontal_ramp; do
  save_gdal.py geo_velocity_$s.h5 -d velocity -m geo_maskTempCoh.h5 -o $OUT/${TAG}_Velocity_$s
  [ -f $OUT/${TAG}_Velocity_$s ] && mv $OUT/${TAG}_Velocity_$s $OUT/${TAG}_Velocity_$s.tif
done
echo "===== 8b NoData=nan on every GeoTIFF (N44, before stats) ===== $(date +%H:%M:%S)"
for s in demErr demErr_ramp Vertical Vertical_ramp Horizontal Horizontal_ramp; do
  gdal_edit.py -a_nodata nan $OUT/${TAG}_Velocity_$s.tif
done
python $S/linog_embed_stats.py --dir $OUT

echo "===== 9 Hillshade PNG x6 ===== $(date +%H:%M:%S)"
for s in demErr demErr_ramp Vertical Vertical_ramp Horizontal Horizontal_ramp; do
  view.py geo_velocity_$s.h5 velocity --dem geo_geometryRadar.h5 --mask geo_maskTempCoh.h5 \
    -v -10 10 -u cm/year --dpi 600 --nodisplay --noverbose -o $OUT/${TAG}_Velocity_Hillshade_$s.png
done
echo "===== 10 Interactive TimeSeries KMZ x2 (LInOG SOP tool) ===== $(date +%H:%M:%S)"
python $S/linog_gen_interactive_kmz.py --path $PN --frame $FR --correction demErr      --frame-dir $B
python $S/linog_gen_interactive_kmz.py --path $PN --frame $FR --correction demErr_ramp --frame-dir $B
echo "===== 11 verify ===== $(date +%H:%M:%S)"
echo -n "deliverables: "; find $OUT -maxdepth 1 -type f | wc -l; ls -A $OUT
echo; echo "PHASE 6 COMPLETE for $TAG  $(date +%H:%M:%S)"
