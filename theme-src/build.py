"""Build the Liquid Glass HyperOS theme (.mtz) plus its previews.

    python3 build.py            ->  ../dist/LiquidGlass.mtz, ../dist/preview.html
"""
import os
import shutil
import zipfile
from datetime import date

from PIL import Image, ImageDraw, ImageFilter

import icons
import lockscreen
import wallpapers

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
BUILD = os.path.join(PROJECT, "build")
DIST = os.path.join(PROJECT, "dist")

THEME = {
    "title": "Liquid Glass",
    "designer": "Joshua",
    "author": "Joshua",
    "version": "1.0.0",
    "ui_version": "17",
    "adapter_version": "8.2",
    "description": "Translucent liquid-glass icons, an aurora lockscreen with a liquid charging orb, "
                   "and violet vortex wallpapers. Built for Xiaomi 17 (1220x2656).",
}

# density bucket -> icon px
ICON_SIZES = {"drawable-xxhdpi": 192}

HOME_GRID = ["gallery", "store", "music", "themes", "files", "browser", "maps", "weather",
             "security", "calculator", "notes", "calendar", "mail", "wallet", "health", "clock"]
LABELS = {"store": "Store", "security": "Security"}
DOCK = ["phone", "messages", "camera", "settings"]


# tells HyperOS to cut every unthemed app icon to the same squircle as the themed ones
TRANSFORM_CONFIG = f'''<?xml version="1.0" encoding="utf-8"?>
<IconTransform>
    <Config name="SupportLayerIcon" value="true"/>
    <Config name="ConfigIconMask" value="{icons.SQ}"/>
</IconTransform>
'''


def _zip_dir(src, dest):
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(src):
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, src))


def build_icons(stage):
    src = os.path.join(BUILD, "icons")
    shutil.rmtree(src, ignore_errors=True)
    masters = {}
    for name, pkgs, img in icons.build_all():
        masters[name] = img
        for folder, px in ICON_SIZES.items():
            d = os.path.join(src, "res", folder)
            os.makedirs(d, exist_ok=True)
            small = img.resize((px, px), Image.LANCZOS)
            for p in pkgs:
                small.save(os.path.join(d, p + ".png"))
    for folder, px in ICON_SIZES.items():
        d = os.path.join(src, "res", folder)
        for fname, img in icons.fallback_layers().items():
            img.resize((px, px), Image.LANCZOS).save(os.path.join(d, fname))
    with open(os.path.join(src, "transform_config.xml"), "w") as f:
        f.write(TRANSFORM_CONFIG)
    _zip_dir(src, os.path.join(stage, "icons"))
    return masters


def build_lockscreen(stage):
    src = os.path.join(BUILD, "lockscreen")
    shutil.rmtree(src, ignore_errors=True)
    imgs = lockscreen.write(src)
    _zip_dir(src, os.path.join(stage, "lockscreen"))
    return imgs


DESIGN_PREVIEWS = {
    "Home screen.png": "preview_launcher_0.jpg",
    "Lock screen.png": "preview_lockscreen_0.jpg",
    "Control center.png": "preview_statusbar_0.jpg",
}


