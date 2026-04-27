"""
Image Compositor — Assembles final ad creative:
  Base photo (Freepik) + Logo + Text + Brand colors = Final Ad
"""
import io
import requests
import structlog
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional
import os

logger = structlog.get_logger()

# Download a Google Font for text rendering
FONT_DIR = "/tmp/agency_fonts"
os.makedirs(FONT_DIR, exist_ok=True)


def _download_font(font_name: str = "Montserrat") -> str:
    """Download font from Google Fonts CDN."""
    font_path = f"{FONT_DIR}/{font_name}-Bold.ttf"
    if os.path.exists(font_path):
        return font_path
    try:
        urls = {
            "Montserrat": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf",
            "Poppins": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
        }
        url = urls.get(font_name, urls["Montserrat"])
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(font_path, "wb") as f:
                f.write(r.content)
            return font_path
    except Exception:
        pass
    return ""


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    font_path = _download_font("Montserrat")
    if font_path and os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str, alpha: int = 255) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r, g, b, alpha)
    return (255, 255, 255, alpha)


def _text_color_for_bg(bg_hex: str) -> tuple:
    """Return black or white text depending on background luminance."""
    rgb = _hex_to_rgb(bg_hex)
    lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    return (20, 20, 20, 255) if lum > 140 else (255, 255, 255, 255)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    for word in words:
        test = f"{current} {word}".strip()
        w = draw.textlength(test, font=font)
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def compose_ad(
    base_image_bytes: bytes,
    headline: str,
    subtext: str = "",
    cta_text: str = "Saiba Mais",
    logo_url: str = "",
    brand_color: str = "#1A1A2E",
    accent_color: str = "#E8A020",
    layout: str = "bottom_bar",  # bottom_bar | top_logo | overlay
) -> bytes:
    """
    Compose final ad creative with logo, text, and brand colors.

    layout options:
    - bottom_bar: colored bar at bottom with text + logo
    - top_logo: logo top-left, gradient overlay at bottom for text
    - overlay: full gradient overlay with centered text
    """
    logger.info("composing_ad", headline=headline[:30], layout=layout)

    # Open base image
    base = Image.open(io.BytesIO(base_image_bytes)).convert("RGBA")
    w, h = base.size

    # Create working canvas
    canvas = base.copy()
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_rgb = _hex_to_rgb(brand_color, 230)
    accent_rgb = _hex_to_rgb(accent_color, 255)
    text_color = _text_color_for_bg(brand_color)

    if layout == "bottom_bar":
        # ── Bottom bar with brand color ──
        bar_h = int(h * 0.22)
        bar_y = h - bar_h

        # Semi-transparent brand color bar
        draw.rectangle([(0, bar_y), (w, h)], fill=brand_rgb)

        # Accent line at top of bar
        draw.rectangle([(0, bar_y), (w, bar_y + 4)], fill=accent_rgb)

        # Headline text
        font_size = max(28, int(w * 0.055))
        font = _get_font(font_size)
        font_small = _get_font(int(font_size * 0.6))

        padding = int(w * 0.05)
        text_area_w = w - padding * 2 - int(w * 0.25)  # Leave space for logo

        lines = _wrap_text(headline, font, text_area_w)
        y = bar_y + int(bar_h * 0.12)
        for line in lines[:2]:
            draw.text((padding, y), line, font=font, fill=text_color)
            y += font_size + 4

        if subtext:
            draw.text((padding, y + 4), subtext[:60], font=font_small, fill=(*text_color[:3], 180))

        # CTA button
        btn_w = int(w * 0.22)
        btn_h = int(bar_h * 0.3)
        btn_x = w - padding - btn_w
        btn_y = bar_y + int(bar_h * 0.55)
        draw.rounded_rectangle([(btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h)],
                               radius=8, fill=accent_rgb)
        btn_font = _get_font(int(font_size * 0.5))
        btn_text_color = _text_color_for_bg(accent_color)
        draw.text((btn_x + btn_w // 2, btn_y + btn_h // 2), cta_text,
                  font=btn_font, fill=btn_text_color, anchor="mm")

    elif layout == "overlay":
        # ── Full gradient overlay from bottom ──
        for i in range(int(h * 0.6)):
            alpha = int(210 * (i / (h * 0.6)))
            y_pos = h - int(h * 0.6) + i
            draw.rectangle([(0, y_pos), (w, y_pos + 1)],
                           fill=(*brand_rgb[:3], alpha))

        font_size = max(32, int(w * 0.07))
        font = _get_font(font_size)
        font_sub = _get_font(int(font_size * 0.55))

        padding = int(w * 0.06)
        lines = _wrap_text(headline, font, w - padding * 2)
        text_start_y = int(h * 0.55)
        y = text_start_y
        for line in lines[:3]:
            draw.text((padding, y), line, font=font, fill=(255, 255, 255, 255))
            y += font_size + 6

        if subtext:
            draw.text((padding, y + 8), subtext[:80], font=font_sub, fill=(255, 255, 255, 200))
            y += int(font_size * 0.7) + 16

        # CTA
        btn_w = int(w * 0.4)
        btn_h = int(font_size * 1.3)
        draw.rounded_rectangle([(padding, y), (padding + btn_w, y + btn_h)],
                               radius=10, fill=accent_rgb)
        draw.text((padding + btn_w // 2, y + btn_h // 2), cta_text,
                  font=_get_font(int(font_size * 0.55)), fill=_text_color_for_bg(accent_color), anchor="mm")

    # Merge overlay
    canvas = Image.alpha_composite(canvas, overlay)

    # ── Add logo ──
    if logo_url:
        try:
            r = requests.get(logo_url, timeout=10)
            if r.status_code == 200:
                logo = Image.open(io.BytesIO(r.content)).convert("RGBA")
                logo_max_w = int(w * 0.2)
                logo_max_h = int(h * 0.08)
                logo.thumbnail((logo_max_w, logo_max_h), Image.LANCZOS)
                lw, lh = logo.size
                if layout == "bottom_bar":
                    lx = w - lw - int(w * 0.04)
                    ly = h - int(h * 0.22) + int(h * 0.22 * 0.15)
                else:
                    lx = int(w * 0.04)
                    ly = int(h * 0.04)
                canvas.paste(logo, (lx, ly), logo)
        except Exception as e:
            logger.warning("logo_add_failed", error=str(e))

    # Convert to JPEG bytes
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
    brand_color: str = "#1A1A2E",
    accent_color: str = "#E8A020",
    layout: str = "bottom_bar",
) -> Optional[bytes]:
    """Download image from URL and compose the final ad."""
    try:
        r = requests.get(image_url, timeout=20)
        if r.status_code != 200:
            return None
        return compose_ad(
            r.content, headline, subtext, cta_text,
            logo_url, brand_color, accent_color, layout,
        )
    except Exception as e:
        logger.error("compose_from_url_error", error=str(e))
        return None
