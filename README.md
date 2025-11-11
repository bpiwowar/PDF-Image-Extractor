# PDF Image Extractor

A lightweight Python application with a GUI to visualize and extract images from PDF files. The app displays PDF pages with red bounding boxes around detected images, allowing you to click on any box to save that image.

## Features

- 📄 **Visual PDF Navigation**: Browse through PDF pages with Previous/Next buttons or jump to specific pages
- 🎯 **Popup Image Preview**: Hover over image descriptions to see a popup with the actual extracted image
- 🖱️ **Click to Save**: Click on image descriptions in the list to extract and save
- 📑 **Smart Navigation**: 
  - **Outline Tab**: PDF table of contents with hierarchical navigation
  - **Thumbnails Tab**: Visual page browser with clickable thumbnails
- 🔍 **Zoom Controls**: Zoom in/out with +/- buttons or fit page to window
- 📊 **Image Info Panel**: Interactive list showing all images on the current page
- 💾 **Batch Extract**: Extract all images from the current page at once
- 🚀 **Pure Python**: No external system dependencies required (no poppler!)
- 🎯 **Lightweight**: Uses tkinter (built-in) - no heavy GUI frameworks needed
- 📐 **Responsive**: Automatically adapts to window resizing
- ⌨️ **Command-line Support**: Open PDFs directly from the command line
- 🖼️ **Fit-to-Window**: PDFs automatically fit to window size when opened

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

Or open a PDF directly from the command line:

```bash
pdf-image-extractor /path/to/document.pdf
```

Or run directly from the source directory:

```bash
python -m pdf_image_extractor.app [optional-pdf-file]
```

### Quick Start Guide

1. **Open a PDF**: Click "Open PDF" button or provide a file path as argument
2. **Navigate**: 
   - Use Previous/Next (◀ ▶) buttons or type a page number
   - Click on entries in the **Outline** tab for TOC navigation
   - Switch to **Thumbnails** tab for visual page browsing
3. **View Images**: Check the right panel for a list of all images on the current page
4. **Preview**: Hover your mouse over any image in the list to see a popup preview
5. **Extract Image**: Click on an image in the list to save it
6. **Zoom**: Use +/- buttons to zoom, or click "Fit" to fit page to window (auto-fits on open)
7. **Batch Extract**: Click "Extract All" to save all images from the current page

### Interface Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Open] [◀][▶] Page:[__]Go  Zoom:[−]100%[+][Fit]  [Extract All]    │
├────────────┬──────────────────────────────────┬─────────────────────┤
│ ┌────────┐ │  PDF Display Area               │  Images on Page     │
│ │Outline │ │  (clean, no overlays)           │                     │
│ │Thumbs  │ │                                 │ ┌─────────────────┐ │
│ └────────┘ │                                 │ │ Image #1  800×600│ │
│            │                                 │ │ Image #2  400×300│ │ ← Hover
│ Chapter 1  │                                 │ │ Image #3  600×450│ │
│ ├─ Sec 1   │          ┌──────────────┐       │ └─────────────────┘ │
│ └─ Sec 2   │          │ Popup shows  │       │                     │
│            │          │ actual image │       │ Hover = popup       │
│ [thumb 1]  │          │  800×600 px  │       │ Click = save        │
│ [thumb 2]  │          └──────────────┘       │                     │
│ [thumb 3]  │                                 │                     │
└────────────┴──────────────────────────────────┴─────────────────────┘
```

## Tips

- **Navigation Methods**: Use keyboard arrows in outline, click thumbnails, or use page number entry
- **Hover Highlighting**: Move your mouse over the image list to preview each image's location
- **Zoom Shortcuts**: Use the +/- buttons or "Fit" to quickly adjust view
- **Window Resize**: The display automatically adjusts when you resize the window
- **High Quality**: Images are extracted in their original resolution
- **Supported Formats**: Save as PNG (lossless) or JPEG
- **TOC Support**: PDFs with table of contents show hierarchical navigation in the Outline tab
- **Multiple Instances**: Same image appearing multiple times shows separate list entries

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
├── LICENSE                 # MIT License
└── src/                    # Source directory
    └── pdf_image_extractor/
        ├── __init__.py     # Package initialization
        └── app.py          # Main application code
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

MIT License - Feel free to use and modify as needed.****