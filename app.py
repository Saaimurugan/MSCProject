from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

SCORING_API_URL = "https://1p3uymdf7g.execute-api.us-east-1.amazonaws.com/dev/elaborateAnswerScore"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/score', methods=['POST'])
def score_answer():
    data = request.json
    payload = {
        "user_answer": data.get("user_answer"),
        "example_answer": data.get("example_answer")
    }
    
    try:
        response = requests.post(SCORING_API_URL, json=payload)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
