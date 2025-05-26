from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from aifunctions import generate_section_names, sectionDictionaryGenerator, getQuizJSONforSection,generateTest,generate_test_from_all_sections,generateRecommendedCourses, generateTestFeedback
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
    
    no_of_sections =  6 # Fixed as per the requirement
    sections = generate_section_names(course_name, difficulty, no_of_sections, additional_info)
    print("Generated Section Name")
    section_content = sectionDictionaryGenerator(course_name, sections, wordlimit=250, difficulty=difficulty)
    print("Generated Section Content, Starting generating quiz")
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

@app.route("/generate-test", methods=["POST"])
@cross_origin()
def generate_test():
    data = request.json
    print("Started Generating Test")
    

    course_name = data.get("course_name", "Default Course")
    difficulty = data.get("difficulty", "medium")
    content = data.get("content", {})

    print("Parsed course_name:", course_name)
    print("Parsed difficulty:", difficulty)
    

    if not content:
        return jsonify({"error": "No content provided"}), 400

    try:
        test = generate_test_from_all_sections(course_name, difficulty, content)
        print(test)
        return jsonify({"test": test}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/recommend-courses", methods=["POST"])
@cross_origin()
def recommend_courses():
    data = request.json
    existing_course_names = data.get("course_names", [])

    if not existing_course_names:
        return jsonify({"error": "No course names provided"}), 400

    try:
        recommended = generateRecommendedCourses(existing_course_names)
        return jsonify({"recommendations": recommended}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/test-feedback", methods=["POST"])
@cross_origin()
def test_feedback():
    data = request.json  # Get the test result object from frontend

    if not data:
        return jsonify({"error": "No test result provided"}), 400

    try:
        feedback = generateTestFeedback(data)
        return jsonify({"feedback": feedback}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


if __name__ == '__main__':
    print("Trying to run")
    app.run(host='0.0.0.0', port=5001, debug=True)
