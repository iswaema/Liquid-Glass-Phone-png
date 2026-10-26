"""Liquid Glass icon set: SVG squircle + glyph, composited with a soft glyph shadow and glass rim."""
import io
import math

import cairosvg
from PIL import Image, ImageChops, ImageFilter

MASTER = 432  # render size; downscaled per density bucket


def squircle(inset=3.0, n=4.3, size=100.0, steps=160):
    """Superellipse path (HyperOS-style continuous-corner squircle) in a 100-unit box."""
    r = size / 2 - inset
    c = size / 2
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        ct, st = math.cos(t), math.sin(t)
        x = c + r * math.copysign(abs(ct) ** (2 / n), ct)
        y = c + r * math.copysign(abs(st) ** (2 / n), st)
        pts.append(f"{x:.3f},{y:.3f}")
    return "M" + " L".join(pts) + " Z"


SQ = squircle()
SQ_RIM = squircle(inset=3.8)


def gear(cx=50, cy=50, ro=26, ri=20.5, teeth=12, hole=9):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4) - math.pi / 2
        r = ro if (i % 4) in (1, 2) else ri
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    outer = "M" + " L".join(pts) + " Z"
    inner = (f"M{cx + hole},{cy} A{hole},{hole} 0 1 0 {cx - hole},{cy} "
             f"A{hole},{hole} 0 1 0 {cx + hole},{cy} Z")
    return f'<path fill-rule="evenodd" d="{outer} {inner}" fill="#fff"/>'



