"""Liquid Glass MAML lockscreen (designed at Xiaomi 17 native width, 1220px)."""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1220, 2656
SS = 3  # supersampling for PIL-drawn assets

FONT = "/usr/share/fonts/truetype/ubuntu/Ubuntu[wdth,wght].ttf"

# layout (px at 1220 width); Y_* ending in _B are offsets from the bottom edge
CARD_W, CARD_H, CARD_R = 520, 513, 70
CARD_Y, CARD_LX, CARD_RX = 743, 63, 637
FACE_D = 430
FACE_X, FACE_Y = CARD_RX + (CARD_W - FACE_D) // 2, CARD_Y + (CARD_H - FACE_D) // 2
PILL_W, PILL_H, PILL_Y = 253, 109, 1303
PILL_X = (342, 625)
ORB_R, HALO_R, ORB_B = 235, 265, 678  # orb centre = screen_height - ORB_B
WAVE_LEN = 470
ORB_LEVELS, ORB_PHASES = 11, 8  # pre-rendered fill frames: 0..100% in 10% steps x wave phases
BOTTOM_B = 268
HAND_SHADOW_DY = 5


def _font(size, weight="Regular"):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(weight)
    return f


def _canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def _down(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def _rim(size, radius, width=2.2, top=0.75, bottom=0.35):
    """Glass rim: bright at top, fading through the sides, a little light at the bottom."""
    w, h = size
    rim = _canvas(w, h)
    ImageDraw.Draw(rim).rounded_rectangle(
        [width * SS / 2, width * SS / 2, w * SS - width * SS / 2, h * SS - width * SS / 2],
        radius * SS, outline=(255, 255, 255, 255), width=int(width * SS))
    grad = Image.new("L", (1, h * SS))
    for y in range(h * SS):
        t = y / (h * SS)
        a = top * (1 - t / 0.5) + 0.10 * (t / 0.5) if t < 0.5 else 0.10 + (bottom - 0.10) * ((t - 0.5) / 0.5)
        grad.putpixel((0, y), int(255 * a))
    alpha = Image.composite(grad.resize(rim.size), Image.new("L", rim.size, 0), rim.getchannel("A"))
    rim.putalpha(alpha)
    return rim


def glass_rect(w, h, r, fill=(26, 14, 78, 105)):
    img = _canvas(w, h)
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=fill)
    # faint top sheen
    sheen = _canvas(w, h)
    ImageDraw.Draw(sheen).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=(255, 255, 255, 22))
    fade = Image.linear_gradient("L").resize(sheen.size).point(lambda v: 255 - v)
    sheen.putalpha(Image.composite(fade, Image.new("L", sheen.size, 0), sheen.getchannel("A")))
    img.alpha_composite(sheen)
    img.alpha_composite(_rim((w, h), r))
    return _down(img)


def clock_face():
    d = FACE_D * SS
    c = d / 2
    img = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.ellipse([0, 0, d - 1, d - 1], fill=(18, 18, 28, 255))
    dr.ellipse([3 * SS, 3 * SS, d - 3 * SS, d - 3 * SS], outline=(255, 255, 255, 40), width=2 * SS)
    for i in range(60):
        a = math.radians(i * 6 - 90)
        r1, r2 = c - 14 * SS, c - (30 if i % 5 == 0 else 22) * SS
        dr.line([(c + r1 * math.cos(a), c + r1 * math.sin(a)), (c + r2 * math.cos(a), c + r2 * math.sin(a))],
                fill=(255, 255, 255, 235 if i % 5 == 0 else 140), width=(3 if i % 5 == 0 else 2) * SS)
    f = _font(38 * SS, "Regular")
    for n in range(1, 13):
        a = math.radians(n * 30 - 90)
        r = c - 66 * SS
        dr.text((c + r * math.cos(a), c + r * math.sin(a)), str(n), font=f, fill=(255, 255, 255, 245), anchor="mm")
    return _down(img)


def hand(length, width, color, tail=0, dot=0):
    d = FACE_D * SS
    c = d / 2
    img = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.line([(c, c + tail * SS), (c, c - length * SS)], fill=color, width=int(width * SS))
    dr.ellipse([c - width * SS / 2, c - length * SS - width * SS / 2, c + width * SS / 2, c - length * SS + width * SS / 2],
               fill=color)
    if dot:
        dr.ellipse([c - dot * SS, c - dot * SS, c + dot * SS, c + dot * SS], fill=color)
        dr.ellipse([c - dot * SS / 2.4, c - dot * SS / 2.4, c + dot * SS / 2.4, c + dot * SS / 2.4], fill=(18, 18, 28, 255))
    return _down(img)