def design_preview(path):
    """Scale a mockup to cover the Xiaomi 17 screen (1220x2656), trimming the sliver of overflow at the sides."""
    W, H = wallpapers.W, wallpapers.H
    img = Image.open(path).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def render_home(wall, masters):
    """Home screen exactly as the theme's assets compose: wallpaper, icon grid, glass dock."""
    W, H = wallpapers.W, wallpapers.H
    img = wall.convert("RGBA")
    font = lockscreen._font(40, "Medium")
    size, cols = 190, 4
    gx = [int(W / cols * (i + 0.5)) for i in range(cols)]
    top = 760
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    labels = []
    for i, name in enumerate(HOME_GRID):
        cx, cy = gx[i % cols], top + (i // cols) * 320
        _with_shadow(img, masters[name].resize((size, size), Image.LANCZOS), cx - size // 2, cy - size // 2)
        labels.append(((cx, cy + size // 2 + 44), LABELS.get(name, name.capitalize())))
    # blurred halo keeps labels legible where they cross the bright light ring
    for xy, label in labels:
        ImageDraw.Draw(shade).text((xy[0], xy[1] + 2), label, font=font, fill=(18, 0, 60, 200), anchor="mm",
                                   stroke_width=3, stroke_fill=(18, 0, 60, 200))
    img.alpha_composite(shade.filter(ImageFilter.GaussianBlur(7)))
    for xy, label in labels:
        ImageDraw.Draw(img).text(xy, label, font=font, fill="white", anchor="mm")

    # glass search pill
    pill = lockscreen.glass_rect(360, 120, 60, (40, 20, 110, 90))
    img.alpha_composite(pill, (W // 2 - 180, 2055))
    ImageDraw.Draw(img).text((W // 2 + 22, 2115), "Search", font=lockscreen._font(50, "Medium"), fill="white",
                             anchor="mm")
    d = ImageDraw.Draw(img)
    d.ellipse([W // 2 - 118, 2096, W // 2 - 84, 2130], outline="white", width=6)
    d.line([(W // 2 - 88, 2126), (W // 2 - 72, 2142)], fill="white", width=7)

    # dock
    dock = lockscreen.glass_rect(1124, 270, 100, (110, 90, 255, 70))
    img.alpha_composite(dock, (48, H - 400))
    for i, name in enumerate(DOCK):
        _with_shadow(img, masters[name].resize((size, size), Image.LANCZOS), gx[i] - size // 2, H - 400 + 40)
    ImageDraw.Draw(img).rounded_rectangle([W // 2 - 210, H - 66, W // 2 + 210, H - 52], 7, fill=(255, 255, 255, 220))
    return img.convert("RGB")


def _with_shadow(base, icon, x, y):
    sh = Image.new("RGBA", icon.size, (15, 5, 50, 0))
    sh.putalpha(icon.getchannel("A").point(lambda v: int(v * 0.35)))
    pad = 30
    canvas = Image.new("RGBA", (icon.width + pad * 2, icon.height + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(sh, (pad, pad))
    canvas = canvas.filter(ImageFilter.GaussianBlur(12))
    base.alpha_composite(canvas, (x - pad, y - pad + 10))
    base.alpha_composite(icon, (x, y))


def render_icon_sheet(wall, masters):
    W, H = wallpapers.W, wallpapers.H
    img = wall.convert("RGBA")
    dark = Image.new("RGBA", img.size, (12, 4, 40, 70))
    img.alpha_composite(dark)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 230), "Liquid Glass", font=lockscreen._font(96, "Medium"), fill="white", anchor="mm")
    d.text((W // 2, 330), f"{len(masters)} glass icons · fallback mask for every other app",
           font=lockscreen._font(38), fill=(255, 255, 255, 200), anchor="mm")
    size, cols = 150, 6
    names = list(masters)
    for i, name in enumerate(names):
        cx = int(60 + (W - 120) / cols * (i % cols + 0.5))
        cy = 540 + (i // cols) * 210
        _with_shadow(img, masters[name].resize((size, size), Image.LANCZOS), cx - size // 2, cy - size // 2)
    return img.convert("RGB")


def description_xml():
    t = THEME
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<theme>
    <title>{t["title"]}</title>
    <designer>{t["designer"]}</designer>
    <author>{t["author"]}</author>
    <version>{t["version"]}</version>
    <uiVersion>{t["ui_version"]}</uiVersion>
    <description>{t["description"]}</description>
    <miuiAdapterVersion>{t["adapter_version"]}</miuiAdapterVersion>
    <createTime>{date.today().isoformat()}</createTime>
</theme>
'''


PREVIEW_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Liquid Glass Preview</title>
<style>
:root{--bg:#0d0a1f;--fg:#f3f0ff;--muted:#a9a3c9;--card:#17122f;--line:#2c2552}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f4f2fb;--fg:#17122f;--muted:#5d5880;--card:#fff;--line:#e2def2}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}
main{max-width:1200px;margin:0 auto;padding:40px 16px 80px}
h1{font-size:clamp(28px,5vw,44px);margin:0}h2{font-size:20px;margin:48px 0 16px}
p.sub{color:var(--muted);margin:6px 0 0}
.row{display:flex;gap:28px;flex-wrap:wrap;justify-content:center}
figure{margin:0;text-align:center}figcaption{color:var(--muted);font-size:14px;margin-top:10px}
.phone{width:min(280px,80vw);aspect-ratio:1220/2656;border-radius:44px;padding:9px;background:#08060f;
 box-shadow:0 0 0 2px #3a335e,0 30px 60px -20px rgba(40,10,120,.55);position:relative}
.phone img{width:100%;height:100%;object-fit:cover;border-radius:36px;display:block}
.phone::after{content:"";position:absolute;top:22px;left:50%;width:14px;height:14px;margin-left:-7px;border-radius:50%;background:#000}
.ref .phone{width:min(220px,70vw)}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:28px}
.meta div{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.meta b{display:block;font-size:13px;color:var(--muted);font-weight:500}
</style></head><body><main>
<h1>Liquid Glass</h1>
<p class="sub">HyperOS theme for the Xiaomi 17 (1220 × 2656). These previews are rendered from the packaged assets.</p>
<div class="meta">
<div><b>Package</b>LiquidGlass.mtz</div><div><b>Icons</b>__ICONS__ apps + fallback mask</div>
<div><b>Lockscreen</b>MAML, live clock and charging orb</div><div><b>Version</b>__VERSION__</div>
</div>
<h2>Previews</h2>
<div class="row">
<figure><div class="phone"><img src="preview/preview_launcher_0.jpg" alt="Home screen"></div><figcaption>Home screen</figcaption></figure>
<figure><div class="phone"><img src="preview/preview_lockscreen_0.jpg" alt="Lockscreen"></div><figcaption>Lockscreen</figcaption></figure>
<figure><div class="phone"><img src="preview/preview_statusbar_0.jpg" alt="Control center"></div><figcaption>Control center</figcaption></figure>
<figure><div class="phone"><img src="preview/preview_icons_0.jpg" alt="Icon set"></div><figcaption>Icon set</figcaption></figure>
</div>
<h2>Wallpapers</h2>
<div class="row">
<figure><div class="phone"><img src="preview/wallpaper_home.jpg" alt="Home wallpaper"></div><figcaption>Home</figcaption></figure>
<figure><div class="phone"><img src="preview/wallpaper_lock.jpg" alt="Lock wallpaper"></div><figcaption>Lock</figcaption></figure>
</div>
</main></body></html>
"""


def main():
    shutil.rmtree(BUILD, ignore_errors=True)
    stage = os.path.join(BUILD, "mtz")
    for d in ("wallpaper", "preview"):
        os.makedirs(os.path.join(stage, d), exist_ok=True)

    home_wall, lock_wall = wallpapers.home(), wallpapers.lock()
    home_wall.save(os.path.join(stage, "wallpaper", "default_wallpaper.jpg"), quality=95)
    lock_wall.save(os.path.join(stage, "wallpaper", "default_lock_wallpaper.jpg"), quality=95)

    masters = build_icons(stage)
    lock_imgs = build_lockscreen(stage)

    # store previews are the design mockups themselves
    pv = os.path.join(stage, "preview")
    for src, name in DESIGN_PREVIEWS.items():
        design_preview(os.path.join(PROJECT, src)).save(os.path.join(pv, name), quality=92)
    render_icon_sheet(home_wall, masters).save(os.path.join(pv, "preview_icons_0.jpg"), quality=90)

    # renders of what the packaged assets actually compose, for checking against the mockups
    renders = os.path.join(BUILD, "renders")
    os.makedirs(renders, exist_ok=True)
    render_home(home_wall, masters).save(os.path.join(renders, "home.jpg"), quality=90)
    lockscreen.simulate(lock_wall, lock_imgs).save(os.path.join(renders, "lockscreen.jpg"), quality=90)

    with open(os.path.join(stage, "description.xml"), "w") as f:
        f.write(description_xml())

    os.makedirs(DIST, exist_ok=True)
    mtz = os.path.join(DIST, "LiquidGlass.mtz")
    _zip_dir(stage, mtz)

    # standalone preview page
    dpv = os.path.join(DIST, "preview")
    shutil.rmtree(dpv, ignore_errors=True)
    shutil.copytree(pv, dpv)
    home_wall.save(os.path.join(dpv, "wallpaper_home.jpg"), quality=88)
    lock_wall.save(os.path.join(dpv, "wallpaper_lock.jpg"), quality=88)
    with open(os.path.join(DIST, "preview.html"), "w") as f:
        f.write(PREVIEW_HTML.replace("__ICONS__", str(len(masters))).replace("__VERSION__", THEME["version"]))
    print(f"built {mtz} ({os.path.getsize(mtz) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