# glyphs drawn in a 100x100 box; white is the base ink
G = {
    "gallery": '''<rect x="22" y="30" width="46" height="38" rx="8" fill="#fff" opacity=".5" transform="rotate(-9 45 49)"/>
<rect x="30" y="33" width="47" height="39" rx="8" fill="#fff"/>
<circle cx="66" cy="44" r="4.6" fill="#FF9A3C"/>
<path d="M34 68 L47 52 L56 62 L62 56 L73 68 Z" fill="#F0455A"/>''',
    "store": '''<path d="M41 40 v-5 a9 9 0 0 1 18 0 v5" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
<path d="M29 40 h42 l-3 30 a7 7 0 0 1 -7 6 h-22 a7 7 0 0 1 -7 -6 z" fill="#fff"/>
<path d="M42 52 a8 8 0 0 0 16 0" stroke="#2F6BF0" stroke-width="4.5" fill="none" stroke-linecap="round"/>''',
    "music": '''<path d="M43 66 V32 L71 25 V60" stroke="#fff" stroke-width="6" fill="none" stroke-linejoin="round" stroke-linecap="round"/>
<ellipse cx="35.5" cy="66" rx="9" ry="7.5" fill="#fff"/><ellipse cx="63.5" cy="60" rx="9" ry="7.5" fill="#fff"/>''',
    "themes": '''<path d="M50 23 C33 23 22 35 22 50 C22 65 34 77 48 77 C54 77 56 72 53 68 C50 63 53 59 59 59 H66 C73 59 78 54 78 46 C78 33 65 23 50 23 Z" fill="#fff"/>
<circle cx="36" cy="47" r="5" fill="#F5B400"/><circle cx="45" cy="35" r="5" fill="#2DBE6C"/>
<circle cx="59" cy="34" r="5" fill="#3D7BFF"/><circle cx="67" cy="46" r="5" fill="#F0455A"/>''',
    "files": '''<path d="M23 35 a6 6 0 0 1 6 -6 h13 l6 6 h23 a6 6 0 0 1 6 6 v26 a6 6 0 0 1 -6 6 h-42 a6 6 0 0 1 -6 -6 z" fill="#fff"/>
<rect x="39" y="50" width="22" height="5.5" rx="2.75" fill="#F59A23"/>''',
    "browser": '''<circle cx="50" cy="50" r="25" fill="none" stroke="#fff" stroke-width="5"/>
<ellipse cx="50" cy="50" rx="11" ry="25" fill="none" stroke="#fff" stroke-width="4.5"/>
<path d="M25 50 H75 M29 37.5 H71 M29 62.5 H71" stroke="#fff" stroke-width="4.5"/>''',
    "maps": '''<path d="M23 35 L38 29 L62 37 L77 31 V68 L62 74 L38 66 L23 72 Z" fill="#fff"/>
<path d="M38 29 V66 M62 37 V74" stroke="#1E9E63" stroke-opacity=".3" stroke-width="2"/>
<path d="M63 17 a10.5 10.5 0 0 1 10.5 10.5 c0 8 -10.5 18.5 -10.5 18.5 s-10.5 -10.5 -10.5 -18.5 a10.5 10.5 0 0 1 10.5 -10.5z" fill="#F0455A"/>
<circle cx="63" cy="27.5" r="3.8" fill="#fff"/>''',
    "weather": '''<circle cx="41" cy="40" r="12.5" fill="#FFC93C"/>
<path d="M35 73 h33 a11.5 11.5 0 0 0 1 -23 a14.5 14.5 0 0 0 -28 -2 a12.5 12.5 0 0 0 -6 25 z" fill="#fff"/>''',
    "security": '''<path d="M50 21 L75 30 V48 C75 63 65 73 50 79 C35 73 25 63 25 48 V30 Z" fill="#fff"/>
<path d="M39 50 L47 58 L62 42" stroke="#16A889" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>''',
    "calculator": '''<rect x="25" y="25" width="22" height="22" rx="6.5" fill="#fff"/><rect x="53" y="25" width="22" height="22" rx="6.5" fill="#fff"/>
<rect x="25" y="53" width="22" height="22" rx="6.5" fill="#fff"/><rect x="53" y="53" width="22" height="22" rx="6.5" fill="#FF9A3C"/>
<path d="M36 30.5 V41.5 M30.5 36 H41.5 M58.5 36 H69.5 M32 60 L40 68 M40 60 L32 68" stroke="#2A2A3A" stroke-width="3.2" stroke-linecap="round"/>
<path d="M58.5 61 H69.5 M58.5 67 H69.5" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/>''',
    "notes": '''<rect x="29" y="23" width="42" height="54" rx="9" fill="#fff"/>
<path d="M29 32 a9 9 0 0 1 9 -9 h24 a9 9 0 0 1 9 9 v4 h-42 z" fill="#F59A23"/>
<path d="M37 48 H63 M37 57 H63 M37 66 H54" stroke="#F5B400" stroke-width="4" stroke-linecap="round"/>''',
    "calendar": '''<rect x="25" y="28" width="50" height="47" rx="10" fill="#fff" stroke="#D9D4EE" stroke-width="1.5"/>
<path d="M25 38 a10 10 0 0 1 10 -10 h30 a10 10 0 0 1 10 10 v5 h-50 z" fill="#F0455A"/>
<rect x="36" y="22" width="5" height="12" rx="2.5" fill="#B42339"/><rect x="59" y="22" width="5" height="12" rx="2.5" fill="#B42339"/>
<g fill="#8A84B0"><circle cx="36" cy="52" r="3"/><circle cx="46" cy="52" r="3"/><circle cx="56" cy="52" r="3"/><circle cx="66" cy="52" r="3"/>
<circle cx="36" cy="63" r="3"/><circle cx="46" cy="63" r="3"/><circle cx="66" cy="63" r="3"/></g>
<circle cx="56" cy="63" r="4.2" fill="#F0455A"/>''',
    "mail": '''<rect x="23" y="31" width="54" height="39" rx="9" fill="#fff"/>
<path d="M28 38 L50 53 L72 38" stroke="#5A55F0" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>''',
    "wallet": '''<rect x="27" y="25" width="46" height="20" rx="6" fill="#3D9BFF"/>
<rect x="27" y="33" width="46" height="20" rx="6" fill="#FFB23D"/>
<rect x="24" y="42" width="52" height="33" rx="9" fill="#fff"/>
<rect x="58" y="54" width="13" height="8" rx="4" fill="#2A2A3A"/>''',
    "health": '''<path d="M50 75 C30 61 22 51 22 41 C22 32 29 25 37 25 C43 25 47 28 50 33 C53 28 57 25 63 25 C71 25 78 32 78 41 C78 51 70 61 50 75 Z" fill="#fff"/>
<path d="M27 49 H40 L45 40 L52 59 L57 46 H73" stroke="#E5304A" stroke-width="4.5" fill="none" stroke-linejoin="round" stroke-linecap="round"/>''',
    "clock": '''<circle cx="50" cy="50" r="27" fill="#fff"/>
<path d="M50 32 V50 L38 59" stroke="#1D1D28" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
<path d="M50 50 L42 65" stroke="#FF8A2B" stroke-width="2.6" stroke-linecap="round"/>
<circle cx="50" cy="50" r="3.6" fill="#1D1D28"/>''',
    "phone": '''<path d="M37 24 c3 0 5 2 6 5 l3 8 c1 3 0 5 -2 7 l-4 3 c3 7 9 13 16 16 l3 -4 c2 -2 4 -3 7 -2 l8 3 c3 1 5 3 5 6 v6 c0 4 -3 7 -7 7 C46 79 21 54 21 31 c0 -4 3 -7 7 -7 z" fill="#fff"/>''',
    "contacts": '''<circle cx="50" cy="39" r="12" fill="#fff"/>
<path d="M27 74 c0 -13 10 -21 23 -21 s23 8 23 21 z" fill="#fff"/>''',
    "messages": '''<path d="M50 23 C65 23 78 33 78 47 C78 61 65 71 50 71 C47 71 44 70.6 41 69.8 L28 76 L31 63.5 C26 59 22 53 22 47 C22 33 35 23 50 23 Z" fill="#fff"/>
<circle cx="38" cy="47" r="3.8" fill="#15A67A"/><circle cx="50" cy="47" r="3.8" fill="#15A67A"/><circle cx="62" cy="47" r="3.8" fill="#15A67A"/>''',
    "camera": '''<circle cx="50" cy="51" r="25" fill="#1B1B2A" stroke="#E8E8F2" stroke-width="4"/>
<circle cx="50" cy="51" r="15" fill="#2D3A8C"/><circle cx="50" cy="51" r="8" fill="#0B0B16"/>
<circle cx="45" cy="46" r="3.2" fill="#fff" opacity=".85"/><circle cx="70" cy="29" r="3" fill="#FF8A2B"/>''',
    "recorder": ''.join(
        f'<rect x="{24 + i * 7}" y="{50 - h / 2}" width="4.5" height="{h}" rx="2.25" fill="#fff"/>'
        for i, h in enumerate([10, 22, 34, 46, 30, 40, 20, 12])),
    "compass": '''<circle cx="50" cy="50" r="26" fill="none" stroke="#fff" stroke-width="4.5"/>
<path d="M50 28 L57 50 H43 Z" fill="#FF5A5F"/><path d="M50 72 L43 50 H57 Z" fill="#fff"/>
<circle cx="50" cy="50" r="3.4" fill="#1D1D28"/>''',
    "screenrecorder": '''<circle cx="50" cy="50" r="25" fill="none" stroke="#fff" stroke-width="5"/>
<circle cx="50" cy="50" r="13" fill="#fff"/>''',
    "scanner": '''<path d="M25 38 V31 a6 6 0 0 1 6 -6 h7 M62 25 h7 a6 6 0 0 1 6 6 v7 M75 62 v7 a6 6 0 0 1 -6 6 h-7 M38 75 h-7 a6 6 0 0 1 -6 -6 v-7"
 stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/>
<rect x="30" y="47.5" width="40" height="5" rx="2.5" fill="#fff"/>''',
    "downloads": '''<path d="M50 24 V58 M36 45 L50 59 L64 45" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="27" y="68" width="46" height="6" rx="3" fill="#fff"/>''',
    "video": '''<path d="M40 30 Q36 28 36 33 V67 Q36 72 40 70 L69 53 Q73 50 69 47 Z" fill="#fff"/>''',
    "youtube": '''<rect x="22" y="31" width="56" height="38" rx="12" fill="#fff"/>
<path d="M44 40 V60 L61 50 Z" fill="#F0303A"/>''',
    "whatsapp": '''<path d="M50 23 a27 27 0 1 1 -14 50 l-12 3.5 3.5 -11.5 A27 27 0 0 1 50 23 Z" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>
<path d="M40 37 c2 0 3 1 3.5 2.5 l1.5 4 c.5 1.5 0 2.5 -1 3.5 l-1.5 1.5 c2 4 5 7 9 9 l1.5 -1.5 c1 -1 2 -1.5 3.5 -1 l4 1.5 c1.5 .5 2.5 1.5 2.5 3 v2.5 c0 2 -1.5 3.5 -3.5 3.5 C47 66 34 53 34 40.5 c0 -2 1.5 -3.5 3.5 -3.5 z" fill="#fff"/>''',
    "search": '''<circle cx="45" cy="45" r="16" fill="none" stroke="#fff" stroke-width="6"/>
<path d="M57 57 L72 72" stroke="#fff" stroke-width="7" stroke-linecap="round"/>''',
    "home": '''<path d="M50 24 L77 47 a3 3 0 0 1 -2 5 h-4 v18 a5 5 0 0 1 -5 5 h-32 a5 5 0 0 1 -5 -5 v-18 h-4 a3 3 0 0 1 -2 -5 Z" fill="#fff"/>
<rect x="44" y="56" width="12" height="19" rx="3" fill="#2E8BFF"/>''',
    "updater": '''<circle cx="50" cy="50" r="26" fill="#fff"/>
<path d="M50 64 V37 M39 47 L50 36 L61 47" stroke="#4B47E8" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>''',
}
G["settings"] = gear() + "".join(
    f'<circle cx="{50 + 14.5 * math.cos(math.radians(a)):.2f}" cy="{50 + 14.5 * math.sin(math.radians(a)):.2f}" r="1.6" fill="#8C8FA3"/>'
    for a in range(0, 360, 30))
