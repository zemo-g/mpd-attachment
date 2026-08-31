#!/opt/homebrew/bin/python3.11
"""Digitize C_T vs J data points from IEPC-97-121 Figure 1 (page 2).

Gilland 1988 argon data on the PBT, 3 g/s (filled circles) and 6 g/s
(open circles). Renders the PDF page at 300 dpi, finds the plot frame and
axis ticks, blob-detects the markers, classifies filled vs open, and writes
out/fig1_points.csv plus a verification overlay out/fig1_overlay.png.

Axis calibration comes from detected tick marks: x ticks at 0..25 kA every
5 kA, y ticks at C_T = 1..7 every 1.
"""
import subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "refs", "iepc97-121.pdf")
OUT = os.path.join(ROOT, "data")
TMP = "/tmp/mpd_fig1"

# Crop window for Figure 1 on the 300 dpi render of page 2 (2550x3300 page).
CROP = (150, 150, 1400, 1300)
# Legend box (crop coords): the two legend markers + dash sample live here.
LEGEND = (560, 130, 1250, 320)

def main():
    os.makedirs(TMP, exist_ok=True)
    subprocess.run(["/opt/homebrew/bin/pdftoppm", "-f", "2", "-l", "2",
                    "-r", "300", "-png", PDF, TMP + "/p2"], check=True)
    im = Image.open(TMP + "/p2-2.png").convert("L")
    im = im.crop(CROP)
    a = np.array(im)
    dark = a < 128

    h, w = dark.shape
    col_counts = dark.sum(axis=0)
    row_counts = dark.sum(axis=1)
    # Frame lines: near-full-length runs. Left/right verticals, top/bottom horizontals.
    vcols = np.where(col_counts > 0.55 * h)[0]
    hrows = np.where(row_counts > 0.55 * w)[0]
    if len(vcols) < 2 or len(hrows) < 2:
        sys.exit(f"frame not found: vcols={vcols}, hrows={hrows}")
    xL, xR = vcols.min(), vcols.max()
    yT, yB = hrows.min(), hrows.max()
    print(f"frame: x [{xL},{xR}]  y [{yT},{yB}]")

    # Bottom ticks: dark columns in a thin band below the bottom frame line.
    band = dark[yB + 3: yB + 14, :]
    tickcols = np.where(band.sum(axis=0) >= 8)[0]
    tickcols = tickcols[(tickcols > xL - 10) & (tickcols < xR + 10)]
    xticks = cluster(tickcols)
    # Left ticks: dark rows in a band left of the left frame line.
    band = dark[:, xL - 14: xL - 3]
    tickrows = np.where(band.sum(axis=1) >= 8)[0]
    yticks = cluster(tickrows)
    print(f"xticks({len(xticks)}): {xticks}")
    print(f"yticks({len(yticks)}): {yticks}")
    if len(xticks) != 6 or len(yticks) != 7:
        sys.exit("tick count mismatch: expected 6 x (0..25 kA), 7 y (1..7)")
    # Linear fits pixel -> data
    jfit = np.polyfit(xticks, np.arange(0, 26, 5) * 1000.0, 1)
    cfit = np.polyfit(yticks, np.arange(7, 0, -1) * 1.0, 1)

    # Marker blobs strictly inside the frame, frame lines excluded.
    inner = dark.copy()
    inner[: yT + 3, :] = False
    inner[yB - 2:, :] = False
    inner[:, : xL + 3] = False
    inner[:, xR - 2:] = False
    lab, n = label(inner)
    pts = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        area = len(ys)
        if area < 60:          # dashes of the Maecker line, specks
            continue
        cx, cy = xs.mean(), ys.mean()
        bw = xs.max() - xs.min() + 1
        bh = ys.max() - ys.min() + 1
        if LEGEND[0] <= cx <= LEGEND[2] and LEGEND[1] <= cy <= LEGEND[3]:
            continue
        if not (10 <= bh <= 30 and bw >= 10):
            continue           # not marker-shaped (text, specks)
        if bw <= 26:
            segs = [(xs, ys)]
        elif bw <= 200:
            # chain of touching markers: split along x into ~marker-width bins
            k = max(2, round(bw / 14.0))
            edges = np.linspace(xs.min() - 0.5, xs.max() + 0.5, k + 1)
            segs = []
            for j in range(k):
                m = (xs >= edges[j]) & (xs < edges[j + 1])
                if m.sum() >= 40:
                    segs.append((xs[m], ys[m]))
        else:
            continue
        for sx, sy in segs:
            scx, scy = sx.mean(), sy.mean()
            sw = sx.max() - sx.min() + 1
            sh = sy.max() - sy.min() + 1
            fill = len(sx) / (np.pi * (max(sw, sh) / 2.0) ** 2)
            series = "3" if fill > 0.62 else "6"
            J = np.polyval(jfit, scx)
            CT = np.polyval(cfit, scy)
            pts.append((J, CT, series, scx, scy, len(sx), fill))

    pts.sort(key=lambda p: (p[2], p[0]))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "fig1_points.csv"), "w") as f:
        f.write("J_A,C_T,mdot_g_s\n")
        for J, CT, s, *_ in pts:
            f.write(f"{J:.0f},{CT:.3f},{s}\n")
    print(f"wrote {len(pts)} points "
          f"(3 g/s: {sum(1 for p in pts if p[2]=='3')}, "
          f"6 g/s: {sum(1 for p in pts if p[2]=='6')})")

    ov = im.convert("RGB")
    d = ImageDraw.Draw(ov)
    for J, CT, s, cx, cy, area, fill in pts:
        c = (255, 0, 0) if s == "3" else (0, 128, 255)
        d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], outline=c, width=2)
    d.rectangle(LEGEND, outline=(0, 200, 0), width=2)
    ov.save(os.path.join(OUT, "fig1_overlay.png"))

def cluster(idx, gap=5):
    """Group sorted pixel indices into clusters; return cluster centers."""
    if len(idx) == 0:
        return []
    groups, cur = [], [idx[0]]
    for v in idx[1:]:
        if v - cur[-1] <= gap:
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    return [float(np.mean(g)) for g in groups]

def label(mask):
    """4-connected component labeling (BFS), no scipy dependency."""
    lab = np.zeros(mask.shape, dtype=np.int32)
    n = 0
    H, W = mask.shape
    for y0 in range(H):
        for x0 in range(W):
            if mask[y0, x0] and lab[y0, x0] == 0:
                n += 1
                stack = [(y0, x0)]
                lab[y0, x0] = n
                while stack:
                    y, x = stack.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and lab[yy, xx] == 0:
                            lab[yy, xx] = n
                            stack.append((yy, xx))
    return lab, n

if __name__ == "__main__":
    main()
