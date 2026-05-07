"""One-shot script to generate static PWA icons (192x192 and 512x512 PNGs).
Run: python _gen_icons.py
After running, the icon-192.png and icon-512.png files appear in the same dir.
This script is committed for reproducibility but is not used at runtime.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

BG = (11, 15, 24, 255)          # #0b0f18
GREEN = (46, 204, 138, 255)     # #2ecc8a
GREEN_DARK = (26, 158, 102, 255)  # #1a9e66
TEXT_MUTED = (122, 143, 168, 255)  # #7a8fa8

def find_emoji_font(size):
    """Try Windows Segoe UI Emoji, else fall back to default."""
    candidates = [
        r"C:\Windows\Fonts\seguiemj.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def find_text_font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_radial_gradient_circle(img, cx, cy, r, color_inner, color_outer):
    """Approximate radial gradient by drawing concentric circles."""
    draw = ImageDraw.Draw(img)
    steps = max(40, int(r))
    for i in range(steps, 0, -1):
        t = (steps - i) / steps  # 0 at edge → 1 at center
        rr = int(r * (i / steps))
        col = tuple(
            int(color_outer[j] + (color_inner[j] - color_outer[j]) * t)
            for j in range(4)
        )
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col)

def make_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # rounded background
    radius = int(size * 0.22)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=BG)

    # green circle with radial-ish gradient
    cx, cy = size // 2, int(size * 0.44)
    r = int(size * 0.28)
    draw_radial_gradient_circle(img, cx, cy, r, GREEN, GREEN_DARK)

    # leaf emoji centered on circle
    emoji_font = find_emoji_font(int(size * 0.32))
    draw = ImageDraw.Draw(img)
    try:
        # Pillow 10+: textbbox returns (l, t, r, b)
        bbox = draw.textbbox((0, 0), "🌿", font=emoji_font, embedded_color=True)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # On Pillow with seguiemj.ttf, embedded_color=True draws colour emoji
        draw.text((cx - tw // 2 - bbox[0], cy - th // 2 - bbox[1]),
                  "🌿", font=emoji_font, embedded_color=True)
    except Exception:
        # fallback: simple white "L"
        draw.text((cx, cy), "L", font=emoji_font, fill=(255, 255, 255, 255), anchor="mm")

    # text "РАЦИОН"
    tfont = find_text_font(int(size * 0.095))
    draw.text((cx, int(size * 0.78)), "РАЦИОН", fill=TEXT_MUTED, font=tfont, anchor="mm")

    # text "САХАЛИНА"
    tfont_b = find_text_font(int(size * 0.095), bold=True)
    draw.text((cx, int(size * 0.88)), "САХАЛИНА", fill=GREEN, font=tfont_b, anchor="mm")

    return img

for s in (192, 512):
    img = make_icon(s)
    out = os.path.join(OUT_DIR, f"icon-{s}.png")
    img.save(out, "PNG")
    print(f"wrote {out} ({os.path.getsize(out)} bytes)")
