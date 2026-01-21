from collections import defaultdict
import os
import csv
from xml.sax.saxutils import escape

# ===============================
# USER CONTROLS
# ===============================

CSV_FILE = "Floor.csv"  # Your CSV file
SVG_FILE = "area_schedule.svg"

PAGE_WIDTH = 1100
PAGE_HEIGHT = 800  # Adjusted for single file

START_X_NAME = 100
START_X_AREA = 1000
START_Y = 180

ROW_GAP = 42

FONT_FAMILY_REGULAR = "Roboto"
FONT_FAMILY_LIGHT = "Roboto Light"

FONT_SIZE_MAIN_TITLE = 36  # For grand total
FONT_SIZE_GROUP = 24
FONT_SIZE_ITEM = 20

COLOR_MAIN_TITLE = "#000000"
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

svg_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{PAGE_WIDTH}" height="{PAGE_HEIGHT}"
     viewBox="0 0 {PAGE_WIDTH} {PAGE_HEIGHT}">

<style>
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400&amp;display=swap');
  .main-title {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_MAIN_TITLE}px;
    font-weight: bold;
    fill: {COLOR_MAIN_TITLE};
  }}
  .group {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_GROUP}px;
    font-weight: bold;
    fill: {COLOR_GROUP};
  }}
  .item {{
    font-family: "{FONT_FAMILY_LIGHT}", sans-serif;
    font-size: {FONT_SIZE_ITEM}px;
    fill: {COLOR_ITEM};
  }}
  .area {{
    font-family: "{FONT_FAMILY_LIGHT}", sans-serif;
    font-size: {FONT_SIZE_ITEM}px;
    fill: {COLOR_AREA};
    text-anchor: end;
  }}
  .group-area {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_GROUP}px;
    font-weight: bold;
    fill: {COLOR_GROUP};
    text-anchor: end;
  }}
