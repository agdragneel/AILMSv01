from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json

model = OllamaLLM(model="llama3.2:3b")



# Global variable to hold the previous content for continuity
previous_content = ""

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
    global previous_content  # Access the global variable for previous content

    SectionBodyGenerationPrompt = f"""
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

    SecBodyPrompt = ChatPromptTemplate.from_template(SectionBodyGenerationPrompt)
    SecBodyChain = SecBodyPrompt | model

    secBody = SecBodyChain.invoke({"course_name": course_name, "section": section, "wordlimit": wordlimit, "difficulty": difficulty}).strip()
    
    # Update previous content with the newly generated body
    previous_content += secBody + "\n"  # Add the new content to previous content for continuity
    
    return secBody

def sectionDictionaryGenerator(course_name, section_list, wordlimit, difficulty): #Prime Function
    section_dict = {}
    for section in section_list:
        section_dict[section] = sectionContentGenerator(course_name=course_name, section=section, wordlimit=wordlimit, difficulty=difficulty)
    return section_dict


###Quiz Generation Area

previous_quizzes = ""

def generateQuiz(course_name, difficulty, sectionBody):
    QuizGenerationPrompt = f"""
    You are an AI quiz generator. Your task is to create one quiz question, strictly following the given format.
    
    Rules:
    1. The output **MUST** only contain the question and options, formatted exactly as follows:
    QuestionBody~Option1~Option2~Option3~Option4~CorrectOptionNumber
    2. You must provide exactly 4 options. One of them must be the correct answer.
    3. Do not include any greetings, extra information, or unnecessary words in the output.
    4. The output should not contain course names or section titles.
    5. The question must be relevant to the sectionBody and match the difficulty level: {difficulty}.
    6. Make sure it doesn't repeat any questions from previous quizzes: {previous_quizzes}.
    
    Format Example:
    What is the capital of India?~Kolkata~Chennai~New Delhi~Mumbai~3
    
    Now generate a question based on:
    Section Body: {sectionBody}

    After generation, make sure the format is correct and matches.
    """

    # Generate quiz using the provided template and model invocation
    QuizPrompt = ChatPromptTemplate.from_template(QuizGenerationPrompt)
    QuizChain = QuizPrompt | model

    # Call the chain and strip extra whitespace to ensure proper formatting
    quiz = QuizChain.invoke({"course_name": course_name, "difficulty": difficulty, "sectionBody": sectionBody}).strip()
    
    # Return the generated quiz question in the correct format
    return quiz


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

def getQuizJSONforSection(course_name, difficulty, noOfQuestions, sectionBody): #Prime Function
    global previous_quizzes
    questions=[]
    for i in range(noOfQuestions):
        questionstring=generateQuiz(course_name=course_name,difficulty=difficulty,sectionBody=sectionBody)
        previous_quizzes+=" "+questionstring
        question=Question(questionstring)
        questions.append(question)
    json_question=convert_questions_to_json(questions)
    validate_json_string(json_question)
    previous_quizzes=""
    return json_question


##Testing Section
'''
courseName = "Indian Politics"
dif = "Advanced"
noOfSections = 3
additionalInfo = ""
sections = generate_section_names(courseName, dif, noOfSections, additionalInfo)
sectiondict=sectionDictionaryGenerator(course_name=courseName, section_list=sections, wordlimit=200, difficulty=dif)
firstSection=sectiondict[sections[0]]
#print(generateQuiz(course_name=courseName,difficulty=dif,sectionBody=firstSection))
print(getQuizJSONforSection(course_name=courseName,difficulty=dif,noOfQuestions=1,sectionBody=firstSection))
'''