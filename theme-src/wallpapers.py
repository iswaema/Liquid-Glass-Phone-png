"""Procedural Liquid Glass wallpapers at Xiaomi 17 native resolution (1220x2656)."""
import numpy as np
from PIL import Image, ImageFilter

W, H = 1220, 2656


def _hex(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def _finish(rgb, blur):
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB").filter(ImageFilter.GaussianBlur(blur))
    arr = np.asarray(img).astype(np.float32)
    arr += np.random.default_rng(7).normal(0, 1.4, arr.shape)  # dither: kills gradient banding
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def home():
    """Violet field with a dark vortex wrapped in a lavender/pink light ring."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    t = y / H
    top, mid, bot = _hex("6A46EC"), _hex("4F2BD8"), _hex("3B1FC6")
    base = np.where(t[..., None] < 0.5,
                    top + (mid - top) * (t[..., None] / 0.5),
                    mid + (bot - mid) * ((t[..., None] - 0.5) / 0.5))

    cx, cy = W * 0.60, H * 0.56
    dx, dy = (x - cx) / (W * 0.62), (y - cy) / (W * 0.50)
    d = np.sqrt(dx ** 2 + dy ** 2)
    theta = np.arctan2(dy, dx)

    vortex = np.exp(-(d / 0.62) ** 2)[..., None]
    rgb = base * (1 - 0.78 * vortex) + _hex("12073F") * 0.78 * vortex

    # light ring, brightest along the upper arc
    arc = (0.55 + 0.45 * np.cos(theta + np.pi / 2)) ** 2
    ring = np.exp(-((d - 1.0) / 0.10) ** 2) * arc
    halo = np.exp(-((d - 1.0) / 0.30) ** 2) * arc * 0.35
    lav = _hex("D9C6FF")
    rgb += (lav - rgb) * np.clip(ring * 0.7 + halo, 0, 1)[..., None]

    # outer faint ring
    ring2 = np.exp(-((d - 1.55) / 0.06) ** 2) * (0.5 + 0.5 * np.cos(theta - np.pi / 2)) * 0.30
    rgb += (_hex("B9A2FF") - rgb) * ring2[..., None]

    # pink glow hugging the right edge
    pink = np.exp(-(((x - W * 1.02) / (W * 0.22)) ** 2 + ((y - H * 0.40) / (H * 0.16)) ** 2))
    rgb += (_hex("F0A8FF") - rgb) * (pink * 0.75)[..., None]

    # soft highlight at top-left
    tl = np.exp(-(((x - W * 0.1) / (W * 0.6)) ** 2 + ((y - H * 0.02) / (H * 0.2)) ** 2))
    rgb += (_hex("7A5CFF") - rgb) * (tl * 0.5)[..., None]
    return _finish(rgb, 6)


def lock():
    """Aurora mesh: violet, teal, coral and cobalt bleeding into each other."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, y / H * (H / W)  # isotropic coords
    pts = [
        (0.18, 0.18, "7A5CFF", 1.3),
        (0.95, 0.05, "0B1030", 1.0),
        (0.95, 0.42, "0E8C8A", 1.2),
        (0.55, 0.30, "3F3AA8", 0.9),
        (0.05, 0.62, "6A2C78", 0.8),
        (0.10, 0.80, "F0603A", 1.3),
        (0.55, 0.62, "4A2E86", 0.9),
        (0.92, 0.75, "2E3FA8", 1.0),
        (0.90, 0.98, "3A5BF0", 1.2),
        (0.35, 1.00, "9A5A8C", 1.0),
    ]
    aspect = H / W
    num = np.zeros((H, W, 3), np.float32)
    den = np.zeros((H, W), np.float32)
    for px, py, col, wgt in pts:
        dd = (u - px) ** 2 + (v - py * aspect) ** 2 + 1e-4
        w = wgt / dd ** 1.25
        num += w[..., None] * _hex(col)
        den += w
    return _finish(num / den[..., None], 40)


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    home().save(f"{out}/home.jpg", quality=95)
    lock().save(f"{out}/lock.jpg", quality=95)
