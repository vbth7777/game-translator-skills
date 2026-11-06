# ============================================================================
# TEMPLATE: Live Floating Language Toggle for Ren'Py
# Place in game/live_language_toggle.rpy
# Allows switching between Vietnamese and English in real-time.
# ============================================================================

screen language_toggle_overlay():
    zorder 1000
    frame:
        xalign 0.98
        yalign 0.02
        background "#000000cc"
        xpadding 10
        ypadding 6
        has hbox:
            spacing 10

        textbutton "🇻🇳 Tiếng Việt":
            action [Language("vietnamese"), SelectedIf(_preferences.language == "vietnamese")]
            text_size 16
            text_selected_color "#ffdd44"
            text_idle_color "#ffffff"
            text_hover_color "#fffaaa"

        textbutton "🇬🇧 English":
            action [Language(None), SelectedIf(_preferences.language is None or _preferences.language == "")]
            text_size 16
            text_selected_color "#ffdd44"
            text_idle_color "#ffffff"
            text_hover_color "#fffaaa"

init 999 python:
    if "language_toggle_overlay" not in config.overlay_screens:
        config.overlay_screens.append("language_toggle_overlay")

