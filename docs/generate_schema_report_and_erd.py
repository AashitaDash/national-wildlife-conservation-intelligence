# -*- coding: utf-8 -*-
"""Generate schema report and ER diagram (crow's‑foot) for NWCIP.

The script:
1. Loads SQLAlchemy models from ``backend/app/models``.
2. Reflects the actual SQLite database (fallback URL from settings).
3. Produces a Markdown report with tables, columns, PK/FK information and notes any
   mismatches between the model definitions and the reflected DB schema.
4. Draws a simple crow's‑foot ER diagram using Pillow (pure‑Python, no external
   Graphviz binary) and saves it as a high‑resolution JPG.
5. Writes the report to ``docs/schema_report.md`` and the diagram to
   ``docs/erd.jpg``.

The script is safe – it only reads metadata, never mutates data.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Tuple

# ------------------------------------------------------------
# 1. Prepare environment – add project root to PYTHONPATH
# ------------------------------------------------------------
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# ------------------------------------------------------------
# 2. Load SQLAlchemy settings to get DB URL
# ------------------------------------------------------------
from backend.app.config import settings

# Use SQLite fallback (project runs on SQLite in this local env)
sqlite_url = settings.FALLBACK_SQLITE_URL

# ------------------------------------------------------------
# 3. Reflect actual DB schema using SQLAlchemy
# ------------------------------------------------------------
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.engine import Engine

engine: Engine = create_engine(sqlite_url, future=True)
metadata = MetaData()
metadata.reflect(bind=engine)
inspector = inspect(engine)

# ------------------------------------------------------------
# 4. Helper to extract column info from reflected tables
# ------------------------------------------------------------
def get_table_info(table: Table) -> Dict:
    cols = []
    for col in table.columns:
        cols.append({
            "name": col.name,
            "type": str(col.type),
            "nullable": col.nullable,
            "primary_key": col.primary_key,
            "default": str(col.default) if col.default is not None else None,
        })
    fks = []
    for fk in table.foreign_keys:
        fks.append({
            "column": fk.parent.name,
            "target_table": fk.column.table.name,
            "target_column": fk.column.name,
        })
    return {"columns": cols, "foreign_keys": fks}

# ------------------------------------------------------------
# 5. Gather reflected schema dictionary
# ------------------------------------------------------------
reflected_schema: Dict[str, Dict] = {}
for tbl_name, tbl_obj in metadata.tables.items():
    reflected_schema[tbl_name] = get_table_info(tbl_obj)

# ------------------------------------------------------------
# 6. Load model definitions and extract their column specs
# ------------------------------------------------------------
model_modules = {}
models_path = project_root / "backend" / "app" / "models"
for py_file in models_path.glob("*.py"):
    if py_file.name.startswith("__"):
        continue
    module_name = f"backend.app.models.{py_file.stem}"
    try:
        model_modules[py_file.stem] = importlib.import_module(module_name)
    except Exception as e:
        print(f"Failed to import {module_name}: {e}")

# Mapping of table name -> list of column definitions from model classes
model_schema: Dict[str, List[Tuple[str, str, bool, bool]]] = {}
for name, mod in model_modules.items():
    for attr in dir(mod):
        cls = getattr(mod, attr)
        if hasattr(cls, "__tablename__"):
            tbl_name = getattr(cls, "__tablename__")
            cols = []
            for col in cls.__table__.columns:
                cols.append((col.name, str(col.type), col.primary_key, col.nullable))
            model_schema[tbl_name] = cols

# ------------------------------------------------------------
# 7. Compare model schema vs reflected schema
# ------------------------------------------------------------
differences: List[str] = []
for tbl, model_cols in model_schema.items():
    if tbl not in reflected_schema:
        differences.append(f"Table '{tbl}' defined in models but missing in DB.")
        continue
    reflected_cols = {c["name"]: c for c in reflected_schema[tbl]["columns"]}
    for col_name, col_type, pk, nullable in model_cols:
        if col_name not in reflected_cols:
            differences.append(f"Column '{col_name}' in table '{tbl}' defined in model but missing in DB.")
            continue
        refl = reflected_cols[col_name]
        # compare type loosely – ignore length specifics
        if col_type.split("(")[0] != refl["type"].split("(")[0]:
            differences.append(
                f"Column '{col_name}' in table '{tbl}' type mismatch: model={col_type}, db={refl['type']}"
            )
        if pk != refl["primary_key"]:
            differences.append(
                f"Column '{col_name}' in table '{tbl}' PK flag mismatch: model={pk}, db={refl['primary_key']}"
            )
        if nullable != refl["nullable"]:
            differences.append(
                f"Column '{col_name}' in table '{tbl}' nullable mismatch: model={nullable}, db={refl['nullable']}"
            )
# tables present in DB but not in models
for tbl in reflected_schema:
    if tbl not in model_schema:
        differences.append(f"Table '{tbl}' present in DB but not defined in models.")

# ------------------------------------------------------------
# 8. Produce Markdown report
# ------------------------------------------------------------
report_lines = ["# NWCIP Database Schema Report", "", "## Reflected Database Schema", ""]
for tbl, info in reflected_schema.items():
    report_lines.append(f"### Table `{tbl}`")
    report_lines.append("| Column | Type | PK | Nullable | Default |")
    report_lines.append("|--------|------|----|----------|---------|")
    for col in info["columns"]:
        report_lines.append(
            f"| {col['name']} | {col['type']} | {'✔' if col['primary_key'] else ''} | {'✔' if col['nullable'] else ''} | {col['default'] or ''} |"
        )
    if info["foreign_keys"]:
        report_lines.append("\n**Foreign Keys**")
        report_lines.append("| Column → Target Table.Column |")
        report_lines.append("|------------------------------|")
        for fk in info["foreign_keys"]:
            report_lines.append(
                f"| {fk['column']} → {fk['target_table']}.{fk['target_column']} |"
            )
    report_lines.append("\n")

report_lines.append("## Model‑Defined Schema (SQLAlchemy)\n")
for tbl, cols in model_schema.items():
    report_lines.append(f"### Table `{tbl}` (from model)")
    report_lines.append("| Column | Type | PK | Nullable |")
    report_lines.append("|--------|------|----|----------|")
    for name, typ, pk, nullable in cols:
        report_lines.append(
            f"| {name} | {typ} | {'✔' if pk else ''} | {'✔' if nullable else ''} |"
        )
    report_lines.append("\n")

report_lines.append("## Differences Detected\n")
if differences:
    for diff in differences:
        report_lines.append(f"- {diff}")
else:
    report_lines.append("*No differences found – model definitions are in sync with the SQLite database.*")

report_content = "\n".join(report_lines)

# Write the markdown report
report_path = project_root / "docs" / "schema_report.md"
report_path.write_text(report_content, encoding="utf-8")
print(f"Report written to {report_path}")

# ------------------------------------------------------------
# 9. Generate a simple crow‑foot ER diagram using Pillow
# ------------------------------------------------------------
from PIL import Image, ImageDraw, ImageFont

# Basic styling constants
BOX_PADDING = 10
LINE_SPACING = 4
FONT_SIZE = 14
TITLE_FONT_SIZE = 16
FONT = ImageFont.load_default()

# Determine layout – simple grid based on number of tables
tables = list(reflected_schema.keys())
cols = 3  # fixed number of columns
rows = (len(tables) + cols - 1) // cols
box_width = 300
box_height = 150
img_width = cols * (box_width + 40) + 40
img_height = rows * (box_height + 60) + 60

image = Image.new("RGB", (img_width, img_height), "white")
draw = ImageDraw.Draw(image)

# Helper to draw a table box

def draw_table(x, y, name, info):
    # Box background
    draw.rectangle([x, y, x + box_width, y + box_height], outline="#2b6d32", width=2, fill="#f2fff0")
    # Title
    title = name
    draw.text((x + BOX_PADDING, y + BOX_PADDING), title, fill="#11682f", font=FONT)
    # Columns list
    cur_y = y + BOX_PADDING + TITLE_FONT_SIZE + LINE_SPACING
    for col in info["columns"]:
        col_text = f"{col['name']} : {col['type']}"
        if col["primary_key"]:
            col_text += " PK"
        if not col["nullable"]:
            col_text += " NOT NULL"
        draw.text((x + BOX_PADDING, cur_y), col_text, fill="#000000", font=FONT)
        cur_y += FONT_SIZE + LINE_SPACING

# Draw all tables
positions = {}
for idx, tbl in enumerate(tables):
    col_idx = idx % cols
    row_idx = idx // cols
    x = 40 + col_idx * (box_width + 40)
    y = 40 + row_idx * (box_height + 60)
    draw_table(x, y, tbl, reflected_schema[tbl])
    positions[tbl] = (x, y)

# Draw foreign‑key relationships (crow's‑foot style: simple arrow)
for tbl, info in reflected_schema.items():
    src_x, src_y = positions[tbl]
    src_center = (src_x + box_width // 2, src_y + box_height)
    for fk in info["foreign_keys"]:
        target = fk["target_table"]
        if target not in positions:
            continue
        tgt_x, tgt_y = positions[target]
        tgt_center = (tgt_x + box_width // 2, tgt_y)
        # line
        draw.line([src_center, tgt_center], fill="#11682f", width=2)
        # simple crow's foot (three short lines)
        arrow_x, arrow_y = tgt_center
        offset = 6
        draw.line([arrow_x, arrow_y, arrow_x - offset, arrow_y - offset], fill="#11682f", width=2)
        draw.line([arrow_x, arrow_y, arrow_x + offset, arrow_y - offset], fill="#11682f", width=2)
        draw.line([arrow_x, arrow_y, arrow_x, arrow_y - offset*2], fill="#11682f", width=2)

# Save as high‑resolution JPG
erd_path = project_root / "docs" / "erd.jpg"
image.save(str(erd_path), "JPEG", quality=95)
print(f"ER diagram saved to {erd_path}")