def hand_shadow(img):
    """Soft dark copy of a hand; drawn a few px lower so the light always falls from above."""
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(img.getchannel("A").point(lambda v: int(v * 0.55)))
    return sh.filter(ImageFilter.GaussianBlur(3))


def orb_assets():
    d = ORB_R * 2
    # empty part of the orb: coral-to-magenta glass
    empty = Image.new("RGBA", (d, d))
    grad = Image.new("RGBA", (d, d))
    gd = ImageDraw.Draw(grad)
    for y in range(d):
        t = y / d
        gd.line([(0, y), (d, y)], fill=(int(235 - 40 * t), int(80 - 20 * t), int(110 + 30 * t), 235))
    mask = Image.new("L", (d * SS, d * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d * SS - 1, d * SS - 1], fill=255)
    mask = mask.resize((d, d), Image.LANCZOS)
    empty.paste(grad, (0, 0), mask)

    # liquid: periodic sine strip; each frame crops it at a level and phase, clipped to the circle
    wave_w, wave_h, amp = d + WAVE_LEN * 2, d + 60, 16
    wave = Image.new("RGBA", (wave_w * SS, wave_h * SS), (0, 0, 0, 0))
    pts = [(x, (amp + amp * math.sin(2 * math.pi * x / (WAVE_LEN * SS))) * SS + 4 * SS)
           for x in range(0, wave_w * SS + 1, SS)]
    ImageDraw.Draw(wave).polygon(pts + [(wave_w * SS, wave_h * SS), (0, wave_h * SS)], fill=(255, 255, 255, 255))
    wave = wave.resize((wave_w, wave_h), Image.LANCZOS)
    col = Image.new("RGBA", (wave_w, wave_h))
    cd = ImageDraw.Draw(col)
    for y in range(wave_h):
        t = y / wave_h
        cd.line([(0, y), (wave_w, y)], fill=(int(90 - 40 * t), int(230 - 30 * t), int(170 - 10 * t), 255))
    col.putalpha(wave.getchannel("A"))

    # gloss highlight + halo ring
    gloss = Image.new("RGBA", (d * SS, d * SS), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(gloss)
    gdr.ellipse([0, 0, d * SS - 1, d * SS - 1], outline=(255, 210, 230, 200), width=3 * SS)
    gdr.ellipse([d * SS * 0.18, d * SS * 0.05, d * SS * 0.82, d * SS * 0.40], fill=(255, 255, 255, 20))
    gloss = gloss.filter(ImageFilter.GaussianBlur(6 * SS)).resize((d, d), Image.LANCZOS)

    hd = HALO_R * 2
    halo = Image.new("RGBA", (hd * SS, hd * SS), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([0, 0, hd * SS - 1, hd * SS - 1], fill=(255, 255, 255, 46))
    ImageDraw.Draw(halo).ellipse([(HALO_R - ORB_R) * SS, (HALO_R - ORB_R) * SS,
                                  (HALO_R + ORB_R) * SS, (HALO_R + ORB_R) * SS], fill=(0, 0, 0, 0))
    halo = halo.resize((hd, hd), Image.LANCZOS)

    out = {"orb_gloss.png": gloss, "orb_halo.png": halo}
    for lv in range(ORB_LEVELS):
        for ph in range(ORB_PHASES):
            frame = empty.copy()
            liquid = Image.new("RGBA", (d, d), (0, 0, 0, 0))
            off = int(WAVE_LEN * ph / ORB_PHASES)
            liquid.alpha_composite(col.crop((off, 0, off + d, wave_h)), (0, int(d - d * lv / (ORB_LEVELS - 1) - 20)))
            liquid.putalpha(Image.composite(liquid.getchannel("A"), Image.new("L", (d, d), 0), mask))
            frame.alpha_composite(liquid)
            out[f"orb_fill_{lv * ORB_PHASES + ph}.png"] = frame
    return out


def _glyph_canvas(size):
    return Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))


