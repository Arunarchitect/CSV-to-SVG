from collections import defaultdict
import os
import csv
from xml.sax.saxutils import escape
import glob

# ===============================
# USER CONTROLS
# ===============================

CSV_FILES_PATTERN = "*.csv"  # Pattern to match CSV files
SVG_FILE = "area_schedule.svg"

PAGE_WIDTH = 1100  # Increased width for better layout
PAGE_HEIGHT = 3000  # Increased height for multiple files

START_X_NAME = 100
START_X_AREA = 1000  # Increased for better alignment
START_Y = 180  # Increased to accommodate file totals

ROW_GAP = 42

FONT_FAMILY_REGULAR = "Roboto"
FONT_FAMILY_LIGHT = "Roboto Light"

FONT_SIZE_MAIN_TITLE = 36  # For grand total
FONT_SIZE_FILE_TITLE = 30  # For individual file titles
FONT_SIZE_GROUP = 24
FONT_SIZE_ITEM = 20

COLOR_MAIN_TITLE = "#000000"
COLOR_FILE_TITLE = "#333333"
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
  .file-title {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_FILE_TITLE}px;
    font-weight: bold;
    fill: {COLOR_FILE_TITLE};
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
  .file-total {{
    font-family: "{FONT_FAMILY_REGULAR}", sans-serif;
    font-size: {FONT_SIZE_FILE_TITLE}px;
    font-weight: bold;
    fill: {COLOR_FILE_TITLE};
    text-anchor: end;
  }}
</style>
'''

svg_footer = "</svg>"

# ===============================
# FUNCTIONS TO PROCESS CSV FILES
# ===============================

def process_csv_file(csv_file_path):
    """Process a single CSV file and return organized data and totals."""
    groups = defaultdict(list)
    file_total_area = 0
    
    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            name = row.get("IFC Class", "").strip()
            area_raw = row.get("Area", "").strip()
            
            if not name or not area_raw:
                continue
            
            try:
                area_value = float(area_raw)
                file_total_area += area_value
            except ValueError:
                continue
            
            # Group key = first word
            group_key = name.split()[0]
            
            groups[group_key].append({
                "name": name,
                "area": area_value
            })
    
    # Calculate group totals for sorting
    group_totals = {}
    for k, items in groups.items():
        total_area = sum(item["area"] for item in items)
        group_totals[k] = total_area
    
    # Sort groups by total area descending
    sorted_groups = sorted(
        groups.items(),
        key=lambda g: group_totals[g[0]],
        reverse=True
    )
    
    return {
        "filename": os.path.basename(csv_file_path),
        "basename": os.path.splitext(os.path.basename(csv_file_path))[0],
        "sorted_groups": sorted_groups,
        "file_total_area": file_total_area,
        "group_totals": group_totals
    }

# ===============================
# PROCESS ALL CSV FILES
# ===============================

# Get all CSV files and sort alphabetically
csv_files = sorted(glob.glob(CSV_FILES_PATTERN))
print(f"Found {len(csv_files)} CSV files: {csv_files}")

if not csv_files:
    print("No CSV files found!")
    exit()

# Process all CSV files
file_data_list = []
grand_total_area = 0

for csv_file in csv_files:
    print(f"Processing: {csv_file}")
    file_data = process_csv_file(csv_file)
    file_data_list.append(file_data)
    grand_total_area += file_data["file_total_area"]

# ===============================
# BUILD SVG CONTENT
# ===============================

elements = []

# Main title with GRAND TOTAL
grand_total_m2 = round(grand_total_area, ROUND_AREA)
grand_total_ft2 = round(grand_total_area * SQM_TO_SQFT, ROUND_AREA)
grand_total_text = f"{grand_total_m2}{AREA_UNIT_M2} / {grand_total_ft2}{AREA_UNIT_FT2}"

elements.append(
    f'<text x="{PAGE_WIDTH/2}" y="80" class="main-title" text-anchor="middle">TOTAL AREA</text>'
)
elements.append(
    f'<text x="{PAGE_WIDTH/2}" y="130" class="main-title" text-anchor="middle">{grand_total_text}</text>'
)

y = START_Y

# Process each file
for file_data in file_data_list:
    filename = file_data["filename"]
    basename = file_data["basename"]
    sorted_groups = file_data["sorted_groups"]
    file_total_area = file_data["file_total_area"]
    
    # File title with its total area
    file_total_m2 = round(file_total_area, ROUND_AREA)
    file_total_ft2 = round(file_total_area * SQM_TO_SQFT, ROUND_AREA)
    file_total_text = f"{file_total_m2}{AREA_UNIT_M2} / {file_total_ft2}{AREA_UNIT_FT2}"
    
    # File name on the left
    elements.append(
        f'<text x="{START_X_NAME}" y="{y}" class="file-title">{escape(basename)}</text>'
    )
    # File total on the right (right-aligned)
    elements.append(
        f'<text x="{START_X_AREA}" y="{y}" class="file-total">{file_total_text}</text>'
    )
    y += ROW_GAP + 10  # Extra space after file title
    
    # Process groups within this file
    for group_name, items in sorted_groups:
        # Single-space entry (main space without sub-items)
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
    
    # Add more space between files
    y += 40

# ===============================
# WRITE SVG FILE
# ===============================

with open(SVG_FILE, "w", encoding="utf-8") as f:
    f.write(svg_header)
    f.write("\n".join(elements))
    f.write(svg_footer)

print(f"\nSVG generated → {SVG_FILE}")
print(f"Processed {len(file_data_list)} files")
print(f"Grand Total Area: {round(grand_total_area, ROUND_AREA)} m² / {round(grand_total_area * SQM_TO_SQFT, ROUND_AREA)} sq.ft")