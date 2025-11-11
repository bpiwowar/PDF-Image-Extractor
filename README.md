# PDF Image Extractor

A lightweight Python application with a GUI to visualize and extract images from PDF files. The app displays PDF pages with red bounding boxes around detected images, allowing you to click on any box to save that image.

## Features

- 📄 **Visual PDF Navigation**: Browse through PDF pages with Previous/Next buttons or jump to specific pages
- 🖼️ **Image Visualization**: Red bounding boxes highlight all extractable images on each page
- 🖱️ **Click to Save**: Simply click any bounding box to extract and save that image
- 📑 **Page Outline**: Sidebar navigation with PDF TOC support for quick page access
- 📊 **Image Info Panel**: View details about all images on the current page
- 💾 **Batch Extract**: Extract all images from the current page at once
- 🚀 **Pure Python**: No external system dependencies required (no poppler!)
- 🎯 **Lightweight**: Uses tkinter (built-in) - no heavy GUI frameworks needed

## Installation

### From Source

Clone or download this repository, then install:

```bash
pip install -e .
```

### From PyPI (if published)

```bash
pip install pdf-image-extractor
```

That's it! No system dependencies needed - PyMuPDF includes everything required.

## Usage

After installation, run from anywhere using the command:

```bash
pdf-image-extractor
```

Or run directly from the source directory:

```bash
python -m pdf_image_extractor.app
```

### Quick Start Guide

1. **Open a PDF**: Click "Open PDF" button and select your PDF file
2. **Navigate**: Use Previous/Next buttons, or type a page number and click Go
3. **Use Outline**: Click on TOC entries in the left sidebar to jump to sections
4. **View Images**: Red boxes show all extractable images on the page
5. **Extract Image**: Click on any red bounding box to save that image
6. **Batch Extract**: Click "Extract All Images" to save all images from the current page

### Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│ [Open PDF] [Previous] [Next] Page: [__] Go  [Extract All]  │
├──────────┬─────────────────────────────────┬────────────────┤
│ Outline  │  PDF Display Area               │  Images Info   │
│          │  (with red bounding boxes)      │                │
│ Chapter 1│                                 │  Image #1      │
│ ├─ Sec 1 │     ┌─────────┐                 │  Size: 800x600 │
│ └─ Sec 2 │     │ Image 1 │                 │  Click to save │
│ Chapter 2│     └─────────┘                 │                │
│ Page 3   │                                 │  Image #2      │
│ ...      │         ┌─────┐                 │  Size: 400x300 │
│          │         │ #2  │                 │  Click to save │
│          │         └─────┘                 │                │
└──────────┴─────────────────────────────────┴────────────────┘
```

## Tips

- **High Quality**: Images are extracted in their original resolution
- **Supported Formats**: Save as PNG (lossless) or JPEG
- **Bounding Box Numbers**: Each box is labeled with #1, #2, etc. matching the info panel
- **Scroll**: Use scrollbars if the PDF page is larger than the display area
- **TOC Support**: PDFs with table of contents show hierarchical navigation
- **Multiple Instances**: Same image appearing multiple times shows separate bounding boxes

## How It Works

The application uses:
- **PyMuPDF (fitz)**: To render PDF pages, extract images, and parse structure - all in pure Python
- **tkinter**: For the lightweight, native GUI (built-in with Python)
- **Pillow**: For image manipulation and saving

## Project Structure

```
pdf-image-extractor/
├── pyproject.toml          # Modern Python packaging configuration
├── README.md               # This file
└── pdf_image_extractor/    # Main package
    ├── __init__.py         # Package initialization
    └── app.py              # Main application code
```

## Development

### Install in Development Mode

```bash
pip install -e ".[dev]"
```

This includes additional development tools (pytest, black, flake8).

### Run Tests

```bash
pytest
```

### Format Code

```bash
black pdf_image_extractor/
```

## Troubleshooting

**"Failed to open PDF"**
- Ensure the PDF is not corrupted or password-protected
- Try opening it in a regular PDF viewer first

**"No images found"**
- The PDF might contain scanned images (rendered as page content, not embedded images)
- Try PDFs with vector graphics or embedded images
- Some PDFs embed images as page backgrounds which may not be detected

**Import errors**
- Make sure you've installed the package: `pip install -e .`
- Verify PyMuPDF is installed: `pip list | grep PyMuPDF`

## Requirements

- Python 3.8 or higher
- PyMuPDF >= 1.23.0 (automatically installed)
- Pillow >= 10.0.0 (automatically installed)
- tkinter (usually included with Python)

## License

MIT License - Feel free to use and modify as needed.
