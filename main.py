from flask import Flask, request, send_file, jsonify, abort
import subprocess
import uuid
import os
import threading
import time

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
API_KEY = os.environ.get("API_KEY", "tajnykluc")
FILE_TTL_SECONDS = 3600  # maže videá po 1 hodine

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def cleanup_old_files():
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(file_path):
                if now - os.path.getmtime(file_path) > FILE_TTL_SECONDS:
                    os.remove(file_path)
        time.sleep(300)

threading.Thread(target=cleanup_old_files, daemon=True).start()

@app.route('/api/download', methods=['POST'])
def download():
    if request.headers.get('X-API-KEY') != API_KEY:
        abort(401)

    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    file_id = str(uuid.uuid4())
    file_path = os.path.join(DOWNLOAD_DIR, f'{file_id}.mp4')

    command = [
        'yt-dlp',
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        '-o', file_path,
        url
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Download failed'}), 500

    return jsonify({
        'download_url': f'/api/file/{file_id}'
    })

@app.route('/api/file/<file_id>', methods=['GET'])
def get_file(file_id):
    file_path = os.path.join(DOWNLOAD_DIR, f'{file_id}.mp4')
    if not os.path.isfile(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True, download_name=f'{file_id}.mp4')

@app.route('/')
def index():
    return 'yt-dlp API server is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
