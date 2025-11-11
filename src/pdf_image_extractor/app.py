#!/usr/bin/env python3
"""
PDF Image Extractor with Visual Bounding Boxes
A lightweight GUI tool to visualize and extract images from PDF files.
Uses PyMuPDF (fitz) - no external dependencies required!
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
import os
import sys


class ImagePreviewPopup(tk.Toplevel):
    """Popup window to show image preview"""

    def __init__(self, parent, pil_image, title="Image Preview"):
        super().__init__(parent)
        self.title(title)
        self.overrideredirect(True)  # Remove window decorations
        self.attributes("-topmost", True)  # Always on top

        # Add border
        self.configure(bg="black", padx=2, pady=2)

        # Create frame for content
        frame = tk.Frame(self, bg="white")
        frame.pack()

        # Resize image if too large
        max_size = 400
        img_width, img_height = pil_image.size
        if img_width > max_size or img_height > max_size:
            ratio = min(max_size / img_width, max_size / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            pil_image = pil_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

        # Add title label
        title_label = tk.Label(
            frame, text=title, bg="white", font=("TkDefaultFont", 9, "bold")
        )
        title_label.pack(pady=(5, 2))

        # Show image
        self.photo = ImageTk.PhotoImage(pil_image)
        img_label = tk.Label(frame, image=self.photo, bg="white")
        img_label.pack(padx=5, pady=5)

        # Size info
        size_text = f"{img_width}×{img_height} pixels"
        size_label = tk.Label(
            frame, text=size_text, bg="white", font=("TkDefaultFont", 8)
        )
        size_label.pack(pady=(2, 5))

        # Update geometry to get actual size
        self.update_idletasks()
        popup_width = self.winfo_width()
        popup_height = self.winfo_height()

        # Get screen dimensions
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()

        # Get cursor position
        cursor_x = parent.winfo_pointerx()
        cursor_y = parent.winfo_pointery()

        # Position to the left of cursor by default
        x = cursor_x - popup_width - 15
        y = cursor_y - popup_height // 2

        # Adjust if goes off left edge - put it to the right instead
        if x < 0:
            x = cursor_x + 15

        # Adjust if goes off right edge
        if x + popup_width > screen_width:
            x = screen_width - popup_width - 10

        # Adjust if goes off top edge
        if y < 0:
            y = 10

        # Adjust if goes off bottom edge
        if y + popup_height > screen_height:
            y = screen_height - popup_height - 10

        self.geometry(f"+{x}+{y}")


class PDFImageExtractor:
    def __init__(self, root, initial_file=None):
        self.root = root
        self.root.title("PDF Image Extractor")
        self.root.geometry("1400x900")

        self.pdf_path = None
        self.pdf_doc = None
        self.current_page = 0
        self.images_data = []  # Store image data with coordinates
        self.canvas_image = None
        self.current_pix = None  # Store current page pixmap
        self.zoom_level = 1.0
        self.preview_popup = None  # Current preview popup
        self.preview_index = None  # Index of currently previewed image
        self.current_view = "outline"  # "outline" or "thumbnails"

        # Thumbnail cache
        self.thumbnail_cache = {}
        self.thumbnail_size = 150

        self.setup_ui()

        # Bind window resize event
        self.root.bind("<Configure>", self.on_window_resize)
        self.last_width = self.root.winfo_width()
        self.last_height = self.root.winfo_height()

        # Open initial file if provided
        if initial_file and os.path.exists(initial_file):
            self.root.after(100, lambda: self.open_pdf_file(initial_file))

    def setup_ui(self):
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Open PDF", command=self.open_pdf).pack(
            side=tk.LEFT, padx=2
        )

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Button(toolbar, text="◀", command=self.prev_page, width=3).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="▶", command=self.next_page, width=3).pack(
            side=tk.LEFT, padx=2
        )

        ttk.Label(toolbar, text="Page:").pack(side=tk.LEFT, padx=(10, 2))
        self.page_entry = ttk.Entry(toolbar, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=2)
        self.page_entry.bind("<Return>", lambda e: self.goto_page())
        ttk.Button(toolbar, text="Go", command=self.goto_page).pack(
            side=tk.LEFT, padx=2
        )

        self.page_label = ttk.Label(toolbar, text="/ 0")
        self.page_label.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(toolbar, text="−", command=self.zoom_out, width=3).pack(
            side=tk.LEFT, padx=2
        )
        self.zoom_label = ttk.Label(toolbar, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="+", command=self.zoom_in, width=3).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="Fit", command=self.zoom_fit, width=4).pack(
            side=tk.LEFT, padx=2
        )

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Button(toolbar, text="Extract All", command=self.extract_all_images).pack(
            side=tk.LEFT, padx=2
        )

        self.status_label = ttk.Label(toolbar, text="No PDF loaded")
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left sidebar with tabs
        left_frame = ttk.Frame(content_frame, width=220)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)

        # Tab control for outline/thumbnails
        self.left_notebook = ttk.Notebook(left_frame)
        self.left_notebook.pack(fill=tk.BOTH, expand=True)

        # Outline tab
        outline_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(outline_frame, text="Outline")

        self.outline_tree = ttk.Treeview(outline_frame, show="tree")
        outline_scroll = ttk.Scrollbar(
            outline_frame, orient=tk.VERTICAL, command=self.outline_tree.yview
        )
        self.outline_tree.configure(yscrollcommand=outline_scroll.set)
        self.outline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        outline_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.outline_tree.bind("<<TreeviewSelect>>", self.on_outline_select)

        # Thumbnails tab
        thumb_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(thumb_frame, text="Thumbnails")

        # Canvas for thumbnails with scrollbar
        thumb_canvas_frame = ttk.Frame(thumb_frame)
        thumb_canvas_frame.pack(fill=tk.BOTH, expand=True)

        thumb_scroll = ttk.Scrollbar(thumb_canvas_frame, orient=tk.VERTICAL)
        thumb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.thumb_canvas = tk.Canvas(
            thumb_canvas_frame, bg="white", yscrollcommand=thumb_scroll.set, width=200
        )
        self.thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        thumb_scroll.config(command=self.thumb_canvas.yview)

        self.thumb_canvas.bind("<Button-1>", self.on_thumbnail_click)

        # Bind mouse wheel for thumbnail scrolling
        self.thumb_canvas.bind("<MouseWheel>", self.on_thumb_mousewheel)  # Windows/Mac
        self.thumb_canvas.bind(
            "<Button-4>", self.on_thumb_mousewheel
        )  # Linux scroll up
        self.thumb_canvas.bind(
            "<Button-5>", self.on_thumb_mousewheel
        )  # Linux scroll down

        # Canvas for PDF display (center)
        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbars
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#f0f0f0",
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)

        # Bind keyboard arrow keys for page navigation
        self.root.bind("<Left>", lambda e: self.prev_page())
        self.root.bind("<Right>", lambda e: self.next_page())

        # Info panel (right) - now with interactive list
        info_frame = ttk.LabelFrame(content_frame, text="Images on Page", width=280)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        info_frame.pack_propagate(False)

        # Create listbox for images
        list_frame = ttk.Frame(info_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=info_scroll.set,
            font=("TkDefaultFont", 9),
            activestyle="none",
        )
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.config(command=self.image_listbox.yview)

        # Bind events
        self.image_listbox.bind("<Motion>", self.on_image_list_hover)
        self.image_listbox.bind("<Leave>", self.on_image_list_leave)
        self.image_listbox.bind("<Button-1>", self.on_image_list_click)

        # Instructions
        instructions = ttk.Label(
            info_frame,
            text="Hover to preview\nClick to save",
            justify=tk.CENTER,
            foreground="gray",
        )
        instructions.pack(side=tk.BOTTOM, pady=5)

    def open_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )

        if file_path:
            self.open_pdf_file(file_path)

    def open_pdf_file(self, file_path):
        """Open a PDF file from a given path"""
        try:
            if self.pdf_doc:
                self.pdf_doc.close()

            self.pdf_path = file_path
            self.pdf_doc = fitz.open(file_path)
            self.current_page = 0
            self.zoom_level = 1.0
            self.thumbnail_cache = {}

            self.load_outline()
            self.load_thumbnails()

            # Display first page
            self.display_page()

            # Apply fit-to-window zoom after a short delay
            self.root.after(100, self.zoom_fit)

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
            parent_stack = [("", 0)]  # (parent_id, level)

            for level, title, page_num in toc:
                # Find appropriate parent
                while parent_stack and parent_stack[-1][1] >= level:
                    parent_stack.pop()

                parent = parent_stack[-1][0] if parent_stack else ""

                # Insert item
                item_id = self.outline_tree.insert(
                    parent,
                    "end",
                    text=f"{title} (p.{page_num})",
                    values=(page_num - 1,),  # Store 0-indexed page number
                )

                parent_stack.append((item_id, level))
        else:
            # No outline, just list pages
            for i in range(len(self.pdf_doc)):
                self.outline_tree.insert("", "end", text=f"Page {i+1}", values=(i,))

    def load_thumbnails(self):
        """Generate thumbnails for all pages"""
        if not self.pdf_doc:
            return

        self.thumb_canvas.delete("all")
        self.thumbnail_cache = {}

        y_offset = 10
        for i in range(len(self.pdf_doc)):
            # Generate thumbnail
            page = self.pdf_doc[i]
            mat = fitz.Matrix(0.2, 0.2)  # Small scale for thumbnails
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to PIL
            img_data = pix.tobytes("ppm")
            thumb = Image.open(io.BytesIO(img_data))

            # Resize to fit width
            aspect = thumb.height / thumb.width
            new_width = self.thumbnail_size
            new_height = int(new_width * aspect)
            thumb = thumb.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Add border
            bordered = Image.new("RGB", (new_width + 4, new_height + 4), "gray")
            bordered.paste(thumb, (2, 2))

            # Store in cache
            photo = ImageTk.PhotoImage(bordered)
            self.thumbnail_cache[i] = photo

            # Draw on canvas
            self.thumb_canvas.create_image(
                10, y_offset, anchor=tk.NW, image=photo, tags=f"thumb_{i}"
            )
            self.thumb_canvas.create_text(
                new_width // 2 + 10,
                y_offset + new_height + 8,
                text=f"Page {i+1}",
                tags=f"thumb_{i}",
            )

            y_offset += new_height + 30

        # Update scroll region
        self.thumb_canvas.config(scrollregion=self.thumb_canvas.bbox("all"))

    def on_thumb_mousewheel(self, event):
        """Handle mouse wheel scrolling in thumbnail canvas"""
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.thumb_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.thumb_canvas.yview_scroll(1, "units")

    def on_thumbnail_click(self, event):
        """Handle thumbnail click"""
        # Convert to canvas coordinates (account for scrolling)
        canvas_y = self.thumb_canvas.canvasy(event.y)

        # Find which thumbnail was clicked
        item = self.thumb_canvas.find_closest(event.x, canvas_y)
        if item:
            tags = self.thumb_canvas.gettags(item[0])
            for tag in tags:
                if tag.startswith("thumb_"):
                    page_num = int(tag.split("_")[1])
                    self.current_page = page_num
                    self.display_page()
                    break

    def on_outline_select(self, event):
        selection = self.outline_tree.selection()
        if selection:
            item = self.outline_tree.item(selection[0])
            values = item.get("values")
            if values:
                page_num = int(values[0])
                self.current_page = page_num
                self.display_page()

    def display_page(self):
        if not self.pdf_doc:
            return

        try:
            page = self.pdf_doc[self.current_page]

            # Render page with current zoom level
            zoom = self.zoom_level * 2.0  # Base zoom multiplier
            mat = fitz.Matrix(zoom, zoom)
            self.current_pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert pixmap to PIL Image
            img_data = self.current_pix.tobytes("ppm")
            self.page_image = Image.open(io.BytesIO(img_data))

            # Extract images and their coordinates
            self.images_data = []
            image_list = page.get_images()

            for idx, img_info in enumerate(image_list):
                xref = img_info[0]

                # Get image bounding boxes on the page
                rects = page.get_image_rects(xref)

                for rect_idx, rect in enumerate(rects):
                    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                    width = x1 - x0
                    height = y1 - y0

                    # Skip images that are too small (likely artifacts or invisible)
                    if width < 1 or height < 1:
                        continue

                    self.images_data.append(
                        {
                            "index": len(self.images_data),
                            "xref": xref,
                            "x0": x0,
                            "y0": y0,
                            "x1": x1,
                            "y1": y1,
                            "width": width,
                            "height": height,
                            "name": f"image_{xref}_{rect_idx}",
                            "pdf_rect": rect,
                        }
                    )

            # Calculate scale factors
            pdf_width = page.rect.width
            pdf_height = page.rect.height
            img_width, img_height = self.page_image.size

            self.scale_x = img_width / pdf_width
            self.scale_y = img_height / pdf_height

            # Store scaled coordinates
            for img_data in self.images_data:
                img_data["scaled_x0"] = img_data["x0"] * self.scale_x
                img_data["scaled_y0"] = img_data["y0"] * self.scale_y
                img_data["scaled_x1"] = img_data["x1"] * self.scale_x
                img_data["scaled_y1"] = img_data["y1"] * self.scale_y

            # Update display
            self.update_canvas()
            self.update_image_list()

            # Update page entry
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(self.current_page + 1))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to display page: {str(e)}")

    def update_canvas(self):
        """Update canvas with current page image"""
        # Display on canvas (no highlighting on main view)
        self.canvas_image = ImageTk.PhotoImage(self.page_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.canvas_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def update_image_list(self):
        """Update the image list in the right panel"""
        self.image_listbox.delete(0, tk.END)

        if not self.images_data:
            self.image_listbox.insert(tk.END, "No images found")
            return

        for img_data in self.images_data:
            info = (
                f"Image #{img_data['index']+1}  "
                f"{int(img_data['width'])}×{int(img_data['height'])}"
            )
            self.image_listbox.insert(tk.END, info)

    def on_image_list_hover(self, event):
        """Show popup preview when hovering over list item"""
        index = self.image_listbox.nearest(event.y)
        if index < len(self.images_data):
            # Only create new popup if index changed
            if index == self.preview_index and self.preview_popup:
                return  # Already showing popup for this image

            # Close existing popup
            if self.preview_popup:
                self.preview_popup.destroy()
                self.preview_popup = None

            # Update preview index
            self.preview_index = index

            # Extract and show the actual image
            try:
                img_data = self.images_data[index]
                xref = img_data["xref"]

                # Extract the image from PDF
                base_image = self.pdf_doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Convert to PIL Image
                pil_image = Image.open(io.BytesIO(image_bytes))

                # Show popup
                title = f"Image #{img_data['index']+1}"
                self.preview_popup = ImagePreviewPopup(self.root, pil_image, title)

            except Exception as e:
                print(f"Error showing preview: {e}")

    def on_image_list_leave(self, event):
        """Close popup when leaving list"""
        if self.preview_popup:
            self.preview_popup.destroy()
            self.preview_popup = None
        self.preview_index = None

    def on_image_list_click(self, event):
        """Save image when clicking on list item"""
        # Close popup first
        if self.preview_popup:
            self.preview_popup.destroy()
            self.preview_popup = None

        index = self.image_listbox.nearest(event.y)
        if index < len(self.images_data):
            self.save_image(self.images_data[index])

    def save_image(self, img_data):
        """Extract and save the selected image"""
        try:
            xref = img_data["xref"]

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
                    ("All files", "*.*"),
                ],
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
                saved_count = 0
                saved_xrefs = set()

                for img_data in self.images_data:
                    xref = img_data["xref"]

                    if xref in saved_xrefs:
                        continue

                    base_image = self.pdf_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    pil_image = Image.open(io.BytesIO(image_bytes))

                    filename = (
                        f"page{self.current_page+1}_image{img_data['index']+1}.png"
                    )
                    file_path = os.path.join(directory, filename)
                    pil_image.save(file_path)
                    saved_count += 1
                    saved_xrefs.add(xref)

                messagebox.showinfo(
                    "Success",
                    f"Extracted {saved_count} unique image(s) to:\n{directory}",
                )

            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract images: {str(e)}")

    def zoom_in(self):
        """Zoom in by 25%"""
        self.zoom_level = min(self.zoom_level * 1.25, 4.0)
        self.update_zoom_label()
        self.display_page()

    def zoom_out(self):
        """Zoom out by 25%"""
        self.zoom_level = max(self.zoom_level * 0.8, 0.25)
        self.update_zoom_label()
        self.display_page()

    def zoom_fit(self):
        """Fit page to canvas"""
        if not self.pdf_doc:
            return

        page = self.pdf_doc[self.current_page]
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width > 1 and canvas_height > 1:
            # Calculate zoom to fit
            scale_x = canvas_width / (page.rect.width * 2.0)
            scale_y = canvas_height / (page.rect.height * 2.0)
            self.zoom_level = min(scale_x, scale_y, 1.0)
            self.update_zoom_label()
            self.display_page()

    def update_zoom_label(self):
        """Update zoom percentage label"""
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")

    def on_window_resize(self, event):
        """Handle window resize events"""
        # Only respond to root window resize, not other widgets
        if event.widget != self.root:
            return

        # Check if size actually changed significantly
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()

        width_change = abs(current_width - self.last_width)
        height_change = abs(current_height - self.last_height)

        if width_change > 50 or height_change > 50:
            self.last_width = current_width
            self.last_height = current_height

            # Redraw if we have a document
            if self.pdf_doc:
                # Small delay to avoid too many redraws
                if hasattr(self, "_resize_timer"):
                    self.root.after_cancel(self._resize_timer)
                self._resize_timer = self.root.after(200, self.update_canvas)

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
                messagebox.showwarning(
                    "Invalid Page",
                    f"Please enter a page number between 1 and {len(self.pdf_doc)}",
                )
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid page number")

    def __del__(self):
        if self.pdf_doc:
            self.pdf_doc.close()


def main():
    """Entry point for the application"""
    root = tk.Tk()

    # Check for command-line argument (file path)
    initial_file = None
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]

    app = PDFImageExtractor(root, initial_file)
    root.mainloop()


if __name__ == "__main__":
    main()
