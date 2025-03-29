import os
import chromadb
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from database.database import get_table_names, insert_answer, insert_question
from utils import get_or_create_chroma_collection, load_questions_and_answers

# Set page configuration
st.set_page_config(
    page_title="Brockport Autism Assessment",
    page_icon="🦅",
    layout="wide")

load_dotenv()

# Initialize OpenAI client
ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY2"))

# Initialize ChromaDB persistent client
persistent_path = "Vector_Storage"
db_client = chromadb.PersistentClient(path=persistent_path)

# Define file paths
module_content_fp = "Test_Data/IRIS Autism Overview.pdf"
questions_fp = "questions_and_answers.json"

@st.cache_resource(show_spinner=False)
def initialize_database(questions_fp):
    if not st.session_state.get("db_initialized", False):
        os.system("python database/init_db.py")
        print("Database initialized")
        print("Tables:")
        print(get_table_names())
        
        intro, questions, answers = load_questions_and_answers(questions_fp)
        for question_id, question in questions.items():
            insert_question(question_id, question)
        for question_id, answer in answers.items():
            insert_answer(question_id, answer)
        
        st.session_state.db_initialized = True
    return True

# Initialize database
with st.spinner("Initializing system, please wait..."):
    db_initialized = initialize_database(questions_fp)

# Get or create Chroma collection
@st.cache_resource(show_spinner=False)
def get_collection(_db_client, module_content_fp, _ai_client):
    return get_or_create_chroma_collection(_db_client, module_content_fp, _ai_client)

with st.spinner("Initializing system, please wait..."):  
    collection = get_collection(db_client, module_content_fp, ai_client)

# Import and run the main function from main.py
from main import main

if __name__ == "__main__":
    main(collection, questions_fp, ai_client)