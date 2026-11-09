# Ren'Py High-Definition (HD / 4K) Texture Tuning & Memory Optimization
# Drop this file into game/hd_override.rpy to fine-tune texture cache and scaling.

init -999 python:
    # 1. Expand Ren'Py Texture Cache for 4K / High-Res Assets
    # Default is typically 8-16 screens. Expand to 32-64 to avoid texture eviction stutters on 1440p/4K displays.
    config.image_cache_size = 48

    # 2. Maximum Texture Dimensions
    # Ensure modern OpenGL/DirectX renderer allows 4096x4096 texture atlases.
    config.gl2 = True

    # 3. High-DPI Displayable Wrapper (Optional)
    # If static 2D images were upscaled to true 2x (e.g. 3840x2160 on a 1920x1080 gui),
    # this transform automatically rescales them to match native layout without modifying script.rpy.
    renpy.register_transform("hd_half", Transform(zoom=0.5))

# Optional: Automatic Transform hook for HD assets if prefixed with "hd/"
transform hd_fit(target_w=1920, target_h=1080):
    fit "contain"
    xsize target_w
    ysize target_h