def glyphs():
    out = {}
    s = 62  # lock
    g = _glyph_canvas(s); d = ImageDraw.Draw(g); k = SS
    d.rounded_rectangle([14 * k, 27 * k, 48 * k, 54 * k], 7 * k, outline="white", width=4 * k)
    d.arc([20 * k, 8 * k, 42 * k, 36 * k], 180, 360, fill="white", width=4 * k)
    d.line([(20 * k, 22 * k), (20 * k, 28 * k)], fill="white", width=4 * k)
    d.line([(42 * k, 22 * k), (42 * k, 28 * k)], fill="white", width=4 * k)
    out["ic_lock.png"] = _down(g)

    s = 70  # camera
    g = _glyph_canvas(s); d = ImageDraw.Draw(g)
    d.rounded_rectangle([6 * k, 18 * k, 64 * k, 58 * k], 9 * k, fill="white")
    d.rounded_rectangle([22 * k, 11 * k, 48 * k, 22 * k], 4 * k, fill="white")
    d.ellipse([24 * k, 26 * k, 46 * k, 48 * k], fill=(0, 0, 0, 0))
    d.ellipse([28 * k, 30 * k, 42 * k, 44 * k], fill="white")
    out["ic_camera.png"] = _down(g)

    s = 56  # battery
    g = _glyph_canvas(s); d = ImageDraw.Draw(g)
    d.rounded_rectangle([3 * k, 15 * k, 48 * k, 41 * k], 7 * k, outline="white", width=3 * k)
    d.rounded_rectangle([49 * k, 23 * k, 54 * k, 33 * k], 2 * k, fill="white")
    d.rounded_rectangle([8 * k, 20 * k, 43 * k, 36 * k], 4 * k, fill=(76, 217, 120, 255))
    d.polygon([(28 * k, 19 * k), (19 * k, 29 * k), (26 * k, 29 * k), (23 * k, 38 * k), (33 * k, 27 * k), (26 * k, 27 * k)],
              fill="white")
    out["ic_battery.png"] = _down(g)

    s = 56  # alarm
    g = _glyph_canvas(s); d = ImageDraw.Draw(g)
    d.ellipse([9 * k, 11 * k, 47 * k, 49 * k], outline="white", width=4 * k)
    d.line([(28 * k, 19 * k), (28 * k, 31 * k), (36 * k, 36 * k)], fill="white", width=4 * k, joint="curve")
    d.arc([2 * k, 2 * k, 20 * k, 20 * k], 180, 270, fill="white", width=4 * k)
    d.arc([36 * k, 2 * k, 54 * k, 20 * k], 270, 360, fill="white", width=4 * k)
    out["ic_alarm.png"] = _down(g)

    s = 76  # weather: sun behind cloud (matches the Weather app icon)
    g = _glyph_canvas(s); d = ImageDraw.Draw(g)
    d.ellipse([12 * k, 8 * k, 44 * k, 40 * k], fill=(255, 201, 60, 255))
    d.ellipse([8 * k, 36 * k, 34 * k, 62 * k], fill="white")
    d.ellipse([22 * k, 22 * k, 56 * k, 56 * k], fill="white")
    d.ellipse([44 * k, 36 * k, 70 * k, 62 * k], fill="white")
    d.rounded_rectangle([8 * k, 46 * k, 70 * k, 62 * k], 8 * k, fill="white")
    out["ic_weather.png"] = _down(g)

    s = 44  # swipe-up chevron
    g = _glyph_canvas(s); d = ImageDraw.Draw(g)
    d.line([(8 * k, 28 * k), (22 * k, 15 * k), (36 * k, 28 * k)], fill="white", width=4 * k, joint="curve")
    for x in (8, 36):
        d.ellipse([(x - 2) * k, 26 * k, (x + 2) * k, 30 * k], fill="white")
    out["ic_chevron.png"] = _down(g)
    return out


