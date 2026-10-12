from flask import Flask, render_template_string, request, send_file, after_this_request
from werkzeug.utils import secure_filename
import os
import tempfile
import subprocess
import shutil
from pypdf import PdfReader, PdfWriter
import img2pdf
import uuid

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

@app.after_request
def add_header(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    return response

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UPShiksha PDF Tools</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        .tool-card { transition: all 0.2s ease; cursor: pointer; }
        .tool-card:hover { border-color: #ec4899; background: #fdf2f8; }
        .tool-card.active { border-color: #ec4899; background: #fce7f3; box-shadow: 0 0 0 2px #ec4899; }
        .pink-btn { background: #ec4899; }
        .pink-btn:hover { background: #db2777; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-lg mx-auto px-4 py-6">

        <!-- Header -->
        <div class="bg-pink-50 rounded-2xl p-4 mb-6 flex items-center justify-between border border-pink-100">
            <div class="flex items-center gap-3">
                <div class="w-11 h-11 bg-pink-500 rounded-xl flex items-center justify-center text-white text-xl font-bold">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </div>
                <div>
                    <h1 class="text-xl font-bold text-pink-700">UPShiksha PDF Tools</h1>
                    <p class="text-xs text-gray-500">Free Online PDF Utilities</p>
                </div>
            </div>
            <div class="text-green-500">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
            </div>
        </div>

        <!-- Question -->
        <h2 class="text-lg font-semibold text-gray-800 mb-4">आपको क्या करना है?</h2>

        <!-- Tool Cards -->
        <div class="grid grid-cols-2 gap-3 mb-6">
            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4" onclick="selectTool('merge')" id="card-merge">
                <div class="text-pink-500 text-2xl mb-2">📚</div>
                <div class="font-semibold text-gray-800">Merge PDF</div>
                <div class="text-xs text-gray-500 mt-1">कई PDFs जोड़ें</div>
            </div>

            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4" onclick="selectTool('compress')" id="card-compress">
                <div class="text-pink-500 text-2xl mb-2">🗜️</div>
                <div class="font-semibold text-gray-800">Compress PDF</div>
                <div class="text-xs text-gray-500 mt-1">File size कम करें</div>
            </div>

            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4" onclick="selectTool('split')" id="card-split">
                <div class="text-pink-500 text-2xl mb-2">✂️</div>
                <div class="font-semibold text-gray-800">Split PDF</div>
                <div class="text-xs text-gray-500 mt-1">Pages अलग करें</div>
            </div>

            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4" onclick="selectTool('img2pdf')" id="card-img2pdf">
                <div class="text-pink-500 text-2xl mb-2">🖼️</div>
                <div class="font-semibold text-gray-800">Image to PDF</div>
                <div class="text-xs text-gray-500 mt-1">फोटो से PDF बनाएँ</div>
            </div>

            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4" onclick="selectTool('rotate')" id="card-rotate">
                <div class="text-pink-500 text-2xl mb-2">🔄</div>
                <div class="font-semibold text-gray-800">Rotate PDF</div>
                <div class="text-xs text-gray-500 mt-1">Pages घुमाएँ</div>
            </div>

            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4" onclick="selectTool('protect')" id="card-protect">
                <div class="text-pink-500 text-2xl mb-2">🔐</div>
                <div class="font-semibold text-gray-800">Password Protect</div>
                <div class="text-xs text-gray-500 mt-1">Password लगाएँ</div>
            </div>

            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4" onclick="selectTool('organize')" id="card-organize">
                <div class="text-pink-500 text-2xl mb-2">📑</div>
                <div class="font-semibold text-gray-800">Organize</div>
                <div class="text-xs text-gray-500 mt-1">Pages reorder करें</div>
            </div>

            <div class="tool-card bg-white border-2 border-gray-200 rounded-2xl p-4 opacity-60" title="Coming soon">
                <div class="text-pink-500 text-2xl mb-2">🔍</div>
                <div class="font-semibold text-gray-800">OCR</div>
                <div class="text-xs text-gray-500 mt-1">Coming soon</div>
            </div>
        </div>

        <!-- Upload Area -->
        <form method="POST" enctype="multipart/form-data" id="pdfForm">
            <input type="hidden" name="action" id="actionInput" value="merge">

            <div class="bg-gray-100 rounded-2xl p-6 text-center mb-4">
                <div class="text-4xl text-gray-400 mb-3">☁️</div>
                <p class="font-medium text-gray-700 mb-1">अपनी फाइल यहाँ चुनें</p>
                <p class="text-xs text-gray-500 mb-4">PDF या Image · अधिकतम 50 MB</p>
                
                <label class="pink-btn text-white font-semibold px-8 py-3 rounded-xl cursor-pointer inline-block">
                    Choose Files
                    <input type="file" name="files" multiple accept=".pdf,image/*" class="hidden" required onchange="showFileName(this)">
                </label>
                <p id="fileName" class="text-sm text-gray-600 mt-3"></p>
            </div>

            <!-- Extra Options -->
            <div id="compressOptions" class="mb-4 hidden">
                <label class="block text-sm font-medium text-gray-700 mb-2">Target Size</label>
                <select name="target_size" class="w-full border border-gray-300 rounded-xl p-3 bg-white">
                    <option value="100">Under 100 KB</option>
                    <option value="200" selected>Under 200 KB</option>
                    <option value="500">Under 500 KB</option>
                    <option value="1024">Under 1 MB</option>
                    <option value="0">High Quality (size important nahi)</option>
                </select>
            </div>

            <div id="splitOptions" class="mb-4 hidden">
                <label class="block text-sm font-medium text-gray-700 mb-2">Pages (example: 1-3,5,7-9)</label>
                <input type="text" name="pages" placeholder="1-5,8" class="w-full border border-gray-300 rounded-xl p-3">
            </div>

            <div id="rotateOptions" class="mb-4 hidden">
                <label class="block text-sm font-medium text-gray-700 mb-2">Angle</label>
                <select name="angle" class="w-full border border-gray-300 rounded-xl p-3">
                    <option value="90">90° Clockwise</option>
                    <option value="180">180°</option>
                    <option value="270">270° / 90° Anti-clockwise</option>
                </select>
            </div>

            <div id="protectOptions" class="mb-4 hidden">
                <label class="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <input type="text" name="password" placeholder="Password likho" class="w-full border border-gray-300 rounded-xl p-3">
            </div>

            <div id="organizeOptions" class="mb-4 hidden">
                <label class="block text-sm font-medium text-gray-700 mb-2">New Order (example: 3,1,2,4)</label>
                <input type="text" name="order" placeholder="3,1,2" class="w-full border border-gray-300 rounded-xl p-3">
            </div>

            <button type="submit" class="w-full pink-btn text-white font-semibold py-3.5 rounded-xl text-lg">
                ✨ Process karo
            </button>
        </form>

        {% if error %}
        <div class="mt-4 p-4 bg-red-50 text-red-600 rounded-xl text-sm border border-red-100">
            {{ error }}
        </div>
        {% endif %}

        {% if message %}
        <div class="mt-4 p-4 bg-green-50 text-green-700 rounded-xl text-sm border border-green-100">
            {{ message }}
        </div>
        {% endif %}

        <p class="text-center text-xs text-gray-400 mt-8">
            Files automatically deleted after processing · Privacy safe
        </p>
    </div>

    <script>
        let currentTool = 'merge';

        function selectTool(tool) {
            currentTool = tool;
            document.getElementById('actionInput').value = tool;

            // Remove active from all
            document.querySelectorAll('.tool-card').forEach(c => c.classList.remove('active'));
            const card = document.getElementById('card-' + tool);
            if (card) card.classList.add('active');

            // Hide all options
            ['compressOptions','splitOptions','rotateOptions','protectOptions','organizeOptions'].forEach(id => {
                document.getElementById(id).classList.add('hidden');
            });

            // Show relevant
            if (tool === 'compress') document.getElementById('compressOptions').classList.remove('hidden');
            if (tool === 'split') document.getElementById('splitOptions').classList.remove('hidden');
            if (tool === 'rotate') document.getElementById('rotateOptions').classList.remove('hidden');
            if (tool === 'protect') document.getElementById('protectOptions').classList.remove('hidden');
            if (tool === 'organize') document.getElementById('organizeOptions').classList.remove('hidden');
        }

        function showFileName(input) {
            const names = Array.from(input.files).map(f => f.name).join(', ');
            document.getElementById('fileName').textContent = names || '';
        }

        // Default select
        selectTool('merge');
    </script>
</body>
</html>
'''

def compress_with_gs(input_path, output_path, target_kb=0):
    if target_kb == 0:
        cmd = [
            "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/prepress", "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={output_path}", input_path
        ]
        subprocess.run(cmd, check=True)
        return

    settings = [
        ("/screen", 72),
        ("/ebook", 150),
        ("/printer", 300),
        ("/prepress", 300),
    ]

    best_file = None
    best_size = float('inf')

    for setting, dpi in settings:
        temp_out = output_path + f".tmp{setting[1:]}.pdf"
        cmd = [
            "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={setting}",
            f"-dColorImageResolution={dpi}",
            f"-dGrayImageResolution={dpi}",
            f"-dMonoImageResolution={dpi}",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={temp_out}", input_path
        ]
        try:
            subprocess.run(cmd, check=True, timeout=90)
            size_kb = os.path.getsize(temp_out) / 1024
            if size_kb < best_size:
                best_size = size_kb
                if best_file and os.path.exists(best_file):
                    os.remove(best_file)
                best_file = temp_out
            else:
                os.remove(temp_out)

            if size_kb <= target_kb:
                break
        except Exception:
            if os.path.exists(temp_out):
                os.remove(temp_out)

    if best_file:
        shutil.move(best_file, output_path)
    else:
        shutil.copy(input_path, output_path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML)

    try:
        files = request.files.getlist("files")
        action = request.form.get("action", "merge")

        if not files or not files[0].filename:
            return render_template_string(HTML, error="कृपया कम से कम एक फाइल चुनें")

        temp_dir = tempfile.mkdtemp()
        input_paths = []

        for f in files:
            filename = secure_filename(f.filename)
            if not filename:
                continue
            path = os.path.join(temp_dir, filename)
            f.save(path)
            input_paths.append(path)

        if not input_paths:
            return render_template_string(HTML, error="Valid file nahi mili")

        output_path = os.path.join(temp_dir, f"result_{uuid.uuid4().hex}.pdf")

        if action == "merge":
            writer = PdfWriter()
            for p in input_paths:
                if p.lower().endswith(".pdf"):
                    writer.append(p)
            if len(writer.pages) == 0:
                return render_template_string(HTML, error="Koi valid PDF nahi mili merge ke liye")
            with open(output_path, "wb") as out:
                writer.write(out)

        elif action == "compress":
            if not input_paths[0].lower().endswith(".pdf"):
                return render_template_string(HTML, error="Compress ke liye PDF file chahiye")
            target = int(request.form.get("target_size", 200))
            compress_with_gs(input_paths[0], output_path, target)

        elif action == "split":
            pages_str = request.form.get("pages", "").strip()
            if not pages_str:
                return render_template_string(HTML, error="Pages number likho (example: 1-3,5)")
            reader = PdfReader(input_paths[0])
            writer = PdfWriter()
            for part in pages_str.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    for i in range(start-1, min(end, len(reader.pages))):
                        writer.add_page(reader.pages[i])
                else:
                    idx = int(part) - 1
                    if 0 <= idx < len(reader.pages):
                        writer.add_page(reader.pages[idx])
            if len(writer.pages) == 0:
                return render_template_string(HTML, error="Valid pages nahi mili")
            with open(output_path, "wb") as out:
                writer.write(out)

        elif action == "rotate":
            angle = int(request.form.get("angle", 90))
            reader = PdfReader(input_paths[0])
            writer = PdfWriter()
            for page in reader.pages:
                page.rotate(angle)
                writer.add_page(page)
            with open(output_path, "wb") as out:
                writer.write(out)

        elif action == "protect":
            password = request.form.get("password", "").strip()
            if not password:
                return render_template_string(HTML, error="Password likho")
            writer = PdfWriter()
            writer.append(input_paths[0])
            writer.encrypt(password)
            with open(output_path, "wb") as out:
                writer.write(out)

        elif action == "organize":
            order_str = request.form.get("order", "").strip()
            if not order_str:
                return render_template_string(HTML, error="New order likho (example: 3,1,2)")
            order = [int(x.strip())-1 for x in order_str.split(",")]
            reader = PdfReader(input_paths[0])
            writer = PdfWriter()
            for i in order:
                if 0 <= i < len(reader.pages):
                    writer.add_page(reader.pages[i])
            if len(writer.pages) == 0:
                return render_template_string(HTML, error="Valid page order nahi mila")
            with open(output_path, "wb") as out:
                writer.write(out)

        elif action == "img2pdf":
            images = [p for p in input_paths if p.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))]
            if not images:
                return render_template_string(HTML, error="Koi image file nahi mili")
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(images))

        else:
            return render_template_string(HTML, error="Invalid action")

        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
            return response

        return send_file(output_path, as_attachment=True, download_name="UPShiksha_PDF_Result.pdf")

    except Exception as e:
        return render_template_string(HTML, error=f"Error: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
