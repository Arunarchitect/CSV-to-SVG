import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import csv
from collections import defaultdict
from xml.sax.saxutils import escape
from pathlib import Path

# ===============================
# SVG CONFIGURATION
# ===============================

PAGE_WIDTH = 1100
PAGE_HEIGHT = 3000

START_X_NAME = 100
START_X_AREA = 1000
START_Y = 180
ROW_GAP = 42

FONT_FAMILY_REGULAR = "Roboto"
FONT_FAMILY_LIGHT = "Roboto Light"

FONT_SIZE_MAIN_TITLE = 36
FONT_SIZE_FILE_TITLE = 30
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
SQM_TO_SQFT = 10.7639

# ===============================
# CSV PROCESSING FUNCTIONS
# ===============================

def process_csv_file(csv_file_path):
    """Process a single CSV file and return organized data and totals."""
    groups = defaultdict(list)
    file_total_area = 0
    
    try:
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
            "filepath": csv_file_path,
            "basename": os.path.splitext(os.path.basename(csv_file_path))[0],
            "sorted_groups": sorted_groups,
            "file_total_area": file_total_area,
            "group_totals": group_totals
        }
    
    except Exception as e:
        print(f"Error processing {csv_file_path}: {e}")
        return None

def generate_svg(ordered_files, output_path="area_schedule.svg"):
    """Generate SVG from ordered list of CSV files."""
    if not ordered_files:
        return False, "No files selected"
    
    # Process all CSV files in order
    file_data_list = []
    grand_total_area = 0
    
    for csv_file in ordered_files:
        file_data = process_csv_file(csv_file)
        if file_data:
            file_data_list.append(file_data)
            grand_total_area += file_data["file_total_area"]
    
    if not file_data_list:
        return False, "No valid data found in CSV files"
    
    # ===============================
    # BUILD SVG CONTENT
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
    
    elements = []
    
    # Main title with GRAND TOTAL
    grand_total_m2 = round(grand_total_area, ROUND_AREA)
    grand_total_ft2 = round(grand_total_area * SQM_TO_SQFT, ROUND_AREA)
    grand_total_text = f"{grand_total_m2}{AREA_UNIT_M2} / {grand_total_ft2}{AREA_UNIT_FT2}"
    
    elements.append(
        f'<text x="{PAGE_WIDTH/2}" y="80" class="main-title" text-anchor="middle">TOTAL CARPET AREA</text>'
    )
    elements.append(
        f'<text x="{PAGE_WIDTH/2}" y="130" class="main-title" text-anchor="middle">{grand_total_text}</text>'
    )
    
    y = START_Y
    
    # Process each file
    for file_data in file_data_list:
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
    
    # Write SVG file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_header)
            f.write("\n".join(elements))
            f.write(svg_footer)
        
        return True, f"SVG generated successfully: {output_path}\nProcessed {len(file_data_list)} files\nGrand Total: {grand_total_m2} m² / {grand_total_ft2} sq.ft"
    
    except Exception as e:
        return False, f"Error writing SVG file: {e}"

# ===============================
# GUI APPLICATION
# ===============================

class CSVProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV to SVG Area Schedule Generator")
        self.root.geometry("700x500")
        
        self.csv_files = []
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title label
        title_label = ttk.Label(
            main_frame, 
            text="CSV to SVG Area Schedule Generator",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Add CSV button
        add_button = ttk.Button(
            button_frame, 
            text="Add CSV Files", 
            command=self.add_csv_files
        )
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear all button
        clear_button = ttk.Button(
            button_frame, 
            text="Clear All", 
            command=self.clear_all_files
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Listbox frame
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Listbox with scrollbar
        self.listbox = tk.Listbox(
            listbox_frame, 
            selectmode=tk.SINGLE, 
            height=10
        )
        listbox_scrollbar = ttk.Scrollbar(
            listbox_frame, 
            orient=tk.VERTICAL, 
            command=self.listbox.yview
        )
        self.listbox.configure(yscrollcommand=listbox_scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Move buttons frame
        move_frame = ttk.Frame(main_frame)
        move_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Button(move_frame, text="Move Up", command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="Move Down", command=self.move_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        
        # Output filename entry
        filename_frame = ttk.Frame(main_frame)
        filename_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(filename_frame, text="Output SVG filename:").pack(side=tk.LEFT, padx=(0, 5))
        self.filename_var = tk.StringVar(value="area_schedule.svg")
        filename_entry = ttk.Entry(filename_frame, textvariable=self.filename_var, width=30)
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Generate button
        generate_button = ttk.Button(
            main_frame, 
            text="Generate SVG", 
            command=self.generate_svg,
            style="Accent.TButton"
        )
        generate_button.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to add CSV files", foreground="blue")
        self.status_label.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        # Configure styles
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
        # Bind listbox selection
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # Set focus
        self.root.focus_force()
    
    def add_csv_files(self):
        """Add CSV files to the list."""
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(
            title="Select CSV files",
            filetypes=filetypes
        )
        
        if files:
            for file in files:
                if file not in self.csv_files:
                    self.csv_files.append(file)
                    self.listbox.insert(tk.END, os.path.basename(file))
            
            self.update_status(f"Added {len(files)} file(s). Total: {len(self.csv_files)}")
    
    def clear_all_files(self):
        """Clear all files from the list."""
        self.csv_files.clear()
        self.listbox.delete(0, tk.END)
        self.update_status("All files cleared")
    
    def remove_selected(self):
        """Remove selected file from the list."""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.listbox.delete(index)
            del self.csv_files[index]
            self.update_status(f"File removed. Total: {len(self.csv_files)}")
    
    def move_up(self):
        """Move selected item up in the list."""
        selection = self.listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            # Swap in listbox
            item_text = self.listbox.get(index)
            self.listbox.delete(index)
            self.listbox.insert(index - 1, item_text)
            self.listbox.select_set(index - 1)
            
            # Swap in internal list
            self.csv_files[index], self.csv_files[index - 1] = self.csv_files[index - 1], self.csv_files[index]
    
    def move_down(self):
        """Move selected item down in the list."""
        selection = self.listbox.curselection()
        if selection and selection[0] < len(self.csv_files) - 1:
            index = selection[0]
            # Swap in listbox
            item_text = self.listbox.get(index)
            self.listbox.delete(index)
            self.listbox.insert(index + 1, item_text)
            self.listbox.select_set(index + 1)
            
            # Swap in internal list
            self.csv_files[index], self.csv_files[index + 1] = self.csv_files[index + 1], self.csv_files[index]
    
    def generate_svg(self):
        """Generate SVG from the ordered CSV files."""
        if not self.csv_files:
            messagebox.showwarning("No Files", "Please add CSV files first.")
            return
        
        output_filename = self.filename_var.get().strip()
        if not output_filename:
            output_filename = "area_schedule.svg"
        elif not output_filename.lower().endswith('.svg'):
            output_filename += '.svg'
        
        # Update status
        self.update_status("Processing CSV files...", "blue")
        self.root.update()
        
        # Generate SVG
        success, message = generate_svg(self.csv_files, output_filename)
        
        if success:
            self.update_status(message, "green")
            messagebox.showinfo("Success", message)
        else:
            self.update_status(message, "red")
            messagebox.showerror("Error", message)
    
    def update_status(self, message, color="blue"):
        """Update the status label."""
        self.status_label.config(text=message, foreground=color)
    
    def on_select(self, event):
        """Handle listbox selection."""
        pass

# ===============================
# MAIN EXECUTION
# ===============================

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVProcessorGUI(root)
    root.mainloop()