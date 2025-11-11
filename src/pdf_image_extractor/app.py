#!/usr/bin/env python3
"""
PDF Image Extractor with Visual Bounding Boxes
A lightweight GUI tool to visualize and extract images from PDF files.
Uses PyMuPDF (fitz) and PySide6 (Qt) for reliable cross-platform support.
"""

import sys
import os
import io
import tempfile
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QSplitter,
    QListWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QScrollArea,
    QTabWidget,
    QFileDialog,
    QMessageBox,
    QListWidgetItem,
    QFrame,
)
from PySide6.QtCore import Qt, QSize, QMimeData, QUrl, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QPen,
    QColor,
    QDrag,
    QKeySequence,
    QShortcut,
)
import fitz  # PyMuPDF
from PIL import Image


class DraggableListWidget(QListWidget):
    """Custom QListWidget with drag-and-drop export support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = None
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SingleSelection)

    def startDrag(self, supportedActions):
        """Handle drag start to export image file"""
        if not self.parent_app or not self.currentItem():
            return

        # Get the index of the current item
        index = self.currentRow()
        if index >= len(self.parent_app.images_data):
            return

        try:
            img_data = self.parent_app.images_data[index]
            xref = img_data["xref"]

            # Extract the image
            base_image = self.parent_app.pdf_doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Convert to PIL Image then save to temp file
            pil_image = Image.open(io.BytesIO(image_bytes))

            # Create temp file
            filename = (
                f'page{self.parent_app.current_page+1}_image{img_data["index"]+1}.png'
            )
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, filename)

            pil_image.save(temp_path, "PNG")
            self.parent_app.temp_files.append(temp_path)

            # Create drag object with file URL
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(temp_path)])
            drag.setMimeData(mime_data)

            # Execute drag
            drag.exec(Qt.CopyAction)

        except Exception as e:
            print(f"Error during drag: {e}")


class ImagePreviewPopup(QWidget):
    """Popup window to show image preview"""

    def __init__(self, parent, pil_image, title="Image Preview"):
        super().__init__(
            parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: white; border: 2px solid black;")

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; border: none;")
        layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Image
        max_size = 400
        img_width, img_height = pil_image.size
        if img_width > max_size or img_height > max_size:
            ratio = min(max_size / img_width, max_size / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            pil_image = pil_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )
            img_width, img_height = new_width, new_height

        # Convert PIL to QPixmap
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        qimage = QImage.fromData(img_byte_arr)
        pixmap = QPixmap.fromImage(qimage)

        img_label = QLabel()
        img_label.setPixmap(pixmap)
        img_label.setStyleSheet("border: none;")
        layout.addWidget(img_label, alignment=Qt.AlignCenter)

        # Size info
        size_label = QLabel(f"{img_width}×{img_height} pixels")
        size_label.setStyleSheet("font-size: 9px; border: none;")
        layout.addWidget(size_label, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.adjustSize()


class PDFImageExtractor(QMainWindow):
    def __init__(self, initial_file=None):
        super().__init__()
        self.setWindowTitle("PDF Image Extractor")
        self.resize(1400, 900)

        self.pdf_doc = None
        self.current_page = 0
        self.images_data = []
        self.zoom_level = 1.0
        self.preview_popup = None
        self.temp_files = []

        self.setup_ui()

        # Open initial file if provided
        if initial_file and os.path.exists(initial_file):
            self.open_pdf_file(initial_file)

    def setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        self.open_btn = QPushButton("Open PDF")
        self.open_btn.clicked.connect(self.open_pdf)
        toolbar_layout.addWidget(self.open_btn)

        toolbar_layout.addWidget(QLabel("|"))

        self.prev_btn = QPushButton("◀")
        self.prev_btn.clicked.connect(self.prev_page)
        toolbar_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("▶")
        self.next_btn.clicked.connect(self.next_page)
        toolbar_layout.addWidget(self.next_btn)

        toolbar_layout.addWidget(QLabel("Page:"))
        self.page_entry = QLineEdit()
        self.page_entry.setMaximumWidth(50)
        self.page_entry.returnPressed.connect(self.goto_page)
        toolbar_layout.addWidget(self.page_entry)

        self.go_btn = QPushButton("Go")
        self.go_btn.clicked.connect(self.goto_page)
        toolbar_layout.addWidget(self.go_btn)

        self.page_label = QLabel("/ 0")
        toolbar_layout.addWidget(self.page_label)

        toolbar_layout.addWidget(QLabel("|"))

        toolbar_layout.addWidget(QLabel("Zoom:"))
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        toolbar_layout.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(self.zoom_in_btn)

        self.fit_btn = QPushButton("Fit")
        self.fit_btn.clicked.connect(self.zoom_fit)
        toolbar_layout.addWidget(self.fit_btn)

        toolbar_layout.addWidget(QLabel("|"))

        self.extract_all_btn = QPushButton("Extract All")
        self.extract_all_btn.clicked.connect(self.extract_all_images)
        toolbar_layout.addWidget(self.extract_all_btn)

        toolbar_layout.addStretch()

        self.status_label = QLabel("No PDF loaded")
        toolbar_layout.addWidget(self.status_label)

        main_layout.addWidget(toolbar)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel (Outline/Thumbnails)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.left_tabs = QTabWidget()

        # Outline tab
        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemClicked.connect(self.on_outline_clicked)
        self.left_tabs.addTab(self.outline_tree, "Outline")

        # Thumbnails tab
        thumb_widget = QWidget()
        thumb_layout = QVBoxLayout(thumb_widget)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.thumb_scroll = QScrollArea()
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.thumb_container = QWidget()
        self.thumb_layout = QVBoxLayout(self.thumb_container)
        self.thumb_layout.setAlignment(Qt.AlignTop)
        self.thumb_scroll.setWidget(self.thumb_container)

        thumb_layout.addWidget(self.thumb_scroll)
        self.left_tabs.addTab(thumb_widget, "Thumbnails")

        left_layout.addWidget(self.left_tabs)
        left_widget.setMinimumWidth(220)
        left_widget.setMaximumWidth(300)

        splitter.addWidget(left_widget)

        # Center panel (PDF display)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #f0f0f0;")

        self.pdf_label = QLabel()
        self.pdf_label.setScaledContents(False)
        self.scroll_area.setWidget(self.pdf_label)

        splitter.addWidget(self.scroll_area)

        # Right panel (Image list)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        list_label = QLabel("Images on Page")
        list_label.setStyleSheet("font-weight: bold; padding: 5px;")
        right_layout.addWidget(list_label)

        self.image_list = DraggableListWidget()
        self.image_list.parent_app = self
        self.image_list.itemClicked.connect(self.on_image_clicked)
        self.image_list.itemEntered.connect(self.on_image_hover)
        self.image_list.setMouseTracking(True)
        right_layout.addWidget(self.image_list)

        instructions = QLabel("Hover to preview\nClick to save\nDrag to export")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet("color: gray; padding: 5px;")
        right_layout.addWidget(instructions)

        right_widget.setMinimumWidth(250)
        right_widget.setMaximumWidth(350)

        splitter.addWidget(right_widget)

        # Set splitter proportions
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        main_layout.addWidget(splitter)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key_Left), self, self.prev_page)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.next_page)

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF file", "", "PDF files (*.pdf);;All files (*)"
        )
        if file_path:
            self.open_pdf_file(file_path)

    def open_pdf_file(self, file_path):
        try:
            if self.pdf_doc:
                self.pdf_doc.close()

            self.pdf_doc = fitz.open(file_path)
            self.current_page = 0
            self.zoom_level = 1.0

            self.load_outline()
            self.load_thumbnails()
            self.display_page()

            # Apply fit after display
            QApplication.processEvents()
            self.zoom_fit()

            self.status_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.page_label.setText(f"/ {len(self.pdf_doc)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open PDF: {str(e)}")

    def load_outline(self):
        self.outline_tree.clear()

        toc = self.pdf_doc.get_toc()

        if toc:
            parent_stack = [(None, 0)]

            for level, title, page_num in toc:
                while parent_stack and parent_stack[-1][1] >= level:
                    parent_stack.pop()

                parent = parent_stack[-1][0] if parent_stack else None

                item = QTreeWidgetItem([f"{title} (p.{page_num})"])
                item.setData(0, Qt.UserRole, page_num - 1)

                if parent:
                    parent.addChild(item)
                else:
                    self.outline_tree.addTopLevelItem(item)

                parent_stack.append((item, level))
        else:
            for i in range(len(self.pdf_doc)):
                item = QTreeWidgetItem([f"Page {i+1}"])
                item.setData(0, Qt.UserRole, i)
                self.outline_tree.addTopLevelItem(item)

    def load_thumbnails(self):
        # Clear existing thumbnails
        while self.thumb_layout.count():
            child = self.thumb_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i in range(len(self.pdf_doc)):
            page = self.pdf_doc[i]
            mat = fitz.Matrix(0.2, 0.2)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qimage = QImage(
                img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimage)

            # Create clickable thumbnail
            thumb_btn = QPushButton()
            thumb_btn.setIcon(pixmap)
            thumb_btn.setIconSize(QSize(150, int(150 * pix.height / pix.width)))
            thumb_btn.setText(f"Page {i+1}")
            thumb_btn.setStyleSheet("text-align: center;")
            thumb_btn.clicked.connect(lambda checked, page=i: self.goto_page_num(page))

            self.thumb_layout.addWidget(thumb_btn)

    def on_outline_clicked(self, item):
        page_num = item.data(0, Qt.UserRole)
        if page_num is not None:
            self.current_page = page_num
            self.display_page()

    def display_page(self):
        if not self.pdf_doc:
            return

        try:
            page = self.pdf_doc[self.current_page]

            # Render page
            zoom = self.zoom_level * 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qimage = QImage(
                img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimage)

            self.pdf_label.setPixmap(pixmap)
            self.pdf_label.resize(pixmap.size())

            # Extract images
            self.images_data = []
            image_list = page.get_images()

            for idx, img_info in enumerate(image_list):
                xref = img_info[0]
                rects = page.get_image_rects(xref)

                for rect_idx, rect in enumerate(rects):
                    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                    width = x1 - x0
                    height = y1 - y0

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
                        }
                    )

            self.update_image_list()

            # Update page entry
            self.page_entry.setText(str(self.current_page + 1))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display page: {str(e)}")

    def update_image_list(self):
        self.image_list.clear()

        if not self.images_data:
            self.image_list.addItem("No images found")
            return

        for img_data in self.images_data:
            text = f"Image #{img_data['index']+1}  {int(img_data['width'])}×{int(img_data['height'])}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, img_data["index"])
            self.image_list.addItem(item)

    def on_image_hover(self, item):
        index = item.data(Qt.UserRole)
        if index is None or index >= len(self.images_data):
            return

        if self.preview_popup:
            self.preview_popup.close()
            self.preview_popup = None

        try:
            img_data = self.images_data[index]
            xref = img_data["xref"]

            base_image = self.pdf_doc.extract_image(xref)
            image_bytes = base_image["image"]
            pil_image = Image.open(io.BytesIO(image_bytes))

            self.preview_popup = ImagePreviewPopup(
                self, pil_image, f"Image #{img_data['index']+1}"
            )

            # Position near cursor
            cursor_pos = self.cursor().pos()
            popup_x = cursor_pos.x() - self.preview_popup.width() - 15
            popup_y = cursor_pos.y() - self.preview_popup.height() // 2

            # Ensure on screen
            screen = QApplication.primaryScreen().geometry()
            if popup_x < 0:
                popup_x = cursor_pos.x() + 15
            if popup_y < 0:
                popup_y = 10
            if popup_y + self.preview_popup.height() > screen.height():
                popup_y = screen.height() - self.preview_popup.height() - 10

            self.preview_popup.move(popup_x, popup_y)
            self.preview_popup.show()

        except Exception as e:
            print(f"Error showing preview: {e}")

    def on_image_clicked(self, item):
        if self.preview_popup:
            self.preview_popup.close()
            self.preview_popup = None

        index = item.data(Qt.UserRole)
        if index is None or index >= len(self.images_data):
            return

        self.save_image(self.images_data[index])

    def save_image(self, img_data):
        try:
            xref = img_data["xref"]
            base_image = self.pdf_doc.extract_image(xref)
            image_bytes = base_image["image"]
            pil_image = Image.open(io.BytesIO(image_bytes))

            default_name = f"page{self.current_page+1}_image{img_data['index']+1}.png"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                default_name,
                "PNG files (*.png);;JPEG files (*.jpg);;All files (*)",
            )

            if file_path:
                pil_image.save(file_path)
                QMessageBox.information(
                    self, "Success", f"Image saved to:\n{file_path}"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image: {str(e)}")

    def extract_all_images(self):
        if not self.images_data:
            QMessageBox.information(self, "Info", "No images found on this page.")
            return

        directory = QFileDialog.getExistingDirectory(
            self, "Select directory to save images"
        )

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

                QMessageBox.information(
                    self,
                    "Success",
                    f"Extracted {saved_count} unique image(s) to:\n{directory}",
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to extract images: {str(e)}"
                )

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
            page_num = int(self.page_entry.text()) - 1
            if 0 <= page_num < len(self.pdf_doc):
                self.current_page = page_num
                self.display_page()
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Page",
                    f"Please enter a page number between 1 and {len(self.pdf_doc)}",
                )
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Input", "Please enter a valid page number"
            )

    def goto_page_num(self, page_num):
        if 0 <= page_num < len(self.pdf_doc):
            self.current_page = page_num
            self.display_page()

    def zoom_in(self):
        self.zoom_level = min(self.zoom_level * 1.25, 4.0)
        self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
        self.display_page()

    def zoom_out(self):
        self.zoom_level = max(self.zoom_level * 0.8, 0.25)
        self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
        self.display_page()

    def zoom_fit(self):
        if not self.pdf_doc:
            return

        page = self.pdf_doc[self.current_page]
        viewport_width = self.scroll_area.viewport().width()
        viewport_height = self.scroll_area.viewport().height()

        if viewport_width > 1 and viewport_height > 1:
            scale_x = viewport_width / (page.rect.width * 2.0)
            scale_y = viewport_height / (page.rect.height * 2.0)
            self.zoom_level = min(scale_x, scale_y, 1.0)
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
            self.display_page()

    def cleanup_temp_files(self):
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up temp file: {e}")
        self.temp_files.clear()

    def closeEvent(self, event):
        self.cleanup_temp_files()
        if self.pdf_doc:
            self.pdf_doc.close()
        event.accept()


def main():
    """Entry point for the application"""
    app = QApplication(sys.argv)

    # Check for command-line argument (file path)
    initial_file = None
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]

    window = PDFImageExtractor(initial_file)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
