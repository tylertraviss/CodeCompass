from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('editor.html')

@app.route('/run_code', methods=['POST'])
def run_code():
    code = request.json.get('code', '')
    try:
        result = subprocess.run(
            ['python3', '-c', code],
            capture_output=True,
            text=True,
            timeout=5  # Prevent infinite loops
        )
        return jsonify({'output': result.stdout, 'error': result.stderr})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/ask_ai', methods=['POST'])
def talk_to_recruiter():
    query = request.json.get('query', '')
    return jsonify({'response': f"Recruiter: {query}"})

@app.route('/request_help', methods=['POST'])
def request_help():
    return jsonify({'response': "Here's some help with your code!"})

@app.route('/get_summary', methods=['POST'])
def get_summary():
    return jsonify({'response': "Here’s a summary of your progress."})

if __name__ == '__main__':
    app.run(debug=True)
