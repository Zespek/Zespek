#!/usr/bin/env python3
"""
Gera o banner animado do perfil (banner.webp na raiz do repositório).

    python banner/generate_banner.py

Para trocar nome ou subtítulo, edite NAME / SUBTITLE abaixo e rode de novo.

Requisitos: Python 3.10+, numpy, Pillow, Microsoft Edge ou Google Chrome (o texto
é renderizado pelo navegador para ter kerning correto) e o img2webp do libwebp no
PATH ou em --img2webp (https://developers.google.com/speed/webp/download). Sem o
img2webp, o Pillow é usado como fallback, com cores de texto um pouco menos fiéis.
As fontes (OFL, Google Fonts) são baixadas para banner/.fonts na primeira execução.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from html import escape as html_escape
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

NAME = "José Felipe"
SUBTITLE = "CTO | Senior Software Engineer | KMP"

W, H, SCALE = 800, 250, 2      # layout em px CSS; saída em W*SCALE x H*SCALE
FPS, DURATION = 20, 9.0        # loop contínuo de DURATION segundos
QUALITY = 75
SEED = 7
RADIUS = 8

# Gradiente vertical (y, rgb) e onda escura do rodapé (x, y), medidos do banner original.
BG_STOPS = [(0, (75, 2, 133)), (25, (73, 2, 128)), (50, (67, 1, 117)), (75, (64, 1, 108)),
            (100, (59, 2, 100)), (125, (52, 2, 90)), (150, (49, 1, 82)), (175, (44, 2, 72)),
            (200, (38, 1, 61)), (250, (29, 2, 44))]
WAVE = [(0, 234.2), (50, 236.6), (100, 237.2), (150, 237.2), (200, 236.2), (250, 233.9),
        (300, 230.2), (350, 226.0), (400, 220.5), (450, 214.9), (500, 212.2), (550, 211.3),
        (600, 211.9), (650, 214.7), (700, 220.0), (750, 226.8), (800, 233.4)]
WAVE_RIM, WAVE_FILL = (15, 15, 26), (8, 9, 14)

# Chuva matrix
RAIN_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
RAIN_COLOR, RAIN_HEAD, SPARKLE_COLOR = (185, 30, 255), (205, 60, 255), (240, 205, 255)
RAIN_OPACITY = 0.65
COL_PITCH, COL_OFFSET, ROW_PITCH, RAIN_FONT_PX = 18, 3, 17, 16
RAIN_SPEED = 530               # px/s
RAIN_FADE = 0.11               # s, decaimento do rastro
DROPS_PER_COLUMN = 7
SPARKLES = 14                  # glifos brilhantes avulsos por loop

TEXT = [
    dict(text=NAME, font="Montserrat", weight=800, size=55, top=80,
         color=(250, 248, 252), shadow=(6, 3, 0.88)),      # sombra: blur sigma, dy, opacidade
    dict(text=SUBTITLE, font="Inter", weight=700, size=17, top=148,
         color=(242, 234, 250), shadow=(2.5, 1, 0.84)),
]

FONT_URLS = {
    "Montserrat": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    "Inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf",
    "FiraCode": "https://github.com/google/fonts/raw/main/ofl/firacode/FiraCode%5Bwght%5D.ttf",
}

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path(__file__).resolve().parent / ".fonts"
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


def ensure_fonts():
    FONT_DIR.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        path = FONT_DIR / f"{name}.ttf"
        if not path.exists():
            print(f"baixando fonte {name}...")
            urllib.request.urlretrieve(url, path)


def find_browser(explicit):
    for cand in [explicit, *BROWSERS]:
        if cand and Path(cand).exists():
            return cand
    for exe in ("msedge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        if shutil.which(exe):
            return shutil.which(exe)
    sys.exit("Edge/Chrome não encontrado; use --browser para indicar o executável.")


def render_text_alpha(spec, browser):
    """Renderiza um bloco de texto em branco sobre fundo transparente e devolve o alfa (H*S, W*S)."""
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Montserrat;src:url(Montserrat.ttf);font-weight:100 900}}
@font-face{{font-family:Inter;src:url(Inter.ttf);font-weight:100 900}}
html,body{{margin:0;background:transparent;width:{W}px;height:{H}px;overflow:hidden}}
div{{position:absolute;left:0;width:{W}px;text-align:center;color:#fff;white-space:pre;line-height:1;
font-family:{spec['font']};font-weight:{spec['weight']};font-size:{spec['size']}px;top:{spec['top']}px}}
</style></head><body><div>{html_escape(spec['text'])}</div></body></html>"""
    page = FONT_DIR / "_text.html"
    shot = FONT_DIR / "_text.png"
    page.write_text(html, encoding="utf-8")
    shot.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={profile}", f"--force-device-scale-factor={SCALE}",
                        f"--window-size={W},{H}", "--default-background-color=00000000",
                        "--virtual-time-budget=3000", f"--screenshot={shot}", page.as_uri()],
                       capture_output=True, timeout=120)
    alpha = np.asarray(Image.open(shot))[..., 3] / 255.0
    page.unlink()
    shot.unlink()
    if alpha.shape != (H * SCALE, W * SCALE) or alpha.max() == 0:
        sys.exit(f"falha ao renderizar o texto {spec['text']!r} com {browser}")
    return alpha