G.update({
    "telegram": '''<path d="M23 48 L73 27 Q78 25 77 31 L69 71 Q67 76 62 73 L50 64 L44 70 Q41 72 41 69 L42 59 L66 37 L38 55 L26 52 Q21 50 23 48 Z" fill="#fff"/>''',
    "instagram": '''<rect x="25" y="25" width="50" height="50" rx="15" fill="none" stroke="#fff" stroke-width="5.5"/>
<circle cx="50" cy="50" r="11.5" fill="none" stroke="#fff" stroke-width="5.5"/><circle cx="64.5" cy="35.5" r="3.4" fill="#fff"/>''',
    "facebook": '''<path d="M54 78 V54 H62 L63.5 44 H54 V38 C54 35 55.5 33.5 58.5 33.5 H64 V24.5 C62 24.2 58.5 24 55.5 24 C47.5 24 43 28.5 43 37 V44 H35 V54 H43 V78 Z" fill="#fff"/>''',
    "spotify": '''<path d="M28 40 C42 35 59 36 72 43 M31 51 C43 47 57 48 68 54 M34 61 C44 58 54 59 63 64" stroke="#fff" stroke-width="5.5" fill="none" stroke-linecap="round"/>''',
    "drive": '''<path d="M40 25 H60 L80 60 L70 76 Z" fill="#FFC93C"/><path d="M40 25 L20 60 L30 76 L50 42 Z" fill="#1FA463"/>
<path d="M30 76 H70 L80 60 H40 Z" fill="#4285F4"/>''',
    "videocall": '''<rect x="21" y="33" width="40" height="34" rx="9" fill="#fff"/><path d="M64 45 L78 36 Q80 35 80 38 V62 Q80 65 78 64 L64 55 Z" fill="#fff"/>''',
    "netflix": '''<path d="M36 24 H46 L54 52 V24 H64 V76 H54 L46 48 V76 H36 Z" fill="#E50914"/>''',
    "tiktok": "".join(
        f'''<g transform="translate({d} {d})"><path d="M54 24 V61 A10 10 0 1 1 44 51 M54 24 C55 33 61 38 70 38.5"
 stroke="{c}" stroke-width="7" fill="none" stroke-linecap="round"/></g>'''
        for d, c in ((-1.6, "#25F4EE"), (1.6, "#FE2C55"), (0, "#fff"))),
    "mpesa": '''<rect x="33" y="21" width="34" height="58" rx="8" fill="#fff"/><rect x="37" y="28" width="26" height="38" rx="3" fill="#2E9E3A"/>
<path d="M41 58 V38 L50 49 L59 38 V58" stroke="#fff" stroke-width="4.2" fill="none" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="50" cy="72" r="2.6" fill="#2E9E3A"/>''',
    "ride": '''<path d="M30 52 L35 38 Q37 33 42 33 H58 Q63 33 65 38 L70 52 Q77 53 77 60 V67 Q77 69 75 69 H25 Q23 69 23 67 V60 Q23 53 30 52 Z" fill="#fff"/>
<path d="M36 51 L39.5 41 Q40.5 38.5 43.5 38.5 H56.5 Q59.5 38.5 60.5 41 L64 51 Z" fill="#2A2A3A"/>
<rect x="28" y="64" width="11" height="11" rx="3.5" fill="#fff"/><rect x="61" y="64" width="11" height="11" rx="3.5" fill="#fff"/>
<circle cx="32" cy="60" r="3.2" fill="#FFC93C"/><circle cx="68" cy="60" r="3.2" fill="#FFC93C"/>''',
})

