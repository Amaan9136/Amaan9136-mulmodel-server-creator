from flask import Flask, send_file, jsonify, request
from pyngrok import ngrok
import socket

app = Flask(__name__)

url = "http://localhost:3000"

file_path = "files/sample-text-file.txt"

def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

# Open Ngrok tunnel and get public URL
def start_ngrok():
    public_url = ngrok.connect(5000, bind_tls=True)
    print(f"Ngrok tunnel available at: {public_url}")
    return public_url

@app.route('/get-details', methods=['GET'])
def get_details():
    # Get local IP and Ngrok URL
    local_ip = get_local_ip()
    ngrok_url = start_ngrok()

    # Return details
    return jsonify({
        "local_ip": f"http://{local_ip}:5000/download-file",
        "ngrok_url": f"{ngrok_url}/download-file",
        "url_to_share": url
    })

@app.route('/download-file', methods=['GET'])
def download_file():
    # Send the file to the user
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    # Start Flask app
    print(f"Server starting on local IP {get_local_ip()}:5000")
    app.run(host='0.0.0.0', port=5000)