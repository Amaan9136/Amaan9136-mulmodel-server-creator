from flask import Flask, send_file, jsonify, request, render_template
from pyngrok import ngrok
import socket
import os
import pickle
import numpy as np
import ast  

app = Flask(__name__)
shared_directory = None

# Function to get the local IP address
def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

# Start Ngrok and return public URL
def start_ngrok():
    from pyngrok import ngrok
    # Ensure ngrok tunnel is started only once
    if not ngrok.get_tunnels():
        public_url = ngrok.connect(5000).public_url
    else:
        public_url = ngrok.get_tunnels()[0].public_url
    return public_url

# Endpoint to retrieve connection details and list of model names
# local = socket
@app.route('/local-details', methods=['GET'])
def get_local_details():
    local_ip = get_local_ip()

    # Get list of model names in the models folder
    try:
        file_names = [f for f in os.listdir(shared_directory)]
    except FileNotFoundError:
        file_names = []

    return jsonify({ 
        "local_ip": f"http://{local_ip}:5000/",
        "predict_local": f"http://{local_ip}:5000/predict/model_name",
        "file_names": file_names
        # file_names has .txt or .md as the description of the model and .pkl is actual model
    })

# global = ngrok
@app.route('/global-details', methods=['GET'])
def get_global_details():
    ngrok_url = start_ngrok()
    
    # Separate models and description files in the shared directory
    model_files = []
    description_files = []
    try:
        for filename in os.listdir(shared_directory):
            if filename.endswith(('.pkl','.h5')):
                model_files.append(filename)
            elif filename.endswith(('.txt', '.md')):
                description_files.append(filename)
    except FileNotFoundError:
        pass

    return jsonify({
        "ngrok_url": ngrok_url,
        "predict_ngrok": f"{ngrok_url}/predict/model_name",
        "model_files": model_files,
        "description_files": description_files
    })

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
    
# Endpoint to set the shared directory path from the host
@app.route('/submit-path', methods=['POST'])
def submit_path():
    global shared_directory
    shared_directory = request.form.get('path')
    
    if os.path.exists(shared_directory):
        return jsonify({"message": "Path set successfully!", "shared_directory": shared_directory})
    else:
        return jsonify({"error": "Path does not exist on the server."}), 400

# Endpoint to handle prediction requests using query parameters
@app.route('/predict/<model_name>', methods=['GET'])
def predict(model_name):
    file_path = os.path.join(shared_directory, model_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "Model file not found"}), 404

    # Load the model
    try:
        with open(file_path, 'rb') as f:
            model = pickle.load(f)
    except Exception as e:
        return jsonify({"error": f"Failed to load model: {str(e)}"}), 500

    # Get input data from query parameters as a string
    input_data_str = request.args.get('data', type=str)
    if not input_data_str:
        return jsonify({"error": "No input data provided"}), 400

    # Safely evaluate the string to a Python literal (like a list, tuple, etc.)
    try:
        input_data = ast.literal_eval(input_data_str)
    except Exception as e:
        return jsonify({"error": f"Failed to parse input data: {str(e)}"}), 400

    # Ensure the input data is in the correct format for prediction
    input_array = np.array(input_data)

    # Make a prediction
    try:
        prediction = model.predict(input_array)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

    # Return the prediction result
    return jsonify({"prediction": prediction.tolist()})

# New endpoint to read data from `.txt` or `.md` files
@app.route('/read/<filename>', methods=['GET'])
def read_model_data(filename):
    # # Allow only '.txt' or files with '.md' extension
    if not (filename.endswith(".txt") or filename.endswith(".md")):
        return jsonify({"error": "Access denied: only '.txt' or '.md' files can be read"}), 403

    file_path = os.path.join(shared_directory, filename)
    print(file_path)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(file_path, 'r') as f:
            data = f.read()
    except Exception as e:
        return jsonify({"error": f"Failed to read data: {str(e)}"}), 500

    return jsonify({
        "data": data,
    })

# Serve the index.html to the host for inputting the path
@app.route('/')
def index():
    return render_template('index.html')

# Function to run the Flask app
def run_app():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    print(f"Server starting on local IP {get_local_ip()}:5000")
    run_app()
