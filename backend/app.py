from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import threading
import shutil


app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
SOURCE_DIR = BASE_DIR / "input" / "sources"
QUESTION_DIR = BASE_DIR / "input" / "questions"
PDF_DIR = BASE_DIR / "output" / "pdfs"

SOURCE_DIR.mkdir(parents=True, exist_ok=True)
QUESTION_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

current_status= "Waiting for input..."
pipeline_running=False


def update_status(message):
    global current_status
    current_status =message
    print(f"[STATUS] {message}")


def clean_workspace():
    folders = [
        SOURCE_DIR,
        QUESTION_DIR,
        BASE_DIR / "output",
        BASE_DIR / "database" / "chroma"
    ]
    for folder in folders:
        if not folder.exists():
            continue
        for item in folder.iterdir():
            if item.name==".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


@app.route("/")
def home():
    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(
        FRONTEND_DIR,
        filename
    )


def run_generation(api_key, rpm, model):
    global pipeline_running
    try:
        from pipeline import run_pipeline
        update_status("Starting pipeline...")
        run_pipeline(
            api_key=api_key,
            rpm=rpm,
            model=model,
            progress_callback=update_status
        )
        update_status("Generation complete!")
    except Exception as e:
        update_status(f"Error: {e}")
    finally:
        pipeline_running = False


@app.route("/upload", methods=["POST"])
def upload():
    files =request.files.getlist("files")
    file_type= request.form.get("type")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400
    if file_type not in {"sources", "questions"}:
        return jsonify({"error": "Invalid file type"}), 400
    
    target_dir= SOURCE_DIR if file_type == "sources" else QUESTION_DIR
    saved_files=[]
    for file in files:
        if not file.filename:
            continue
        file_path = target_dir / Path(file.filename).name
        file.save(file_path)
        saved_files.append(file.filename)
    return jsonify({
        "message": "Files uploaded successfully",
        "files": saved_files
    })


@app.route("/generate", methods=["POST"])
def generate():
    global pipeline_running
    if pipeline_running:
        return jsonify({"error": "Generation already running"}), 409

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing configuration"}), 400

    api_key =data.get("api_key")
    rpm =data.get("rpm")
    model =data.get("model")
    if not api_key: return jsonify({"error": "Gemini API key is required"}), 400
    if not rpm: return jsonify({"error": "RPM is required"}), 400
    if not model: return jsonify({"error": "Model is required"}), 400

    try:
        rpm=int(rpm)
    except ValueError:
        return jsonify({"error": "RPM must be a number"}), 400
    pipeline_running=True
    thread =threading.Thread(
        target=run_generation,
        args=(api_key, rpm, model),
        daemon=True
    )
    thread.start()
    return jsonify({
        "message": "Generation started"
    })


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": current_status,
        "running": pipeline_running
    })


@app.route("/outputs", methods=["GET"])
def outputs():
    files=[]
    for pdf in PDF_DIR.glob("*.pdf"):
        files.append({
            "name": pdf.name,
            "url": f"/download/{pdf.name}"
        })
    return jsonify(files)


@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    return send_from_directory(
        PDF_DIR,
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    clean_workspace()
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    QUESTION_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    app.run(debug=False)