# RPG Maker MV/MZ Asset Encryption Specification (.rpgmvp)

## 1. Overview of RPG Maker Encryption

RPG Maker MV and MZ provide a built-in asset obfuscation mechanism:
- Image assets (PNG) are saved as `.rpgmvp` (or `.png_` in some engines).
- Audio assets (M4A / OGG) are saved as `.rpgmvm` and `.rpgmvo`.

This encryption is **lightweight XOR masking** applied exclusively to the file header, leaving the remainder of the file unencrypted to enable fast browser-based decoding via Web Audio and WebGL.

---

## 2. Binary File Layout

An encrypted `.rpgmvp` file consists of three sequential byte segments:

```
┌───────────────────────────────┬───────────────────────────────┬───────────────────────────────┐
│     Bytes 0 - 15 (16 B)       │     Bytes 16 - 31 (16 B)      │     Bytes 32 - End (N B)      │
│     Header Signature          │     XOR-Masked PNG Header     │     Pure Unencrypted Body     │
│ 52 50 47 4d 56 00 00 00 ...   │ byte[i] ^ encryption_key[i]   │ standard compressed PNG bytes │
└───────────────────────────────┴───────────────────────────────┴───────────────────────────────┘
```

1. **Header Signature (16 bytes)**:
   - RPG Maker MV Signature: `52 50 47 4d 56 00 00 00 00 03 01 00 00 00 00 00` (`RPGMV\x00\x00\x00\x00\x03\x01\x00\x00\x00\x00\x00`).
   - RPG Maker MZ Signature: `52 50 47 4d 5a 00 00 00 00 03 01 00 00 00 00 00` (`RPGMZ\x00\x00\x00\x00\x03\x01\x00\x00\x00\x00\x00`).
2. **XOR-Masked Header (16 bytes)**:
   - Corresponds to the first 16 bytes of the original PNG file:
     - First 8 bytes: PNG Magic Header (`89 50 4e 47 0d 0a 1a 0a`).
     - Next 4 bytes: IHDR Chunk Length (`00 00 00 0d`).
     - Next 4 bytes: IHDR Chunk Type (`49 48 44 52`).
   - Each byte is XORed with the corresponding byte of the 16-byte encryption key:
     $$\text{MaskedByte}[i] = \text{OriginalByte}[i] \oplus \text{Key}[i], \quad i \in [0, 15]$$
3. **Payload (Bytes 32 onwards)**:
   - Remains 100% untouched raw PNG binary data (containing the rest of IHDR chunk, image dimensions, IDAT chunks, and IEND).

---

## 3. Key Discovery in `System.json`

The 16-byte encryption key is stored as a 32-character hex string in:
`www/data/System.json` (or `data/System.json`):

```json
{
  "hasEncryptedImages": true,
  "hasEncryptedAudio": true,
  "encryptionKey": "d41d8cd98f00b204e9800998ecf8427e"
}
```

If `encryptionKey` is absent or the default empty string MD5, fallback to:
`bytes.fromhex("d41d8cd98f00b204e9800998ecf8427e")`.

---

## 4. In-Memory Crypto Implementation

```python
def decrypt_rpgmvp(raw_file_bytes, key_16_bytes):
    # Strip 16-byte RPGMV header, XOR next 16 bytes
    png_data = bytearray(raw_file_bytes[16:])
    for i in range(16):
        png_data[i] ^= key_16_bytes[i]
    return bytes(png_data)

def encrypt_png(png_bytes, key_16_bytes, header_16_bytes):
    result = bytearray(header_16_bytes)
    masked_chunk = bytearray(png_bytes[:16])
    for i in range(16):
        masked_chunk[i] ^= key_16_bytes[i]
    result.extend(masked_chunk)
    result.extend(png_bytes[16:])
    return bytes(result)
```
