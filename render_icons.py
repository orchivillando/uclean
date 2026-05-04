#!/usr/bin/env python3
"""Render uclean.svg to PNG in all standard hicolor icon sizes."""
import cairosvg
import os

SIZES = [16, 22, 24, 32, 48, 64, 128, 256]
SVG_PATH = os.path.join(os.path.dirname(__file__), "uclean.svg")
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")

with open(SVG_PATH, "rb") as f:
    svg_data = f.read()

for size in SIZES:
    out_dir = os.path.join(ICON_DIR, f"{size}x{size}", "apps")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "uclean.png")

    cairosvg.svg2png(
        bytestring=svg_data,
        write_to=out_path,
        output_width=size,
        output_height=size,
    )
    print(f"✅ {size}x{size} → {out_path}")

# Also copy 256px as the main icon for the .deb root
cairosvg.svg2png(
    bytestring=svg_data,
    write_to=os.path.join(os.path.dirname(__file__), "uclean.png"),
    output_width=256,
    output_height=256,
)

print("\nDone! All icon sizes rendered.")
