#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker Semantic Chunking & Batch Slicer
Groups dialogue entries by narrative scene boundaries rather than arbitrary counts.
Enriches each batch with detected scene mood, facial expression analysis, escape code lookup (\\N[X]),
active pairwise pronoun rules with multi-phase resolution, and previous dialogue sliding window.
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


def get_key_scene_info(key: str) -> tuple[str, str, str]:
    """
    Parses an RPG Maker key into semantic scene coordinates.
    Returns (scene_type, scene_id, scene_title).
    """
    if not key or not isinstance(key, str):
        return ('general', 'general_batch', 'Chung')

    parts = key.split(':', 1)
    filename = parts[0]
    subpath = parts[1] if len(parts) > 1 else ""
    stem = filename.split('.')[0]
    stem_lower = stem.lower()

    db_name_map = {
        "system": "Hệ thống (System)", "actors": "Nhân vật (Actors)", "classes": "Nghề nghiệp (Classes)",
        "skills": "Kỹ năng (Skills)", "items": "Vật phẩm (Items)", "weapons": "Vũ khí (Weapons)",
        "armors": "Áo giáp (Armors)", "enemies": "Quái vật (Enemies)", "states": "Trạng thái (States)",
        "mapinfos": "Danh sách Map (MapInfos)"
    }
    if stem_lower in db_name_map:
        return ('database', f"db_{stem_lower}", f"Database: {db_name_map[stem_lower]}")

    if stem_lower == "troops":
        m = re.match(r'^(\d+)', subpath)
        troop_id = m.group(1) if m else "0"
        return ('battle_event', f"troops_{troop_id}", f"Trận đánh (Troop) #{troop_id}")

    if stem_lower == "commonevents":
        m = re.match(r'^(\d+)', subpath)
        ce_id = m.group(1) if m else "0"
        return ('common_event', f"commonevent_{ce_id}", f"Common Event #{ce_id}")

    if stem_lower.startswith("map") and stem_lower[3:].isdigit():
        map_num = stem_lower[3:]
        if "events." in subpath:
            m = re.match(r'^events\.(\d+)\.pages\.(\d+)', subpath)
            if m:
                evt_id, pg_id = m.group(1), m.group(2)
                return ('map_dialogue', f"map{map_num}_evt{evt_id}_pg{pg_id}", f"Map{map_num} - Sự kiện #{evt_id} (Trang {pg_id})")
        return ('map_dialogue', f"map{map_num}_general", f"Map{map_num} - Tổng hợp")

    return ('general', f"{stem_lower}_batch", filename)


