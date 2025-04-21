from flask import Flask, render_template, request, jsonify
from aifunctions import generate_section_names, sectionDictionaryGenerator, getQuizJSONforSection
import time
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_content():
    print("Started Generating")
    course_name = request.form['course_name']
    difficulty = request.form['difficulty']
    additional_info = request.form['additional_info']

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
    print("Time Taken:",time_taken)
    
    return jsonify({'sections': sections, 'content': section_content, 'quiz': section_quiz})

@app.route('/get_section', methods=['POST'])
def get_section():
    index = int(request.form['index'])
    sections = request.form.getlist('sections[]')
    content = request.form['content']
    quiz = request.form['quiz']
    
    section_title = sections[index]
    section_body = content[section_title]
    section_quiz = quiz[section_title]
    
    return jsonify({'title': section_title, 'content': section_body, 'quiz': section_quiz})

if __name__ == '__main__':
    app.run(debug=True)
