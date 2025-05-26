from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json
import time
import random

model = OllamaLLM(model="llama3.2:3b")



# Global variable to hold the previous content for continuity
previous_content = ""
previous_test_questions = set()

def generate_section_names(CName: str, Dif: str, SecNo: str, AdDetails: str):   #Prime Function
    
    SectionNameGenerationPrompt = """
    Ignore all previous instructions and context. Focus on this.
    You are an Expert Course Author for Educational Content.
    Your task is to generate the name of sections, given name of a course, difficulty of the course, number of sections
    and some points to be kept in mind while authoring the course.
    The number of sections MUST be equal to the number of sections specified in the prompt.
    The output should be a string, each section name separated by the symbol ~.
    Do not add any introductory concluding or conversation statements.
    The output should be the string, and the string alone.

    For example:

    Input:

    Name:"Rainbows"
    Difficulty:"Beginner"
    Number of Sections:"5"
    Points:"Focus on types of rainbows"

    Output:"Introduction to Rainbows ~ Types of Rainbows ~ Formation of Primary and Secondary Rainbows ~ Rare and Unique Rainbow Types ~ Conclusion and Key Takeaways"

    Now, generate section names on:

    Name:{CName}
    Difficulty:{Dif}
    Number of Sections:{SecNo}
    Points:{AdDetails}
    """

    SecNamePrompt = ChatPromptTemplate.from_template(SectionNameGenerationPrompt)
    SecNameChain = SecNamePrompt | model

    SecNameString = SecNameChain.invoke({"CName": CName, "Dif": Dif, "SecNo": SecNo, "AdDetails": AdDetails})
    
    SectionList = SecNameString.split("~")
    SectionList = [sentence.strip() for sentence in SectionList]
    return SectionList

def sectionContentGenerator(course_name, section, wordlimit, difficulty):
    global previous_content

    SectionBodyGenerationPrompt = """
You are an Expert Course Author for Educational Content.
You are given a course_name, section name, word_limit, difficulty, and previous content. 
Generate a section body on the given section name (subtopic name). The number of words should be equal or near the word_limit, 
and the difficulty should be kept in mind while generating the content. 
Include relevant context from the previous sections to maintain continuity.
Do not add any greeting, extra messages, or any other things in the output, only the topic content.

Previous Content: {previous_content}

Generate on the following input:

Course Name: {course_name}
Section Name: {section}
Word Limit: {wordlimit}
Difficulty: {difficulty}
"""

    # Fix: Tell LangChain which variables are expected in this prompt
    SecBodyPrompt = ChatPromptTemplate.from_template(SectionBodyGenerationPrompt)
    SecBodyChain = SecBodyPrompt | model

    secBody = SecBodyChain.invoke({
        "course_name": course_name,
        "section": section,
        "wordlimit": wordlimit,
        "difficulty": difficulty,
        "previous_content": previous_content
    }).strip()

    previous_content += secBody + "\n"
    return secBody

def sectionDictionaryGenerator(course_name, section_list, wordlimit, difficulty): #Prime Function
    section_dict = {}
    for section in section_list:
        print("Generating  section:",section)
        section_dict[section] = sectionContentGenerator(course_name=course_name, section=section, wordlimit=wordlimit, difficulty=difficulty)
    return section_dict


###Quiz Generation Area

previous_quizzes = ""

def generateQuiz(course_name, difficulty, sectionBody):
    QuizGenerationPrompt = """
You are an AI quiz generator. You never make mistakes in marking the correct option. Your task is to create one quiz question, strictly following the given format. 

Rules:
1. The output **MUST** only contain the question and options, formatted exactly as follows:
   QuestionBody~Option1~Option2~Option3~Option4~CorrectOptionNumber
2. You must provide exactly 4 options. One of them must be the correct answer. Ensure that ONLY one answer is correct, and it is clearly distinguishable from the incorrect options. Avoid any ambiguity or overlap between the correct and incorrect options.
3. Do not ask questions that can have multiple correct answers, partially correct answers, or subjective answers.
4. Avoid vague or opinion-based questions (e.g., "What are popular...") or questions where answers may vary based on context.
5. The output must not include greetings, extra information, or unnecessary words.
6. The output should not contain course names or section titles.
7. Ensure that the question is directly relevant to the Section Body and matches the specified difficulty level: {difficulty}.
8. Do not repeat any questions from previous quizzes: {previous_quizzes}.
9. All options must be plausible and relevant to the question but only ONE option should be definitively correct.
10. MAKE SURE THAT THE ANSWER IS CORRECT. DOUBLE CHECK IT TO MAKE SURE
Examples of allowed question types:
- Factual (e.g., "What is the capital of India?")
- Definition-based (e.g., "What does HTTP stand for?")

Examples of disallowed question types:
- Opinion-based (e.g., "What is the best...")
- Context-dependent (e.g., "What are popular...")
- Ambiguous (e.g., "Which of the following *could* be...")
- More than one correct options(e.g., "What was used to make Ice Creams?" "Options: Milk, Sugar, Chocolate, Vanilla")

Format Example:
What is the capital of India?~Kolkata~Chennai~New Delhi~Mumbai~3

Now generate a question based on:
Section Body: {sectionBody}

After generation, validate that the format is correct, the question is unambiguous, and only one option is clearly the correct answer.
"""

    # No f-string anymore — treat as pure LangChain template
    QuizPrompt = ChatPromptTemplate.from_template(QuizGenerationPrompt)

    QuizChain = QuizPrompt | model

    quiz = QuizChain.invoke({
        "course_name": course_name,
        "difficulty": difficulty,
        "sectionBody": sectionBody,
        "previous_quizzes": previous_quizzes
    }).strip()

    return quiz

