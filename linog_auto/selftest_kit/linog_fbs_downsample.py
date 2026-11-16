#!/usr/bin/env python3
"""Downsample ALOS PALSAR FBS L1.1 SLC from 28 MHz to 14 MHz common bandwidth.

Method (following Werner et al., 2007 - GAMMA approach):
1. For each range line of the complex SLC:
   a. FFT in range direction
   b. Apply Hanning-tapered bandpass window retaining central 50% of spectrum
   c. IFFT back to spatial domain
   d. Decimate by factor 2 in range

This produces an SLC with identical pixel spacing and bandwidth to native FBD data,
enabling mixed-mode interferometric processing in ISCE2 stackStripMap.

Input:  ISCE2-unpacked FBS SLC directory (contains .slc and .slc.xml)
Output: Downsampled SLC directory with updated .xml metadata

Reference:
    Werner, C. et al. (2007). "PALSAR Multi-Mode Interferometric Processing."
    Proc. 1st Joint PI Symposium of ALOS Data Nodes, Kyoto, Japan.

Usage:
    python linog_fbs_downsample.py /path/to/FBS_SLC/ /path/to/output/
    python linog_fbs_downsample.py --batch raw_fbs_unpacked/ raw_fbs_downsampled/
    LInOG uses --keep-fraction 0.4 (NOT the 0.5 fallback below).
"""

import os
import sys
import glob
import numpy as np
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil

KEEP_FRACTION = 0.4   # LInOG standard, used on every p448 frame.
                      # ALOS FBS: 28 MHz BW at 32 MHz Fs; 0.4375 = exact 14 MHz.
                      # 0.5 was the old fallback and is a silent wrong-bandwidth trap.
TAPER_WIDTH   = 0.05


def create_hanning_bandpass(n_samples, keep_fraction=0.5, taper_width=0.05):
    """Create a Hanning-tapered bandpass filter in frequency domain.
    
    Args:
        n_samples: number of range samples
        keep_fraction: fraction of bandwidth to keep (0.5 = 14/28 MHz)
        taper_width: width of Hanning taper transition (fraction of total BW)
    
    Returns:
        filter array in standard FFT order
    """
    freqs = np.fft.fftfreq(n_samples)
    cutoff = keep_fraction / 2.0
    taper = taper_width / 2.0
    
    filt = np.zeros(n_samples, dtype=np.float64)
    
    for i, f in enumerate(freqs):
        af = abs(f)
        if af < cutoff - taper:
            filt[i] = 1.0
        elif af < cutoff + taper:
            filt[i] = 0.5 * (1.0 + np.cos(np.pi * (af - (cutoff - taper)) / (2 * taper)))
        else:
            filt[i] = 0.0
    
    return filt


def downsample_slc(input_slc, output_slc, width, length, dtype='complex64'):
    """Apply spectral filtering and decimation to an SLC file."""
    print(f"  Reading SLC: {width} x {length} ({dtype})")
    
    slc_in = np.fromfile(input_slc, dtype=dtype).reshape(length, width)
    filt = create_hanning_bandpass(width, keep_fraction=KEEP_FRACTION, taper_width=TAPER_WIDTH)
    
    out_width = width // 2
    slc_out = np.zeros((length, out_width), dtype=dtype)
    
    print(f"  Filtering and decimating: {width} -> {out_width} range samples")
    
    for i in range(length):
        if i % 5000 == 0:
            print(f"    Processing line {i}/{length} ({100*i/length:.1f}%)")
        spectrum = np.fft.fft(slc_in[i, :])
        spectrum *= filt
        filtered = np.fft.ifft(spectrum)
        slc_out[i, :] = filtered[::2]
    
    slc_out.tofile(output_slc)
    print(f"  Written: {output_slc} ({out_width} x {length})")
    return out_width, length


def update_xml_metadata(input_xml, output_xml, new_width):
    """Update ISCE2 .slc.xml metadata for the downsampled SLC."""
    tree = ET.parse(input_xml)
    root = tree.getroot()
    
    def find_and_update(element, name, new_value):
        for prop in element.iter('property'):
            if prop.get('name', '').lower() == name.lower():
                val = prop.find('value')
                if val is not None:
                    old = val.text
                    val.text = str(new_value)
                    print(f"    XML: {name}: {old} -> {new_value}")
                    return True
        return False
    
    find_and_update(root, 'width', new_width)
    find_and_update(root, 'NUMBER_OF_SAMPLES', new_width)
    
    tree.write(output_xml, xml_declaration=True, encoding='unicode')
    print(f"  Updated XML: {output_xml}")


def process_scene(scene_dir, output_dir):
    """Process a single FBS scene directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    slc_files = glob.glob(os.path.join(scene_dir, "*.slc"))
    if not slc_files:
        print(f"  ERROR: No .slc file found in {scene_dir}")
        return False
    
    for slc_file in slc_files:
        basename = os.path.basename(slc_file)
        xml_file = slc_file + ".xml"
        
        if not os.path.exists(xml_file):
            print(f"  ERROR: No XML metadata: {xml_file}")
            return False
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        width = length = None
        for prop in root.iter('property'):
            name = prop.get('name', '').lower()
            val = prop.find('value')
            if val is not None:
                if name == 'width':
                    width = int(val.text)
                elif name == 'length':
                    length = int(val.text)
        
        if width is None or length is None:
            print(f"  ERROR: Could not read dimensions from {xml_file}")
            return False
        
        print(f"\nProcessing: {basename}")
        print(f"  Input dimensions: {width} x {length}")
        
        output_slc = os.path.join(output_dir, basename)
        output_xml = output_slc + ".xml"
        
        new_width, _ = downsample_slc(slc_file, output_slc, width, length)
        
        shutil.copy2(xml_file, output_xml)
        update_xml_metadata(output_xml, output_xml, new_width)
    
    return True


def batch_process(input_parent, output_parent):
    """Process all FBS scene directories in a parent directory."""
    os.makedirs(output_parent, exist_ok=True)
    
    scene_dirs = sorted(d for d in glob.glob(os.path.join(input_parent, "*")) if os.path.isdir(d))
    print(f"Found {len(scene_dirs)} scene directories")
    
    success = fail = 0
    for scene_dir in scene_dirs:
        dirname = os.path.basename(scene_dir)
        output_dir = os.path.join(output_parent, dirname)
        print(f"\n{'='*60}\nScene: {dirname}\n{'='*60}")
        
        if process_scene(scene_dir, output_dir):
            success += 1
        else:
            fail += 1
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {success} success, {fail} failed out of {len(scene_dirs)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downsample ALOS PALSAR FBS SLC 28->14 MHz")
    parser.add_argument("input", help="Input scene dir or parent dir (with --batch)")
    parser.add_argument("output", help="Output scene dir or parent dir")
    parser.add_argument("--batch", action="store_true", help="Process all subdirectories")
    parser.add_argument("--keep-fraction", type=float, default=0.5)
    parser.add_argument("--taper-width",   type=float, default=0.05)
    args = parser.parse_args()
    KEEP_FRACTION = args.keep_fraction
    TAPER_WIDTH   = args.taper_width
    print("LInOG: keep_fraction=%.4f taper_width=%.4f" % (KEEP_FRACTION, TAPER_WIDTH))
    
    start = datetime.now()
    if args.batch:
        batch_process(args.input, args.output)
    else:
        process_scene(args.input, args.output)
    print(f"\nTotal elapsed time: {datetime.now() - start}")
