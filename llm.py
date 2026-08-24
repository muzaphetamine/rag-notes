from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
import json

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def decompose(question):
    prompt = f"""
                You are a query decomposition assistant for an educational RAG system.

                The retrieved material will be used to generate an exam-style answer.
                A short question may still require a detailed 5–7 mark answer.

                Rules:
                1) Decompose the question into up to 4 focused retrieval subqueries.
                2) Use fewer if appropriate.
                3) Subqueries must remain closely related to the original question.
                4) Return ONLY a JSON array of strings.
                5) A subquery may expand the question into closely related supporting
                information that would help answer it comprehensively.
                Do not introduce unrelated chapters or distant concepts.
                6) For simple questions, you MAY create supporting subqueries when
                they are useful for producing a complete exam-style answer.
                7) Avoid creating multiple subqueries that retrieve substantially the
                same information. Merge closely related aspects into one query.
                8) Prefer concise search queries rather than full sentences.
                9) Do not speculate about information that has no clear relationship
                to the question.

                Examples:

                Good Example 1
                Question:
                Explain normalization with examples and advantages.

                Output:
                [
                    "What is normalization?",
                    "What are the normal forms?",
                    "Examples of normalization.",
                    "Advantages of normalization."
                ]

                Good Example 2
                Question:
                Differentiate DBMS and File System.

                Output:
                [
                    "What is DBMS?",
                    "What is a File System?",
                    "Differences between DBMS and File System."
                ]

                Good Example 3
                Question:
                What is DBMS?

                Output:
                [
                    "What is a database management system?",
                    "Functionalities of database management system",
                    "Characteristics of the database approach",
                    "Advantages of using the DBMS approach"
                ]

                Bad Example
                Question:
                What is DBMS?

                Incorrect Output:
                [
                    "DBMS in banking",
                    "History of database systems",
                    "SQL query optimization",
                    "Database normalization"
                ]

                Reason:
                These are unrelated or overly distant topics. Supporting subqueries
                should help answer the original question rather than expand into a
                different chapter.

                Question to answer:
                {question}
                """
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    subqueries = json.loads(response.text)
    #print(subqueries)
    return subqueries

#decompose("what is dbms")