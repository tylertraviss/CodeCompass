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
from flask import Flask, render_template, request, jsonify
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
    logger.info("Loading dashboard...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../data/leetcode_questions.json')

    try:
        with open(json_path, 'r') as f:
            questions = json.load(f)
        logger.info("Successfully loaded questions from leetcode_questions.json")
    except FileNotFoundError as e:
        logger.error(f"Failed to load questions: {e}")
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
    logger.info(f"Loading question with ID: {question_id}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../data/leetcode_questions.json')

    try:
        with open(json_path, 'r') as f:
            questions = json.load(f)
        question = next((q for q in questions if q['id'] == question_id), None)
        if not question:
            logger.warning(f"Question with ID {question_id} not found.")
            return "Question not found", 404
        logger.info(f"Successfully loaded question: {question['title']}")
    except FileNotFoundError as e:
        logger.error(f"Failed to load questions file: {e}")
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

    logger.info("Executing user code with test case.")
    
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

        return jsonify({
            'actual_output': actual_output,
            'expected_output': expected_output,
            'correct': is_correct
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Code execution timed out.'})
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

    logger.info("Processing AI recruiter feedback.")
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
        logger.info("Successfully fetched AI feedback.")
        return jsonify({'response': recruiter_feedback})
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
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

    logger.info("Processing help request.")
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
        logger.info("Successfully processed help request.")
        return jsonify({'response': help_response})
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return jsonify({'error': f"OpenAI API error: {str(e)}"})

@app.route('/get_summary', methods=['GET'])
def return_to_dashboard():
    """
    Displays a summary of the user's progress.

    Returns:
        str: Rendered HTML template with the summary of progress.
    """
    logger.info("Generating user summary.")
    summary = "Here's a summary of your progress so far: You've solved X problems, optimized Y solutions, and practiced Z edge cases."
    return render_template('summary.html', summary=summary)

if __name__ == '__main__':
    logger.info("Starting the Flask application...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
