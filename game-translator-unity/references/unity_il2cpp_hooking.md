# CẨM NANG CAN THIỆP & HOOKING UNITY IL2CPP VỚI BEPINEX 6

Kiến trúc Unity IL2CPP biên dịch mã nguồn C# thành mã máy native C++ (được đóng gói trong `GameAssembly.dll`). Do đó, không thể dùng DNSpy hay sửa assembly như Unity Mono thông thường.

---

## 1. Kiến trúc BepInEx 6 IL2CPP
BepInEx 6 IL2CPP sử dụng công nghệ Harmony detours can thiệp trực tiếp vào bảng địa chỉ hàm native thông qua metadata il2cpp:
- Thư mục cài đặt:
  ```
  <GameDir>/
  ├── BepInEx/
  │   ├── config/
  │   ├── core/
  │   └── plugins/
  │       └── GameTranslation/
  │           ├── GameTranslation.dll
  │           └── translations/
  │               ├── dialogue.json
  │               ├── ui.json
  │               └── characters.json
  ├── doorstop_config.ini
  ├── winhttp.dll (Doorstop proxy loader)
  └── GameAssembly.dll
  ```

---

## 2. Các điểm Hook chính (Injection Points)

### Điểm 1: `TMP_Text.set_text` & `TMP_Text.SetText`
TextMeshPro là giải pháp hiển thị văn bản phổ biến nhất trên Unity hiện đại.
Móc vào setter của thuộc tính `text`:
```csharp
[HarmonyPatch(typeof(TMP_Text), "set_text")]
[HarmonyPrefix]
public static void Prefix(TMP_Text __instance, ref string value)
{
    if (string.IsNullOrEmpty(value)) return;
    if (TranslationStore.TryGetTranslation(value, out string translated))
    {
        value = translated;
    }
}
```

### Điểm 2: `TextMeshProUGUI.OnEnable`
Dành cho các chuỗi giao diện tĩnh (Static UI labels) được dựng sẵn từ Unity Scene/Prefab:
```csharp
[HarmonyPatch(typeof(TextMeshProUGUI), "OnEnable")]
[HarmonyPostfix]
public static void Postfix(TextMeshProUGUI __instance)
{
    if (__instance != null && TranslationStore.TryGetTranslation(__instance.text, out string translated))
    {
        __instance.text = translated;
    }
}
```

### Điểm 3: `UnityEngine.UI.Text` (Legacy UGUI)
Với các game dùng UI Text truyền thống:
```csharp
[HarmonyPatch(typeof(Text), "set_text")]
[HarmonyPrefix]
public static void Prefix(Text __instance, ref string value)
{
    if (TranslationStore.TryGetTranslation(value, out string translated))
    {
        value = translated;
    }
}
```

### Điểm 4: Hiệu ứng gõ chữ (Typewriter Effect)
Nhiều Visual Novel Unity sử dụng script in chữ từng ký tự (Typewriter / TextPrinter). Khi chuỗi tiếng Việt có độ dài khác với chuỗi gốc Nhật/Anh, typewriter có thể bị kẹt hoặc hiển thị lỗi:
-> Cần hook vào hàm cập nhật của máy in chữ (ví dụ: `TextPrinter.Update` hoặc `ScenarioText.PrintNextChar`) để đảm bảo chiều dài chuỗi mới được đồng bộ.