def validate_question_string(question_string: str) -> bool:
    """
    Validates the format of a generated question string.
    The string must have exactly 6 components separated by '~'.
    """
    parts = question_string.split('~')
    if len(parts) != 6:
        return False
    try:
        # Check if the last part (correct option) can be cast to an integer
        correct_option = int(parts[5].strip())
        # Check if the correct option is between 1 and 4
        return 1 <= correct_option <= 4
    except ValueError:
        return False


class Question:
    def __init__(self, question_string: str):
        # Split the string by '~' and strip whitespace
        try:
            parts = [part.strip() for part in question_string.split('~') if part]
            #print(parts)
            
            # Initialize attributes from the split parts
            self.question_body = parts[0]               # The question body
            self.option1 = parts[1]                     # First option
            self.option2 = parts[2]                     # Second option
            self.option3 = parts[3]                     # Third option
            self.option4 = parts[4]                     # Fourth option
            self.correctoptionNumber = int(parts[5])    # Correct option number
        except Exception as e:
            print(question_string)
            print(parts)
            print(e)

    def __str__(self):
        return (f"Question: {self.question_body}\n"
                f"Options: 1) {self.option1}, 2) {self.option2}, 3) {self.option3}, 4) {self.option4}\n"
                f"Correct Option: {self.correctoptionNumber}")



def validate_question_string(question_string: str) -> bool:
    """
    Validates the format of a generated question string.
    The string must have exactly 6 components separated by '~'.
    """
    parts = question_string.split('~')
    if len(parts) != 6:
        return False
    try:
        # Check if the last part (correct option) can be cast to an integer
        correct_option = int(parts[5].strip())
        # Check if the correct option is between 1 and 4
        return 1 <= correct_option <= 4
    except ValueError:
        return False

    

def convert_questions_to_json(questions):
    # Convert the list of Question objects to a list of dictionaries
    questions_dict = [vars(question) for question in questions]
    
    # Convert to JSON string
    json_string = json.dumps(questions_dict, indent=4)
    return json_string

def validate_json_string(json_string):
    try:
        json_data = json.loads(json_string)  # Attempt to load the JSON data
        print("JSON is valid.")
        return json_data
    except json.JSONDecodeError as e:
        print("Invalid JSON:", e)

def getQuizJSONforSection(course_name, difficulty, noOfQuestions, sectionBody, max_retries=5):  
    global previous_quizzes
    questions = []

    for i in range(noOfQuestions):
        retries = 0
        while retries < max_retries:
            try:
                # Generate the question string
                questionstring = generateQuiz(course_name=course_name, difficulty=difficulty, sectionBody=sectionBody)
                # Validate the generated question string
                if not validate_question_string(questionstring):
                    raise ValueError("Invalid question format")

                # Append to previous quizzes to avoid duplicates
                previous_quizzes += " " + questionstring
                # Attempt to create the Question object
                question = Question(questionstring)
                # If successful, add to the list and break the loop
                questions.append(question)
                break
            except Exception as e:
                print(f"Error generating question (attempt {retries + 1}): {e}")
                # Increment retries and try again
                retries += 1

                # Optional: Log the invalid question string for debugging
                print(f"Invalid question string: {questionstring}")

                # Reset the invalid question from previous quizzes
                previous_quizzes = previous_quizzes.replace(questionstring, "").strip()

        if retries == max_retries:
            print("Max retries reached. Skipping this question.")
    
    # Convert the list of Question objects to JSON
    json_question = convert_questions_to_json(questions)
    validate_json_string(json_question)
    
    # Reset the previous quizzes for the next section
    previous_quizzes = ""
    return json_question