# name -> (glyph, top colour, bottom colour, packages)
ICONS = {
    "gallery": ("gallery", "#FF8A5C", "#E8364F", ["com.miui.gallery", "com.google.android.apps.photos"]),
    "store": ("store", "#5AAEFF", "#2A5BEA", ["com.xiaomi.market", "com.xiaomi.mipicks", "com.android.vending"]),
    "music": ("music", "#FF6FB5", "#D9267E", ["com.miui.player", "com.google.android.apps.youtube.music"]),
    "themes": ("themes", "#C08BFF", "#7B3FF2", ["com.android.thememanager"]),
    "files": ("files", "#FFCB55", "#F08A1C", ["com.android.fileexplorer", "com.mi.android.globalFileexplorer",
                                               "com.google.android.documentsui"]),
    "browser": ("browser", "#45D6FF", "#1E7BF0", ["com.android.browser", "com.mi.globalbrowser", "com.android.chrome"]),
    "maps": ("maps", "#52D98F", "#1E9E63", ["com.google.android.apps.maps"]),
    "weather": ("weather", "#7CC0FF", "#3D6FF0", ["com.miui.weather2"]),
    "security": ("security", "#45DDB6", "#119C86", ["com.miui.securitycenter"]),
    "calculator": ("calculator", "#545468", "#22222E", ["com.miui.calculator"]),
    "notes": ("notes", "#FFE470", "#F5B400", ["com.miui.notes"]),
    "calendar": ("calendar", "#FFFFFF", "#E3DEF7", ["com.android.calendar", "com.xiaomi.calendar",
                                                    "com.google.android.calendar"]),
    "mail": ("mail", "#8A90FF", "#4B47E8", ["com.android.email", "com.google.android.gm"]),
    "wallet": ("wallet", "#4A4A5E", "#1E1E2A", ["com.mipay.wallet", "com.google.android.apps.walletnfcrel"]),
    "health": ("health", "#FF7A88", "#E5304A", ["com.mi.health"]),
    "clock": ("clock", "#4A4A5E", "#1E1E2A", ["com.android.deskclock", "com.google.android.deskclock"]),
    # MIUI resolves the dialer/contacts entry points by activity name
    "phone": ("phone", "#62E583", "#1FAE4A", ["com.android.contacts.activities.TwelveKeyDialer",
                                              "com.android.contacts.TwelveKeyDialer",
                                              "com.android.contacts.activities.CallLogActivity",
                                              "com.google.android.dialer", "com.android.incallui"]),
    "contacts": ("contacts", "#FFB067", "#F0702A", ["com.android.contacts.activities.PeopleActivity",
                                                     "com.android.contacts", "com.google.android.contacts"]),
    "messages": ("messages", "#55E3AE", "#14A076", ["com.android.mms", "com.google.android.apps.messaging"]),
    "camera": ("camera", "#9494AA", "#4A4A5E", ["com.android.camera", "com.google.android.GoogleCamera"]),
    "settings": ("settings", "#D2D4E0", "#8C8FA3", ["com.android.settings"]),
    "recorder": ("recorder", "#FF7E9A", "#E0335F", ["com.android.soundrecorder"]),
    "compass": ("compass", "#4A4A5E", "#1E1E2A", ["com.miui.compass"]),
    "screenrecorder": ("screenrecorder", "#FFA35C", "#F0602A", ["com.miui.screenrecorder"]),
    "scanner": ("scanner", "#5AAEFF", "#3550E8", ["com.xiaomi.scanner"]),
    "downloads": ("downloads", "#5AC8FF", "#2A72EA", ["com.android.providers.downloads.ui"]),
    "video": ("video", "#B47BFF", "#E2368F", ["com.miui.videoplayer", "com.miui.video"]),
    "youtube": ("youtube", "#FF5F5F", "#D11F2C", ["com.google.android.youtube"]),
    "whatsapp": ("whatsapp", "#5BE07F", "#169E4A", ["com.whatsapp"]),
    "search": ("search", "#9C8BFF", "#5A3BEA", ["com.google.android.googlequicksearchbox",
                                               "com.android.quicksearchbox"]),
    "smarthome": ("home", "#E9F3FF", "#B8D4FF", ["com.xiaomi.smarthome"]),
    "updater": ("updater", "#8A90FF", "#4B47E8", ["com.android.updater"]),
    "mpesa": ("mpesa", "#7BDB6E", "#2E9E3A", ["com.safaricom.mpesa.lifestyle", "com.safaricom.mysafaricom"]),
    "telegram": ("telegram", "#62CDFF", "#2385E0", ["org.telegram.messenger"]),
    "instagram": ("instagram", "#FFB46B", "#B33BEB", ["com.instagram.android"]),
    "facebook": ("facebook", "#5E8FFF", "#1F57E0", ["com.facebook.katana"]),
    "spotify": ("spotify", "#45E07E", "#159A47", ["com.spotify.music"]),
    "drive": ("drive", "#FFFFFF", "#E3DEF7", ["com.google.android.apps.docs"]),
    "videocall": ("videocall", "#5AA8FF", "#2D5BEA", ["us.zoom.videomeetings", "com.google.android.apps.tachyon"]),
    "netflix": ("netflix", "#3A3A4C", "#141419", ["com.netflix.mediaclient"]),
    "tiktok": ("tiktok", "#3A3A4C", "#141419", ["com.zhiliaoapp.musically", "com.ss.android.ugc.trill"]),
    "ride": ("ride", "#4A4A5E", "#1E1E2A", ["com.ubercab", "com.taxify.client"]),
}


