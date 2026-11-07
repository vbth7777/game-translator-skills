#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentic In-Game Screenshot Mockup Generator for Ren'Py Walkthroughs
Composites game assets (backgrounds, character busts, textboxes, choice buttons)
with automated line-wrapping and coordinate highlights to create authentic playthrough visuals.
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class WalkthroughScreenRenderer:
    def __init__(self, width: int = 1920, height: int = 1080):
        self.w = width
        self.h = height

        # Standard fonts
        font_main = "C:/Windows/Fonts/segoeui.ttf"
        font_bold = "C:/Windows/Fonts/segoeuib.ttf"
        font_black = "C:/Windows/Fonts/seguibl.ttf"

        try:
            self.font_title = ImageFont.truetype(font_bold, 24)
            self.font_desc = ImageFont.truetype(font_main, 18)
            self.font_speaker = ImageFont.truetype(font_bold, 28)
            self.font_dialogue = ImageFont.truetype(font_main, 24)
            self.font_choice = ImageFont.truetype(font_bold, 24)
            self.font_target = ImageFont.truetype(font_bold, 20)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_desc = ImageFont.load_default()
            self.font_speaker = ImageFont.load_default()
            self.font_dialogue = ImageFont.load_default()
            self.font_choice = ImageFont.load_default()
            self.font_target = ImageFont.load_default()

    def wrap_text(self, text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
        """Wraps text into lines that do not exceed max_width."""
        lines = []
        for paragraph in text.splitlines():
            words = paragraph.split(" ")
            curr_line = ""
            for word in words:
                test_line = f"{curr_line} {word}".strip()
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_w = bbox[2] - bbox[0]
                if line_w <= max_width:
                    curr_line = test_line
                else:
                    if curr_line:
                        lines.append(curr_line)
                    curr_line = word
            if curr_line:
                lines.append(curr_line)
        return lines

    def create_screen(
        self,
        bg_image_path: Path | None,
        out_path: Path,
        step_title: str,
        step_action: str,
        speaker: str | None = None,
        dialogue: str | None = None,
        character_sprite_path: Path | None = None,
        sprite_pos: tuple[int, int] = (0, 0),
        choices: list[dict] | None = None,
        target_highlight: tuple[int, int, int, int] | None = None,  # (x1, y1, x2, y2)
        target_label: str | None = None,
        danger_warning: str | None = None
    ) -> Path:
        # 1. Base Canvas
        if bg_image_path and bg_image_path.is_file():
            canvas = Image.open(bg_image_path).convert("RGBA")
            if canvas.size != (self.w, self.h):
                canvas = canvas.resize((self.w, self.h), Image.Resampling.LANCZOS)
        else:
            canvas = Image.new("RGBA", (self.w, self.h), (20, 24, 39, 255))

        # 2. Layer Character Sprite (if present)
        if character_sprite_path and character_sprite_path.is_file():
            sprite = Image.open(character_sprite_path).convert("RGBA")
            canvas.alpha_composite(sprite, sprite_pos)

        draw = ImageDraw.Draw(canvas)

        # 3. Top Guidance HUD Banner
        banner_w, banner_h = 1100, 90
        bx = (self.w - banner_w) // 2
        by = 30
        draw.rectangle([bx, by, bx + banner_w, by + banner_h], fill=(15, 23, 42, 235), outline=(56, 189, 248), width=3)
        draw.text((bx + 25, by + 16), step_title, font=self.font_title, fill=(255, 215, 0))
        draw.text((bx + 25, by + 50), step_action, font=self.font_desc, fill=(226, 232, 240))

        # Danger Alert Tag
        if danger_warning:
            dw_box_w = 400
            dw_x = bx + banner_w - dw_box_w - 20
            draw.rectangle([dw_x, by + 18, dw_x + dw_box_w, by + banner_h - 18], fill=(185, 28, 28, 240), outline=(254, 202, 202), width=2)
            draw.text((dw_x + 15, by + 28), f"⚠️ {danger_warning}", font=self.font_desc, fill=(255, 255, 255))

        # 4. Target Coordinate Box & Pointer
        if target_highlight:
            x1, y1, x2, y2 = target_highlight
            draw.rectangle([x1, y1, x2, y2], outline=(251, 191, 36), width=4)
            if target_label:
                lbl_bbox = draw.textbbox((0, 0), target_label, font=self.font_target)
                lw = lbl_bbox[2] - lbl_bbox[0] + 20
                lh = lbl_bbox[3] - lbl_bbox[1] + 12
                ly = max(10, y1 - lh - 8)
                lx = max(10, x1)
                draw.rectangle([lx, ly, lx + lw, ly + lh], fill=(15, 23, 42, 230), outline=(251, 191, 36), width=2)
                draw.text((lx + 10, ly + 6), target_label, font=self.font_target, fill=(255, 215, 0))

        # 5. Choices Menu (if interactive decision)
        if choices:
            c_w, c_h = 860, 56
            spacing = 16
            total_h = len(choices) * c_h + (len(choices) - 1) * spacing
            c_y = (self.h - total_h) // 2
            c_x = (self.w - c_w) // 2

            for ch in choices:
                text = ch.get("text", "")
                selected = ch.get("recommended", False)
                fill_col = (30, 41, 59, 245) if not selected else (20, 83, 45, 245)
                out_col = (100, 116, 139) if not selected else (34, 197, 94)
                txt_col = (255, 255, 255) if not selected else (187, 247, 208)

                draw.rectangle([c_x, c_y, c_x + c_w, c_y + c_h], fill=fill_col, outline=out_col, width=3)
                prefix = "👉 [CHỌN MỤC NÀY] " if selected else ""
                draw.text((c_x + 30, c_y + 14), f"{prefix}{text}", font=self.font_choice, fill=txt_col)
                c_y += c_h + spacing

        # 6. Dialogue Textbox & Speaker Namebox (Docked at Bottom)
        if dialogue:
            tb_h = 240
            tb_y = self.h - tb_h
            # Draw semi-transparent textbox background
            draw.rectangle([0, tb_y, self.w, self.h], fill=(15, 23, 42, 235), outline=(56, 189, 248), width=2)

            if speaker:
                nb_w, nb_h = 320, 50
                nb_x = 160
                nb_y = tb_y - 25
                draw.rectangle([nb_x, nb_y, nb_x + nb_w, nb_y + nb_h], fill=(30, 41, 59, 250), outline=(251, 191, 36), width=2)
                draw.text((nb_x + 25, nb_y + 8), speaker, font=self.font_speaker, fill=(255, 215, 0))

            # Wrapped dialogue lines (Safe padding: 180px left, 180px right)
            max_dialogue_w = self.w - 360
            wrapped = self.wrap_text(dialogue, self.font_dialogue, max_dialogue_w, draw)
            dy = tb_y + 45
            for line in wrapped[:4]:  # Max 4 lines to prevent overlap
                draw.text((180, dy), line, font=self.font_dialogue, fill=(255, 255, 255))
                dy += 36

        out_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_path, "PNG")
        print(f"✅ Generated walkthrough screen: {out_path.name}")
        return out_path


def main():
    parser = argparse.ArgumentParser(description="Render authentic Ren'Py walkthrough mockup screens.")
    parser.add_argument("--out", "-o", required=True, help="Output PNG path")
    parser.add_argument("--bg", help="Background image path")
    parser.add_argument("--title", required=True, help="Step title")
    parser.add_argument("--action", required=True, help="Step action instruction")
    parser.add_argument("--speaker", help="Dialogue speaker name")
    parser.add_argument("--dialogue", help="Dialogue text")
    parser.add_argument("--sprite", help="Character sprite path")
    args = parser.parse_args()

    renderer = WalkthroughScreenRenderer()
    renderer.create_screen(
        bg_image_path=Path(args.bg) if args.bg else None,
        out_path=Path(args.out),
        step_title=args.title,
        step_action=args.action,
        speaker=args.speaker,
        dialogue=args.dialogue,
        character_sprite_path=Path(args.sprite) if args.sprite else None
    )


if __name__ == "__main__":
    main()