def blur(img, sigma):
    r = int(np.ceil(3 * sigma))
    x = np.arange(-r, r + 1)
    k = np.exp(-x ** 2 / (2 * sigma ** 2))
    k /= k.sum()
    p = np.pad(img, r)
    tmp = sum(k[i] * p[i:i + img.shape[0]] for i in range(len(k)))
    return sum(k[i] * tmp[:, i:i + img.shape[1]] for i in range(len(k)))


def shadow_layer(alpha, sigma, dy, opacity):
    shifted = np.zeros_like(alpha)
    d = int(round(dy * SCALE))
    shifted[d:] = alpha[:alpha.shape[0] - d]
    return np.clip(opacity * blur(shifted, sigma * SCALE), 0, 1)


def catmull_rom(points, xs):
    px = np.array([p[0] for p in points], float)
    py = np.array([p[1] for p in points], float)
    m = np.gradient(py, px)
    i = np.clip(np.searchsorted(px, xs) - 1, 0, len(px) - 2)
    h = px[i + 1] - px[i]
    t = (xs - px[i]) / h
    return ((2 * t ** 3 - 3 * t ** 2 + 1) * py[i] + (t ** 3 - 2 * t ** 2 + t) * h * m[i]
            + (-2 * t ** 3 + 3 * t ** 2) * py[i + 1] + (t ** 3 - t ** 2) * h * m[i + 1])


def static_layers():
    ys = (np.arange(H * SCALE) + 0.5) / SCALE
    stops_y = [s[0] for s in BG_STOPS]
    bg = np.stack([np.interp(ys, stops_y, [s[1][c] for s in BG_STOPS]) for c in range(3)], -1)
    bg = np.broadcast_to(bg[:, None, :], (H * SCALE, W * SCALE, 3)).copy()

    xs = (np.arange(W * SCALE) + 0.5) / SCALE
    crest = catmull_rom(WAVE, xs) * SCALE
    yy = np.arange(H * SCALE)[:, None]
    wave_a = np.clip(yy + 1 - crest[None, :], 0, 1)
    depth = (yy + 0.5 - crest[None, :]) / SCALE
    t = np.clip((depth - 1.5) / 4.5, 0, 1)[..., None]
    wave_rgb = np.array(WAVE_RIM) * (1 - t) + np.array(WAVE_FILL) * t

    y, x = np.mgrid[0:H * SCALE, 0:W * SCALE] + 0.5
    r = RADIUS * SCALE
    cx = np.clip(x, r, W * SCALE - r)
    cy = np.clip(y, r, H * SCALE - r)
    corner_a = np.clip(r - np.hypot(x - cx, y - cy) + 0.5, 0, 1)
    return bg, wave_a, wave_rgb, corner_a


def rain_glyphs():
    font = ImageFont.truetype(str(FONT_DIR / "FiraCode.ttf"), RAIN_FONT_PX * SCALE)
    try:
        font.set_variation_by_axes([700])
    except Exception:
        pass
    cw, ch = COL_PITCH * SCALE, ROW_PITCH * SCALE
    glyphs = []
    for c in RAIN_CHARS:
        im = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(im).text((cw / 2, ch / 2), c, font=font, fill=255, anchor="mm")
        glyphs.append(np.asarray(im) / 255.0)
    return glyphs


