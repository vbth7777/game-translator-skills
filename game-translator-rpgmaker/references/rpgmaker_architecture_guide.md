# RPG Maker Engine Architecture & Localization Guide

This reference document outlines the internal data structures, event codes, and technical nuances of RPG Maker MV, MZ, VX Ace, and XP engines for high-fidelity Vietnamese localization.

---

## 1. Engine Versions & Data Layout

| Engine | Release | Data Format | Scripts / Engine Language | Typical Data Folder |
|---|---|---|---|---|
| **RPG Maker MZ** | 2020 | JSON (`*.json`) | ES6+ JavaScript, WebGL / Pixi.js | `<root>/data/` |
| **RPG Maker MV** | 2015 | JSON (`*.json`) | ES5 JavaScript, WebGL / Pixi.js | `<root>/www/data/` or `<root>/data/` |
| **RPG Maker VX Ace** | 2011 | Ruby Marshal (`*.rvdata2`) | Ruby 1.9 (RGSS3) | `<root>/Data/` |
| **RPG Maker XP** | 2004 | Ruby Marshal (`*.rxdata`) | Ruby 1.8 (RGSS1) | `<root>/Data/` |

---

## 2. Core Database & Map Files

In MV and MZ, the game database is stored as human-readable JSON files inside `data/`:

1. **System & Terms**:
   - `System.json`: Game title, currency unit (`currencyUnit`), element names, skill/weapon/armor types, and system terms (`terms.basic`, `terms.commands`, `terms.params`, `terms.messages`).
2. **Characters & Entities**:
   - `Actors.json`: Character names (`name`), nicknames (`nickname`), profiles/biographies (`profile`).
   - `Classes.json`: Class names.
   - `Enemies.json`: Monster and boss names.
3. **Gameplay & Battle Data**:
   - `Skills.json`: Skill names, descriptions, battle use messages (`message1` - `message4`).
   - `Items.json`, `Weapons.json`, `Armors.json`: Item names and descriptions.
   - `States.json`: Status effects (Poison, Stun, Charm) and infliction/recovery messages.
4. **Narrative & Events**:
   - `MapInfos.json`: Index and display names of all maps in the world.
   - `MapXXX.json` (e.g., `Map001.json`, `Map045.json`): Map display names, tile events, NPC dialogs, cutscenes, and triggers.
   - `CommonEvents.json`: Global reusable events, cutscenes, system functions, and major storyline sequences.
   - `Troops.json`: Combat formations and battle event pages (dialogue occurring mid-fight).

---

## 3. Event Command Codes Reference

RPG Maker stores event page actions as an array of command objects (`obj['list']`), each containing `code`, `indent`, and `parameters`:

| Event Code | Action Name | Parameter Format | Localization Role |
|---|---|---|---|
| **101** | **Show Text (Setup)** | `[faceName, faceIndex, background, positionType, speakerName]` | Defines speaker, face graphic, and expression. In MZ, `parameters[4]` is the speaker name. |
| **401** | **Show Text (Body)** | `[lineText]` | Individual line of dialogue inside the text box. Consecutive 401s form a single message window! |
| **405** | **Show Scrolling Text** | `[lineText]` | Continuous scrolling cutscene text. |
| **102** | **Show Choices** | `[[choice1, choice2, ...], defaultType, cancelType, ...]` | Interactive dialogue options chosen by the player. |
| **108 / 408** | **Comment** | `[commentText]` | Developer notes, plugin metadata tags (`<WordWrap>`, `<Speaker: X>`). |
| **355 / 655** | **Script Call** | `[jsCodeString]` | Raw JavaScript execution (must be skipped during string extraction!). |

---

## 4. Multi-Line Dialogue Aggregation & Reconstruction

### The Core Problem
In the raw JSON, RPG Maker splits a 4-line dialogue box into 4 distinct code `401` commands:
```json
{"code": 101, "parameters": ["Heroine_face", 0, 0, 2, "Alice"]},
{"code": 401, "parameters": ["Anh có chắc là muốn đi vào đó không?"]},
{"code": 401, "parameters": ["Nơi đó rất nguy hiểm đấy..."]},
{"code": 401, "parameters": ["Em không muốn anh bị thương đâu."]}
```

### The Solution (from `rpg-translate`)
1. **At Extraction (`extract_rpgmaker.py`)**:
   Consecutive `401` / `405` commands are merged into a single multi-line string joined by `\n`. This allows the AI translator to see the full sentence and paragraph flow rather than translating disjointed line fragments.
2. **At Injection (`inject_rpgmaker.py`)**:
   The translated block is split by `\n`, and new `401` objects are generated with matching `indent` so the game engine displays the lines seamlessly.

---

## 5. Face Graphic & Facial Expression Analysis

RPG Maker face sheets typically arrange 8 facial expressions in a **2x4 grid** (2 rows of 4 faces) numbered from `0` to `7`:

```
┌─────────┬─────────┬─────────┬─────────┐
│ Index 0 │ Index 1 │ Index 2 │ Index 3 │
│ Neutral │ Smile   │ Anger   │ Sadness │
├─────────┼─────────┼─────────┼─────────┤
│ Index 4 │ Index 5 │ Index 6 │ Index 7 │
│ Shock   │ Blushing│ Ecstasy │ Defeated│
└─────────┴─────────┴─────────┴─────────┘
```

- When `code 101` has parameters `["Alice_face", 5, ...]`:
  * Face File: `Alice_face` -> Cleaned character name: `Alice`.
  * Index: `5` -> Blushing / Shy / Aroused expression.
- The `slice_rpgmaker_batches.py` script automatically surfaces this expression context to the translator so the dialogue tone matches the character's facial expression 100%!
