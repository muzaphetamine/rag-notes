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


def generate_answer(question, results):
    prompt = f"""
            You are a query answering assistant for a RAG system.

            You will be provided a question and retrieved study material.
            Answer the question using ONLY the information contained in the
            provided study material.

            Evaluate each retrieved chunk for relevance to the question.
            Use the most relevant chunks as the basis for the answer.
            Retrieved chunks may contain irrelevant results; ignore them.
            Do not give preference to a chunk based on its retrieval method.
            DO NOT introduce information from outside the provided chunks.

            You may rearrange, combine, summarize, and format the information
            to make the answer clear and readable.

            Answer the question in sufficient depth for an exam-style answer.
            Include all relevant information from the retrieved material, but
            do not add unrelated information.

            The answer should be written as a 10-mark university exam answer.

            Formatting:
            - Use a clear title or heading for the answer.
            - Use numbered points and subpoints where appropriate.
            - Explain each point in complete sentences.
            - Use tables only when the question asks for a comparison/difference and a table is appropriate.
            - Avoid excessive bold text.
            - Do not use decorative Markdown such as horizontal rules.
            - Do not write like a web article or ChatGPT explanation.
            - Make the answer structured, detailed, and suitable for directly studying
            or reproducing in a university examination.

            Question:
            {question}

            Retrieved study material:
            """
    for res in results:
        prompt += f"""
                    --- Chunk ---
                    ID: {res['id']}
                    Heading: {res['heading']}
                    Content:
                    {res['text']}
                    """
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text


def extract_questions(text):
    prompt = f"""
            You are an assistant that extracts university examination questions
            from question papers and question banks.

            Extract ONLY the actual examination questions.

            For each question return:
            {{
                "label": "original question number/label, if present otherwise just a Q",
                "question": "complete question text"
            }}

            Rules:
            1. Preserve the original wording as closely as possible.
            2. Ignore marks, CO levels, Bloom levels, module numbers, and other
            metadata that are not part of the question itself.
            3. Do not combine separate questions.
            4. If a question spans multiple lines or table cells, combine those
            parts into one question.
            5. Preserve labels such as 1a, 1b, 2a, etc.
            6. Do not invent, complete, or answer questions.
            7. Return ONLY a JSON array.

            Question paper content:
            {text}
            """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)