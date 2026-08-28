#!/usr/bin/env python3
"""Compose the recorded vhs segments into the README demo.

Each segment is a real recording (see demo/seg/*.tape). This adds the framing:
window chrome, a soft shadow on a gradient ground, a caption per segment, and
crossfades between them. Run demo/build.sh rather than this directly.
"""
import shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
SEG = HERE / "seg"
WORK = HERE / ".build"
FPS = 16

# (gif, caption, [(skip, keep), ...])  windows let a dead wait be cut out
SEGMENTS = [
    ("1.gif", "Every agent on one screen",                [(0.3, 5.2)]),
    ("2.gif", "Read what it is doing, in plain English",   [(0.4, 8.0)]),
    ("3.gif", "Ask what it changed, answered in seconds",  [(0.8, 6.4), (16.4, 7.5)]),
]

CANVAS = (1440, 880)
INSET_Y = 74
RADIUS = 14
BAR_H = 34
BG_TOP, BG_BOT = (24, 26, 34), (14, 15, 20)
DOTS = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]

FONT_PATHS = [
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]

def font(size):
    for p in FONT_PATHS:
        try: return ImageFont.truetype(p, size)
        except Exception: continue
    return ImageFont.load_default()

def gradient(size):
    w, h = size
    g = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(g)
    for y in range(h):
        t = y / max(1, h - 1)
        d.point((0, y), tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOT)))
    return g.resize(size, Image.BILINEAR)

def rounded(im, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1],
                                           radius=r, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out

def shadow(size, r, blur=26, spread=10):
    w, h = size
    s = Image.new("RGBA", (w + blur * 4, h + blur * 4), (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle(
        [blur * 2 - spread, blur * 2 - spread + 6, blur * 2 + w + spread,
         blur * 2 + h + spread + 6], radius=r + spread, fill=(0, 0, 0, 150))
    return s.filter(ImageFilter.GaussianBlur(blur))

def chrome(term, caption, base, sh, f_cap, f_hint):
    """One finished frame: shadow, window bar, terminal, caption."""
    tw, th = term.size
    panel = Image.new("RGB", (tw, th + BAR_H), (30, 31, 40))
    d = ImageDraw.Draw(panel)
    for i, c in enumerate(DOTS):
        d.ellipse([18 + i * 20, BAR_H // 2 - 5, 28 + i * 20, BAR_H // 2 + 5], fill=c)
    d.text((tw // 2, BAR_H // 2), "mini", font=f_hint, fill=(150, 155, 170), anchor="mm")
    panel.paste(term, (0, BAR_H))
    panel = rounded(panel, RADIUS)

    frame = base.copy()
    x = (CANVAS[0] - tw) // 2
    frame.paste(sh, (x - 52, INSET_Y - 52), sh)
    frame.paste(panel, (x, INSET_Y), panel)

    d = ImageDraw.Draw(frame)
    cy = INSET_Y + th + BAR_H + 40
    d.text((CANVAS[0] // 2, cy), caption, font=f_cap, fill=(228, 232, 240), anchor="mm")
    return frame

def frames_of(gif, keep, skip, idx=0):
    out = WORK / (gif.replace(".gif", "") + f"_{idx}")
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(skip), "-t", str(keep),
                    "-i", str(SEG / gif), "-vf", f"fps={FPS}",
                    str(out / "f%04d.png")], check=True)
    return sorted(out.glob("*.png"))

def main():
    if WORK.exists(): shutil.rmtree(WORK)
    WORK.mkdir()
    base = gradient(CANVAS)
    f_cap, f_hint = font(27), font(14)
    outdir = WORK / "final"; outdir.mkdir()
    n, sh, prev_last = 0, None, None

    for gif, caption, windows in SEGMENTS:
        built = []
        clips = []
        for wi, (skip, keep) in enumerate(windows):
            clips += frames_of(gif, keep, skip, wi)
        for fp in clips:
            term = Image.open(fp).convert("RGB")
            if sh is None or sh.size[0] != term.size[0] + 104:
                sh = shadow((term.size[0], term.size[1] + BAR_H), RADIUS)
            built.append(chrome(term, caption, base, sh, f_cap, f_hint))
        if prev_last is not None:                      # crossfade into this segment
            for i in range(1, 7):
                Image.blend(prev_last, built[0], i / 7.0).save(outdir / f"{n:05d}.png"); n += 1
        for im in built:
            im.save(outdir / f"{n:05d}.png"); n += 1
        prev_last = built[-1]

    for _ in range(int(FPS * 0.8)):                    # hold on the last frame
        prev_last.save(outdir / f"{n:05d}.png"); n += 1

    pal = WORK / "pal.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS),
                    "-i", str(outdir / "%05d.png"), "-vf",
                    "palettegen=max_colors=160:stats_mode=diff", str(pal)], check=True)
    out = HERE / "agentview.gif"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS),
                    "-i", str(outdir / "%05d.png"), "-i", str(pal), "-lavfi",
                    "paletteuse=dither=bayer:bayer_scale=4", str(out)], check=True)
    print(f"{n} frames -> {out} ({out.stat().st_size // 1024} KB)")

main()
