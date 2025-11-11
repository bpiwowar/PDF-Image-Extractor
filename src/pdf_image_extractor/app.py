#!/usr/bin/env python3
"""
PDF Image Extractor with Visual Bounding Boxes
A lightweight GUI tool to visualize and extract images from PDF files.
Uses PyMuPDF (fitz) - no external dependencies required!
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw
import io
import os


class PDFImageExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Image Extractor")
        self.root.geometry("1200x800")
        
        self.pdf_path = None
        self.pdf_doc = None
        self.current_page = 0
        self.images_data = []  # Store image data with coordinates
        self.canvas_image = None
        self.scale_factor = 1.0
        self.selected_box = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="Previous", command=self.prev_page).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Next", command=self.next_page).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text="Page:").pack(side=tk.LEFT, padx=(10, 2))
        self.page_entry = ttk.Entry(toolbar, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=2)
        self.page_entry.bind('<Return>', lambda e: self.goto_page())
        ttk.Button(toolbar, text="Go", command=self.goto_page).pack(side=tk.LEFT, padx=2)
        
        self.page_label = ttk.Label(toolbar, text="/ 0")
        self.page_label.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="Extract All Images", command=self.extract_all_images).pack(side=tk.LEFT, padx=2)
        
        self.status_label = ttk.Label(toolbar, text="No PDF loaded")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content area with sidebar for outline
        content_frame = ttk.Frame(self.root)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Outline sidebar (left)
        outline_frame = ttk.LabelFrame(content_frame, text="Outline", width=200)
        outline_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        outline_frame.pack_propagate(False)
        
        self.outline_tree = ttk.Treeview(outline_frame, show='tree')
        outline_scroll = ttk.Scrollbar(outline_frame, orient=tk.VERTICAL, command=self.outline_tree.yview)
        self.outline_tree.configure(yscrollcommand=outline_scroll.set)
        self.outline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        outline_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.outline_tree.bind('<<TreeviewSelect>>', self.on_outline_select)
        
        # Canvas for PDF display (center)
        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(canvas_frame, bg='gray', 
                               xscrollcommand=h_scroll.set,
                               yscrollcommand=v_scroll.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)
        
        # Bind click event for image selection
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        
        # Info panel (right)
        info_frame = ttk.LabelFrame(content_frame, text="Images on Page", width=250)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        info_frame.pack_propagate(False)
        
        self.info_text = tk.Text(info_frame, wrap=tk.WORD, width=30)
        info_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def open_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if self.pdf_doc:
                    self.pdf_doc.close()
                
                self.pdf_path = file_path
                self.pdf_doc = fitz.open(file_path)
                self.current_page = 0
                
                self.load_outline()
                self.display_page()
                
                self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
                self.page_label.config(text=f"/ {len(self.pdf_doc)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF: {str(e)}")
    
    def load_outline(self):
        """Load PDF outline/table of contents"""
        self.outline_tree.delete(*self.outline_tree.get_children())
        
        # Get PDF outline/TOC
        toc = self.pdf_doc.get_toc()
        
        if toc:
            # Build tree from TOC
            parent_stack = [('', 0)]  # (parent_id, level)
            
            for level, title, page_num in toc:
                # Find appropriate parent
                while parent_stack and parent_stack[-1][1] >= level:
                    parent_stack.pop()
                
                parent = parent_stack[-1][0] if parent_stack else ''
                
                # Insert item
                item_id = self.outline_tree.insert(
                    parent, 'end', 
                    text=f"{title} (p.{page_num})", 
                    values=(page_num - 1,)  # Store 0-indexed page number
                )
                
                parent_stack.append((item_id, level))
        else:
            # No outline, just list pages
            for i in range(len(self.pdf_doc)):
                self.outline_tree.insert('', 'end', text=f"Page {i+1}", values=(i,))
    
    def on_outline_select(self, event):
        selection = self.outline_tree.selection()
        if selection:
            item = self.outline_tree.item(selection[0])
            values = item.get('values')
            if values:
                page_num = int(values[0])
                self.current_page = page_num
                self.display_page()
    
    def display_page(self):
        if not self.pdf_doc:
            return
        
        try:
            page = self.pdf_doc[self.current_page]
            
            # Render page to image using PyMuPDF
            # Get page at good resolution (150 DPI)
            zoom = 2.0  # Zoom factor (2.0 = 144 DPI)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert pixmap to PIL Image
            img_data = pix.tobytes("ppm")
            page_image = Image.open(io.BytesIO(img_data))
            
            # Extract images and their coordinates from the page
            self.images_data = []
            image_list = page.get_images()
            
            for idx, img_info in enumerate(image_list):
                xref = img_info[0]  # Image reference number
                
                # Get image bounding boxes on the page
                # One image can appear multiple times with different positions
                rects = page.get_image_rects(xref)
                
                for rect_idx, rect in enumerate(rects):
                    # Convert rect to coordinates
                    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                    
                    # Store image info with coordinates
                    self.images_data.append({
                        'index': len(self.images_data),
                        'xref': xref,
                        'x0': x0,
                        'y0': y0,
                        'x1': x1,
                        'y1': y1,
                        'width': x1 - x0,
                        'height': y1 - y0,
                        'name': f'image_{xref}_{rect_idx}'
                    })
            
            # Draw bounding boxes on the page image
            draw = ImageDraw.Draw(page_image)
            
            # Calculate scale factor from PDF coordinates to image coordinates
            pdf_width = page.rect.width
            pdf_height = page.rect.height
            img_width, img_height = page_image.size
            
            scale_x = img_width / pdf_width
            scale_y = img_height / pdf_height
            
            for idx, img_data in enumerate(self.images_data):
                # Convert PDF coordinates to image coordinates
                x0 = img_data['x0'] * scale_x
                y0 = img_data['y0'] * scale_y
                x1 = img_data['x1'] * scale_x
                y1 = img_data['y1'] * scale_y
                
                # Draw bounding box
                draw.rectangle([x0, y0, x1, y1], outline='red', width=3)
                
                # Draw label
                label = f"#{idx+1}"
                # Create background for label
                bbox = draw.textbbox((x0 + 5, y0 + 5), label)
                draw.rectangle(bbox, fill='red')
                draw.text((x0 + 5, y0 + 5), label, fill='white')
                
                # Store scaled coordinates for click detection
                self.images_data[idx]['scaled_x0'] = x0
                self.images_data[idx]['scaled_y0'] = y0
                self.images_data[idx]['scaled_x1'] = x1
                self.images_data[idx]['scaled_y1'] = y1
            
            # Resize for display if needed
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calculate scale to fit canvas
                scale_x = canvas_width / img_width
                scale_y = canvas_height / img_height
                self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up
                
                if self.scale_factor < 1.0:
                    new_width = int(img_width * self.scale_factor)
                    new_height = int(img_height * self.scale_factor)
                    page_image = page_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Display on canvas
            self.canvas_image = ImageTk.PhotoImage(page_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.canvas_image)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            
            # Update info panel
            self.update_info_panel()
            
            # Update page entry
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(self.current_page + 1))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display page: {str(e)}")
    
    def update_info_panel(self):
        self.info_text.delete(1.0, tk.END)
        
        if not self.images_data:
            self.info_text.insert(tk.END, "No images found on this page.")
            return
        
        self.info_text.insert(tk.END, f"Found {len(self.images_data)} image(s):\n\n")
        
        for img_data in self.images_data:
            info = (f"Image #{img_data['index']+1}\n"
                   f"  Name: {img_data['name']}\n"
                   f"  Size: {int(img_data['width'])}x{int(img_data['height'])}\n"
                   f"  Position: ({int(img_data['x0'])}, {int(img_data['y0'])})\n"
                   f"  Click box to save\n\n")
            self.info_text.insert(tk.END, info)
    
    def on_canvas_click(self, event):
        if not self.images_data:
            return
        
        # Get click coordinates on canvas
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Adjust for scale factor
        click_x = canvas_x / self.scale_factor
        click_y = canvas_y / self.scale_factor
        
        # Check which bounding box was clicked
        for img_data in self.images_data:
            x0 = img_data['scaled_x0']
            y0 = img_data['scaled_y0']
            x1 = img_data['scaled_x1']
            y1 = img_data['scaled_y1']
            
            if x0 <= click_x <= x1 and y0 <= click_y <= y1:
                self.save_image(img_data)
                break
    
    def save_image(self, img_data):
        """Extract and save the clicked image"""
        try:
            page = self.pdf_doc[self.current_page]
            xref = img_data['xref']
            
            # Extract the image from PDF
            base_image = self.pdf_doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Ask user where to save
            default_name = f"page{self.current_page+1}_image{img_data['index']+1}.png"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_name,
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                pil_image.save(file_path)
                messagebox.showinfo("Success", f"Image saved to:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")
    
    def extract_all_images(self):
        """Extract all images from current page"""
        if not self.images_data:
            messagebox.showinfo("Info", "No images found on this page.")
            return
        
        # Ask for directory
        directory = filedialog.askdirectory(title="Select directory to save images")
        
        if directory:
            try:
                page = self.pdf_doc[self.current_page]
                saved_count = 0
                
                # Keep track of saved xrefs to avoid duplicates
                saved_xrefs = set()
                
                for img_data in self.images_data:
                    xref = img_data['xref']
                    
                    # Skip if we already saved this image
                    if xref in saved_xrefs:
                        continue
                    
                    # Extract the image from PDF
                    base_image = self.pdf_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    filename = f"page{self.current_page+1}_image{img_data['index']+1}.png"
                    file_path = os.path.join(directory, filename)
                    pil_image.save(file_path)
                    saved_count += 1
                    saved_xrefs.add(xref)
                
                messagebox.showinfo("Success", f"Extracted {saved_count} unique image(s) to:\n{directory}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract images: {str(e)}")
    
    def prev_page(self):
        if self.pdf_doc and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def next_page(self):
        if self.pdf_doc and self.current_page < len(self.pdf_doc) - 1:
            self.current_page += 1
            self.display_page()
    
    def goto_page(self):
        if not self.pdf_doc:
            return
        
        try:
            page_num = int(self.page_entry.get()) - 1
            if 0 <= page_num < len(self.pdf_doc):
                self.current_page = page_num
                self.display_page()
            else:
                messagebox.showwarning("Invalid Page", f"Please enter a page number between 1 and {len(self.pdf_doc)}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid page number")
    
    def __del__(self):
        if self.pdf_doc:
            self.pdf_doc.close()


def main():
    """Entry point for the application"""
    root = tk.Tk()
    app = PDFImageExtractor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
