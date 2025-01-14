"""
Flask application for a coding practice platform with AI-powered assistance and live code execution features.

Modules:
    - `Flask`: Provides the web framework.
    - `subprocess`: Executes Python code submitted by users in a secure environment.
    - `dotenv`: Loads environment variables.
    - `os`: Handles file paths and environment variable management.
    - `json`: Handles JSON operations.
    - `openai`: Integrates with the OpenAI API for AI-powered feedback and assistance.

Environment:
    - Requires an `.env` file with the variable `OPENAI_API_KEY` set for OpenAI API integration.

Routes:
    - `/`: Displays the dashboard with the list of coding questions.
    - `/about`: Displays the about us page.
    - `/question/<int:question_id>`: Displays the coding question and its editor page.
    - `/run_code`: Executes user-submitted Python code.
    - `/ask_ai`: Fetches feedback from an AI technical recruiter.
    - `/request_help`: Provides AI-powered hints and guidance for solving coding problems.
    - `/get_summary`: Displays a summary of the user's progress.

Attributes:
    - `app (Flask)`: The Flask application instance.
    - `STATIC_CONTEXT (str)`: Predefined AI system prompt for technical recruiter interactions.

"""

from flask import Flask, render_template, request, jsonify
import subprocess
from dotenv import load_dotenv
import os, json
import openai

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

STATIC_CONTEXT = """
TALK AS IF you are an interviewer, talking to the interviewee. Speak in second person
ABSOLUTELY REFUSE to answer anything that is not related to the question in context. DO NOT ANSWER any questions that are un-affiliated
Act as a blunt yet kind technical recruiter evaluating a candidate's solution to a coding problem.
Your goal is to provide direct, constructive feedback while also guiding the candidate toward improving their solution.
Evaluate the code based on correctness, efficiency, readability, scalability, and handling of edge cases.
Be honest and critical, but also supportive—offer actionable steps for improvement and ask guiding questions to help the candidate think critically about their approach.
"""

@app.route('/')
def dashboard():
    """
    Displays the dashboard with the list of coding questions.

    Returns:
        str: Rendered HTML template with a list of questions from `leetcode_questions.json`.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../data/leetcode_questions.json')

    with open(json_path, 'r') as f:
        questions = json.load(f)

    return render_template('dashboard.html', questions=questions)

@app.route('/about')
def about_us_page():
    """
    Displays a simple About Us page.

    Returns:
        str: HTML string for the About Us page.
    """
    return "<h1> About us page! </h1>"

@app.route('/question/<int:question_id>')
def question_page(question_id):
    """
    Displays a specific coding question and its editor.

    Args:
        question_id (int): ID of the coding question.

    Returns:
        str: Rendered HTML template for the coding question and editor.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../data/leetcode_questions.json')

    try:
        with open(json_path, 'r') as f:
            questions = json.load(f)
    except FileNotFoundError:
        return "Questions file not found!", 404

    question = next((q for q in questions if q['id'] == question_id), None)

    if not question:
        return "Question not found", 404

    return render_template('editor.html', **question)

@app.route('/run_code', methods=['POST'])
def run_code():
    """
    Executes Python code submitted by the user.

    Returns:
        dict: Output or error message from the code execution.
    """
    code = request.json.get('code', '')
    try:
        result = subprocess.run(
            ['python3', '-c', code],
            capture_output=True,
            text=True,
            timeout=5
        )
        return jsonify({'output': result.stdout, 'error': result.stderr})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/ask_ai', methods=['POST'])
def talk_to_recruiter():
    """
    Fetches feedback from an AI technical recruiter based on the user's query and code.

    Returns:
        dict: AI-generated feedback or error message.
    """
    query = request.json.get('query', '')
    code = request.json.get('code', '')
    problem_context = request.json.get('problem_context', '')

    messages = [
        {"role": "system", "content": STATIC_CONTEXT},
        {"role": "user", "content": f"""
### Problem:
{problem_context}

### Candidate's Code:
{code}

### Candidate's Query:
{query}
        """}
    ]

    try:
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
    """
    Provides AI-powered hints and guidance for coding problems.

    Returns:
        dict: AI-generated hints or error message.
    """
    query = request.json.get('query', '')
    code = request.json.get('code', '')
    problem_context = request.json.get('problem_context', '')

    messages = [
        {"role": "system", "content": """
You are an AI assistant providing helpful hints and guidance to a candidate solving a coding problem.
Be informative and offer explanations to help the candidate improve their understanding.
If explicitly asked for the answer, provide hints rather than the full solution, nudging them in the right direction.
Your tone should be kind, encouraging, and focused on teaching.
"""},
        {"role": "user", "content": f"""
### Problem:
{problem_context}

### Candidate's Code:
{code}

### Candidate's Query:
{query}
        """}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        help_response = response['choices'][0]['message']['content'].strip()
        return jsonify({'response': help_response})
    except Exception as e:
        return jsonify({'error': f"OpenAI API error: {str(e)}"})

@app.route('/get_summary', methods=['GET'])
def return_to_dashboard():
    """
    Displays a summary of the user's progress.

    Returns:
        str: Rendered HTML template with the summary of progress.
    """
    summary = "Here's a summary of your progress so far: You've solved X problems, optimized Y solutions, and practiced Z edge cases."
    return render_template('summary.html', summary=summary)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
