from flask import Flask, render_template, request, jsonify
import subprocess
from dotenv import load_dotenv
import os
import openai

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

STATIC_CONTEXT = """
TALK AS IF you are a interviewer, talking to the interviewee. Speak in second person
ABSOLUTELY REFUSE to answer anything that is not related to the question in context. DO NOT ANSWER any questions that are un-affiliated
Act as a blunt yet kind technical recruiter evaluating a candidate's solution to a coding problem.
Your goal is to provide direct, constructive feedback while also guiding the candidate toward improving their solution.
Evaluate the code based on correctness, efficiency, readability, scalability, and handling of edge cases.
Be honest and critical, but also supportive—offer actionable steps for improvement and ask guiding questions to help the candidate think critically about their approach.
"""

# Pages 

@app.route('/') #Eventually will be dashboard
def home():
    return render_template('two_sum_editor.html')

@app.route('/2')
def reverse_string_page():
    return render_template('reverse_string_editor.html')

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
    # Fetch user inputs
    query = request.json.get('query', '')
    code = request.json.get('code', '')
    problem_context = request.json.get('problem_context', '')

    # Combine static context with user-specific data
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

Please help me understand how to approach this problem or improve my solution. If I explicitly ask for the answer, guide me toward it without directly providing it.
        """}
    ]

    try:
        # Use ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or "gpt-4" if available
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        help_response = response['choices'][0]['message']['content'].strip()
        return jsonify({'response': help_response})
    except Exception as e:
        return jsonify({'error': f"OpenAI API error: {str(e)}"})

@app.route('/get_summary', methods=['GET'])
def get_summary():
    # Generate or fetch a summary
    summary = "Here's a summary of your progress so far: You've solved X problems, optimized Y solutions, and practiced Z edge cases."
    
    # Render the summary page with the summary injected
    return render_template('summary.html', summary=summary)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
