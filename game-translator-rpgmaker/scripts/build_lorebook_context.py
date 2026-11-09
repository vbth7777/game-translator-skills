#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker Lorebook & Context Generator
Synthesizes character profiles, actor escape codes (\\N[X]), multi-phase pairwise pronoun rules,
scoped glossary terms, and scene tone directives modeled after the rpg-translate system.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def resolve_game_data_dir(dir_path: str) -> str:
    """Finds the directory containing RPG Maker JSON files."""
    if not dir_path or not os.path.exists(dir_path):
        return dir_path

    if os.path.isdir(dir_path):
        files = os.listdir(dir_path)
        if any(f in files for f in ["System.json", "Actors.json", "CommonEvents.json"]):
            return os.path.abspath(dir_path)

    www_data = os.path.join(dir_path, "www", "data")
    if os.path.exists(www_data) and os.path.isdir(www_data):
        return os.path.abspath(www_data)

    plain_data = os.path.join(dir_path, "data")
    if os.path.exists(plain_data) and os.path.isdir(plain_data):
        return os.path.abspath(plain_data)

    return os.path.abspath(dir_path)


def load_json_safe(file_path: str):
    if not os.path.isfile(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return None


def clean_character_name_from_face(face_str: str) -> str:
    if not face_str or not isinstance(face_str, str):
        return ""
    f = face_str.strip()
    f_lower = f.lower()
    if "_face" in f_lower:
        f = f[:f_lower.index("_face")]
    elif "_face" not in f_lower and "_" in f:
        parts = f.split("_")
        if parts[0] and not parts[0].isdigit():
            f = parts[0]
    f = re.sub(r'[\d_\-]+$', '', f).strip()
    if f and len(f) >= 2:
        return f.capitalize() if f.isascii() else f
    return face_str.strip()


def build_lorebook(game_dir: str, source_path: str = None, meta_path: str = None) -> dict:
    """Builds an omniscient game lorebook from database and extracted metadata."""
    data_dir = resolve_game_data_dir(game_dir)
    real_root = game_dir

    # 1. Load Actors
    actors_data = load_json_safe(os.path.join(data_dir, "Actors.json")) or []
    characters = []
    actor_map = {}

    for idx, act in enumerate(actors_data):
        if act and isinstance(act, dict) and act.get("name"):
            act_id = act.get("id", idx)
            name = act.get("name", "").strip()
            nick = act.get("nickname", "").strip()
            profile = act.get("profile", "").strip()
            role = "protagonist" if act_id == 1 else "companion"

            char_obj = {
                "id": act_id,
                "name": name,
                "aliases": [nick] if nick and nick != name else [],
                "escape_code": f"\\N[{act_id}]",
                "gender": "male" if act_id == 1 else "unknown",
                "role": role,
                "pronouns": {
                    "self": "tôi",
                    "to_others": "cậu / cô"
                },
                "personality": profile or "Chưa rõ",
                "notes": f"Actor #{act_id}"
            }
            characters.append(char_obj)
            actor_map[act_id] = char_obj

    # 2. Load Metadata for additional characters found in dialogues
    actual_meta_path = meta_path or os.path.join(game_dir, "translation_metadata.json")
    meta_db = load_json_safe(actual_meta_path) or {}

    discovered_speakers = set()
    discovered_faces = set()
    for item in meta_db.values():
        if isinstance(item, dict):
            spk = item.get("speaker")
            if spk and len(spk) > 1 and not spk.isdigit():
                discovered_speakers.add(spk)
            face = item.get("face")
            if face and ":" in face:
                fname = face.split(":")[0]
                clean_name = clean_character_name_from_face(fname)
                if clean_name and len(clean_name) > 1:
                    discovered_faces.add(clean_name)

    existing_names = {c["name"].lower() for c in characters}
    extra_names = (discovered_speakers | discovered_faces) - existing_names
    for en in sorted(extra_names):
        if len(en) < 2 or en.lower() in ["system", "narrator", "lời dẫn", "tiếng động"]:
            continue
        characters.append({
            "name": en,
            "aliases": [],
            "gender": "unknown",
            "role": "npc",
            "pronouns": {
                "self": "tôi",
                "to_others": "ngươi / bạn"
            },
            "personality": "",
            "notes": "Phát hiện từ hội thoại/ảnh face"
        })

    # 3. Generate Pairwise Relationship Pronoun Rules
    relationships = []
    # If we have at least 2 key characters, create standard pairs
    named_chars = [c["name"] for c in characters[:8]]
    for i, c1 in enumerate(named_chars):
        for j, c2 in enumerate(named_chars):
            if i != j:
                relationships.append({
                    "speaker": c1,
                    "listener": c2,
                    "self_pronoun": "tôi",
                    "listener_pronoun": "cậu / cô",
                    "tone": "bình thường / thân mật",
                    "phases": [
                        {
                            "stage_name": "Mặc định (Default)",
                            "condition": "default",
                            "self_pronoun": "tôi",
                            "listener_pronoun": "cậu",
                            "tone": "thân thiện, bình thường"
                        },
                        {
                            "stage_name": "Thù địch / Biến chất (Corrupted / Hostile)",
                            "condition": "corrupted, hostile, betrayal, thù địch, phản bội, hắc hóa",
                            "self_pronoun": "ta / tao",
                            "listener_pronoun": "ngươi / mày / con khốn",
                            "tone": "khinh bỉ, đe dọa, thống trị"
                        },
                        {
                            "stage_name": "Thân mật / Tình nhân (Intimate / Lovers)",
                            "condition": "intimate, lover, h-scene, người yêu, quyến rũ",
                            "self_pronoun": "anh / em",
                            "listener_pronoun": "em / anh",
                            "tone": "ngọt ngào, say đắm, gợi cảm"
                        }
                    ]
                })

    # 4. Extract Glossary Candidates
    glossary = []
    # System terms
    sys_data = load_json_safe(os.path.join(data_dir, "System.json")) or {}
    cur_unit = sys_data.get("currencyUnit", "G")
    if cur_unit:
        glossary.append({
            "original": cur_unit,
            "translated": cur_unit,
            "category": "term",
            "notes": "Đơn vị tiền tệ game"
        })

    # MapInfos (Locations)
    map_infos = load_json_safe(os.path.join(data_dir, "MapInfos.json")) or []
    for m in map_infos:
        if m and isinstance(m, dict) and m.get("name"):
            m_name = m.get("name").strip()
            if m_name and not m_name.isdigit():
                glossary.append({
                    "original": m_name,
                    "translated": m_name,
                    "category": "location",
                    "notes": "Địa danh trên bản đồ"
                })

    # Items / Skills
    for fn, cat in [("Items.json", "item"), ("Skills.json", "skill"), ("Weapons.json", "item")]:
        db_items = load_json_safe(os.path.join(data_dir, fn)) or []
        for it in db_items[:15]:
            if it and isinstance(it, dict) and it.get("name"):
                name = it.get("name").strip()
                if name and len(name) > 1 and not name.isdigit():
                    glossary.append({
                        "original": name,
                        "translated": name,
                        "category": cat,
                        "notes": f"Thuật ngữ {cat}"
                    })

    # 5. Assemble Lorebook Object
    lorebook = {
        "game_title": sys_data.get("gameTitle", Path(game_dir).name),
        "version": 1.0,
        "characters": characters,
        "relationships": relationships,
        "glossary": glossary,
        "tone_notes": (
            "Game RPG có cốt truyện phiêu lưu kết hợp tương tác nhân vật. "
            "Dịch tự nhiên theo phong cách Việt hóa game chuyên nghiệp, giữ nguyên văn phong cá tính nhân vật. "
            "Khi vào phân cảnh 18+/H-scene, tuyệt đối dịch sát nghĩa, bảo lưu trọn vẹn dirty talk, tiếng rên (moans) "
            "và âm thanh nhạy cảm mà không né tránh hay giảm nhẹ."
        ),
        "soft_constraint_directive": (
            "[LƯU Ý VỀ DIỄN BIẾN TÂM LÝ & XƯNG HÔ (SOFT CONSTRAINT)]:\n"
            "Các quy tắc xưng hô trong Lorebook là thiết lập nền tảng mặc định. Nếu phân cảnh hiện tại thể hiện "
            "rõ sự thù địch, phản bội, hắc hóa, khinh bỉ, biến chất hoặc thân mật khác thường, AI ĐƯỢC PHÉP "
            "linh hoạt thay đổi đại từ xưng hô (ví dụ: chuyển từ 'em/anh' sang 'tôi/ngươi/thằng khốn' hoặc 'mày/tao') "
            "để phản ánh chính xác 100% cảm xúc của nhân vật trong cảnh."
        ),
        "escape_code_rules": (
            "Giữ nguyên 100% các mã điều khiển của RPG Maker: \\V[n], \\N[n], \\P[n], \\G, \\C[n], \\I[n], "
            "\\., \\|, \\!, \\^, \\>, \\<, \\{, \\}. Tra cứu \\N[n] theo bảng nhân vật đã cung cấp."
        )
    }

    return lorebook


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive RPG Maker Lorebook and context.")
    parser.add_argument("game_dir", help="Path to RPG Maker game root or data folder")
    parser.add_argument("--source", default=None, help="Path to translation_source.json")
    parser.add_argument("--metadata", default=None, help="Path to translation_metadata.json")
    parser.add_argument("--out", default=None, help="Output path for LOREBOOK.json")
    args = parser.parse_args()

    game_dir = os.path.abspath(args.game_dir)
    lorebook = build_lorebook(game_dir, args.source, args.metadata)

    out_file = args.out or os.path.join(game_dir, "LOREBOOK.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(lorebook, f, ensure_ascii=False, indent=2)

    print(f"Generated Lorebook with {len(lorebook['characters'])} characters, "
          f"{len(lorebook['relationships'])} relationship rules, "
          f"{len(lorebook['glossary'])} glossary terms.")
    print(f"Saved to: {out_file}")


if __name__ == "__main__":
    main()

