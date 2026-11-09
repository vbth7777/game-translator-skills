#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker MV/MZ Deep Data & Dialogue Extractor
Extracts all database entries, common events, map events, choices, and dialogue
with rich scene context, character metadata, and facial expression indices.
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
    """Finds the actual directory containing RPG Maker JSON files."""
    if not dir_path or not os.path.exists(dir_path):
        return dir_path

    # 1. Direct match if already points to data folder
    try:
        if os.path.isdir(dir_path):
            files = os.listdir(dir_path)
            if any(f in files for f in ["System.json", "Actors.json", "MapInfos.json", "CommonEvents.json"]):
                return os.path.abspath(dir_path)
    except Exception:
        pass

    # 2. Check www/data (RPG Maker MV typical layout)
    www_data = os.path.join(dir_path, "www", "data")
    if os.path.exists(www_data) and os.path.isdir(www_data):
        return os.path.abspath(www_data)

    # 3. Check data (RPG Maker MZ or unpacked MV)
    plain_data = os.path.join(dir_path, "data")
    if os.path.exists(plain_data) and os.path.isdir(plain_data):
        return os.path.abspath(plain_data)

    # 4. Shallow walk search
    try:
        for root, dirs, files in os.walk(dir_path):
            if "System.json" in files or "Actors.json" in files:
                return os.path.abspath(root)
            if root[len(dir_path):].count(os.sep) > 3:
                del dirs[:]
    except Exception:
        pass

    return os.path.abspath(dir_path)


def clean_text(txt: str) -> str | None:
    """Filters out empty strings, pure numbers/symbols, and JS scripts."""
    if not txt or not isinstance(txt, str):
        return None
    cleaned = txt.strip()
    if not cleaned:
        return None

    # Skip pure numbers/symbols
    if re.match(r'^[0-9\s\-\+\*\/\\=<>!,.;:"\'\?_%&|$#@\[\]\(\)\{\}]+$', cleaned):
        return None

    # Skip JavaScript code / Plugin command signatures / URLs
    if any(cleaned.startswith(prefix) for prefix in [
        "//", "/*", "http://", "https://", "javascript:", "eval(", "$game",
        "AudioManager.", "SceneManager.", "Galv.", "YEP.", "StorageManager."
    ]):
        return None

    # Skip lines that look like pure JS script execution (e.g. "$gameVariables.setValue(1, 2);")
    if re.match(r'^\$?[a-zA-Z0-9_\.]+\s*\([^\)]*\)\s*;?$', cleaned):
        return None

    return txt


def extract_speaker_from_text(text: str) -> str:
    """Extracts speaker names embedded in dialogue text."""
    if not text or not isinstance(text, str):
        return ""
    # Format \C[x]Name\C[0] or \c[x]Name\c[0]
    m = re.match(r'^\s*\\[cC]\[\d+\]\s*([^\\:\n\r]+?)\s*\\[cC]\[\d+\](?:\s*:\s*|\s*\n|\s+)', text)
    if m:
        return m.group(1).strip()
    # Format 【Name】 or [Name]
    m_bracket = re.match(r'^\s*[【\[]([^】\]\n\r]+?)[】\]](?:\s*:\s*|\s*\n|\s+)', text)
    if m_bracket:
        return m_bracket.group(1).strip()
    # Format Name: Dialogue
    m2 = re.match(r'^\s*([A-Z][a-zA-Z0-9_\'\-]{1,20})\s*:\s*', text)
    if m2:
        return m2.group(1).strip()
    return ""


def clean_character_name_from_face(face_str: str) -> str:
    """Derives character name from face asset filename (e.g. 'Actor1_face' -> 'Actor1')."""
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