def generate_test_from_all_sections(course_name: str,
                                     difficulty: str,
                                     section_dict: dict,
                                     num_questions: int = 5):
    """
    Generates a test by picking random sections and creating a question for each.
    Ensures each question is unique compared to previous_test_questions.
    If after 3 failed attempts it still duplicates, falls back to using section title.
    Returns a JSON string of the complete test.
    """
    global previous_test_questions
    questions = []
    section_titles = list(section_dict.keys())

    for i in range(num_questions):
        print("Generating Test Question", i + 1)
        retries = 0
        while retries < 5:
            try:
                # Pick a random section
                random_section = random.choice(section_titles)
                section_content = section_dict[random_section]

                # After 3 retries, fallback to using only the section title
                if retries >= 3:
                    print(f"[Question {i+1}] Using fallback: section title instead of full content.")
                    prompt_body = random_section
                else:
                    prompt_body = section_content

                # Generate a quiz question
                quiz_dict = generateTest(
                    course_name=course_name,
                    difficulty=difficulty,
                    sectionBody=prompt_body,
                    previous_test_questions="; ".join(previous_test_questions)
                )
                qbody = quiz_dict.get("question_body", "").strip()

                # Ensure uniqueness
                if qbody in previous_test_questions:
                    print(f"[Question {i+1}] Duplicate question detected. Retry #{retries+1}.")
                    retries += 1
                    continue

                # Record and add the new question
                previous_test_questions.add(qbody)
                questions.append(quiz_dict)
                break

            except Exception as e:
                print(f"[Question {i+1} Attempt {retries+1}] Error: {e}")
                retries += 1

        if retries == 10:
            print(f"Max retries reached for question {i+1}. Skipping.")

    # Reset for next call if needed
    previous_test_questions.clear()
    return json.dumps(questions)


def generateTest(course_name, difficulty, sectionBody, previous_test_questions):
    QuizGenerationPrompt = f"""
You are an AI quiz generator. Your task is to create ONE multiple-choice question from the given section content.

### Rules:
1. Return your output strictly as a JSON object with these exact keys:

       "question_body": "...",
       "option1": "...",
       "option2": "...",
       "option3": "...",
       "option4": "...",
       "correctoptionNumber": X

2. Provide exactly 4 options. Only one should be correct.
3. Avoid opinion-based or ambiguous questions, and make SURE it is a question. Not anything else.
4. Match the difficulty: "{difficulty}".
5. DO NOT include the course name or section title.
6. Ensure the correct answer is accurate.
7. Do not repeat any questions from previous quizzes: {previous_test_questions}. Questions should not be repeated in wording or context. If you feel it is hard to come up with a question that is unique and from the section, ask a similar logical or tricky question that can be answered with common sense and the section content provided.

### Section Content:
{sectionBody}

### Output:
Only return a valid JSON object in the described format. Nothing else.
"""

    # Create prompt chain
    QuizPrompt = ChatPromptTemplate.from_template(QuizGenerationPrompt)
    QuizChain = QuizPrompt | model

    # Invoke LLM once; uniqueness handled externally
    quiz_json_str = QuizChain.invoke({
        "course_name": course_name,
        "difficulty": difficulty,
        "sectionBody": sectionBody,
        "previous_test_questions": previous_test_questions
    }).strip()

    # Parse and validate
    quiz_dict = json.loads(quiz_json_str)
    required_keys = ["question_body", "option1", "option2", "option3", "option4", "correctoptionNumber"]
    if not all(key in quiz_dict for key in required_keys):
        raise ValueError("Invalid question format from LLM")

    return quiz_dict

def generateRecommendedCourses(genCourses):
    prompt = f"""
You are an AI-based course advisor. Based on the following courses the user has already generated:

{genCourses}

### TASK:
Suggest 3 new relevant courses the user might be interested in next. Each should be logically connected to their learning history.

### RULES:
1. Output a **JSON list of 3 objects**.
2. Each object must contain:
    - "course_name": str
    - "reason": str
3. Ensure there is no overlap or duplication with existing courses.
4. Keep course names concise but specific.
5. Reasons should be clear, based on user learning progression or gaps.
6. No padding text with the JSON. No greetings, no explanations, nothing. Just a complete, and usable JSON.

"""

    # Create prompt chain
    recPrompt = ChatPromptTemplate.from_template(prompt)
    recChain = recPrompt | model

    # Invoke and parse
    response_json = recChain.invoke({
        "genCourses": genCourses
    }).strip()
    # print(response_json)
    try:
        recommended = json.loads(response_json)
        if not isinstance(recommended, list) or not all("course_name" in r and "reason" in r for r in recommended):
            raise ValueError("Invalid format from LLM.")
    except Exception as e:
        raise ValueError(f"LLM response error: {e}")

    return recommended


def generateTestFeedback(testResult):
    # Escape braces in JSON to avoid ChatPromptTemplate parsing errors
    answers_json = json.dumps(testResult.get("answers", []), indent=2)
    answers_json_escaped = answers_json.replace("{", "{{").replace("}", "}}")

    prompt = f"""
You are an AI feedback assistant for students taking quizzes.

### STUDENT TEST RESULT:

Course Name: {testResult.get("course_name", "Unknown")}
Score: {testResult.get("score", 0)} / {testResult.get("total_questions", 0)}
Date: {testResult.get("created_at", "N/A")}

Answers:
{answers_json_escaped}

### TASK:
Write one helpful sentence of feedback for the student, based on their performance.

### RULES:
1. Use a positive, constructive tone.
2. Focus on specific patterns — strengths or areas to improve.
3. **Do not mention exact question content.**
4. Output must be just a **single sentence**, nothing else.
5. No JSON, no greetings, no bullet points. Just the feedback line.

"""

    feedbackPrompt = ChatPromptTemplate.from_template(prompt)
    feedbackChain = feedbackPrompt | model

    feedback = feedbackChain.invoke({
        "testResult": testResult
    }).strip()


    return feedback


