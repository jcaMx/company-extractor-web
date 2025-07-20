from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS for cross-origin requests
from company_extractor import extract_company_info

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

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

if __name__ == '__main__':
    app.run(debug=True)