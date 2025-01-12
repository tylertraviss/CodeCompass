from flask import Flask, render_template, request, jsonify
import subprocess
from dotenv import load_dotenv
import os
import openai

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

STATIC_CONTEXT = """
Act as a blunt yet kind technical recruiter evaluating a candidate's solution to a coding problem.
Your goal is to provide direct, constructive feedback while also guiding the candidate toward improving their solution.
Evaluate the code based on correctness, efficiency, readability, scalability, and handling of edge cases.
Be honest and critical, but also supportive—offer actionable steps for improvement and ask guiding questions to help the candidate think critically about their approach.

If it is earlier in the process of answering the question, 
1) Questions that will slowly guide them to the correct answer.
2) Consise, as if a normal human was talking to you. I want this to replicate as if a recruiter was talking to you.

Assuming that it looks closer to done or the person is stuck, follow this scheme..
Break your feedback into clear sections:
0) Consise, as if a normal human was talking to you. I want this to replicate as if a recruiter was talking to you.
1) What is working,
2) What is not working,
3) What to improve,
4) Guiding Questions, and
5) Next Steps.

Talk in human sentences. If it asks to talk to a technical recruiter, it will give some feedback so far 
End with encouragement to motivate the candidate.
"""

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