def extract_rpgmaker_data(data_dir: str) -> tuple[dict, dict]:
    """
    Extracts all translatable strings and metadata from RPG Maker JSON files.
    Returns (translation_db, metadata_db).
    """
    actual_dir = resolve_game_data_dir(data_dir)
    translation_db = {}
    metadata_db = {}

    if not os.path.exists(actual_dir) or not os.path.isdir(actual_dir):
        print(f"[Extract Error] Data directory does not exist: {actual_dir}")
        return {}, {}

    raw_files = [f for f in os.listdir(actual_dir) if f.endswith('.json')]
    print(f"[Extract] Scanning {len(raw_files)} JSON files in: {actual_dir}")

    db_order = [
        "System.json", "Actors.json", "Classes.json", "Skills.json",
        "Items.json", "Weapons.json", "Armors.json", "Enemies.json",
        "States.json", "Troops.json", "MapInfos.json"
    ]

    def file_sort_key(fname: str):
        for idx, db_f in enumerate(db_order):
            if fname.lower() == db_f.lower():
                return (0, idx)
        if fname.lower() == "commonevents.json":
            return (1, 0)
        if fname.lower().startswith("map") and fname[3:-5].isdigit():
            return (2, int(fname[3:-5]))
        return (3, fname)

    files = sorted(raw_files, key=file_sort_key)

    for filename in files:
        filepath = os.path.join(actual_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[Extract Warning] Error reading {filename}: {e}")
            continue

        def add(key, value):
            val = clean_text(value)
            if val is not None:
                translation_db[f"{filename}:{key}"] = val

        def record_metadata(full_key, full_text, code_101_params, scene_name="", event_name=""):
            if not full_key or not full_text:
                return
            spk = extract_speaker_from_text(full_text)
            face_str = ""
            if code_101_params:
                # In MZ, param[4] holds the custom speaker name
                if not spk and len(code_101_params) > 4 and code_101_params[4]:
                    spk = str(code_101_params[4]).strip()
                # If still no speaker, derive from face graphic name
                if not spk and len(code_101_params) > 0 and code_101_params[0]:
                    spk = clean_character_name_from_face(str(code_101_params[0]).strip())
                if len(code_101_params) > 0 and code_101_params[0]:
                    f_name = str(code_101_params[0]).strip()
                    f_idx = code_101_params[1] if len(code_101_params) > 1 else 0
                    face_str = f"{f_name}:{f_idx}"
            if not spk and event_name and not event_name.upper().startswith("EV"):
                spk = event_name

            metadata_db[full_key] = {
                "speaker": spk,
                "scene": scene_name,
                "event_name": event_name,
                "face": face_str
            }

        if filename == 'Actors.json':
            for i, obj in enumerate(data):
                if obj:
                    add(f"{i}.name", obj.get('name'))
                    add(f"{i}.nickname", obj.get('nickname'))
                    add(f"{i}.profile", obj.get('profile'))

        elif filename == 'Classes.json':
            for i, obj in enumerate(data):
                if obj:
                    add(f"{i}.name", obj.get('name'))

        elif filename == 'Skills.json':
            for i, obj in enumerate(data):
                if obj:
                    add(f"{i}.name", obj.get('name'))
                    add(f"{i}.description", obj.get('description'))
                    for m_idx in range(1, 5):
                        add(f"{i}.message{m_idx}", obj.get(f'message{m_idx}'))

        elif filename in ['Items.json', 'Armors.json', 'Weapons.json']:
            for i, obj in enumerate(data):
                if obj:
                    add(f"{i}.name", obj.get('name'))
                    add(f"{i}.description", obj.get('description'))

        elif filename == 'Enemies.json':
            for i, obj in enumerate(data):
                if obj:
                    add(f"{i}.name", obj.get('name'))

        elif filename == 'States.json':
            for i, obj in enumerate(data):
                if obj:
                    add(f"{i}.name", obj.get('name'))
                    for m_idx in range(1, 5):
                        add(f"{i}.message{m_idx}", obj.get(f'message{m_idx}'))

        elif filename == 'System.json':
            if data:
                add("gameTitle", data.get('gameTitle'))
                add("currencyUnit", data.get('currencyUnit'))
                for i, x in enumerate(data.get('skillTypes', [])):
                    add(f"skillTypes.{i}", x)
                for i, x in enumerate(data.get('weaponTypes', [])):
                    add(f"weaponTypes.{i}", x)
                for i, x in enumerate(data.get('armorTypes', [])):
                    add(f"armorTypes.{i}", x)
                for i, x in enumerate(data.get('elements', [])):
                    add(f"elements.{i}", x)
                for i, x in enumerate(data.get('equipTypes', [])):
                    add(f"equipTypes.{i}", x)
                terms = data.get('terms', {})
                for k in ['basic', 'commands', 'params']:
                    for i, x in enumerate(terms.get(k, [])):
                        add(f"terms.{k}.{i}", x)
                messages = terms.get('messages', {})
                for k, v in messages.items():
                    add(f"terms.messages.{k}", v)

        elif filename == 'MapInfos.json':
            for i, obj in enumerate(data):
                if obj:
                    add(f"{i}.name", obj.get('name'))

        elif filename == 'CommonEvents.json':
            for i, obj in enumerate(data):
                if obj and 'list' in obj:
                    current_dialogue = []
                    start_idx = -1
                    last_code_101 = None
                    scene_name = obj.get('name', '')
                    for idx, cmd in enumerate(obj['list']):
                        code = cmd.get('code')
                        params = cmd.get('parameters', [])

                        if code in (401, 405):
                            if start_idx == -1:
                                start_idx = idx
                            current_dialogue.append(params[0])
                        else:
                            if current_dialogue:
                                full_text = "\n".join(current_dialogue)
                                k_dialogue = f"{i}.event_list.{start_idx}.dialogue"
                                add(k_dialogue, full_text)
                                record_metadata(f"{filename}:{k_dialogue}", full_text, last_code_101, scene_name=scene_name)
                                current_dialogue = []
                                start_idx = -1

                            if code == 101:
                                last_code_101 = params
                            elif code == 102:
                                for choice_idx, choice_txt in enumerate(params[0]):
                                    add(f"{i}.event_list.{idx}.choice.{choice_idx}", choice_txt)

                    if current_dialogue:
                        full_text = "\n".join(current_dialogue)
                        k_dialogue = f"{i}.event_list.{start_idx}.dialogue"
                        add(k_dialogue, full_text)
                        record_metadata(f"{filename}:{k_dialogue}", full_text, last_code_101, scene_name=scene_name)

        elif filename == 'Troops.json':
            for i, obj in enumerate(data):
                if obj and 'pages' in obj:
                    t_name = obj.get('name', '')
                    for page_idx, page in enumerate(obj['pages']):
                        if 'list' in page:
                            current_dialogue = []
                            start_idx = -1
                            last_code_101 = None
                            for idx, cmd in enumerate(page['list']):
                                code = cmd.get('code')
                                params = cmd.get('parameters', [])

                                if code in (401, 405):
                                    if start_idx == -1:
                                        start_idx = idx
                                    current_dialogue.append(params[0])
                                else:
                                    if current_dialogue:
                                        full_text = "\n".join(current_dialogue)
                                        k_dialogue = f"troops.{i}.pages.{page_idx}.list.{start_idx}.dialogue"
                                        add(k_dialogue, full_text)
                                        record_metadata(f"{filename}:{k_dialogue}", full_text, last_code_101, scene_name=t_name)
                                        current_dialogue = []
                                        start_idx = -1

                                    if code == 101:
                                        last_code_101 = params
                                    elif code == 102:
                                        for choice_idx, choice_txt in enumerate(params[0]):
                                            add(f"troops.{i}.pages.{page_idx}.list.{idx}.choice.{choice_idx}", choice_txt)

                            if current_dialogue:
                                full_text = "\n".join(current_dialogue)
                                k_dialogue = f"troops.{i}.pages.{page_idx}.list.{start_idx}.dialogue"
                                add(k_dialogue, full_text)
                                record_metadata(f"{filename}:{k_dialogue}", full_text, last_code_101, scene_name=t_name)

        elif filename.startswith('Map') and filename[3:-5].isdigit():
            display_name = data.get('displayName', '')
            add("displayName", display_name)
            events = data.get('events', [])
            for evt_idx, evt in enumerate(events):
                if evt and 'pages' in evt:
                    evt_name = evt.get('name', '')
                    for page_idx, page in enumerate(evt['pages']):
                        if 'list' in page:
                            current_dialogue = []
                            start_idx = -1
                            last_code_101 = None
                            for idx, cmd in enumerate(page['list']):
                                code = cmd.get('code')
                                params = cmd.get('parameters', [])

                                if code in (401, 405):
                                    if start_idx == -1:
                                        start_idx = idx
                                    current_dialogue.append(params[0])
                                else:
                                    if current_dialogue:
                                        full_text = "\n".join(current_dialogue)
                                        k_dialogue = f"events.{evt_idx}.pages.{page_idx}.list.{start_idx}.dialogue"
                                        add(k_dialogue, full_text)
                                        record_metadata(
                                            f"{filename}:{k_dialogue}",
                                            full_text,
                                            last_code_101,
                                            scene_name=display_name or f"Map {filename[3:-5]}",
                                            event_name=evt_name
                                        )
                                        current_dialogue = []
                                        start_idx = -1

                                    if code == 101:
                                        last_code_101 = params
                                    elif code == 102:
                                        for choice_idx, choice_txt in enumerate(params[0]):
                                            add(f"events.{evt_idx}.pages.{page_idx}.list.{idx}.choice.{choice_idx}", choice_txt)

                            if current_dialogue:
                                full_text = "\n".join(current_dialogue)
                                k_dialogue = f"events.{evt_idx}.pages.{page_idx}.list.{start_idx}.dialogue"
                                add(k_dialogue, full_text)
                                record_metadata(
                                    f"{filename}:{k_dialogue}",
                                    full_text,
                                    last_code_101,
                                    scene_name=display_name or f"Map {filename[3:-5]}",
                                    event_name=evt_name
                                )

    print(f"[Extract Done] Extracted {len(translation_db)} entries with {len(metadata_db)} metadata records.")
    return translation_db, metadata_db


def main():
    parser = argparse.ArgumentParser(description="Extract RPG Maker MV/MZ dialogue and database strings.")
    parser.add_argument("game_dir", help="Path to RPG Maker game root or data folder")
    parser.add_argument("--out", default=None, help="Output path for translation_source.json")
    parser.add_argument("--metadata", default=None, help="Output path for translation_metadata.json")
    args = parser.parse_args()

    game_dir = os.path.abspath(args.game_dir)
    source_db, metadata_db = extract_rpgmaker_data(game_dir)

    out_source = args.out or os.path.join(game_dir, "translation_source.json")
    out_meta = args.metadata or os.path.join(game_dir, "translation_metadata.json")

    with open(out_source, "w", encoding="utf-8") as f:
        json.dump(source_db, f, ensure_ascii=False, indent=2)
    print(f"Saved source entries to: {out_source}")

    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(metadata_db, f, ensure_ascii=False, indent=2)
    print(f"Saved metadata records to: {out_meta}")


if __name__ == "__main__":
    main()

