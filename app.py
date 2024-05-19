import json
from langchain_experimental.agents import create_csv_agent
from langchain.llms import OpenAI
from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import RateLimitError
import pandas as pd
from flask import render_template
import random
#from werkzeug import secure_filename

app = Flask(__name__)

# Allow requests from 'http://localhost:3000'
CORS(app)


app.config['MAX_CONTENT_LENGTH'] = 0.2 * 1024 * 1024  # 200kb
# Create a directory for storing uploaded files within the app context
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def calculator(filename)->str:
    load_dotenv()
    df = pd.read_csv(os.path.join(UPLOAD_FOLDER, filename))
    response = df.to_json(orient='records')
    return response

def fetch_from_query(query,csvfilename):
    load_dotenv()

    # Load the OpenAI API key from the environment variable
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "":
        return "Server Error!"

    if csvfilename is None:
        return "No CSV File Provided!"

    # Create a path for saving the uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, csvfilename)
    # Save the uploaded file with the original name

    agent = create_csv_agent(
        OpenAI(temperature=0, max_tokens=500), file_path, verbose=True)

    prompt = query #"Which product line had the lowest average price"

    if prompt is None or prompt == "":
        return "No Query Provided!!"
    
    try: 
        response = agent.run(prompt)
    except RateLimitError as e:
        return "Limit Exceed!!"
    
    # You can format the response as needed, e.g., convert to JSON
    #response_json = {"answer": response}
    return response

@app.route('/',methods=['POST','GET'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        query = request.form.get('query')
        print(query)
        if uploaded_file.filename != '':
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)
        res = calculator(uploaded_file.filename)
        answer = fetch_from_query(query,uploaded_file.filename)
        return render_template("user_data.html", value=json.loads(res),answer=answer)
    else:
        return render_template("user_data.html", value=[])
    
# @app.route('/',methods=['POST','GET'])
# def query():
#     query = request.form.get('query')
#     print(query)
#     res = calculator(uploaded_file.filename)
#     return render_template("user_data.html", value=json.loads(res))
        

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/chat_csv', methods=['GET'])
def chat_csv_2():
    response = calculator()
    return jsonify({"data" : json.loads(response)}),200

    
    
    
@app.route('/chat_csv', methods=['POST'])
def chat_csv():
    load_dotenv()

    # Load the OpenAI API key from the environment variable
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "":
        return jsonify({"error": "OPENAI_API_KEY is not set"}), 500
    query = request.form.get('query')
    csv_file = request.files.get('csv_file')
    if csv_file is None:
        return jsonify({"error": "No CSV file provided"}), 400
    # Get the original file name
    original_filename = csv_file.filename
    # Create a path for saving the uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, original_filename)
    # Save the uploaded file with the original name
    csv_file.save(file_path)
    agent = create_csv_agent(
        OpenAI(temperature=0, max_tokens=500), file_path, verbose=True)

    prompt = query #"Which product line had the lowest average price"

    if prompt is None or prompt == "":
        return jsonify({"error": "No user question provided"}), 400
    
    try: 
        response = agent.run(prompt)
    except RateLimitError as e:
        return jsonify({"error": e.message}), 500
    
    # You can format the response as needed, e.g., convert to JSON
    response_json = {"answer": response}
    
    return jsonify(response_json), 200

if __name__ == "__main__":
    app.run(debug=True)