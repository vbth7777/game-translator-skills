# HƯỚNG DẪN XỬ LÝ FONT FALLBACK TEXTMESHPRO TIẾNG VIỆT (UNITY)

Trong Unity, TextMeshPro sử dụng bảng ảnh đồ họa chứa các ký tự (Font Texture Atlas). Nếu font asset mặc định của game không có sẵn ký tự có dấu tiếng Việt (ă, â, đ, ê, ô, ơ, ư...), chữ sẽ bị rỗng, hiển thị ô vuông hoặc biến mất hoàn toàn.

---

## 1. Phương pháp Font Fallback Hook (Khuyến nghị cho BepInEx)
Không cần chỉnh sửa file assets của game; plugin BepInEx sẽ tự động tiêm (inject) một Font Asset hỗ trợ tiếng Việt vào danh sách `fallbackFontAssetTable` của TextMeshPro khi game khởi chạy.

### C# Code mẫu trong plugin:
```csharp
public static void AddVietnameseFallbackFont(TMP_FontAsset vietnameseFontAsset)
{
    // Lấy TMP_Settings mặc định hoặc font hiện hành
    var defaultFont = TMP_Settings.defaultFontAsset;
    if (defaultFont != null)
    {
        if (defaultFont.fallbackFontAssetTable == null)
            defaultFont.fallbackFontAssetTable = new Il2CppSystem.Collections.Generic.List<TMP_FontAsset>();

        if (!defaultFont.fallbackFontAssetTable.Contains(vietnameseFontAsset))
        {
            defaultFont.fallbackFontAssetTable.Add(vietnameseFontAsset);
            Plugin.Logger.LogInfo("Successfully added Vietnamese TMP Fallback Font!");
        }
    }
}
```

---

## 2. Phương pháp nạp AssetBundle Font rời
1. Dùng Unity Editor (cùng phiên bản engine với game) tạo một AssetBundle chứa file TTF chuẩn Unicode (ví dụ: `NotoSans-Regular.ttf` hoặc `SegoeUI.ttf`).
2. Sinh Font Asset SDF từ file TTF trong Unity Editor.
3. Xuất AssetBundle (ví dụ: `vietnamesefont.bundle`).
4. Khi plugin BepInEx nạp:
```csharp
var bundle = AssetBundle.LoadFromFile(Path.Combine(pluginDir, "vietnamesefont.bundle"));
var fontAsset = bundle.LoadAsset<TMP_FontAsset>("NotoSans SDF");
AddVietnameseFallbackFont(fontAsset);
```
Mọi văn bản TextMeshPro khi gặp ký tự tiếng Việt không có trong font gốc sẽ tự động mượn glyph từ font SDF dự phòng, hiển thị sắc nét 100%.

