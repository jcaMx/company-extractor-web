from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from company_extractor import extract_company_info
import os

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)  # Enable CORS for all routes

# API Routes
@app.route('/api/extract', methods=['POST'])
def extract():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        result = extract_company_info(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Serve React Frontend
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

# Catch-all route to handle React Router paths
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):  # Don't interfere with API routes
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)