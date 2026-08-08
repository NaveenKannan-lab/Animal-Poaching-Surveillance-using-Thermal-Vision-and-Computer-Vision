from flask import Flask, render_template, Response, request, jsonify, send_file
from detector.engine import DetectionEngine
from detector.state import AppState
import threading
import os
import base64
import zipfile
import io
from datetime import datetime

app = Flask(__name__)

# Default settings
app_settings = {
    "confidence": 35,
    "model": "yolov8l.pt",
    "soundEnabled": True
}

engine = DetectionEngine(model_path=app_settings["model"])
state = AppState()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    video = request.files["video"]
    path = "temp_video.mp4"
    video.save(path)
    state.set_video(path, video.filename)
    return jsonify({"status": "uploaded", "filename": video.filename})

@app.route("/start", methods=["POST"])
def start():
    global engine
    if not state.running:
        # Update engine settings before starting
        engine.confidence = app_settings["confidence"] / 100
        engine.sound_enabled = app_settings["soundEnabled"]
        threading.Thread(
            target=engine.run,
            args=(state,),
            daemon=True
        ).start()
    return jsonify({"status": "started"})

@app.route("/video")
def video():
    return Response(
        state.stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/humans")
def humans():
    return jsonify(state.get_stats())

@app.route("/settings", methods=["GET", "POST"])
def settings():
    global app_settings, engine
    if request.method == "POST":
        data = request.json
        app_settings["confidence"] = data.get("confidence", 35)
        app_settings["soundEnabled"] = data.get("soundEnabled", True)
        
        # If model changed, reload engine
        new_model = data.get("model", "yolov8m.pt")
        if new_model != app_settings["model"]:
            app_settings["model"] = new_model
            engine = DetectionEngine(model_path=new_model)
        
        return jsonify({"status": "saved"})
    return jsonify(app_settings)

@app.route("/export", methods=["GET"])
def export():
    """Export all alert frames as a zip file"""
    alert_frames = state.get_human_frames()
    
    if not alert_frames:
        return jsonify({"error": "No alert frames to export"}), 400
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, frame_b64 in enumerate(alert_frames, 1):
            # Decode base64 to bytes
            frame_bytes = base64.b64decode(frame_b64)
            # Add to zip
            zip_file.writestr(f"alert_frame_{idx:04d}.jpg", frame_bytes)
    
    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"alert_frames_{timestamp}.zip"
    
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(debug=False, threaded=True)