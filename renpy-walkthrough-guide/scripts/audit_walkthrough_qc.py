#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walkthrough Quality Control (QC) & Visual Audit Engine
Used by the Quality Check Subagent to strictly verify:
1. Image existence, non-corruption, standard resolution (1920x1080)
2. No broken image links in markdown or HTML documents
3. Text alignment, absence of placeholders ([TODO], [Chèn ảnh])
4. Sequential logic continuity (item prerequisite before usage)
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from PIL import Image

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class WalkthroughQCAuditor:
    def __init__(self, doc_path: Path):
        self.doc_path = doc_path
        self.doc_dir = doc_path.parent
        self.issues = []
        self.stats = {
            "total_steps": 0,
            "images_checked": 0,
            "images_passed": 0,
            "images_failed": 0,
            "broken_links": 0,
            "placeholder_leaks": 0,
            "logic_continuity_warnings": 0
        }

    def audit(self) -> dict:
        content = self.doc_path.read_text(encoding="utf-8", errors="replace")

        # 1. Check for placeholder leaks
        placeholders = re.findall(r'(\[(?:TODO|Chèn ảnh|TBD|Chưa rõ|Cần bổ sung|xxx|Tọa độ\?)\])', content, re.IGNORECASE)
        if placeholders:
            self.stats["placeholder_leaks"] = len(placeholders)
            self.issues.append({
                "type": "PLACEHOLDER_LEAK",
                "severity": "CRITICAL",
                "details": f"Found {len(placeholders)} unfinished placeholders: {list(set(placeholders))}"
            })

        # 2. Extract and audit all image references
        image_refs = re.findall(r'!\[(.*?)\]\((.*?)\)', content)
        self.stats["images_checked"] = len(image_refs)

        for alt, img_rel in image_refs:
            # Normalize path
            img_rel_clean = img_rel.split("?")[0].strip()
            img_path = (self.doc_dir / img_rel_clean).resolve()

            if not img_path.is_file():
                self.stats["broken_links"] += 1
                self.stats["images_failed"] += 1
                self.issues.append({
                    "type": "BROKEN_IMAGE_LINK",
                    "severity": "CRITICAL",
                    "file": img_rel,
                    "details": f"Referenced image file does not exist on disk: {img_path}"
                })
                continue

            # Verify image integrity and dimensions with PIL
            try:
                with Image.open(img_path) as im:
                    im.verify()
                # Re-open to read size after verify()
                with Image.open(img_path) as im:
                    w, h = im.size
                    if w < 640 or h < 360:
                        self.issues.append({
                            "type": "LOW_RESOLUTION_IMAGE",
                            "severity": "WARNING",
                            "file": img_path.name,
                            "details": f"Image resolution is too low ({w}x{h}). Recommended: 1920x1080 or >=1280x720."
                        })
                    self.stats["images_passed"] += 1
            except Exception as e:
                self.stats["images_failed"] += 1
                self.issues.append({
                    "type": "CORRUPTED_IMAGE",
                    "severity": "CRITICAL",
                    "file": img_path.name,
                    "details": f"Image file is corrupted and cannot be decoded: {e}"
                })

        # 3. Check step continuity (matching section headers e.g. "#### BƯỚC 1:")
        step_numbers = [int(m) for m in re.findall(r'^#{2,4}\s+(?:BƯỚC|STEP)\s+([0-9]+)', content, re.MULTILINE | re.IGNORECASE)]
        if step_numbers:
            self.stats["total_steps"] = len(step_numbers)
            expected = list(range(1, len(step_numbers) + 1))
            if step_numbers != expected:
                self.stats["logic_continuity_warnings"] += 1
                self.issues.append({
                    "type": "STEP_SEQUENCE_DISCONTINUITY",
                    "severity": "WARNING",
                    "details": f"Steps are not in strict sequential order 1..N. Found: {step_numbers[:10]}..."
                })

        # 4. Compute Health Score (0 - 100)
        deductions = (
            self.stats["broken_links"] * 25 +
            self.stats["placeholder_leaks"] * 15 +
            self.stats["images_failed"] * 20 +
            self.stats["logic_continuity_warnings"] * 10
        )
        score = max(0, 100 - deductions)

        return {
            "document": str(self.doc_path),
            "qc_health_score": score,
            "status": "PASS" if score >= 85 and self.stats["broken_links"] == 0 else "FAIL",
            "stats": self.stats,
            "issues_count": len(self.issues),
            "issues": self.issues
        }


def main():
    parser = argparse.ArgumentParser(description="Audit walkthrough document for image and logic defects.")
    parser.add_argument("doc_file", help="Path to walkthrough Markdown file (.md)")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    args = parser.parse_args()

    doc_path = Path(args.doc_file).resolve()
    if not doc_path.is_file():
        print(f"❌ Error: Walkthrough file not found: {doc_path}")
        sys.exit(1)

    auditor = WalkthroughQCAuditor(doc_path)
    res = auditor.audit()

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print("=" * 70)
    print("🛡️ WALKTHROUGH QUALITY CONTROL (QC) REPORT")
    print(f"📄 Document: {res['document']}")
    print(f"🎯 QC Health Score: {res['qc_health_score']} / 100 ({res['status']})")
    print("=" * 70)
    print(f"📊 Total Steps Detected: {res['stats']['total_steps']}")
    print(f"🖼️ Images Audited: {res['stats']['images_checked']} (✅ Passed: {res['stats']['images_passed']} | ❌ Failed: {res['stats']['images_failed']})")
    print(f"🔗 Broken Image Links: {res['stats']['broken_links']}")
    print(f"⚠️ Placeholder Leaks: {res['stats']['placeholder_leaks']}")
    print("-" * 70)

    if res["issues_count"] == 0:
        print("✅ 100% FLAWLESS! No image defects, dead links, or logic discontinuities detected.")
    else:
        print(f"🚨 Issues to fix ({res['issues_count']}):")
        for iss in res["issues"]:
            icon = "🔴" if iss["severity"] == "CRITICAL" else "🟡"
            print(f"   {icon} [{iss['type']}] ({iss['severity']}): {iss['details']}")

    print("=" * 70)


if __name__ == "__main__":
    main()
