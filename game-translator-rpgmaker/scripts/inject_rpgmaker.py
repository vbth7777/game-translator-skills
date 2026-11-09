#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker MV/MZ Dialogue & Data Injector
Safely re-injects translated dialogue, choices, and database terms into RPG Maker JSON files.
Preserves engine control codes, splits multi-line dialogue back into 401 Show Text commands,
and performs automatic pre-injection backups.
"""

import os
import sys
import json
import re
import shutil
import textwrap
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


def auto_word_wrap(text: str, width: int = 50) -> str:
    """Wraps text lines cleanly to avoid dialogue window overflow."""
    if width <= 0 or not text:
        return text

    text = text.replace('\n\n', ' <PARAGRAPH_BREAK> ')
    text = text.replace('\n', ' ')
    text = text.replace(' <PARAGRAPH_BREAK> ', '\n\n')
    text = re.sub(' +', ' ', text)

    lines = []
    for p in text.split('\n'):
        if not p.strip():
            lines.append('')
            continue
        wrapped = textwrap.wrap(p.strip(), width=width, break_long_words=False)
        lines.extend(wrapped)
    return '\n'.join(lines)


def restore_engine_tags(original_text: str, translated_text: str) -> str:
    """Restores any stripped or mangled RPG Maker tags and control codes."""
    if not isinstance(original_text, str) or not isinstance(translated_text, str):
        return translated_text

    # 1. XML / Chevron tags like <WordWrap>, <Speaker: X>
    orig_tags = re.findall(r'<[^>]+>', original_text)
    trans_tags = re.findall(r'<[^>]+>', translated_text)
    if orig_tags and orig_tags != trans_tags:
        for orig_tag in orig_tags:
            if orig_tag not in translated_text:
                tag_name = orig_tag.strip('<>').split(':')[0].strip()
                mangled_pattern = r'<\s*' + re.escape(tag_name) + r'[^>]*>'
                if re.search(mangled_pattern, translated_text, re.IGNORECASE):
                    translated_text = re.sub(mangled_pattern, orig_tag, translated_text, flags=re.IGNORECASE)
                elif orig_tag.startswith('<') and orig_tag.endswith('>'):
                    if original_text.strip().startswith(orig_tag) and not translated_text.startswith(orig_tag):
                        translated_text = orig_tag + " " + translated_text

    # 2. Control codes like \c[1], \v[2], \n[3], \., \|, \!, \^, \>, \<, \{, \}
    orig_codes = re.findall(r'\\[a-zA-Z]+\[[^\]]*\]|\\[\{\}\.\|!><\^]', original_text)
    for code in orig_codes:
        if code not in translated_text:
            clean_code = code.lstrip('\\')
            if clean_code in translated_text:
                translated_text = translated_text.replace(clean_code, code)

    return translated_text


def set_by_path(obj, path: str, value):
    """Sets a value in nested dictionary/list by dot-separated path."""
    parts = path.split('.')
    curr = obj
    for i, part in enumerate(parts[:-1]):
        key = int(part) if part.isdigit() else part
        curr = curr[key]

    last_part = parts[-1]
    last_key = int(last_part) if last_part.isdigit() else last_part
    curr[last_key] = value


def backup_directory(src_dir: str, dest_dir: str) -> bool:
    """Creates a pristine backup of game data files before modifying them."""
    if not os.path.exists(src_dir):
        return False
    if os.path.exists(dest_dir):
        print(f"[Backup] Existing backup found at {dest_dir}. Skipping backup to preserve pristine original.")
        return True
    try:
        shutil.copytree(src_dir, dest_dir)
        print(f"[Backup] Pristine backup created at: {dest_dir}")
        return True
    except Exception as e:
        print(f"[Backup Warning] Failed to create backup: {e}")
        return False


def inject_rpgmaker_data(game_dir: str, translations: dict, wrap_limit: int = 0) -> int:
    """Injects translation dictionary into RPG Maker JSON files."""
    actual_dir = resolve_game_data_dir(game_dir)
    if not os.path.isdir(actual_dir):
        print(f"Error: Data directory does not exist: {actual_dir}")
        return 0

    backup_dir = os.path.join(os.path.dirname(actual_dir), "data_original_backup")
    backup_directory(actual_dir, backup_dir)

    files = sorted([f for f in os.listdir(actual_dir) if f.endswith('.json')])
    injected_count = 0

    print(f"[Inject] Processing {len(files)} files in: {actual_dir}")

    for filename in files:
        filepath = os.path.join(actual_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        file_modified = False

        def get_trans(key_path: str, original_val: str) -> str:
            nonlocal file_modified, injected_count
            if not isinstance(original_val, str) or not original_val.strip():
                return original_val

            full_key = f"{filename}:{key_path}"
            res = translations.get(full_key, original_val)

            if res != original_val:
                file_modified = True
                injected_count += 1
                res = restore_engine_tags(original_val, res)
                if wrap_limit > 0:
                    res = auto_word_wrap(res, wrap_limit)
            return res

        # 1. CommonEvents.json Rebuild
        if filename == 'CommonEvents.json':
            for i, obj in enumerate(data):
                if obj and 'list' in obj:
                    old_list = obj['list']
                    new_list = []
                    idx = 0
                    while idx < len(old_list):
                        cmd = old_list[idx]
                        code = cmd.get('code')
                        params = cmd.get('parameters', [])

                        if code in (401, 405):
                            start_idx = idx
                            consecutive_401s = [params[0]]
                            idx += 1
                            while idx < len(old_list) and old_list[idx].get('code') in (401, 405):
                                consecutive_401s.append(old_list[idx].get('parameters')[0])
                                idx += 1

                            original_block = "\n".join(consecutive_401s)
                            translated_block = get_trans(f"{i}.event_list.{start_idx}.dialogue", original_block)

                            for line in translated_block.split('\n'):
                                new_list.append({
                                    "code": cmd.get('code', 401),
                                    "indent": cmd.get('indent', 0),
                                    "parameters": [line]
                                })
                        else:
                            if code == 102:
                                for choice_idx in range(len(params[0])):
                                    params[0][choice_idx] = get_trans(
                                        f"{i}.event_list.{idx}.choice.{choice_idx}",
                                        params[0][choice_idx]
                                    )
                            new_list.append(cmd)
                            idx += 1
                    obj['list'] = new_list

        # 2. Troops.json Rebuild
        elif filename == 'Troops.json':
            for i, obj in enumerate(data):
                if obj and 'pages' in obj:
                    for page_idx, page in enumerate(obj['pages']):
                        if 'list' in page:
                            old_list = page['list']
                            new_list = []
                            idx = 0
                            while idx < len(old_list):
                                cmd = old_list[idx]
                                code = cmd.get('code')
                                params = cmd.get('parameters', [])

                                if code in (401, 405):
                                    start_idx = idx
                                    consecutive_401s = [params[0]]
                                    idx += 1
                                    while idx < len(old_list) and old_list[idx].get('code') in (401, 405):
                                        consecutive_401s.append(old_list[idx].get('parameters')[0])
                                        idx += 1

                                    original_block = "\n".join(consecutive_401s)
                                    translated_block = get_trans(
                                        f"troops.{i}.pages.{page_idx}.list.{start_idx}.dialogue",
                                        original_block
                                    )

                                    for line in translated_block.split('\n'):
                                        new_list.append({
                                            "code": cmd.get('code', 401),
                                            "indent": cmd.get('indent', 0),
                                            "parameters": [line]
                                        })
                                else:
                                    if code == 102:
                                        for choice_idx in range(len(params[0])):
                                            params[0][choice_idx] = get_trans(
                                                f"troops.{i}.pages.{page_idx}.list.{idx}.choice.{choice_idx}",
                                                params[0][choice_idx]
                                            )
                                    new_list.append(cmd)
                                    idx += 1
                            page['list'] = new_list

        # 3. MapXXX.json Rebuild
        elif filename.startswith('Map') and filename[3:-5].isdigit():
            if 'displayName' in data:
                data['displayName'] = get_trans("displayName", data['displayName'])

            events = data.get('events', [])
            for evt_idx, evt in enumerate(events):
                if evt and 'pages' in evt:
                    for page_idx, page in enumerate(evt['pages']):
                        if 'list' in page:
                            old_list = page['list']
                            new_list = []
                            idx = 0
                            while idx < len(old_list):
                                cmd = old_list[idx]
                                code = cmd.get('code')
                                params = cmd.get('parameters', [])

                                if code in (401, 405):
                                    start_idx = idx
                                    consecutive_401s = [params[0]]
                                    idx += 1
                                    while idx < len(old_list) and old_list[idx].get('code') in (401, 405):
                                        consecutive_401s.append(old_list[idx].get('parameters')[0])
                                        idx += 1

                                    original_block = "\n".join(consecutive_401s)
                                    translated_block = get_trans(
                                        f"events.{evt_idx}.pages.{page_idx}.list.{start_idx}.dialogue",
                                        original_block
                                    )

                                    for line in translated_block.split('\n'):
                                        new_list.append({
                                            "code": cmd.get('code', 401),
                                            "indent": cmd.get('indent', 0),
                                            "parameters": [line]
                                        })
                                else:
                                    if code == 102:
                                        for choice_idx in range(len(params[0])):
                                            params[0][choice_idx] = get_trans(
                                                f"events.{evt_idx}.pages.{page_idx}.list.{idx}.choice.{choice_idx}",
                                                params[0][choice_idx]
                                            )
                                    new_list.append(cmd)
                                    idx += 1
                            page['list'] = new_list

        # 4. Database Files
        else:
            prefix = f"{filename}:"
            matching_keys = [k for k in translations if k.startswith(prefix)]
            for full_k in matching_keys:
                subpath = full_k[len(prefix):]
                trans_val = translations[full_k]
                try:
                    set_by_path(data, subpath, trans_val)
                    file_modified = True
                    injected_count += 1
                except Exception as e:
                    pass

        # Write file back if updated
        if file_modified:
            try:
                with open(filepath, 'w', encoding='utf-8-sig') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving {filename}: {e}")

    print(f"[Inject Done] Successfully injected {injected_count} translated entries into RPG Maker files.")
    return injected_count


def main():
    parser = argparse.ArgumentParser(description="Inject translations into RPG Maker MV/MZ data.")
    parser.add_argument("game_dir", help="Path to RPG Maker game root or data folder")
    parser.add_argument("translations", help="Path to translation_vietnamese.json")
    parser.add_argument("--wrap", type=int, default=0, help="Line width wrap limit (0 = disabled, e.g. 50)")
    args = parser.parse_args()

    game_dir = os.path.abspath(args.game_dir)
    trans_file = os.path.abspath(args.translations)

    with open(trans_file, "r", encoding="utf-8-sig") as f:
        translations = json.load(f)

    inject_rpgmaker_data(game_dir, translations, wrap_limit=args.wrap)


if __name__ == "__main__":
    main()

