# PDF Image Extractor

A lightweight Python application with a GUI to visualize and extract images from PDF files.

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
- 🚀 **Pure Python**: No external system dependencies required

## Running

### With uvx (or pipx)

The simplest option

```bash
uvx extract-pdf-images
```

## Installation

### From Source

Clone or download this repository, then install:

```bash
pip install -e .
```

### From PyPI

```bash
pip install extract-pdf-images
```

## Usage

After installation, run from anywhere using the command:

```bash
extract-pdf-images
```

Or open a PDF directly from the command line:

```bash
extract-pdf-images /path/to/document.pdf
```

Or run directly from the source directory:

```bash
python -m extract_pdf_images.app [optional-pdf-file]
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

## Development

### Install in Development Mode

```bash
pip install -e ".[dev]"
```

## License

MIT License - Feel free to use and modify as needed.
