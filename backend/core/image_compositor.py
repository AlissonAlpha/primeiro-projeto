"""
Image Compositor — Professional ad creative assembly
Base photo (Freepik) + Logo + Text + Brand colors = Final Ad
"""
import io
import requests
import structlog
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from typing import Optional
import os

logger = structlog.get_logger()

FONT_DIR = "/tmp/agency_fonts"
os.makedirs(FONT_DIR, exist_ok=True)


def _download_font(variant: str = "Bold") -> str:
    path = f"{FONT_DIR}/Montserrat-{variant}.ttf"
    if os.path.exists(path):
        return path
    urls = {
        "Bold": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf",
        "Regular": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf",
        "SemiBold": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-SemiBold.ttf",
    }
    try:
        r = requests.get(urls.get(variant, urls["Bold"]), timeout=15)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return path
    except Exception:
        pass
    return ""


def _font(size: int, variant: str = "Bold") -> ImageFont.FreeTypeFont:
    p = _download_font(variant)
    if p and os.path.exists(p):
        return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _hex(h: str, a: int = 255) -> tuple:
    h = h.lstrip("#")
    if len(h) != 6:
        return (30, 30, 30, a)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def _luminance(hex_color: str) -> float:
    rgb = _hex(hex_color)
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _contrast_color(bg: str) -> tuple:
    return (15, 15, 15, 255) if _luminance(bg) > 128 else (255, 255, 255, 255)


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for w in words:
        test = f"{cur} {w}".strip()
        if dummy_draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def compose_ad(
    base_image_bytes: bytes,
    headline: str,
    subtext: str = "",
    cta_text: str = "Saiba Mais",
    logo_url: str = "",
    brand_color: str = "#1a1a1a",
    accent_color: str = "#fccc04",
    layout: str = "bottom_bar",
) -> bytes:
    """Compose final ad: photo + brand bar + headline + CTA + logo."""
    logger.info("composing_ad", headline=headline[:40], has_logo=bool(logo_url))

    base = Image.open(io.BytesIO(base_image_bytes)).convert("RGBA")
    W, H = base.size

    canvas = base.copy()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)

    brand_rgb = _hex(brand_color, 245)
    accent_rgb = _hex(accent_color, 255)
    text_on_brand = _contrast_color(brand_color)
    text_on_accent = _contrast_color(accent_color)

    if layout == "bottom_bar":
        # ── Dark brand bar at bottom (28% height) ──
        bar_h = int(H * 0.28)
        bar_y = H - bar_h
        pad = int(W * 0.05)

        # Gradient fade at top of bar
        for i in range(60):
            alpha = int(brand_rgb[3] * (i / 60))
            draw.rectangle([(0, bar_y - 60 + i), (W, bar_y - 59 + i)],
                           fill=(*brand_rgb[:3], alpha))

        # Solid bar
        draw.rectangle([(0, bar_y), (W, H)], fill=brand_rgb)

        # Accent top line (4px)
        draw.rectangle([(0, bar_y), (W, bar_y + 5)], fill=accent_rgb)

        # Headline
        fs_h = max(int(W * 0.058), 30)
        f_headline = _font(fs_h, "Bold")
        fs_sub = max(int(W * 0.032), 16)
        f_sub = _font(fs_sub, "Regular")

        logo_space = int(W * 0.28) if logo_url else 0
        text_max_w = W - pad * 2 - logo_space

        lines = _wrap(headline, f_headline, text_max_w)
        y = bar_y + int(bar_h * 0.13)
        for line in lines[:2]:
            draw.text((pad, y), line, font=f_headline, fill=text_on_brand)
            y += fs_h + int(fs_h * 0.2)

        if subtext:
            y += 4
            sub_lines = _wrap(subtext, f_sub, text_max_w)
            for sl in sub_lines[:1]:
                draw.text((pad, y), sl, font=f_sub, fill=(*text_on_brand[:3], 180))

        # CTA button (accent colored)
        btn_w = int(W * 0.26)
        btn_h = int(bar_h * 0.26)
        btn_x = W - pad - btn_w
        btn_y = H - pad - btn_h
        draw.rounded_rectangle(
            [(btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h)],
            radius=int(btn_h * 0.3), fill=accent_rgb
        )
        f_btn = _font(max(int(btn_h * 0.4), 14), "Bold")
        draw.text(
            (btn_x + btn_w // 2, btn_y + btn_h // 2),
            cta_text, font=f_btn, fill=text_on_accent, anchor="mm"
        )

    elif layout == "overlay":
        # ── Bottom gradient overlay ──
        grad_h = int(H * 0.55)
        for i in range(grad_h):
            alpha = int(230 * (i / grad_h) ** 1.2)
            y_pos = H - grad_h + i
            draw.rectangle([(0, y_pos), (W, y_pos + 1)],
                           fill=(*brand_rgb[:3], alpha))

        pad = int(W * 0.06)
        fs_h = max(int(W * 0.072), 34)
        f_h = _font(fs_h, "Bold")
        fs_sub = max(int(W * 0.038), 18)
        f_s = _font(fs_sub, "Regular")

        lines = _wrap(headline, f_h, W - pad * 2)
        y = int(H * 0.5)
        for line in lines[:3]:
            draw.text((pad, y), line, font=f_h, fill=(255, 255, 255, 255))
            y += fs_h + 6

        if subtext:
            y += 10
            for sl in _wrap(subtext, f_s, W - pad * 2)[:1]:
                draw.text((pad, y), sl, font=f_s, fill=(255, 255, 255, 200))
                y += fs_sub + 8

        y += 16
        btn_w = int(W * 0.42)
        btn_h = int(fs_h * 1.4)
        draw.rounded_rectangle(
            [(pad, y), (pad + btn_w, y + btn_h)],
            radius=int(btn_h * 0.25), fill=accent_rgb
        )
        f_btn = _font(max(int(btn_h * 0.42), 16), "Bold")
        draw.text(
            (pad + btn_w // 2, y + btn_h // 2),
            cta_text, font=f_btn, fill=text_on_accent, anchor="mm"
        )

    # Merge overlay onto canvas
    canvas = Image.alpha_composite(canvas, ov)

    # ── Add logo ──
    if logo_url:
        try:
            r = requests.get(logo_url, timeout=12)
            if r.status_code == 200:
                logo_img = Image.open(io.BytesIO(r.content)).convert("RGBA")

                # Target size: 18% of width
                logo_target_w = int(W * 0.18)
                logo_target_h = int(H * 0.09)
                logo_img.thumbnail((logo_target_w, logo_target_h), Image.LANCZOS)
                lw, lh = logo_img.size

                if layout == "bottom_bar":
                    # Center vertically in brand bar, right side
                    bar_y = H - int(H * 0.28)
                    pad = int(W * 0.04)
                    lx = W - lw - pad
                    ly = bar_y + (int(H * 0.28) - lh) // 2
                else:
                    # Top left
                    lx = int(W * 0.04)
                    ly = int(H * 0.03)

                canvas.paste(logo_img, (lx, ly), logo_img)
                logger.info("logo_added", size=(lw, lh), pos=(lx, ly))
        except Exception as e:
            logger.warning("logo_failed", error=str(e))

    # Final JPEG output
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def compose_from_url(
    image_url: str,
    headline: str,
    subtext: str = "",
    cta_text: str = "Saiba Mais",
    logo_url: str = "",
    brand_color: str = "#1a1a1a",
    accent_color: str = "#fccc04",
    layout: str = "bottom_bar",
) -> Optional[bytes]:
    try:
        r = requests.get(image_url, timeout=20)
        if r.status_code != 200:
            return None
        return compose_ad(r.content, headline, subtext, cta_text,
                          logo_url, brand_color, accent_color, layout)
    except Exception as e:
        logger.error("compose_from_url_error", error=str(e))
        return None
