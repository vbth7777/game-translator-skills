# DẤU HIỆU NHẬN BIẾT & CHỮ KÝ CÁC GAME ENGINE (ENGINE FINGERPRINTS)

Tài liệu này cung cấp ma trận nhận diện nhanh các loại game engine dựa trên cấu trúc file, thư mục và tệp thực thi (executable).

---

## 1. Ren'Py Visual Novel Engine
- **Thư mục đặc trưng**:
  - `game/`: Chứa kịch bản, âm thanh, hình ảnh.
  - `renpy/`: Chứa mã nguồn lõi của engine Ren'Py.
  - `lib/py3-windows-x86_64` hoặc `lib/py2-windows-x86_64`: Trình thông dịch Python tích hợp.
- **Tệp tin đặc trưng**:
  - `game/*.rpa`: Tệp lưu trữ nén của Ren'Py (RPA v2 hoặc RPA v3).
  - `game/*.rpyc`: Kịch bản bytecode đã biên dịch từ Python/Ren'Py AST.
  - `game/*.rpy`: Kịch bản mã nguồn rõ (nếu chưa bị xóa).
  - `<GameName>.py` hoặc `<GameName>.exe`.
- **Cơ chế dịch thuật**:
  - Sử dụng thư mục `game/tl/<language>/`.
  - Có các khối lệnh `translate <language> <label>:` và `translate <language> strings:`.

---

## 2. Unity Engine
- **Thư mục đặc trưng**:
  - `<GameName>_Data/`: Thư mục dữ liệu chính của game.
- **Tệp tin đặc trưng**:
  - `UnityPlayer.dll`: Thư viện lõi Unity.
  - `UnityCrashHandler64.exe` hoặc `UnityCrashHandler32.exe`.
  - `globalgamemanagers`, `data.unity3d`, `level0`, `sharedassets*.assets`.
- **Phân loại kiến trúc**:
  1. **Unity Mono (.NET Managed)**:
     - Thư mục `<GameName>_Data/Managed/` chứa các file DLL: `Assembly-CSharp.dll`, `UnityEngine.dll`.
     - Dễ dàng can thiệp bằng DNSpy, ILSpy hoặc BepInEx 5.
  2. **Unity IL2CPP (Ahead-Of-Time Native)**:
     - Tệp `GameAssembly.dll` (kích thước lớn, thường từ 30MB đến 100MB+).
     - Thư mục `<GameName>_Data/il2cpp_data/`.
     - Không có DLL managed thông thường; code C# đã được biên dịch thành mã máy C++.
     - Can thiệp bằng BepInEx 6 (IL2CPP build), Harmony detours hoặc Cpp2IL / Il2CppDumper.

---

## 3. RPG Maker
- **RPG Maker MV / MZ**:
  - `package.json` với trường `"main": "index.html"` (chạy trên môi trường NW.js).
  - Thư mục `www/data/` (MV) hoặc `data/` (MZ) chứa các file `MapXXX.json`, `Actors.json`, `CommonEvents.json`, `System.json`.
  - `js/rmmv_core.js` (MV) hoặc `js/rmmz_core.js` (MZ).
- **RPG Maker VX Ace / XP**:
  - Tệp `Game.rgss3a` (VX Ace) hoặc `Game.rgssad` / `Game.rxdata` (XP).
  - Dùng ngôn ngữ lập trình Ruby / RGSS.

---

## 4. Unreal Engine
- **Thư mục đặc trưng**:
  - `<GameName>/Binaries/Win64/`.
  - `<GameName>/Content/Paks/`.
  - `Engine/Binaries/`.
- **Tệp tin đặc trưng**:
  - `*.pak` hoặc `*.ucas` / `*.utoc` (Zen Store từ Unreal Engine 5).
  - Công cụ can thiệp: UnrealPak, FModel, UAssetGUI, Repak.

---

## 5. Godot Engine
- **Tệp tin đặc trưng**:
  - `<GameName>.pck`: Tệp nén tài nguyên của Godot.
  - Executable tích hợp engine Godot.
  - Công cụ can thiệp: GDRE Tools, GodotPCKExplorer.

