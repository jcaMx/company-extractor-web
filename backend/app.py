from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from company_extractor import extract_company_info
import os

# app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
app = Flask(__name__)

# Configure static files based on environment
if os.environ.get('RENDER'):
    app.static_folder = os.path.join(os.getcwd(), 'frontend/build')
else:  # Local development
    app.static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))
print("STATIC FOLDER USED:", app.static_folder)


print(f"Flask app object: {app}") 
CORS(app) 

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

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(app.static_folder, 'static'), filename)


# Serve React Frontend
@app.route('/')
def serve():
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except FileNotFoundError:
        return jsonify({"error": "React build not found. Run 'npm run build' in frontend folder."}), 404

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"}), 200

# Catch-all route to handle React Router paths
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):  # Don't interfere with API routes
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(app.static_folder, 'index.html')

# if __name__ == '__main__':
#     app.run(debug=True)