def _svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{MASTER}" height="{MASTER}" viewBox="0 0 100 100">{body}</svg>'


def _png(body):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=_svg(body).encode()))).convert("RGBA")


def _plate(top, bottom, opacity=1.0):
    light = top.upper() == "#FFFFFF"
    return _png(f'''<defs>
<linearGradient id="bg" x1="0.2" y1="0" x2="0.5" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>
<radialGradient id="spec" cx="0.5" cy="0.05" r="0.62"><stop offset="0" stop-color="#fff" stop-opacity="{.16 if light else .42}"/>
<stop offset=".55" stop-color="#fff" stop-opacity="{.04 if light else .12}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<radialGradient id="refr" cx="0.5" cy="1.08" r="0.62"><stop offset="0" stop-color="{top}" stop-opacity="{0 if light else .9}"/>
<stop offset=".5" stop-color="#fff" stop-opacity="{0 if light else .10}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<clipPath id="c"><path d="{SQ}"/></clipPath></defs>
<g opacity="{opacity}"><path d="{SQ}" fill="url(#bg)"/>
<g clip-path="url(#c)"><rect width="100" height="62" fill="url(#spec)"/><rect y="38" width="100" height="62" fill="url(#refr)"/></g></g>''')


def _rim(light=False):
    """Glass edge: bright specular top, almost gone at the sides, refracted glow at the bottom."""
    a = .6 if light else .95
    return _png(f'''<defs><linearGradient id="r" x1="0" y1="0" x2="0.3" y2="1">
<stop offset="0" stop-color="#fff" stop-opacity="{a}"/><stop offset=".35" stop-color="#fff" stop-opacity=".18"/>
<stop offset=".7" stop-color="#fff" stop-opacity=".06"/><stop offset="1" stop-color="#fff" stop-opacity="{a * .65}"/></linearGradient></defs>
<path d="{SQ_RIM}" fill="none" stroke="url(#r)" stroke-width="1.8"/>''')


