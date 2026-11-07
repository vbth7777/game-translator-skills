#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AAA Graphic Asset Localizer & Supersampling Inpainter
Localizes UI texture banners, buttons, and prompts while preserving alpha channel
and applying 4x supersampling with multi-layer stroke outlines and drop shadows.
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def render_text_supersampled(
    text: str,
    font_path: str,
    font_size: int,
    text_color: tuple,
    stroke_color: tuple = (0, 0, 0, 255),
    stroke_width: int = 4,
    shadow_offset: tuple = (3, 3),
    shadow_color: tuple = (0, 0, 0, 180),
    supersample_scale: int = 4
) -> Image.Image:
    """Renders text at 4x resolution with smooth antialiased stroke and shadow, then downsamples."""
    scaled_size = font_size * supersample_scale
    scaled_stroke = stroke_width * supersample_scale
    scaled_offset = (shadow_offset[0] * supersample_scale, shadow_offset[1] * supersample_scale)

    try:
        font = ImageFont.truetype(font_path, scaled_size)
    except Exception:
        font = ImageFont.load_default()

    # Measure text bounding box
    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), text, font=font, stroke_width=scaled_stroke)

    text_w = bbox[2] - bbox[0] + abs(scaled_offset[0]) + scaled_stroke * 4
    text_h = bbox[3] - bbox[1] + abs(scaled_offset[1]) + scaled_stroke * 4

    canvas = Image.new("RGBA", (int(text_w), int(text_h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    pos_x = scaled_stroke * 2 - bbox[0]
    pos_y = scaled_stroke * 2 - bbox[1]

    # Draw shadow layer
    if shadow_color and shadow_color[3] > 0:
        draw.text(
            (pos_x + scaled_offset[0], pos_y + scaled_offset[1]),
            text,
            font=font,
            fill=shadow_color,
            stroke_width=scaled_stroke,
            stroke_fill=shadow_color
        )

    # Draw main text with stroke
    draw.text(
        (pos_x, pos_y),
        text,
        font=font,
        fill=text_color,
        stroke_width=scaled_stroke,
        stroke_fill=stroke_color
    )

    # Downsample with high-quality Lanczos filter
    final_w = int(text_w // supersample_scale)
    final_h = int(text_h // supersample_scale)
    result = canvas.resize((final_w, final_h), Image.Resampling.LANCZOS)
    return result


def overlay_text_on_asset(
    input_image_path: Path,
    output_image_path: Path,
    text: str,
    bounding_box: tuple[int, int, int, int],  # (x1, y1, x2, y2)
    font_path: str = "C:/Windows/Fonts/seguibl.ttf",
    font_size: int = 36,
    text_color: tuple = (255, 255, 255, 255),
    stroke_color: tuple = (0, 0, 0, 255),
    stroke_width: int = 3,
    clear_box: bool = False,
    bg_color: tuple | None = None
):
    orig = Image.open(input_image_path).convert("RGBA")
    bx1, by1, bx2, by2 = bounding_box
    target_w = bx2 - bx1
    target_h = by2 - by1

    # Optional inpainting / clearing box
    if clear_box:
        fill_col = bg_color if bg_color else (0, 0, 0, 0)
        draw = ImageDraw.Draw(orig)
        draw.rectangle([bx1, by1, bx2, by2], fill=fill_col)

    text_img = render_text_supersampled(
        text=text,
        font_path=font_path,
        font_size=font_size,
        text_color=text_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    )

    # Center text inside bounding box
    paste_x = bx1 + (target_w - text_img.width) // 2
    paste_y = by1 + (target_h - text_img.height) // 2

    orig.alpha_composite(text_img, (paste_x, paste_y))
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    orig.save(output_image_path, "PNG")
    print(f"✅ Saved localized asset to: {output_image_path}")


def main():
    parser = argparse.ArgumentParser(description="Inpaint and localize game texture asset with supersampling.")
    parser.add_argument("input_img", help="Input image file")
    parser.add_argument("output_img", help="Output image file")
    parser.add_argument("text", help="Vietnamese text to render")
    parser.add_argument("--bbox", nargs=4, type=int, required=True, metavar=("X1", "Y1", "X2", "Y2"), help="Target bounding box")
    parser.add_argument("--size", type=int, default=32, help="Font size (default: 32)")
    parser.add_argument("--font", default="C:/Windows/Fonts/seguibl.ttf", help="Font path")
    parser.add_argument("--clear", action="store_true", help="Clear original bounding box before drawing")
    args = parser.parse_args()

    overlay_text_on_asset(
        input_image_path=Path(args.input_img),
        output_image_path=Path(args.output_img),
        text=args.text,
        bounding_box=tuple(args.bbox),
        font_path=args.font,
        font_size=args.size,
        clear_box=args.clear
    )


if __name__ == "__main__":
    main()

