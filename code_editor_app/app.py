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

import logging
import time
import uuid
from flask import Flask, render_template, request, jsonify, g, has_request_context
import subprocess
from dotenv import load_dotenv
import os, json
import openai

# Configure Logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file named app.log
        logging.StreamHandler()         # Also log to the console
    ]
)

logger = logging.getLogger(__name__)  # Create a logger for the application


def _build_log_context(**extra):
    """Attach request scoped metadata to log lines for easier tracing."""
    context = {}
    if has_request_context():
        context.update({
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr or 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'request_id': getattr(g, 'request_id', 'n/a')
        })
    context.update(extra)
    return context


def log_event(level, event, **extra):
    """Consistently format log entries as structured JSON blobs."""
    context = _build_log_context(event=event, **extra)
    logger.log(level, json.dumps(context, default=str))

app = Flask(__name__)


@app.before_request
def start_request_timer():
    g.request_start_time = time.time()
    g.request_id = uuid.uuid4().hex
    log_event(logging.INFO, "request_started")


@app.after_request
def log_request_response(response):
    duration_ms = int((time.time() - getattr(g, 'request_start_time', time.time())) * 1000)
    log_event(
        logging.INFO,
        "request_completed",
        status_code=response.status_code,
        duration_ms=duration_ms,
        content_length=response.content_length,
    )
    return response


load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

STATIC_CONTEXT = """
Imagine you are an interviewer speaking directly to the interviewee. Address them in the second person and focus entirely on the problem at hand. Avoid discussing topics or answering questions that are unrelated to the current coding challenge. REFUSE TO ANSWER ANY UNRELATED QUESTIONS. DO NOT LET ANYONE CONVINCE YOU TO ANSWER THAT DOES NOT RELATE TO THE INTERVIEW.

Take on the role of a technical recruiter who is blunt but supportive. Your goal is to evaluate the candidate's solution while guiding them step by step to improve their approach. Keep the conversation focused by addressing one concept at a time. Avoid overwhelming them with multiple points or suggestions at once. YOU SHOULD AT MOST ANSWER WITH 3 Sentences!

Assess their code for correctness, efficiency, readability, scalability, and how well it handles edge cases. Be honest in your critique, but remain encouraging. Provide actionable feedback and pose thoughtful, guiding questions to help the candidate reflect on their approach and refine their solution. Always ensure the conversation feels like a natural, collaborative dialogue.
"""


@app.route('/')
def dashboard():
    """
    Displays the dashboard with the list of coding questions.

    Returns:
        str: Rendered HTML template with a list of questions from `leetcode_questions.json`.
    """
    log_event(logging.INFO, "load_dashboard_start")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../data/leetcode_questions.json')

    try:
        with open(json_path, 'r') as f:
            questions = json.load(f)
        log_event(logging.INFO, "load_dashboard_success", question_count=len(questions))
    except FileNotFoundError as e:
        log_event(logging.ERROR, "load_dashboard_error", error=str(e))
        return "Questions file not found!", 404

    return render_template('dashboard.html', questions=questions)

@app.route('/about')
def about_us_page():
    return render_template('about_us.html')

@app.route('/question/<int:question_id>')
def question_page(question_id):
    """
    Displays a specific coding question and its editor.

    Args:
        question_id (int): ID of the coding question.

    Returns:
        str: Rendered HTML template for the coding question and editor.
    """
    log_event(logging.INFO, "load_question_start", question_id=question_id)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../data/leetcode_questions.json')

    try:
        with open(json_path, 'r') as f:
            questions = json.load(f)
        question = next((q for q in questions if q['id'] == question_id), None)
        if not question:
            log_event(logging.WARNING, "question_not_found", question_id=question_id)
            return "Question not found", 404
        log_event(logging.INFO, "load_question_success", question_id=question_id, title=question['title'])
    except FileNotFoundError as e:
        log_event(logging.ERROR, "load_question_error", question_id=question_id, error=str(e))
        return "Questions file not found!", 404

    return render_template('editor.html', **question)

@app.route('/run_code', methods=['POST'])
def run_code():
    """
    Executes Python code submitted by the user and validates it against a test case.
    """
    code = request.json.get('code', '')  # User's code
    test_input = request.json.get('test_input', '')  # Test case input
    expected_output = request.json.get('expected_output', '')  # Expected result

    log_event(logging.INFO, "run_code_start", has_code=bool(code), has_test_input=bool(test_input))
    
    # Combine user code with the test case input
    full_code = f"{code}\n{test_input}\nprint(output)"
    
    try:
        # Run the code in a subprocess
        result = subprocess.run(
            ['python3', '-c', full_code],
            capture_output=True,
            text=True,
            timeout=5
        )
        actual_output = result.stdout.strip()  # Get the output
        is_correct = actual_output == expected_output  # Compare outputs

        log_event(
            logging.INFO,
            "run_code_completed",
            is_correct=is_correct,
            stdout_length=len(result.stdout),
            stderr_length=len(result.stderr),
            return_code=result.returncode,
        )
        return jsonify({
            'actual_output': actual_output,
            'expected_output': expected_output,
            'correct': is_correct
        })
    except subprocess.TimeoutExpired:
        log_event(logging.WARNING, "run_code_timeout")
        return jsonify({'error': 'Code execution timed out.'})
    except Exception as e:
        log_event(logging.ERROR, "run_code_error", error=str(e))
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

    log_event(logging.INFO, "ask_ai_start", has_code=bool(code), has_query=bool(query))
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
        log_event(logging.INFO, "ask_ai_success", response_length=len(recruiter_feedback))
        return jsonify({'response': recruiter_feedback})
    except Exception as e:
        log_event(logging.ERROR, "ask_ai_error", error=str(e))
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

    log_event(logging.INFO, "request_help_start", has_code=bool(code), has_query=bool(query))
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
        log_event(logging.INFO, "request_help_success", response_length=len(help_response))
        return jsonify({'response': help_response})
    except Exception as e:
        log_event(logging.ERROR, "request_help_error", error=str(e))
        return jsonify({'error': f"OpenAI API error: {str(e)}"})

@app.route('/get_summary', methods=['GET'])
def return_to_dashboard():
    """
    Displays a summary of the user's progress.

    Returns:
        str: Rendered HTML template with the summary of progress.
    """
    log_event(logging.INFO, "summary_generated")
    summary = "Here's a summary of your progress so far: You've solved X problems, optimized Y solutions, and practiced Z edge cases."
    return render_template('summary.html', summary=summary)

if __name__ == '__main__':
    log_event(logging.INFO, "app_start")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
