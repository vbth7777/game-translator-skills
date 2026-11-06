# ============================================================================
# TEMPLATE: Ren'Py In-Memory Dictionary & Callback Monkey-Patch
# Place in game/memory_patch_template.rpy
# Solves strings embedded in Python objects/dictionaries (e.g. Live2D dating, stats)
# ============================================================================

init 990 python:
    # 1. Custom in-memory dictionary for strings that renpy translate ignores
    custom_inmemory_dict = {
        "Sample English Key": "Bản dịch tiếng Việt tương ứng",
        "Watch Scene": "Xem phân cảnh",
        "Inventory": "Túi đồ",
        "Happy": "Vui vẻ",
        "Angry": "Tức giận",
        "Dominant": "Áp Đảo",
        "Submissive": "Thuần Phục"
    }

    # 2. Dynamic state / names update function
    def update_custom_vietnamese_runtime():
        if _preferences.language != "english":
            # Translate dictionary in place if target dict exists
            if globals().get("game_stats_dict"):
                for k, v in custom_inmemory_dict.items():
                    if k in game_stats_dict:
                        game_stats_dict[k] = v
        else:
            # Restore English defaults if player switches back
            pass

    # 3. Register hooks to run on game start and save load
    if update_custom_vietnamese_runtime not in config.start_callbacks:
        config.start_callbacks.append(update_custom_vietnamese_runtime)
    if hasattr(config, "after_load_callbacks") and update_custom_vietnamese_runtime not in config.after_load_callbacks:
        config.after_load_callbacks.append(update_custom_vietnamese_runtime)

