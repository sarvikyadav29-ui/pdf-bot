# Intelligent Image Compressor

A clean and powerful web tool built with Python (Flask) that optimizes your images and saves you time. It allows you to target a specific maximum KB size, dynamically compressing the image without unnecessary loss in quality until it fits precisely within the specified target range.

## Features
- **Strict KB Targeting:** Uses a smart binary-search backend algorithm to hit a precise 10KB window below your target size.
- **Custom Dimensions & DPI:** Control over resolution and print metadata.
- **Support for Modern Formats:** JPEG, PNG, WebP.
- **No Disk Storage:** Processes entirely in-memory using `io.BytesIO`. Temporary files are never written to disk, ensuring maximum security and performance.
- **Iframe Ready & Responsive:** Clean Tailwind UI handles everything.

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/image-compressor.git](https://github.com/yourusername/image-compressor.git)
   cd image-compressor
