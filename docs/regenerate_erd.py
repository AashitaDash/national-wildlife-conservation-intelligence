# -*- coding: utf-8 -*-
"""Regenerate ER diagram with improved layout.

This version computes a grid based on the number of tables to avoid overlap
and uses a slightly larger canvas. It keeps the same visual style (white
background, dark‑green accents) and outputs a high‑resolution JPG.
"""

import os, sys, math, importlib
from pathlib import Path
from sqlalchemy import create_engine, inspect, MetaData

# -------------------------------------------------------------------
# Setup paths and import settings
# -------------------------------------------------------------------
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from backend.app.config import settings

engine = create_engine(settings.FALLBACK_SQLITE_URL, future=True)
metadata = MetaData()
metadata.reflect(bind=engine)
inspector = inspect(engine)

# -------------------------------------------------------------------
# Helper to collect table info
# -------------------------------------------------------------------
def collect_info(table):
    cols = []
    for col in table.columns:
        cols.append({
            "name": col.name,
            "type": str(col.type),
            "pk": col.primary_key,
            "nullable": col.nullable,
        })
    fks = []
    for fk in table.foreign_keys:
        fks.append({
            "col": fk.parent.name,
            "reftable": fk.column.table.name,
            "refcol": fk.column.name,
        })
    return {"columns": cols, "fks": fks}

tables_info = {name: collect_info(t) for name, t in metadata.tables.items()}

# -------------------------------------------------------------------
# Layout calculation – try to keep a roughly square grid
# -------------------------------------------------------------------
# Layout parameters
box_w, box_h = 300, 150
h_gap, v_gap = 80, 80

num_tables = len(tables_info)
# Initial column count aiming for a wider layout
cols = max(2, min(6, int(math.sqrt(num_tables) * 1.5)))
rows = (num_tables + cols - 1) // cols
# Adjust to enforce landscape (width >= height)
canvas_w = cols * (box_w + h_gap) + h_gap
canvas_h = rows * (box_h + v_gap) + v_gap
if canvas_w < canvas_h and cols < 6:
    cols = min(6, cols + 1)
    rows = (num_tables + cols - 1) // cols
    canvas_w = cols * (box_w + h_gap) + h_gap
    canvas_h = rows * (box_h + v_gap) + v_gap

from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB", (canvas_w, canvas_h), "white")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()

# -------------------------------------------------------------------
# Draw table boxes
# -------------------------------------------------------------------
positions = {}
for idx, (tbl_name, info) in enumerate(tables_info.items()):
    col_idx = idx % cols
    row_idx = idx // cols
    x = h_gap + col_idx * (box_w + h_gap)
    y = v_gap + row_idx * (box_h + v_gap)
    # box
    draw.rectangle([x, y, x + box_w, y + box_h], outline="#2b6d32", width=2, fill="#f2fff0")
    # title
    draw.text((x + 8, y + 8), tbl_name, fill="#11682f", font=font)
    # columns list (show PK flag)
    cur_y = y + 30
    for col in info["columns"]:
        txt = f"{col['name']} : {col['type']}"
        if col['pk']:
            txt += " PK"
        draw.text((x + 8, cur_y), txt, fill="#000000", font=font)
        cur_y += 12
    positions[tbl_name] = (x, y)

# -------------------------------------------------------------------
# Draw relationships (simple crow's foot)
# -------------------------------------------------------------------
for src, info in tables_info.items():
    src_x, src_y = positions[src]
    src_center = (src_x + box_w // 2, src_y + box_h)
    for fk in info["fks"]:
        tgt = fk["reftable"]
        if tgt not in positions:
            continue
        tgt_x, tgt_y = positions[tgt]
        tgt_center = (tgt_x + box_w // 2, tgt_y)
        draw.line([src_center, tgt_center], fill="#11682f", width=2)
        # crow's foot near target
        ax, ay = tgt_center
        off = 6
        draw.line([ax, ay, ax - off, ay - off], fill="#11682f", width=2)
        draw.line([ax, ay, ax + off, ay - off], fill="#11682f", width=2)
        draw.line([ax, ay, ax, ay - off*2], fill="#11682f", width=2)

# Save
erd_path = project_root / "docs" / "erd.jpg"
img.save(str(erd_path), "JPEG", quality=95)
print(f"ER diagram regenerated at {erd_path}")


