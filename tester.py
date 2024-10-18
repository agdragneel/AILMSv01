from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json

model = OllamaLLM(model="llama3.2:3b")

# Global variable to hold the previous content for continuity
previous_content = ""

def generate_section_names(CName: str, Dif: str, SecNo: str, AdDetails: str):
    
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

def sectionDictionaryGenerator(course_name, section_list, wordlimit, difficulty):
    section_dict = {}
    for section in section_list:
        section_dict[section] = sectionContentGenerator(course_name=course_name, section=section, wordlimit=wordlimit, difficulty=difficulty)
    return section_dict


def generateQuiz(course_name, difficulty, noOfQuestions, sectionBody):
    QuizGenerationPrompt = f"""
    You are an expert quiz creator. Generate a JSON object with {noOfQuestions} quiz questions based on the course name and section body provided.
    The questions should match the difficulty level: {difficulty}.
    Each question should have the following format:
    - question: "Your question here"
    - option1: "Option1"
    - option2: "Option2"
    - option3: "Option3"
    - option4: "option4"
    - answer: "correct option number"
    
    Make sure the questions are relevant to the content of the course and the section body:
    Do not add any extra words, greetings, concluding statements, or text to the output.
    It should have only the JSON object.
    
    Course Name: {course_name}
    Section Body: {sectionBody}
    
    """

    QuizPrompt = ChatPromptTemplate.from_template(QuizGenerationPrompt)
    QuizChain = QuizPrompt | model

    quiz_json = QuizChain.invoke({"course_name": course_name, "difficulty": difficulty, "noOfQuestions": noOfQuestions, "sectionBody": sectionBody}).strip()
    
    # Parse the returned JSON string into a Python dictionary
    return quiz_json


courseName = "Quantum Computing"
dif = "Beginner"
noOfSections = 3
additionalInfo = ""
sections = generate_section_names(courseName, dif, noOfSections, additionalInfo)
sectiondict=sectionDictionaryGenerator(course_name=courseName, section_list=sections, wordlimit=200, difficulty=dif)
firstSection=sectiondict[sections[0]]
print(generateQuiz(course_name=courseName,difficulty=dif,noOfQuestions=3,sectionBody=firstSection))
