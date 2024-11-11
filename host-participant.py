from flask import Flask, send_file, jsonify, request, render_template, redirect, url_for
import os

app = Flask(__name__)

# Store the shared directory path globally
shared_directory = None

# Serve the index.html to the host for inputting the path
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to set the shared directory path from the host
@app.route('/submit-path', methods=['POST'])
def submit_path():
    global shared_directory
    shared_directory = request.form.get('path')
    
    if os.path.exists(shared_directory):
        return jsonify({"message": "Path set successfully!", "shared_directory": shared_directory})
    else:
        return jsonify({"error": "Path does not exist on the server."}), 400

# Endpoint to list files in the shared directory for participants
@app.route('/files', methods=['GET'])
def list_files():
    if not shared_directory:
        return jsonify({"error": "No shared directory set by the host."}), 400
    
    try:
        # List files in the shared directory
        file_list = os.listdir(shared_directory)
        return jsonify({"files": file_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint for participants to download files from the shared directory
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    if not shared_directory:
        return jsonify({"error": "No shared directory set by the host."}), 400
    
    file_path = os.path.join(shared_directory, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