</style>
'''

svg_footer = "</svg>"

# ===============================
# PROCESS CSV FILE
# ===============================

def process_csv_file(csv_file_path):
    """Process the CSV file and return organized data."""
    groups = defaultdict(list)
    total_area = 0
    
    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            name = row.get("IFC Class", "").strip()
            area_raw = row.get("Area", "").strip()
            
            if not name or not area_raw:
                continue
            
            try:
                area_value = float(area_raw)
                total_area += area_value
            except ValueError:
                continue
            
            # Extract first word as group key
            # For example: "First Floor" -> "First", "Ground Floor Verandah" -> "Ground"
            group_key = name.split()[0] if ' ' in name else name
            
            groups[group_key].append({
                "name": name,
                "area": area_value
            })
    
    # Calculate group totals for sorting
    group_totals = {}
    for k, items in groups.items():
        total_group_area = sum(item["area"] for item in items)
        group_totals[k] = total_group_area
    
    # Sort groups by total area descending
    sorted_groups = sorted(
        groups.items(),
        key=lambda g: group_totals[g[0]],
        reverse=True
    )
    
    return {
        "sorted_groups": sorted_groups,
        "total_area": total_area,
        "group_totals": group_totals
    }

# ===============================
# PROCESS THE CSV FILE
# ===============================

print(f"Processing: {CSV_FILE}")

if not os.path.exists(CSV_FILE):
    print(f"Error: CSV file '{CSV_FILE}' not found!")
    exit()

file_data = process_csv_file(CSV_FILE)
sorted_groups = file_data["sorted_groups"]
total_area = file_data["total_area"]
group_totals = file_data["group_totals"]

# ===============================
# BUILD SVG CONTENT
# ===============================

elements = []
y = START_Y

# Main title with TOTAL AREA
total_m2 = round(total_area, ROUND_AREA)
total_ft2 = round(total_area * SQM_TO_SQFT, ROUND_AREA)
total_text = f"{total_m2}{AREA_UNIT_M2} / {total_ft2}{AREA_UNIT_FT2}"

elements.append(
    f'<text x="{PAGE_WIDTH/2}" y="80" class="main-title" text-anchor="middle">AREA SCHEDULE</text>'
)
elements.append(
    f'<text x="{PAGE_WIDTH/2}" y="130" class="main-title" text-anchor="middle">{total_text}</text>'
)

# Process groups
for group_name, items in sorted_groups:
    # Single-space entry (no sub-items)
    if len(items) == 1:
        item = items[0]
        area_m2 = round(item['area'], ROUND_AREA)
        area_ft2 = round(item['area'] * SQM_TO_SQFT, ROUND_AREA)
        area_text = f"{area_m2}{AREA_UNIT_M2} / {area_ft2}{AREA_UNIT_FT2}"
        
        # Name on the left
        elements.append(
            f'<text x="{START_X_NAME}" y="{y}" class="group">{escape(item["name"])}</text>'
        )
        # Area on the right (right-aligned)
        elements.append(
            f'<text x="{START_X_AREA}" y="{y}" class="group-area">{area_text}</text>'
        )
        y += ROW_GAP
        continue  # skip the normal group loop
    
    # Multi-space group heading with total area
    group_total = round(sum(item["area"] for item in items), ROUND_AREA)
    total_ft2 = round(group_total * SQM_TO_SQFT, ROUND_AREA)
    total_text = f"{group_total}{AREA_UNIT_M2} / {total_ft2}{AREA_UNIT_FT2}"
    
    # Group name on the left
    elements.append(
        f'<text x="{START_X_NAME}" y="{y}" class="group">{escape(group_name)}</text>'
    )
    # Total area on the right (right-aligned)
    elements.append(
        f'<text x="{START_X_AREA}" y="{y}" class="group-area">(Total: {total_text})</text>'
    )
    y += ROW_GAP
    
    # Sort items inside group by area descending
    items.sort(key=lambda x: x["area"], reverse=True)
    
    for item in items:
        area_m2 = round(item['area'], ROUND_AREA)
        area_ft2 = round(item['area'] * SQM_TO_SQFT, ROUND_AREA)
        area_text = f"{area_m2}{AREA_UNIT_M2} / {area_ft2}{AREA_UNIT_FT2}"
        
        # Item name on the left (indented)
        elements.append(
            f'<text x="{START_X_NAME + 20}" y="{y}" class="item">{escape(item["name"])}</text>'
        )
        # Item area on the right (right-aligned)
        elements.append(
            f'<text x="{START_X_AREA}" y="{y}" class="area">{area_text}</text>'
        )
        
        y += ROW_GAP
    
    # Space between groups
    y += 12

# Adjust page height based on content
PAGE_HEIGHT = max(y + 100, PAGE_HEIGHT)
svg_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{PAGE_WIDTH}" height="{PAGE_HEIGHT}"
     viewBox="0 0 {PAGE_WIDTH} {PAGE_HEIGHT}">

<style>
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400&amp;display=swap');
  .main-title {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_MAIN_TITLE}px;
    font-weight: bold;
    fill: {COLOR_MAIN_TITLE};
  }}
  .group {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_GROUP}px;
    font-weight: bold;
    fill: {COLOR_GROUP};
  }}
  .item {{
    font-family: "{FONT_FAMILY_LIGHT}", sans-serif;
    font-size: {FONT_SIZE_ITEM}px;
    fill: {COLOR_ITEM};
  }}
  .area {{
    font-family: "{FONT_FAMILY_LIGHT}", sans-serif;
    font-size: {FONT_SIZE_ITEM}px;
    fill: {COLOR_AREA};
    text-anchor: end;
  }}
  .group-area {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_GROUP}px;
    font-weight: bold;
    fill: {COLOR_GROUP};
    text-anchor: end;
  }}
</style>
'''

# ===============================
# WRITE SVG FILE
# ===============================

with open(SVG_FILE, "w", encoding="utf-8") as f:
    f.write(svg_header)
    f.write("\n".join(elements))
    f.write(svg_footer)

print(f"\nSVG generated → {SVG_FILE}")
print(f"Total Area: {round(total_area, ROUND_AREA)} m² / {round(total_area * SQM_TO_SQFT, ROUND_AREA)} sq.ft")

# Display group information
print("\nGroup Summary:")
for group_name, items in sorted_groups:
    group_total = sum(item["area"] for item in items)
    group_total_m2 = round(group_total, ROUND_AREA)
    group_total_ft2 = round(group_total * SQM_TO_SQFT, ROUND_AREA)
    print(f"  {group_name}: {group_total_m2} m² / {group_total_ft2} sq.ft ({len(items)} items)")

print(f"\nFile saved as: {SVG_FILE}")