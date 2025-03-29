import json
import os

import chromadb
import PyPDF2
import streamlit as st
import yaml
from chromadb.utils import embedding_functions
from openai import OpenAI


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


def embed_content_in_chunks(content, ai_client):
    chunk_size = 800
    chunk_overlap = 200
    chunks = [
        content[i : i + chunk_size]
        for i in range(0, len(content), chunk_size - chunk_overlap)
    ]

    embeddings = []
    for chunk in chunks:
        response = ai_client.embeddings.create(
            input=chunk, model="text-embedding-ada-002"
        )
        embeddings.append(response.data[0].embedding)
    return chunks, embeddings


def load_questions_and_answers(json_path):
    with open(json_path, "r") as file:
        data = json.load(file)
    
    intro = data.get("intro", "")
    questions = {k: f"{k}: {v}" for k, v in data["questions"].items()}
    return intro, questions, data["answers"]

def get_relevant_content(collection, user_answer, actual_answer, question):

    combined_query = f"{actual_answer}{question}"
    
    # Perform the queries and collect results
    results = collection.query(query_texts=combined_query, n_results=5)

    # Extract relevant documents from results
    relevant_content = ("\n\n".join(results["documents"][0]))

    # Return content focusing on what the student missed
    return relevant_content if any(relevant_content) else ""


def load_prompts():
    with open("prompts.yaml", "r") as file:
        return yaml.safe_load(file)


def get_feedback(ai_client, user_answer, question, relevant_content, actual_answer):
    prompts = load_prompts()

    # Prepare the feedback prompt
    feedback_prompt = prompts["feedback_prompt"].format(
        question=question,
        user_answer=user_answer,
    )

    # System prompt for feedback
    feedback_system_prompt = f"""
    You are an expert educator providing constructive feedback to students.
    Use the following information to inform your feedback:

    Actual Answer:
    {actual_answer}

    Relevant Course Content:
    {relevant_content}

    Provide brief feedback in 2-3 sentences, focusing on key strengths and areas for improvement. Your response should not exceed 150 tokens, so keep it short.

    """

    # Call the AI API for feedback
    feedback_response = ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": feedback_system_prompt},
            {"role": "user", "content": feedback_prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    feedback = feedback_response.choices[0].message.content.strip()

    # Prepare the grading prompt
    grading_prompt = prompts["grading_prompt"].format(
        question=question,
        user_answer=user_answer,
    )

    # System prompt for grading
    grading_system_prompt = f"""
    You are an expert grader assessing student answers based on their alignment with the actual answer.

    Actual Answer:
    {actual_answer}
    """

    # Call the AI API for grading
    grading_response = ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": grading_system_prompt},
            {"role": "user", "content": grading_prompt},
        ],
        temperature=0.1,
        max_tokens=5,
    )

    grade = grading_response.choices[0].message.content.strip()

    # Combine feedback and grade
    formatted_response = f"**Feedback:** {feedback}\n\n**Grade:** {grade}"
    return formatted_response




@st.cache_resource
def get_or_create_chroma_collection(_db_client, module_content_fp, _ai_client):
    collection_name = "module_content"

    embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY2"), model_name="text-embedding-ada-002"
    )

    try:
        collection = _db_client.get_collection(
            name=collection_name, embedding_function=embedding_function
        )
        print("Using existing ChromaDB collection.")
    except chromadb.errors.InvalidCollectionException:
        print("No existing ChromaDB collection found. Creating a new one...")
        pdf_text = extract_text_from_pdf(module_content_fp)
        chunks, embeddings = embed_content_in_chunks(pdf_text, _ai_client)
        collection = _db_client.create_collection(
            name=collection_name, embedding_function=embedding_function
        )
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=[f"embedding_{i}" for i in range(len(embeddings))],
        )
        print("New collection created and embeddings added to ChromaDB.")

    return collection

def group_question(questions):
    grouped = {}
    for q_id, question in questions.items():
        base_id = q_id[0]  # Get the first character of the question ID
        if base_id not in grouped:
            grouped[base_id] = []
        grouped[base_id].append((q_id, question))  # Append a tuple instead of two separate arguments
    return grouped
