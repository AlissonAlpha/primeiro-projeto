"""
Professional Ad Creative Compositor
Assembles: Base photo + Brand overlay + Campaign texts + Logo
"""
import io, os, requests, structlog
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional

logger = structlog.get_logger()
FONT_DIR = "/tmp/agency_fonts"
os.makedirs(FONT_DIR, exist_ok=True)

FONT_URLS = {
    "bold":     "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf",
    "semibold": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-SemiBold.ttf",
    "regular":  "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf",
    "light":    "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Light.ttf",
}

def _get_font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    path = f"{FONT_DIR}/montserrat_{weight}.ttf"
    if not os.path.exists(path):
        try:
            r = requests.get(FONT_URLS[weight], timeout=15)
            if r.status_code == 200:
                open(path, "wb").write(r.content)
        except Exception:
            pass
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def _hex(h: str, a: int = 255) -> tuple:
    h = h.lstrip("#")
    if len(h) != 6: return (20, 20, 20, a)
    return (int(h[:2],16), int(h[2:4],16), int(h[4:],16), a)

def _lum(h: str) -> float:
    c = _hex(h)
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]

def _contrast(h: str) -> tuple:
    return (15,15,15,255) if _lum(h) > 128 else (255,255,255,255)

def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    draw = ImageDraw.Draw(Image.new("RGB",(1,1)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=font) <= max_w: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def compose_ad(
    base_image_bytes: bytes,
    texts: dict,
    logo_url: str = "",
    brand_color: str = "#1a1a1a",
    accent_color: str = "#fccc04",
    layout: str = "bottom_bar",
) -> bytes:
    """
    Compose final ad with multiple text layers.

    texts dict keys:
    - tagline: small text above headline (ex: "Dia das Mães 2026")
    - headline: main message (ex: "Mãe é amor que nunca pede nada em troca ❤️")
    - subtext: secondary line (ex: "Neste Dia das Mães, retribua com carinho.")
    - cta: call to action button text (ex: "Presenteie com Gotrix ✨")
    """
    logger.info("composing_ad", layout=layout, has_logo=bool(logo_url))

    base = Image.open(io.BytesIO(base_image_bytes)).convert("RGBA")
    W, H = base.size
    canvas = base.copy()
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    draw = ImageDraw.Draw(ov)

    brand_rgba = _hex(brand_color, 240)
    accent_rgba = _hex(accent_color, 255)
    text_main = _contrast(brand_color)
    text_accent = _contrast(accent_color)
    pad = int(W * 0.055)

    if layout in ("bottom_bar", "bottom_gradient"):
        bar_h = int(H * 0.32)
        bar_y = H - bar_h

        if layout == "bottom_bar":
            # Gradient fade then solid
            for i in range(80):
                a = int(brand_rgba[3] * (i/80)**1.5)
                draw.rectangle([(0, bar_y-80+i),(W, bar_y-79+i)], fill=(*brand_rgba[:3], a))
            draw.rectangle([(0, bar_y),(W, H)], fill=brand_rgba)
            draw.rectangle([(0, bar_y),(W, bar_y+5)], fill=accent_rgba)
        else:
            for i in range(bar_h + 100):
                a = int(220 * (i/(bar_h+100))**1.3)
                draw.rectangle([(0, H-bar_h-100+i),(W, H-bar_h-99+i)], fill=(*brand_rgba[:3], a))

        logo_w_reserve = int(W * 0.26) if logo_url else 0
        text_w = W - pad*2 - logo_w_reserve

        y = bar_y + int(bar_h * 0.09)

        # Tagline (small, accent color)
        tagline = texts.get("tagline", "")
        if tagline:
            f_tag = _get_font(max(int(W*0.025), 13), "semibold")
            tag_color = (*accent_rgba[:3], 220)
            draw.text((pad, y), tagline.upper(), font=f_tag, fill=tag_color)
            y += int(W*0.025) + int(H*0.012)

        # Headline (large, white/contrast)
        headline = texts.get("headline", "")
        if headline:
            f_h = _get_font(max(int(W*0.052), 26), "bold")
            lines = _wrap(headline, f_h, text_w)
            for line in lines[:2]:
                draw.text((pad, y), line, font=f_h, fill=text_main)
                y += int(W*0.052) + int(H*0.008)

        # Subtext
        subtext = texts.get("subtext", "")
        if subtext:
            y += int(H*0.006)
            f_s = _get_font(max(int(W*0.031), 15), "regular")
            sub_color = (*text_main[:3], 190)
            for sl in _wrap(subtext, f_s, text_w)[:2]:
                draw.text((pad, y), sl, font=f_s, fill=sub_color)
                y += int(W*0.031) + int(H*0.006)

        # CTA button
        cta = texts.get("cta", "")
        if cta:
            f_btn = _get_font(max(int(W*0.032), 16), "bold")
            cta_w = int(draw.textlength(cta, font=f_btn) + W*0.08)
            btn_h = max(int(H*0.055), 40)
            btn_x = pad
            btn_y = H - pad - btn_h
            draw.rounded_rectangle([(btn_x, btn_y),(btn_x+cta_w, btn_y+btn_h)],
                                   radius=int(btn_h*0.3), fill=accent_rgba)
            draw.text((btn_x + cta_w//2, btn_y + btn_h//2), cta,
                      font=f_btn, fill=text_accent, anchor="mm")

    elif layout == "overlay_center":
        # Full overlay with centered text
        for i in range(H):
            a = int(180 * (i/H)**0.8)
            draw.rectangle([(0,i),(W,i+1)], fill=(*brand_rgba[:3], a))

        y = int(H * 0.25)
        tagline = texts.get("tagline", "")
        if tagline:
            f_t = _get_font(max(int(W*0.03), 14), "semibold")
            draw.text((W//2, y), tagline, font=f_t,
                      fill=(*accent_rgba[:3], 220), anchor="mm")
            y += int(W*0.06)

        headline = texts.get("headline", "")
        if headline:
            f_h = _get_font(max(int(W*0.065), 30), "bold")
            for line in _wrap(headline, f_h, int(W*0.85))[:3]:
                draw.text((W//2, y), line, font=f_h,
                          fill=(255,255,255,255), anchor="mm")
                y += int(W*0.065) + int(H*0.01)

        subtext = texts.get("subtext","")
        if subtext:
            y += int(H*0.02)
            f_s = _get_font(max(int(W*0.035), 16), "regular")
            for sl in _wrap(subtext, f_s, int(W*0.8))[:2]:
                draw.text((W//2, y), sl, font=f_s,
                          fill=(255,255,255,190), anchor="mm")
                y += int(W*0.035) + int(H*0.008)

        cta = texts.get("cta","")
        if cta:
            f_b = _get_font(max(int(W*0.035), 16), "bold")
            cta_w = int(draw.textlength(cta, font=f_b) + W*0.1)
            btn_h = max(int(H*0.06), 44)
            bx = (W - cta_w)//2
            by = int(H*0.75)
            draw.rounded_rectangle([(bx,by),(bx+cta_w,by+btn_h)],
                                   radius=int(btn_h*0.3), fill=accent_rgba)
            draw.text((W//2, by+btn_h//2), cta, font=f_b,
                      fill=text_accent, anchor="mm")

    canvas = Image.alpha_composite(canvas, ov)

    # ── Logo ──
    if logo_url:
        try:
            r = requests.get(logo_url, timeout=12)
            if r.status_code == 200:
                logo = Image.open(io.BytesIO(r.content)).convert("RGBA")
                max_lw, max_lh = int(W*0.20), int(H*0.09)
                logo.thumbnail((max_lw, max_lh), Image.LANCZOS)
                lw, lh = logo.size
                if layout in ("bottom_bar","bottom_gradient"):
                    bar_y = H - int(H*0.32)
                    lx = W - lw - int(W*0.04)
                    ly = bar_y + (int(H*0.32) - lh)//2
                else:
                    lx = int(W*0.04)
                    ly = int(H*0.04)
                canvas.paste(logo, (lx, ly), logo)
                logger.info("logo_placed", pos=(lx,ly), size=(lw,lh))
        except Exception as e:
            logger.warning("logo_failed", error=str(e))

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=95)
    return buf.getvalue()
