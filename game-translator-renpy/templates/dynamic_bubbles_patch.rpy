# ============================================================================
# TEMPLATE: Ren'Py Dynamic Speech Bubbles & In-Memory Notification Hook
# Place in game/dynamic_bubbles_patch.rpy
# Intercepts Python functions that generate speech bubbles, floating text,
# notifications, and reaction lines, routing them to renpy.translation.translate_string().
# ============================================================================

init 999 python:
    def _tl_translate_string(s):
        """Translates a dynamic string using Ren'Py's strings translation table."""
        if not s or not isinstance(s, str):
            return s
        _s = s.strip()
        _quoted = False
        if (_s.startswith('"') and _s.endswith('"')) or (_s.startswith("'") and _s.endswith("'")):
            _s = _s[1:-1]
            _quoted = True
        # Attempt translation
        _tl = renpy.translation.translate_string(_s)
        if _tl != _s:
            return f'"{_tl}"' if _quoted else _tl
        return renpy.translation.translate_string(s)

    # 1. Intercept Speech Bubble Text
    if "get_bubble_text" in globals():
        _orig_get_bubble_text = get_bubble_text
        def _tl_get_bubble_text(action, w=None):
            res = _orig_get_bubble_text(action, w)
            return _tl_translate_string(res) if isinstance(res, str) else res
        get_bubble_text = _tl_get_bubble_text

    # 2. Intercept Flavor / Reaction Text
    if "get_flavor_text" in globals():
        _orig_get_flavor_text = get_flavor_text
        def _tl_get_flavor_text(action, w=None):
            res = _orig_get_flavor_text(action, w)
            if isinstance(res, list):
                return [_tl_translate_string(x) if isinstance(x, str) else x for x in res]
            elif isinstance(res, str):
                return _tl_translate_string(res)
            return res
        get_flavor_text = _tl_get_flavor_text

    # 3. Intercept In-Game Notifications
    if "add_notification" in globals():
        _orig_add_notification = add_notification
        def _tl_add_notification(text, *args, **kwargs):
            if text and isinstance(text, str):
                text = _tl_translate_string(text)
            return _orig_add_notification(text, *args, **kwargs)
        add_notification = _tl_add_notification

    # 4. Intercept Dialogue Multi-step Sequences
    if "_emit_talk_steps" in globals():
        _orig_emit_talk_steps = _emit_talk_steps
        def _tl_emit_talk_steps(first, steps, col=None):
            translated_steps = []
            for kind, txt in steps:
                translated_steps.append((kind, _tl_translate_string(txt)))
            return _orig_emit_talk_steps(first, translated_steps, col)
        _emit_talk_steps = _tl_emit_talk_steps

    # 5. Intercept Character Log Say Statements
    if "log_say" in globals():
        _orig_log_say = log_say
        def _tl_log_say(speaker, line, speaker_color="#ffccff"):
            return _orig_log_say(speaker, _tl_translate_string(line), speaker_color)
        log_say = _tl_log_say
