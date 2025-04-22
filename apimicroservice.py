from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from aifunctions import generate_section_names, sectionDictionaryGenerator, getQuizJSONforSection,generateTest,generate_test_from_all_sections
import time

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_content():
    print("Started Generating")
    data = request.json  # Access the JSON data
    print("Received Data:")
    print(data)
    course_name = data['course_name']
    difficulty = data['difficulty']
    additional_info = data['additional_info']

    start_time = time.time()
    
    no_of_sections = 5  # Fixed as per the requirement
    sections = generate_section_names(course_name, difficulty, no_of_sections, additional_info)
    section_content = sectionDictionaryGenerator(course_name, sections, wordlimit=200, difficulty=difficulty)
    
    section_quiz = {}
    for section in sections:
        quiz = getQuizJSONforSection(course_name, difficulty, 1, section_content[section])
        section_quiz[section] = quiz

    end_time = time.time()
    
    # Calculate time taken
    time_taken = end_time - start_time
    print("Time Taken:", time_taken)
    
    return jsonify({'sections': sections, 'content': section_content, 'quiz': section_quiz})

@app.route('/get_section', methods=['POST'])
def get_section():
    data = request.json  # Access the JSON data

    index = int(data['index'])
    sections = data['sections']
    content = data['content']
    quiz = data['quiz']
    
    section_title = sections[index]
    section_body = content[section_title]
    section_quiz = quiz[section_title]
    
    return jsonify({'title': section_title, 'content': section_body, 'quiz': section_quiz})

if __name__ == '__main__':
    print("Trying to run")
    app.run(host='0.0.0.0', port=5001, debug=True)
