from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
import json

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def decompose(question):
    prompt = f"""
                You are a query decomposition assistant.
                Rules:
                1)Decompose the question into up to 4 focused subqueries.
                2)Use fewer if appropriate.
                3)Do not invent unrelated topics.
                4)Return ONLY a JSON array of strings.
                5)A subquery must not introduce a new chapter or concept that is not explicitly mentioned in the original question.
                    It should only break the question into smaller parts required to answer it comprehensively.
                6)Avoid creating multiple subqueries that retrieve substantially the same information.
                    Merge closely related aspects into a single subquery.
                7)Return concise search queries, not sentences.

                Question to answer:
                {question}

                I have prepared few examples for you
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

                Bad Example
                Question:
                What is DBMS?
                Incorrect Output:
                [
                "Types of DBMS",
                "DBMS Architecture",
                "Examples of DBMS"
                ]
                Reason: These introduce new topics that were not requested.
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