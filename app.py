from flask import Flask, send_file, jsonify, request
from pyngrok import ngrok
import socket
import os
import pickle
import numpy as np
import ast  # For safely evaluating strings as Python literal expressions

app = Flask(__name__)
models_file_path = "models_folder/"

# Function to get the local IP address
def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

# Start Ngrok and return public URL
def start_ngrok():
    public_url = ngrok.connect(5000, bind_tls=True)
    return public_url

# Endpoint to retrieve connection details
@app.route('/get-details', methods=['GET'])
def get_details():
    local_ip = get_local_ip()
    ngrok_url = start_ngrok()
    return jsonify({
        "local_ip": f"http://{local_ip}:5000/download-model/model_name",
        "ngrok_url": f"{ngrok_url}/download-model/model_name",
        "predict_local": f"http://{local_ip}:5000/predict/model_name",
        "predict_ngrok": f"{ngrok_url}/predict/model_name"
    })

# Endpoint to download a specified model file
@app.route('/download-model/<model_name>', methods=['GET'])
def download_file(model_name):
    file_path = os.path.join(models_file_path, model_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404
    

# Endpoint to handle prediction requests using query parameters
@app.route('/predict/<model_name>', methods=['GET'])
def predict(model_name):
    file_path = os.path.join(models_file_path, model_name)
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

# Function to run the Flask app
def run_app():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    print(f"Server starting on local IP {get_local_ip()}:5000")
    run_app()
