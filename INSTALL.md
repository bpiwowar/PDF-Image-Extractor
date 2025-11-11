# Quick Installation Guide

## Step 1: Install the Package

Navigate to this directory and run:

```bash
pip install -e .
```

This will install the package in "editable" mode, meaning you can modify the code and see changes immediately.

## Step 2: Run the Application

After installation, you can run the app from anywhere:

```bash
pdf-image-extractor
```

That's it! No system dependencies required.

## Alternative: Run Without Installing

If you prefer not to install, you can run directly:

```bash
python -m pdf_image_extractor.app
```

## What Gets Installed

- `PyMuPDF` (fitz) - Pure Python PDF library with embedded binaries
- `Pillow` - Image processing library
- Command-line tool: `pdf-image-extractor`

## Verify Installation

Check that the command is available:

```bash
which pdf-image-extractor  # Linux/Mac
where pdf-image-extractor  # Windows
```

Or simply run:

```bash
pdf-image-extractor
```

The GUI should open!
