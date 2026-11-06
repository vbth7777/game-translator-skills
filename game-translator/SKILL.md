---
name: game-translator
description: Master router and orchestrator for translating video games into Vietnamese and other languages. Detects engine (Ren'Py, Unity, RPG Maker, Unreal, Godot), extracts lore, deploys specialized subagents, and invokes engine-specific translation sub-skills.
---

# Game Translator (Master Router & Orchestrator)

This skill serves as the primary gateway and pipeline orchestrator for localizing video games into Vietnamese (or any target language) with human-grade quality, zero machine-translation awkwardness, and engine-level integrity.

## 1. Operating Workflow

Whenever the user asks to translate a game or points to a game directory/archive:

```
[Target Game Folder] ──> Step 1: Detect Engine & Architecture
                     ──> Step 2: Lore & Universe Reconnaissance
                     ──> Step 3: Route to Engine Sub-Skill (Ren'Py or Unity)
                     ──> Step 4: Dispatch Parallel Subagents
                     ──> Step 5: Verification, QC & Repackaging
```

---

## 2. Step 1: Engine Fingerprinting

Run the detection tool to identify the engine and runtime:

```bash
python game-translator/scripts/detect_engine.py "<PATH_TO_GAME>" --json
```

- If **Ren'Py**: Route immediately to `game-translator-renpy`.
- If **Unity** (Mono or IL2CPP): Route immediately to `game-translator-unity`.
- If **RPG Maker / Unreal / Godot**: Inform the user and apply standard extraction fallback.

See [engine_fingerprints.md](file:///d:/Development/Projects/game-translator-skills/game-translator/references/engine_fingerprints.md) for full architecture signatures.

---

## 3. Step 2: Lore & Context Reconnaissance

Before translating any dialogue, invoke the Lore Researcher agent or run:

```bash
python game-translator/scripts/search_game_lore.py "<GAME_TITLE>" --out "<GAME_DIR>/LORE_CONTEXT.json"
```

1. **Conduct Proactive Web Search**: Use search engines to gather character summaries, relationships, and wiki pages (VNDB, Fandom, Steam, F95zone).
2. **Build the Persona Matrix**: Define Vietnamese pronoun pairs for each character (e.g., `tôi - cậu`, `ta - ngươi`, `chị - cưng`).
3. **Set Tone Guidelines**: Enforce the **Anti-Sanitization Directive** (no euphemistic toning down of mature, suspenseful, or eroge text).

---

## 4. Step 3: Subagent Orchestration Matrix

Deploy modular subagents following the guidelines in [subagent_prompts.md](file:///d:/Development/Projects/game-translator-skills/game-translator/references/subagent_prompts.md):

1. **`game-lore-researcher`**: Populates `LORE_CONTEXT.json`.
2. **`game-string-extractor`**: Extracts strings into classified JSON / TSV files.
3. **`game-glossary-curator`**: Locks proper nouns, item names, and skill terms.
4. **`game-chunk-translator`**: Translates batches of 200–500 dialogue entries in parallel.
5. **`game-qc-linter`**: Audits tag preservation, rich text tokens, and unescaped symbols.
6. **`game-asset-localizer`**: Inpaints and redraws UI texture banners at 4x supersampling.
7. **`game-engine-packer`**: Re-compiles bytecode, verifies font Unicode coverage, and tests launch.

---

## 5. Sub-Skill Routing

- **For Ren'Py Games**: Invoke [game-translator-renpy](file:///d:/Development/Projects/game-translator-skills/game-translator-renpy/SKILL.md).
- **For Unity Games**: Invoke [game-translator-unity](file:///d:/Development/Projects/game-translator-skills/game-translator-unity/SKILL.md).

