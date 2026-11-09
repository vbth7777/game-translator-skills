#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker MV/MZ Encrypted Image Crypto Engine (.rpgmvp <-> .png)
Supports header stripping, XOR de-masking, and re-encryption.
"""

import os
import json
import cv2
import numpy as np

DEFAULT_HEADER = bytes.fromhex('5250474d560000000003010000000000') # RPGMV\x00\x00\x00\x00\x03\x01\x00\x00\x00\x00\x00
PNG_MAGIC = bytes.fromhex('89504e470d0a1a0a')

def find_system_json(game_root="."):
    """Finds System.json across common RPG Maker directory structures."""
    candidates = [
        os.path.join(game_root, "data", "System.json"),
        os.path.join(game_root, "www", "data", "System.json"),
        os.path.join(game_root, "System.json")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def get_encryption_key(game_root="."):
    """Reads encryption key from System.json, default fallback to empty MD5."""
    sys_path = find_system_json(game_root)
    if sys_path and os.path.exists(sys_path):
        try:
            with open(sys_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                key_hex = data.get("encryptionKey", "d41d8cd98f00b204e9800998ecf8427e")
                return bytes.fromhex(key_hex)
        except Exception as e:
            print(f"[Crypto] Warning reading {sys_path}: {e}")
    # Default RPG Maker MV default key (MD5 of empty string)
    return bytes.fromhex("d41d8cd98f00b204e9800998ecf8427e")

class RPGMVCrypto:
    def __init__(self, key=None, game_root="."):
        if key is None:
            self.key = get_encryption_key(game_root)
        elif isinstance(key, str):
            self.key = bytes.fromhex(key)
        else:
            self.key = key
        self.header = DEFAULT_HEADER

    def decrypt_bytes_to_png(self, file_bytes):
        """Decrypts raw bytearray of an .rpgmvp file into standard PNG bytes."""
        if len(file_bytes) < 32:
            raise ValueError("File is too small to be a valid .rpgmvp")

        # First 16 bytes: header
        # Next 16 bytes: XOR masked with key
        raw = bytearray(file_bytes[16:])
        for i in range(16):
            raw[i] ^= self.key[i]
        
        if bytes(raw[:8]) != PNG_MAGIC:
            raise ValueError(f"Decryption failed: expected PNG magic header, got {bytes(raw[:8]).hex()}")
        return bytes(raw)

    def encrypt_png_to_bytes(self, png_bytes):
        """Encrypts standard PNG bytes into an .rpgmvp bytearray."""
        if len(png_bytes) < 16:
            raise ValueError("PNG bytes too short to encrypt")
        
        result = bytearray(self.header)
        masked_head = bytearray(png_bytes[:16])
        for i in range(16):
            masked_head[i] ^= self.key[i]
        
        result.extend(masked_head)
        result.extend(png_bytes[16:])
        return bytes(result)

    def load_image(self, file_path):
        """Loads .rpgmvp, .png, or .jpg and returns cv2/numpy image (BGRA/BGR)."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.rpgmvp', '.rpgmvm', '.rpgmvo']:
            with open(file_path, 'rb') as f:
                enc_data = f.read()
            png_bytes = self.decrypt_bytes_to_png(enc_data)
            img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
            return img, 'rpgmvp'
        elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
            # Use imdecode with fromfile to safely support Unicode paths on Windows
            with open(file_path, 'rb') as f:
                raw = f.read()
            img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_UNCHANGED)
            return img, ext[1:]
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def save_image(self, img_np, out_path, orig_format='rpgmvp'):
        """Encodes cv2/numpy image and saves to disk as .rpgmvp or standard image."""
        ext = os.path.splitext(out_path)[1].lower()
        if ext == '.rpgmvp' or orig_format == 'rpgmvp':
            success, buf = cv2.imencode('.png', img_np, [cv2.IMWRITE_PNG_COMPRESSION, 6])
            if not success:
                raise RuntimeError("Failed to encode image to PNG buffer")
            enc_bytes = self.encrypt_png_to_bytes(buf.tobytes())
            with open(out_path, 'wb') as f:
                f.write(enc_bytes)
        else:
            save_ext = f'.{orig_format}' if not ext else ext
            success, buf = cv2.imencode(save_ext, img_np)
            if not success:
                raise RuntimeError(f"Failed to encode image to {save_ext}")
            with open(out_path, 'wb') as f:
                f.write(buf.tobytes())

if __name__ == '__main__':
    crypto = RPGMVCrypto()
    print("[rpgmv_crypto] Crypto engine ready. Encryption Key:", crypto.key.hex())
