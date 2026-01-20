import csv
from collections import defaultdict
import os
from xml.sax.saxutils import escape  # <-- to escape special XML characters

# ===============================
# USER CONTROLS
# ===============================

CSV_FILE = "FF.csv"          # Input CSV
SVG_FILE = "area_schedule.svg"  # Output SVG

PAGE_WIDTH = 900
PAGE_HEIGHT = 1400

START_X_NAME = 100
START_X_AREA = 750
START_Y = 160

ROW_GAP = 42

FONT_FAMILY_REGULAR = "Roboto"
FONT_FAMILY_LIGHT = "Roboto Light"

FONT_SIZE_GROUP = 24   # For group headings and single spaces
FONT_SIZE_ITEM = 20    # For individual items

COLOR_GROUP = "#000000"
COLOR_ITEM = "#222222"
COLOR_AREA = "#444444"

AREA_UNIT_M2 = " m²"
AREA_UNIT_FT2 = " sq.ft"
ROUND_AREA = 2

# Conversion factor
SQM_TO_SQFT = 10.7639

# ===============================
# SVG HEADER
# ===============================

svg_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{PAGE_WIDTH}" height="{PAGE_HEIGHT}"
     viewBox="0 0 {PAGE_WIDTH} {PAGE_HEIGHT}">

<style>
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400&display=swap');
  .title {{
    font-family: '{FONT_FAMILY_REGULAR}', sans-serif;
    font-size: {FONT_SIZE_GROUP + 8}px;
    font-weight: bold;
    fill: #000;
  }}
  .group {{
    font-family: '{FONT_FAMILY_REGULAR}', sans-serif;
    font-size: {FONT_SIZE_GROUP}px;
    font-weight: bold;
    fill: {COLOR_GROUP};
  }}
  .item {{
    font-family: '{FONT_FAMILY_LIGHT}', sans-serif;
    font-size: {FONT_SIZE_ITEM}px;
    fill: {COLOR_ITEM};
  }}
  .area {{
    font-family: '{FONT_FAMILY_LIGHT}', sans-serif;
    font-size: {FONT_SIZE_ITEM}px;
    fill: {COLOR_AREA};
    text-anchor: end;
  }}
</style>
"""

svg_footer = "</svg>"

# ===============================
# READ CSV AND GROUP DATA
# ===============================

groups = defaultdict(list)

with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        name = row.get("IFC Class", "").strip()
        area_raw = row.get("Area", "").strip()

        if not name or not area_raw:
            continue

        try:
            area_value = float(area_raw)
        except ValueError:
            continue

        # Group key = first word
        group_key = name.split()[0]

        groups[group_key].append({
            "name": name,
            "area": area_value
        })

# ===============================
# SORT GROUPS BY TOTAL AREA DESC
# ===============================

# Calculate group totals for sorting
group_totals = {}
for k, items in groups.items():
    total_area = sum(item["area"] for item in items)
    group_totals[k] = total_area

sorted_groups = sorted(
    groups.items(),
    key=lambda g: group_totals[g[0]],
    reverse=True
)

# ===============================
# BUILD SVG CONTENT
# ===============================

elements = []

# Title: CSV file name without extension
main_title = os.path.splitext(os.path.basename(CSV_FILE))[0]

elements.append(
    f'<text x="{PAGE_WIDTH/2}" y="90" class="title" text-anchor="middle">{escape(main_title)}</text>'
)

y = START_Y

for group_name, items in sorted_groups:

    # Single-space entry
    if len(items) == 1:
        item = items[0]
        area_m2 = round(item['area'], ROUND_AREA)
        area_ft2 = round(item['area'] * SQM_TO_SQFT, ROUND_AREA)
        area_text = f"{area_m2}{AREA_UNIT_M2} / {area_ft2}{AREA_UNIT_FT2}"

        elements.append(
            f'<text x="{START_X_NAME}" y="{y}" class="group">{escape(item["name"])}  ({area_text})</text>'
        )
        y += ROW_GAP
        continue  # skip the normal group loop

    # Multi-space group heading
    group_total = round(sum(item["area"] for item in items), ROUND_AREA)
    elements.append(
        f'<text x="{START_X_NAME}" y="{y}" class="group">{escape(group_name)}  (Total: {group_total}{AREA_UNIT_M2} / {round(group_total*SQM_TO_SQFT,2)}{AREA_UNIT_FT2})</text>'
    )
    y += ROW_GAP

    # Sort items inside group by area descending
    items.sort(key=lambda x: x["area"], reverse=True)

    for item in items:
        area_m2 = round(item['area'], ROUND_AREA)
        area_ft2 = round(item['area'] * SQM_TO_SQFT, ROUND_AREA)
        area_text = f"{area_m2}{AREA_UNIT_M2} / {area_ft2}{AREA_UNIT_FT2}"

        elements.append(
            f'<text x="{START_X_NAME + 20}" y="{y}" class="item">{escape(item["name"])}</text>'
        )
        elements.append(
            f'<text x="{START_X_AREA}" y="{y}" class="area">{area_text}</text>'
        )

        y += ROW_GAP

    # Space between groups
    y += 12

# ===============================
# WRITE SVG FILE
# ===============================

with open(SVG_FILE, "w", encoding="utf-8") as f:
    f.write(svg_header)
    f.write("\n".join(elements))
    f.write(svg_footer)

print(f"SVG generated → {SVG_FILE}")