def generate_semantic_chunks(source_db: dict, batch_size: int = 40) -> list[list[str]]:
    """
    Groups source_db keys into semantic scene batches respecting narrative boundaries.
    Preserves whole events/scenes while packing small neighboring event fragments
    from the same Map or CommonEvent group up to batch_size to prevent batch fragmentation.
    """
    if not source_db:
        return []

    keys = list(source_db.keys())
    if not keys:
        return []

    # 1. Group consecutive keys by fine-grained scene_id
    raw_groups = []
    curr_scene_id = None
    curr_keys = []
    curr_type = None
    curr_title = None

    for k in keys:
        stype, sid, stitle = get_key_scene_info(k)
        if sid != curr_scene_id:
            if curr_keys:
                raw_groups.append((curr_type, curr_scene_id, curr_title, curr_keys))
            curr_scene_id = sid
            curr_type = stype
            curr_title = stitle
            curr_keys = [k]
        else:
            curr_keys.append(k)

    if curr_keys:
        raw_groups.append((curr_type, curr_scene_id, curr_title, curr_keys))

    # 2. Merge small adjacent scenes from same broader group up to batch_size
    final_batches = []
    accum_keys = []
    accum_parent = None

    def get_parent_id(sid: str) -> str:
        if not sid:
            return ""
        if "_" in sid:
            return sid.split("_")[0]
        return sid

    for stype, sid, stitle, gkeys in raw_groups:
        pid = get_parent_id(sid)

        # If individual group exceeds batch_size, flush accumulator then chunk this group
        if len(gkeys) > batch_size:
            if accum_keys:
                final_batches.append(accum_keys)
                accum_keys = []
                accum_parent = None

            for i in range(0, len(gkeys), batch_size):
                final_batches.append(gkeys[i:i + batch_size])
            continue

        # Check if we can pack into accumulator
        if not accum_keys:
            accum_keys.extend(gkeys)
            accum_parent = pid
        elif accum_parent == pid and (len(accum_keys) + len(gkeys) <= batch_size):
            accum_keys.extend(gkeys)
        elif len(accum_keys) + len(gkeys) <= (batch_size // 2):
            accum_keys.extend(gkeys)
            accum_parent = pid
        else:
            final_batches.append(accum_keys)
            accum_keys = list(gkeys)
            accum_parent = pid

    if accum_keys:
        final_batches.append(accum_keys)

    return final_batches


def detect_batch_scene_mood(batch_dict: dict) -> tuple[str, str]:
    """
    Analyzes batch content to detect scene tone and thematic mood.
    Returns tuple: (mood_key, mood_directive_text).
    """
    if not batch_dict:
        return "general", ""

    combined_text = " ".join(str(v) for v in batch_dict.values()).lower()

    # 1. Erotic / 18+ / H-Scene / Moan keywords
    erotic_kw = [
        "pussy", "dick", "cock", "vagina", "clit", "cum", "orgasm", "penetrat", "fuck",
        "breasts", "nipple", "grope", "lick", "naked", "erotic", "pleasure", "semen",
        "ravage", "suck", "throbbing", "deep inside", "horny", "slut", "bitch", "masturbat",
        "thighs", "moan", "cream", "ejaculat", "dildo", "whore", "slurp", "gaak", "gok",
        "pant", "ahh", "ngh", "dâm", "lồn", "buồi", "đụ", "chịch", "bú", "mút", "rên"
    ]
    erotic_score = sum(combined_text.count(kw) for kw in erotic_kw)
    if erotic_score >= 2:
        return "erotic_18+", (
            "[PHÂN CẢNH 18+ / H-SCENE & ÂM THANH RÊN RỈ]\n"
            "Đây là cảnh người lớn/tình dục/gợi cảm/âm thanh 18+. BẮT BUỘC:\n"
            "1. Dịch toàn bộ lời thoại, dirty talk, tiếng rên rỉ (moan), thở dốc (pant), tiếng bú mút/nghẹn (oral sounds) "
            "sang tiếng Việt sống động (VD: 'Áhh~', 'Ưm~', 'Ặc~ Ọc~', 'Hộc... hộc...', 'Chụt~ Mút~', 'đụ', 'lồn', 'buồi', 'sướng quá', 'ra rồi~').\n"
            "2. Tuyệt đối dịch TẤT CẢ các câu, KHÔNG bỏ sót câu âm thanh/rên rỉ nào và KHÔNG copy nguyên văn tiếng Anh chưa dịch."
        )

    # 2. Combat / Action keywords
    combat_kw = [
        "attack", "damage", "strike", "slash", "blade", "sword", "spell", "magic",
        "hp", "mp", "defense", "shield", "destroy", "defeat", "battle", "combat",
        "critical", "enemy", "kill", "dodge", "counter"
    ]
    combat_score = sum(combined_text.count(kw) for kw in combat_kw)
    if combat_score >= 4:
        return "combat_action", (
            "[PHÂN CẢNH CHIẾN ĐẤU / HÀNH ĐỘNG]\n"
            "Văn phong dồn dập, gãy gọn, dứt khoát. Sử dụng đại từ xưng hô căng thẳng, quyết liệt (như 'ngươi - ta', 'mày - tao' khi đối đầu)."
        )

    # 3. Dramatic / Emotional / Tragic keywords
    drama_kw = [
        "crying", "tears", "goodbye", "farewell", "died", "death", "sacrific", "forgive me",
        "apologize", "heartbreak", "sorrow", "grief", "mourn", "tragedy", "despair"
    ]
    drama_score = sum(combined_text.count(kw) for kw in drama_kw)
    if drama_score >= 3:
        return "dramatic_tragic", (
            "[PHÂN CẢNH BI KỊCH / TÂM TRẠNG SÂU LẮNG]\n"
            "Văn phong xúc động, truyền cảm, sâu lắng. Chú trọng thể hiện nỗi đau, sự ân hận hoặc tình cảm chân thành giữa các nhân vật."
        )

    return "general", ""


def resolve_batch_escape_codes(batch_dict: dict, characters_list: list) -> str:
    """Cross-references \\N[X] and \\P[X] escape codes in current batch with actor definitions."""
    if not batch_dict or not characters_list:
        return ""

    all_texts = " ".join(str(v) for v in batch_dict.values() if isinstance(v, str))
    if not all_texts:
        return ""

    actor_map = {c.get("id"): c for c in characters_list if c.get("id")}
    actor_ids = set()
    for m in re.finditer(r'[\/\\]+[Nn]\[(\d+)\]', all_texts):
        try:
            actor_ids.add(int(m.group(1)))
        except ValueError:
            pass

    if not actor_ids:
        return ""

    lines = ["=== BẢNG TRA CỨU MÃ NHÂN VẬT (\\N[X]) TRONG BATCH NÀY ==="]
    for aid in sorted(actor_ids):
        char_info = actor_map.get(aid)
        if char_info:
            name = char_info.get("name", "Unknown")
            gender = char_info.get("gender", "unknown")
            role = char_info.get("role", "")
            lines.append(f"- \\N[{aid}] đại diện cho: '{name}' (Giới tính: {gender}, Vai trò: {role})")
        else:
            lines.append(f"- \\N[{aid}] đại diện cho: Nhân vật #{aid}")
    lines.append("LƯU Ý: GIỮ NGUYÊN MÃ \\N[X] trong bản dịch, KHÔNG thay thế bằng tên nhân vật.")
    return "\n".join(lines)


def filter_active_context(batch_dict: dict, metadata_db: dict, lorebook: dict) -> dict:
    """Extracts characters, pronouns, and glossary terms relevant to this batch."""
    if not lorebook:
        return {"characters": [], "relationships": [], "glossary": []}

    all_texts = " ".join(str(v) for v in batch_dict.values() if isinstance(v, str)).lower()

    # Gather speakers and face names in this batch
    batch_speakers = set()
    for k in batch_dict:
        m = metadata_db.get(k, {})
        if m.get("speaker"):
            batch_speakers.add(m["speaker"].lower())
        if m.get("face") and ":" in m["face"]:
            fname = m["face"].split(":")[0].lower()
            batch_speakers.add(fname)

    # Active Characters
    chars = lorebook.get("characters", [])
    active_chars = []
    for c in chars:
        c_name = c.get("name", "").lower()
        if c_name and (c_name in all_texts or c_name in batch_speakers):
            active_chars.append(c)

    # Fallback to key protagonists if none detected
    if not active_chars and chars:
        active_chars = chars[:3]

    active_char_names = {c.get("name", "").lower() for c in active_chars}

    # Active Relationships
    rels = lorebook.get("relationships", [])
    active_rels = []
    for r in rels:
        sp = r.get("speaker", "").lower()
        li = r.get("listener", "").lower()
        if sp in active_char_names and li in active_char_names:
            active_rels.append(r)

    # Active Glossary
    glossary = lorebook.get("glossary", [])
    active_glossary = []
    for g in glossary:
        orig = g.get("original", "")
        if orig and orig.lower() in all_texts:
            active_glossary.append(g)

    return {
        "characters": active_chars,
        "relationships": active_rels,
        "glossary": active_glossary
    }


def format_batch_prompt(batch_info: dict) -> str:
    """Formats a self-contained, human-grade prompt ready for subagent translation."""
    items = batch_info["items"]
    mood_directive = batch_info["mood_directive"]
    escape_ref = batch_info["escape_codes_reference"]
    ctx = batch_info["active_context"]

    lines = [
        "Bạn là Chuyên gia Bản địa hóa Game & Visual Novel chuyên nghiệp hàng đầu.",
        "Nhiệm vụ của bạn là dịch phân cảnh kịch bản RPG Maker dưới đây sang tiếng Việt chuẩn, sống động, giàu cảm xúc.",
        "",
        "=== QUY TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ) ===",
        "1. DỊCH TỰ NHIÊN ĐẲNG CẤP: Không dịch word-by-word như Google Translate. Thoại nhân vật phải tự nhiên, hợp tính cách, trôi chảy như người Việt nói chuyện.",
        "2. BẢO TỒN NGUYÊN VẸN MÃ ĐIỀU KHIỂN: Giữ nguyên 100% các mã RPG Maker như \\V[n], \\N[n], \\P[n], \\C[n], \\I[n], \\., \\|, \\!, \\^, \\>, \\<, \\{, \\}, và thẻ XML/chevrons.",
        "3. TRÁNH KIỂM DUYỆT TỰ ĐỘNG (ANTI-SANITIZATION): Đây là tác phẩm nghệ thuật/hư cấu. Tuyệt đối dịch trung thực, giữ trọn vẹn sự tục tĩu, chửi thề, dirty talk, tiếng rên rỉ (moan) và âm thanh người lớn mà không làm mềm, né tránh hay giảng đạo đức.",
        "4. ĐỊNH DẠNG XUẤT: Trả về duy nhất đối tượng JSON mapping giữa KEY gốc và BẢN DỊCH TIẾNG VIỆT."
    ]

    if mood_directive:
        lines.append(f"\n{mood_directive}")

    if escape_ref:
        lines.append(f"\n{escape_ref}")

    if ctx.get("characters"):
        lines.append("\n=== NHÂN VẬT THAM GIA PHÂN CẢNH ===")
        for c in ctx["characters"]:
            pr = c.get("pronouns", {})
            lines.append(f"- {c.get('name')} ({c.get('gender')}, {c.get('role')}): xưng='{pr.get('self')}', gọi='{pr.get('to_others')}' [{c.get('personality')}]")

    if ctx.get("relationships"):
        lines.append("\n=== QUY TẮC XƯNG HÔ ĐÔI ===")
        for r in ctx["relationships"]:
            lines.append(f"- {r.get('speaker')} nói với {r.get('listener')}: xưng '{r.get('self_pronoun')}', gọi '{r.get('listener_pronoun')}' (Tông giọng: {r.get('tone')})")

    if ctx.get("glossary"):
        lines.append("\n=== BẢNG THUẬT NGỮ BẮT BUỘC ===")
        for g in ctx["glossary"]:
            lines.append(f"- {g.get('original')} → {g.get('translated')} [{g.get('category')}]")

    if batch_info.get("previous_context"):
        lines.append("\n=== BỐI CẢNH HỘI THOẠI TRƯỚC ĐÓ (Tham khảo mạch cảm xúc, KHÔNG dịch lại) ===")
        for prev in batch_info["previous_context"]:
            lines.append(f"> {prev}")

    lines.append(f"\n=== DANH SÁCH CÂU CẦN DỊCH ({len(items)} CÂU) ===")
    for item in items:
        spk_info = f" [Người nói: {item['speaker']}]" if item.get('speaker') else ""
        face_info = f" [Face: {item['face']}]" if item.get('face') else ""
        lines.append(f"KEY: {item['key']}{spk_info}{face_info}")
        lines.append(f"ORIGINAL:\n{item['original']}\n")

    lines.append("=== YÊU CẦU TRẢ VỀ ===")
    lines.append("Trả về mã JSON thuần túy theo định dạng:")
    lines.append("```json")
    lines.append("{")
    lines.append('  "File.json:key1": "Bản dịch tiếng Việt 1",')
    lines.append('  "File.json:key2": "Bản dịch tiếng Việt 2"')
    lines.append("}")
    lines.append("```")

    return "\n".join(lines)


def slice_batches(game_dir: str, source_path: str = None, meta_path: str = None,
                  lorebook_path: str = None, batch_size: int = 40, out_dir: str = None) -> list[str]:
    """Slices source into rich contextual translation batches and saves them to disk."""
    actual_source = source_path or os.path.join(game_dir, "translation_source.json")
    actual_meta = meta_path or os.path.join(game_dir, "translation_metadata.json")
    actual_lorebook = lorebook_path or os.path.join(game_dir, "LOREBOOK.json")

    with open(actual_source, "r", encoding="utf-8-sig") as f:
        source_db = json.load(f)

    meta_db = {}
    if os.path.isfile(actual_meta):
        with open(actual_meta, "r", encoding="utf-8-sig") as f:
            meta_db = json.load(f)

    lorebook = {}
    if os.path.isfile(actual_lorebook):
        with open(actual_lorebook, "r", encoding="utf-8-sig") as f:
            lorebook = json.load(f)

    chunks = generate_semantic_chunks(source_db, batch_size=batch_size)
    print(f"[Batch Slicer] Generated {len(chunks)} semantic scene batches from {len(source_db)} entries.")

    target_dir = out_dir or os.path.join(game_dir, "batches")
    os.makedirs(target_dir, exist_ok=True)

    batch_files = []
    previous_sliding_window = []

    for idx, key_chunk in enumerate(chunks, 1):
        batch_dict = {k: source_db[k] for k in key_chunk}
        first_k = key_chunk[0]
        stype, sid, stitle = get_key_scene_info(first_k)

        mood, mood_directive = detect_batch_scene_mood(batch_dict)
        escape_ref = resolve_batch_escape_codes(batch_dict, lorebook.get("characters", []))
        active_ctx = filter_active_context(batch_dict, meta_db, lorebook)

        batch_items = []
        for k in key_chunk:
            m_item = meta_db.get(k, {})
            batch_items.append({
                "key": k,
                "original": source_db[k],
                "speaker": m_item.get("speaker", ""),
                "face": m_item.get("face", ""),
                "scene": m_item.get("scene", stitle),
                "event_name": m_item.get("event_name", "")
            })

        batch_obj = {
            "batch_id": f"batch_{idx:03d}",
            "batch_index": idx,
            "total_batches": len(chunks),
            "scene_type": stype,
            "scene_id": sid,
            "scene_title": stitle,
            "item_count": len(batch_items),
            "mood": mood,
            "mood_directive": mood_directive,
            "escape_codes_reference": escape_ref,
            "active_context": active_ctx,
            "previous_context": list(previous_sliding_window),
            "items": batch_items
        }

        # Inject formatted subagent prompt
        batch_obj["formatted_prompt"] = format_batch_prompt(batch_obj)

        out_path = os.path.join(target_dir, f"batch_{idx:03d}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(batch_obj, f, ensure_ascii=False, indent=2)

        batch_files.append(out_path)

        # Update sliding window (last 3 items of this batch)
        previous_sliding_window = [
            f"[{it['speaker'] or 'Lời dẫn'}]: {it['original'][:120]}"
            for it in batch_items[-3:]
        ]

    print(f"[Batch Slicer] Saved {len(batch_files)} batch files to: {target_dir}")
    return batch_files


def main():
    parser = argparse.ArgumentParser(description="Slice RPG Maker sources into rich semantic batches.")
    parser.add_argument("game_dir", help="Path to RPG Maker game root")
    parser.add_argument("--source", default=None, help="Path to translation_source.json")
    parser.add_argument("--metadata", default=None, help="Path to translation_metadata.json")
    parser.add_argument("--lorebook", default=None, help="Path to LOREBOOK.json")
    parser.add_argument("--batch-size", type=int, default=40, help="Target batch size (default: 40)")
    parser.add_argument("--out-dir", default=None, help="Output directory for batches")
    args = parser.parse_args()

    slice_batches(
        game_dir=os.path.abspath(args.game_dir),
        source_path=args.source,
        meta_path=args.metadata,
        lorebook_path=args.lorebook,
        batch_size=args.batch_size,
        out_dir=args.out_dir
    )


if __name__ == "__main__":
    main()