def assets():
    a = {
        "card_weather.png": glass_rect(CARD_W, CARD_H, CARD_R, (24, 14, 84, 120)),
        "card_clock.png": glass_rect(CARD_W, CARD_H, CARD_R, (10, 40, 70, 90)),
        "pill.png": glass_rect(PILL_W, PILL_H, PILL_H // 2, (40, 20, 90, 110)),
        "clock_face.png": clock_face(),
        "hand_hour.png": hand(108, 11, (255, 255, 255, 255), tail=18),
        "hand_min.png": hand(160, 8, (255, 255, 255, 255), tail=22),
        "hand_sec.png": hand(178, 3.5, (64, 132, 255, 255), tail=34, dot=11),
    }
    for n in ("hand_hour", "hand_min", "hand_sec"):
        a[n + "_shadow.png"] = hand_shadow(a[n + ".png"])
    a.update(orb_assets())
    a.update(glyphs())
    return a


MANIFEST = f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Liquid Glass lockscreen. Designed at 1220px width (Xiaomi 17, 1220x2656). -->
<Lockscreen version="2" frameRate="60" screenWidth="1220" displayDesktop="false">
  <VariableBinders>
    <ContentProviderBinder name="weather" uri="content://weather/actualWeatherData/1"
        columns="city_name,description,temperature,tmphighs,tmplows" countName="has_weather">
      <Variable name="w_city" type="string" column="city_name"/>
      <Variable name="w_desc" type="string" column="description"/>
      <Variable name="w_temp" type="int" column="temperature"/>
      <Variable name="w_high" type="int" column="tmphighs"/>
      <Variable name="w_low" type="int" column="tmplows"/>
    </ContentProviderBinder>
  </VariableBinders>

  <Var name="charging" expression="eq(#battery_state,1)+eq(#battery_state,3)"/>
  <Var name="orb_cy" expression="#screen_height-{ORB_B}"/>
  <Var name="drag" expression="0"/>
  <Var name="start_y" expression="0"/>

  <Wallpaper/>

  <Group name="content" x="0" y="-#drag*0.35" alpha="max(0,255-#drag*0.6)">
    <Image src="ic_lock.png" x="610" y="208" align="center" alignV="center"/>
    <DateTime x="610" y="310" align="center" alignV="center" color="#FFFFFF" size="50" fontFamily="mipro-medium"
        format="EEEE, d MMMM" shadowColor="#30000000" shadowDy="2"/>
    <DateTime x="610" y="516" align="center" alignV="center" color="#FFFFFF" size="325" fontFamily="mipro-regular"
        format="HH:mm" visibility="eq(#time_format,1)"/>
    <DateTime x="610" y="516" align="center" alignV="center" color="#FFFFFF" size="325" fontFamily="mipro-regular"
        format="h:mm" visibility="ne(#time_format,1)"/>

    <!-- weather card -->
    <Image src="card_weather.png" x="{CARD_LX}" y="{CARD_Y}"/>
    <Image src="ic_weather.png" x="{CARD_LX + CARD_W - 52 - 76}" y="{CARD_Y + 52}"/>
    <Group visibility="gt(#has_weather,0)">
      <Text x="{CARD_LX + 59}" y="{CARD_Y + 81}" alignV="center" color="#FFFFFF" size="47" bold="true"
          fontFamily="mipro-demibold" textExp="@w_city"/>
      <Text x="{CARD_LX + 59}" y="{CARD_Y + 142}" alignV="center" color="#B8FFFFFF" size="44" textExp="@w_desc"/>
      <Text x="{CARD_LX + 52}" y="{CARD_Y + 289}" alignV="center" color="#FFFFFF" size="164" fontFamily="mipro-light"
          format="%d°" paras="#w_temp"/>
      <Text x="{CARD_LX + 59}" y="{CARD_Y + 433}" alignV="center" color="#FFFFFF" size="39"
          format="High %d°  Low %d°" paras="#w_high,#w_low"/>
    </Group>
    <Group visibility="eq(#has_weather,0)">
      <Text x="{CARD_LX + 59}" y="{CARD_Y + 81}" alignV="center" color="#FFFFFF" size="47" bold="true" text="Weather"/>
      <Text x="{CARD_LX + 59}" y="{CARD_Y + 142}" alignV="center" color="#B8FFFFFF" size="44" text="Unavailable"/>
      <DateTime x="{CARD_LX + 52}" y="{CARD_Y + 289}" alignV="center" color="#FFFFFF" size="164" fontFamily="mipro-light"
          format="d"/>
      <DateTime x="{CARD_LX + 59}" y="{CARD_Y + 433}" alignV="center" color="#FFFFFF" size="39" format="EEEE"/>
    </Group>

    <!-- analog clock card -->
    <Image src="card_clock.png" x="{CARD_RX}" y="{CARD_Y}"/>
    <Image src="clock_face.png" x="{FACE_X}" y="{FACE_Y}"/>
    <Image src="hand_hour_shadow.png" x="{FACE_X}" y="{FACE_Y + HAND_SHADOW_DY}" pivotX="{FACE_D // 2}" pivotY="{FACE_D // 2}"
        rotation="#hour12*30+#minute*0.5"/>
    <Image src="hand_hour.png" x="{FACE_X}" y="{FACE_Y}" pivotX="{FACE_D // 2}" pivotY="{FACE_D // 2}"
        rotation="#hour12*30+#minute*0.5"/>
    <Image src="hand_min_shadow.png" x="{FACE_X}" y="{FACE_Y + HAND_SHADOW_DY}" pivotX="{FACE_D // 2}" pivotY="{FACE_D // 2}"
        rotation="#minute*6+#second*0.1"/>
    <Image src="hand_min.png" x="{FACE_X}" y="{FACE_Y}" pivotX="{FACE_D // 2}" pivotY="{FACE_D // 2}"
        rotation="#minute*6+#second*0.1"/>
    <Image src="hand_sec_shadow.png" x="{FACE_X}" y="{FACE_Y + HAND_SHADOW_DY}" pivotX="{FACE_D // 2}" pivotY="{FACE_D // 2}"
        rotation="#second*6"/>
    <Image src="hand_sec.png" x="{FACE_X}" y="{FACE_Y}" pivotX="{FACE_D // 2}" pivotY="{FACE_D // 2}"
        rotation="#second*6"/>

    <!-- pills: battery, next alarm -->
    <Image src="pill.png" x="{PILL_X[0]}" y="{PILL_Y}"/>
    <Image src="ic_battery.png" x="{PILL_X[0] + 34}" y="{PILL_Y + PILL_H // 2}" alignV="center"/>
    <Text x="{PILL_X[0] + 104}" y="{PILL_Y + PILL_H // 2}" alignV="center" color="#FFFFFF" size="42"
        fontFamily="mipro-medium" format="%d%%" paras="#battery_level"/>
    <Image src="pill.png" x="{PILL_X[1]}" y="{PILL_Y}"/>
    <Image src="ic_alarm.png" x="{PILL_X[1] + 34}" y="{PILL_Y + PILL_H // 2}" alignV="center"/>
    <Text x="{PILL_X[1] + 104}" y="{PILL_Y + PILL_H // 2}" alignV="center" color="#FFFFFF" size="42"
        fontFamily="mipro-medium" textExp="ifelse(strIsEmpty(@next_alarm_time),'Off',@next_alarm_time)"/>

    <!-- liquid charging orb -->
    <Group visibility="gt(#charging,0)">
      <Image src="orb_halo.png" x="610" y="#orb_cy" align="center" alignV="center"/>
      <!-- frame = level bucket * phases + wave phase; srcid N loads orb_fill_N.png -->
      <Image src="orb_fill.png" x="610" y="#orb_cy" align="center" alignV="center"
          srcid="int(#battery_level/10+0.5)*{ORB_PHASES}+int(#time/140)%{ORB_PHASES}"/>
      <Image src="orb_gloss.png" x="610" y="#orb_cy" align="center" alignV="center"/>
      <Text x="610" y="#orb_cy-12" align="center" alignV="center" color="#FFFFFF" size="130" fontFamily="mipro-light"
          format="%d%%" paras="#battery_level" shadowColor="#40000000" shadowDy="3"/>
      <Text x="610" y="#orb_cy+78" align="center" alignV="center" color="#FFFFFF" size="35" fontFamily="mipro-medium"
          textExp="ifelse(eq(#battery_state,3),'Fully charged','Charging')"/>
    </Group>

    <Text x="610" y="#screen_height-{BOTTOM_B}" align="center" alignV="center" color="#E6FFFFFF" size="40"
        text="Swipe up to unlock"/>
    <Image src="ic_chevron.png" x="610" y="#screen_height-{BOTTOM_B}-62-abs(sin(#time/450))*10" align="center"
        alignV="center" alpha="200"/>
    <Image src="ic_camera.png" x="1021" y="#screen_height-{BOTTOM_B}" align="center" alignV="center"/>
  </Group>

  <!-- swipe-up gesture over the whole screen -->
  <Button x="0" y="0" w="#screen_width" h="#screen_height">
    <Triggers>
      <Trigger action="down">
        <VariableCommand name="start_y" expression="#touch_y"/>
      </Trigger>
      <Trigger action="move">
        <VariableCommand name="drag" expression="max(0,#start_y-#touch_y)"/>
      </Trigger>
      <Trigger action="up">
        <ExternCommand command="unlock" condition="ge(#drag,320)"/>
        <VariableCommand name="drag" expression="0"/>
      </Trigger>
      <Trigger action="cancel">
        <VariableCommand name="drag" expression="0"/>
      </Trigger>
    </Triggers>
  </Button>

  <!-- camera shortcut sits above the gesture layer so it gets the tap -->
  <Button x="1021-70" y="#screen_height-{BOTTOM_B}-70" w="140" h="140">
    <Triggers>
      <Trigger action="up">
        <IntentCommand action="android.media.action.STILL_IMAGE_CAMERA_SECURE" flags="268435456"/>
      </Trigger>
    </Triggers>
  </Button>
</Lockscreen>
'''


def write(out_dir):
    adv = os.path.join(out_dir, "advance")
    os.makedirs(adv, exist_ok=True)
    imgs = assets()
    for name, img in imgs.items():
        img.save(os.path.join(adv, name))
    with open(os.path.join(adv, "manifest.xml"), "w") as f:
        f.write(MANIFEST)
    return imgs


def simulate(wallpaper, imgs, battery=53, charging=True, hh=12, mm=25, ss=34):
    """Draw the manifest's layout with PIL so the theme ships a truthful lockscreen preview."""
    img = wallpaper.convert("RGBA").resize((W, H))

    def text(xy, s, size, weight="Regular", fill="white", anchor="lm"):
        ImageDraw.Draw(img).text(xy, s, font=_font(size, weight), fill=fill, anchor=anchor)

    def paste(name, x, y, center=False):
        im = imgs[name]
        if center:
            x, y = x - im.width // 2, y - im.height // 2
        img.alpha_composite(im, (int(x), int(y)))

    paste("ic_lock.png", 610, 208, True)
    text((610, 310), "Saturday, 24 October", 50, "Medium", anchor="mm")
    text((610, 516), f"{hh}:{mm:02d}", 300, "Light", anchor="mm")

    paste("card_weather.png", CARD_LX, CARD_Y)
    paste("ic_weather.png", CARD_LX + CARD_W - 52 - 76, CARD_Y + 52)
    text((CARD_LX + 59, CARD_Y + 81), "Nairobi", 47, "Medium")
    text((CARD_LX + 59, CARD_Y + 142), "Cloudy", 44, fill=(255, 255, 255, 184))
    text((CARD_LX + 52, CARD_Y + 289), "23°", 164, "Light")
    text((CARD_LX + 59, CARD_Y + 433), "High 31°  Low 17°", 39)

    paste("card_clock.png", CARD_RX, CARD_Y)
    paste("clock_face.png", FACE_X, FACE_Y)
    for name, ang in (("hand_hour.png", (hh % 12) * 30 + mm * 0.5),
                      ("hand_min.png", mm * 6 + ss * 0.1), ("hand_sec.png", ss * 6)):
        shadow = imgs[name.replace(".png", "_shadow.png")]
        img.alpha_composite(shadow.rotate(-ang, resample=Image.BICUBIC), (FACE_X, FACE_Y + HAND_SHADOW_DY))
        img.alpha_composite(imgs[name].rotate(-ang, resample=Image.BICUBIC), (FACE_X, FACE_Y))

    for x, icon, label in ((PILL_X[0], "ic_battery.png", f"{battery}%"), (PILL_X[1], "ic_alarm.png", "07:00")):
        paste("pill.png", x, PILL_Y)
        paste(icon, x + 34, PILL_Y + PILL_H // 2 - imgs[icon].height // 2)
        text((x + 104, PILL_Y + PILL_H // 2), label, 42, "Medium")

    if charging:
        cy = H - ORB_B
        paste("orb_halo.png", 610, cy, True)
        paste(f"orb_fill_{int(battery / 10 + 0.5) * ORB_PHASES + 3}.png", 610, cy, True)
        paste("orb_gloss.png", 610, cy, True)
        text((610, cy - 12), f"{battery}%", 130, "Light", anchor="mm")
        text((610, cy + 78), "Charging", 35, "Medium", anchor="mm")

    text((610, H - BOTTOM_B), "Swipe up to unlock", 40, fill=(255, 255, 255, 230), anchor="mm")
    paste("ic_chevron.png", 610, H - BOTTOM_B - 66, True)
    paste("ic_camera.png", 1021, H - BOTTOM_B, True)
    return img.convert("RGB")
