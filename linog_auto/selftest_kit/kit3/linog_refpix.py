#!/usr/bin/env python3
"""G19 v2 -- reference pixel by MINIMUM coherence over the KEPT network.
Run from WORK_DIR.

MintPy's default prints "random select pixel with coherence > 0.85" and applies
that threshold to the TEMPORAL AVERAGE.  On f0310 the pixel it chose averaged
0.9051 while sitting at 0.3269 in one pair.  The reference pixel sets the
constant subtracted from every interferogram, so where its coherence is ~0.33
that constant is wrong by up to +/-pi for that pair, and the error propagates
across the whole scene.  The pick is also random, so the product is not
reproducible run to run.

f0310's G19 restricted candidates to pixels inside EVERY kept pair's main
connected component; 37.8% of that scene qualified.  On f0320 that intersection
is EMPTY (56 of 137 pairs below 80% main component), so the threshold is walked
down until a usable candidate set appears.

MAIN COMPONENT = the label holding the most pixels among labels >= 1.
NOT label 1: snaphu numbers components arbitrarily and caps NCOMP at 20.  On
f0320's fragmented pairs label 1 holds under 1% while label 2 holds 14-18%.
                                                          LInOG 2026-08-28
"""
import argparse, sys
import numpy as np, h5py

ap = argparse.ArgumentParser()
ap.add_argument("--stack", default="mintpy/inputs/ifgramStack.h5")
ap.add_argument("--win", type=int, default=5)
ap.add_argument("--edge", type=int, default=20)
ap.add_argument("--top", type=int, default=6)
a = ap.parse_args()

f = h5py.File(a.stack, "r")
drop = f["dropIfgram"][:]
kept = np.where(drop)[0]
dt = f["date"][:]
d12 = ["%s_%s" % (r[0].decode(), r[1].decode()) for r in dt]
COH, CC = f["coherence"], f["connectComponent"]
N, L, W = COH.shape

mn = np.ones((L, W), np.float32)
sm = np.zeros((L, W), np.float64)
inm = np.zeros((L, W), np.float32)
worst = np.zeros((L, W), np.int32)
for i in kept:
    c = COH[i].astype(np.float32)
    upd = c < mn
    worst[upd] = i
    np.minimum(mn, c, out=mn)
    sm += c
    g = CC[i]
    bc = np.bincount(g.ravel().astype(np.int64))
    if bc.size > 1:
        bc[0] = 0
        inm += (g == int(np.argmax(bc)))
av = (sm / len(kept)).astype(np.float32)
inm /= len(kept)

def winmin(x, k):
    o = x.copy(); r = k // 2
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy == 0 and dx == 0: continue
            np.minimum(o, np.roll(np.roll(x, dy, 0), dx, 1), out=o)
    return o
mn5 = winmin(mn, a.win)

e = a.edge
valid = np.zeros((L, W), bool); valid[e:L - e, e:W - e] = True
valid &= np.isfinite(mn) & (av > 0)

print("kept pairs %d of %d   grid %d x %d" % (len(kept), N, L, W))
print("component fraction over valid area: max %.4f  mean %.4f\n"
      % (inm[valid].max(), inm[valid].mean()))
print("THRESH  CANDIDATES   best y,x    MIN_COH  MIN5x5   AVG_COH  COMPFRAC")
chosen = None
for t in (1.0, 0.995, 0.99, 0.98, 0.95, 0.90, 0.85, 0.80, 0.70):
    m = valid & (inm >= t - 1e-9)
    n = int(m.sum())
    if n < 25:
        print("%5.3f %11d   -" % (t, n)); continue
    s = np.where(m, mn5, -1)
    k = int(np.argmax(s)); y, x = k // W, k % W
    print("%5.3f %11d   %4d,%4d   %6.4f  %6.4f   %6.4f   %6.4f"
          % (t, n, y, x, mn[y, x], mn5[y, x], av[y, x], inm[y, x]))
    if chosen is None and n >= 100:
        chosen = (t, y, x, s.copy())

if chosen is None:
    print("\n*** no candidate set reached 100 pixels"); sys.exit(1)
t, y, x, s = chosen
print("\n--- top %d candidates at component fraction >= %.3f" % (a.top, t))
for k in np.argsort(s.ravel())[::-1][:a.top]:
    yy, xx = int(k) // W, int(k) % W
    print("   %4d,%4d  min %6.4f  min5x5 %6.4f  avg %6.4f  comp %6.4f  worst %s"
          % (yy, xx, mn[yy, xx], mn5[yy, xx], av[yy, xx], inm[yy, xx], d12[worst[yy, xx]]))

am = np.where(valid, av, -1)
k = int(np.argmax(am)); ya, xa = k // W, k % W
print("\n--- what MintPy's criterion favours (highest AVERAGE coherence)")
print("   %4d,%4d  min %6.4f  avg %6.4f  comp %6.4f  worst %s"
      % (ya, xa, mn[ya, xa], av[ya, xa], inm[ya, xa], d12[worst[ya, xa]]))
print("\n--- paste into mintpy/smallbaselineApp.cfg ---")
print("mintpy.reference.yx            = %d,%d" % (y, x))
