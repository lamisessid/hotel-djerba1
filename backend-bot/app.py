from flask import Flask, request, jsonify
from flask_cors import CORS
from brain import brain
import os


app = Flask(__name__)
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    print(f"API appelée avec: {data.get('message')}") 
    response = brain.process(data.get('message', ''), data.get('user_id', 'guest'))
    return jsonify({"response": response})

@app.route('/api/health', methods=['GET'])
def health():
    ai_status = brain.gemini is not None
    print(f"Health check - IA: {ai_status}")
    return jsonify({"status": "OK", "ai": ai_status})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 