def rain_schedule(rng):
    rows = int(np.ceil(H / ROW_PITCH)) + 1
    drops = []
    for col in range(int(np.ceil(W / COL_PITCH)) + 1):
        phase = rng.uniform(0, DURATION)
        for k in range(DROPS_PER_COLUMN):
            t0 = (phase + k * DURATION / DROPS_PER_COLUMN + rng.uniform(-0.6, 0.6)) % DURATION
            drops.append(dict(col=col, t0=t0, speed=RAIN_SPEED * rng.uniform(0.85, 1.15),
                              y0=-ROW_PITCH * rng.uniform(0, 3), level=rng.uniform(0.55, 1.0),
                              chars=rng.integers(0, len(RAIN_CHARS), rows)))
    sparkles = [dict(col=int(rng.integers(0, W // COL_PITCH)), row=int(rng.integers(0, 12)),
                     t0=rng.uniform(0, DURATION), char=int(rng.integers(0, len(RAIN_CHARS))))
                for _ in range(SPARKLES)]
    return drops, sparkles


def paint_glyph(frame, glyph, col, row, color, opacity):
    cw, ch = glyph.shape[1], glyph.shape[0]
    x0 = int(round((COL_OFFSET + col * COL_PITCH) * SCALE)) - cw // 2
    y0 = row * ch
    fx0, fy0 = max(x0, 0), max(y0, 0)
    fx1, fy1 = min(x0 + cw, frame.shape[1]), min(y0 + ch, frame.shape[0])
    if fx1 <= fx0 or fy1 <= fy0:
        return
    a = glyph[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0, None] * opacity
    region = frame[fy0:fy1, fx0:fx1]
    region *= 1 - a
    region += a * np.array(color, float)


def paint_rain(frame, t, drops, sparkles, glyphs):
    rows = int(np.ceil(H / ROW_PITCH)) + 1
    cell_time = ROW_PITCH / RAIN_SPEED
    for d in drops:
        for t0 in (d["t0"] - DURATION, d["t0"], d["t0"] + DURATION):
            since = t - t0
            if since < 0:
                continue
            head_y = d["y0"] + d["speed"] * since
            last = min(int(head_y // ROW_PITCH), rows - 1)
            for row in range(last, -1, -1):
                lit_at = t0 + ((row + 0.5) * ROW_PITCH - d["y0"]) / d["speed"]
                age = t - lit_at
                if age < 0:
                    continue
                level = d["level"] * np.exp(-age / RAIN_FADE)
                if level < 0.03:
                    break
                head = age < cell_time
                paint_glyph(frame, glyphs[d["chars"][row]], d["col"], row,
                            RAIN_HEAD if head else RAIN_COLOR, RAIN_OPACITY * level)
    for s in sparkles:
        for t0 in (s["t0"] - DURATION, s["t0"], s["t0"] + DURATION):
            age = t - t0
            if 0 <= age < 0.25:
                paint_glyph(frame, glyphs[s["char"]], s["col"], s["row"], SPARKLE_COLOR,
                            0.85 * (1 - age / 0.25))


def encode(frames_dir, n, out, img2webp):
    delay = int(round(1000 / FPS))
    if img2webp:
        args = ["-loop", "0", "-sharp_yuv", "-lossy", "-q", str(QUALITY), "-m", "6", "-d", str(delay)]
        args += [f"f{i:04d}.png" for i in range(n)] + ["-o", str(Path(out).resolve())]
        res = subprocess.run([img2webp, *args], cwd=frames_dir, capture_output=True, text=True)
        if res.returncode:
            sys.exit(f"img2webp falhou:\n{res.stderr}")
    else:
        imgs = [Image.open(frames_dir / f"f{i:04d}.png") for i in range(n)]
        imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=delay, loop=0,
                     quality=QUALITY, method=6, lossless=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--browser", help="caminho do Edge/Chrome")
    ap.add_argument("--img2webp", help="caminho do img2webp (libwebp)")
    ap.add_argument("--out", default=str(ROOT / "banner.webp"))
    args = ap.parse_args()

    ensure_fonts()
    browser = find_browser(args.browser)
    img2webp = args.img2webp or shutil.which("img2webp")
    if not img2webp:
        print("aviso: img2webp não encontrado, usando o encoder do Pillow")

    bg, wave_a, wave_rgb, corner_a = static_layers()
    texts = []
    keep = np.ones(bg.shape[:2])
    for spec in TEXT:
        alpha = render_text_alpha(spec, browser)
        keep *= 1 - shadow_layer(alpha, *spec["shadow"])
        texts.append((alpha[..., None], np.array(spec["color"], float)))
    wave_a = wave_a[..., None]
    keep = keep[..., None]

    rng = np.random.default_rng(SEED)
    drops, sparkles = rain_schedule(rng)
    glyphs = rain_glyphs()
    n = int(round(FPS * DURATION))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for i in range(n):
            frame = bg.copy()
            paint_rain(frame, i / FPS, drops, sparkles, glyphs)
            frame = frame * (1 - wave_a) + wave_rgb * wave_a
            frame *= keep
            for alpha, color in texts:
                frame = frame * (1 - alpha) + color * alpha
            rgba = np.dstack([frame, corner_a * 255])
            Image.fromarray(np.clip(np.round(rgba), 0, 255).astype(np.uint8), "RGBA").save(tmp / f"f{i:04d}.png")
        encode(tmp, n, Path(args.out), img2webp)
    print(f"{args.out}: {n} frames, {os.path.getsize(args.out) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
