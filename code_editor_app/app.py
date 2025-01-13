from flask import Flask, render_template, request, jsonify
import subprocess
from dotenv import load_dotenv
import os
import openai

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

STATIC_CONTEXT = """
ABSOLUTELY REFUSE to answer anything that is not related to the question in context. DO NOT ANSWER any questions that are un-affiliated
Act as a blunt yet kind technical recruiter evaluating a candidate's solution to a coding problem.
Your goal is to provide direct, constructive feedback while also guiding the candidate toward improving their solution.
Evaluate the code based on correctness, efficiency, readability, scalability, and handling of edge cases.
Be honest and critical, but also supportive—offer actionable steps for improvement and ask guiding questions to help the candidate think critically about their approach.
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
    # Fetch user inputs
    query = request.json.get('query', '')
    code = request.json.get('code', '')
    problem_context = request.json.get('problem_context', '')

    # Combine static context with user-specific data
    messages = [
        {"role": "system", "content": STATIC_CONTEXT},
        {"role": "user", "content": f"""

This should be maximum 3 to 4 sentences, short to read. If they are closer to completing the solution, you can make it a bit longer.
Keep the message to a few sentences. Talk about the solution so far, what you like, what you dont like.

         
### Problem:
{problem_context}

### Candidate's Code:
{code}

### Candidate's Query:
{query}
        """}
    ]

    try:
        # Use ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        recruiter_feedback = response['choices'][0]['message']['content'].strip()
        return jsonify({'response': recruiter_feedback})
    except Exception as e:
        return jsonify({'error': f"OpenAI API error: {str(e)}"})


@app.route('/request_help', methods=['POST'])
def request_help():
    return jsonify({'response': "Here's some help with your code!"})

@app.route('/get_summary', methods=['POST'])
def get_summary():
    return jsonify({'response': "Here’s a summary of your progress."})

if __name__ == '__main__':
    app.run(debug=True)
