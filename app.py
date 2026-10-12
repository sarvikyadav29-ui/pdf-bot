import io
import base64
from flask import Flask, request, jsonify, render_template
from PIL import Image

app = Flask(__name__)

def process_image(img, target_kb, target_w, target_h, maintain_ratio, target_dpi, original_format):
    # Apply Resize
    if target_w or target_h:
        orig_w, orig_h = img.size
        new_w = target_w or orig_w
        new_h = target_h or orig_h
        
        if maintain_ratio and target_w and not target_h:
            ratio = target_w / orig_w
            new_h = int(orig_h * ratio)
        elif maintain_ratio and target_h and not target_w:
            ratio = target_h / orig_h
            new_w = int(orig_w * ratio)
        elif maintain_ratio and target_w and target_h:
            img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            new_w, new_h = img.size
            
        if not maintain_ratio or (target_w and target_h and not maintain_ratio):
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    target_bytes = int(target_kb * 1024)
    min_bytes = int(max(0, (target_kb - 10) * 1024))
    
    fmt = original_format if original_format else 'JPEG'
    if fmt == 'MPO': fmt = 'JPEG' # Fix for some JPEG types

    # Iterative Compression Function
    def attempt_compression(current_img):
        best_bytes = None
        best_q = 100
        low, high = 1, 100
        
        # Binary search for quality
        while low <= high:
            mid_q = (low + high) // 2
            out = io.BytesIO()
            save_kwargs = {'format': fmt, 'optimize': True}
            
            if target_dpi:
                save_kwargs['dpi'] = (target_dpi, target_dpi)
            if fmt in ['JPEG', 'WEBP']:
                save_kwargs['quality'] = mid_q
                
            try:
                current_img.save(out, **save_kwargs)
            except Exception:
                # Fallback for formats that don't support certain kwargs
                current_img.save(out, format=fmt)
                
            size = out.tell()
            
            if size <= target_bytes:
                best_bytes = out.getvalue()
                best_q = mid_q
                if size >= min_bytes:
                    return best_bytes, mid_q, True # Hit target range
                low = mid_q + 1
            else:
                high = mid_q - 1
                
        return best_bytes, best_q, False

    current_img = img.copy()
    if current_img.mode in ("RGBA", "P") and fmt == "JPEG":
        current_img = current_img.convert("RGB")
        
    scale_factor = 1.0
    
    # Try quality reduction first, then progressively scale down dimensions if still too big
    for attempt in range(10):
        result_bytes, final_q, hit_target = attempt_compression(current_img)
        
        if hit_target and result_bytes:
            return result_bytes, final_q, current_img.size
            
        if not result_bytes: # Even quality=1 was too large
            scale_factor *= 0.9
            new_w = max(1, int(current_img.width * scale_factor))
            new_h = max(1, int(current_img.height * scale_factor))
            current_img = current_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            return result_bytes, final_q, current_img.size # Closest possible fit

    # Fallback if iterations fail
    out = io.BytesIO()
    save_kwargs = {'format': fmt}
    if target_dpi: save_kwargs['dpi'] = (target_dpi, target_dpi)
    current_img.save(out, **save_kwargs)
    return out.getvalue(), 1, current_img.size

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    try:
        target_kb = float(request.form.get('target_kb', 100))
        target_w = request.form.get('width', '')
        target_h = request.form.get('height', '')
        target_w = int(target_w) if target_w else None
        target_h = int(target_h) if target_h else None
        maintain_ratio = request.form.get('maintain_ratio', 'true') == 'true'
        target_dpi = request.form.get('dpi', '')
        target_dpi = int(target_dpi) if target_dpi else 72

        img = Image.open(file)
        orig_format = img.format or 'JPEG'
        orig_size_kb = len(file.read()) / 1024
        file.seek(0)
        orig_w, orig_h = img.size
        
        # Extract original DPI if available
        orig_dpi = img.info.get('dpi', (72, 72))[0]

        final_bytes, quality, final_dimensions = process_image(
            img, target_kb, target_w, target_h, maintain_ratio, target_dpi, orig_format
        )
        
        final_kb = len(final_bytes) / 1024
        in_range = (target_kb - 10) <= final_kb <= target_kb
        
        b64_img = base64.b64encode(final_bytes).decode('utf-8')
        mime_type = f"image/{orig_format.lower()}"

        return jsonify({
            'success': True,
            'image_data': f"data:{mime_type};base64,{b64_img}",
            'filename': f"compressed_{file.filename}",
            'original': {
                'size_kb': round(orig_size_kb, 2),
                'dimensions': f"{orig_w}x{orig_h}",
                'dpi': round(orig_dpi)
            },
            'final': {
                'size_kb': round(final_kb, 2),
                'dimensions': f"{final_dimensions[0]}x{final_dimensions[1]}",
                'dpi': target_dpi,
                'quality': quality,
                'in_range': in_range,
                'target_range': f"{max(0, target_kb - 10)} - {target_kb} KB"
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