GLYPH_SCALE = 0.84


def _shade(img):
    """Faint top-to-bottom falloff so glyphs read as embossed glass rather than flat stickers."""
    tint = Image.composite(Image.new("RGB", img.size, (226, 222, 246)), Image.new("RGB", img.size, "white"),
                           Image.linear_gradient("L").resize(img.size))
    out = ImageChops.multiply(img.convert("RGB"), tint).convert("RGBA")
    out.putalpha(img.getchannel("A"))
    return out


def render(glyph, top, bottom):
    img = _plate(top, bottom)
    g = _shade(_png(f'<g transform="translate(50 50) scale({GLYPH_SCALE}) translate(-50 -50)">{glyph}</g>'))
    shadow = Image.new("RGBA", g.size, (20, 8, 60, 0))
    shadow.putalpha(g.getchannel("A").point(lambda v: int(v * 0.30)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(MASTER * 0.016))
    img.alpha_composite(shadow, (0, int(MASTER * 0.014)))
    img.alpha_composite(g)
    img.alpha_composite(_rim(top.upper() == "#FFFFFF"))
    return img


def fallback_layers():
    """Shape layers HyperOS uses to theme apps without a dedicated icon, plus the folder backdrop."""
    folder = _plate("#F2EEFF", "#C9BEFF", opacity=0.42)
    folder.alpha_composite(_rim())
    return {
        "icon_background.png": _plate("#A38FFF", "#6A4BF0"),
        "icon_mask.png": _png(f'<path d="{SQ}" fill="#000"/>'),
        "icon_border.png": _rim(),
        "icon_folder.png": folder,
    }


def build_all():
    """Yield (name, packages, master_image)."""
    for name, (glyph, top, bottom, pkgs) in ICONS.items():
        yield name, pkgs, render(G[glyph], top, bottom)
