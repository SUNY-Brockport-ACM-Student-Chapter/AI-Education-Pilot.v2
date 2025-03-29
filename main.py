import streamlit as st
from database.database import (get_ai_feedback, get_student_answers,
                               insert_ai_feedback, insert_student_answer, 
                               get_current_attempt, get_or_create_student, 
                               update_student_attempt, enter_student_waiver)
from utils import (get_feedback, get_or_create_chroma_collection,
                   get_relevant_content, load_questions_and_answers, group_question)
import time

@st.cache_resource
def initialize_resources(_questions_fp):
    intro, questions, answers = load_questions_and_answers(_questions_fp)
    return intro, questions, answers

def research_waiver(intro):
    if not st.session_state.get("intro_dismissed", False):
        st.write(intro)

        left, middle, right = st.columns(3)

        waiver_status = 0
        if left.button("Yes, I Agree", use_container_width=True):
            waiver_status = 1
            

        elif middle.button("No, I Do Not Agree", use_container_width=True):
            waiver_status = 2
           

        elif right.button("No, I Am Not Eligible", use_container_width=True):
            waiver_status = 3

        if waiver_status != 0:  # Only update state if a button was clicked
            st.session_state.waiver_status = waiver_status
            st.session_state.intro_dismissed = True
            enter_student_waiver(st.session_state.student_id, waiver_status)
            st.rerun()
           
           

    else:
        handle_waiver_response()

def handle_waiver_response():
    """Show exam or close message based on waiver status."""
    waiver_status = st.session_state.get("waiver_status")

    if waiver_status == 1:
        st.write("✅ You have agreed to the waiver.")

    elif waiver_status == 2:
        st.write("❌ You have declined the waiver. You may close this window.")
    
    elif waiver_status == 3:
        st.write("🚫 You are not eligible to participate. Please close this window.")

def get_waiver_status():
    """Retrieve the waiver status from session state or database."""
    if "waiver_status" in st.session_state:
        return st.session_state.waiver_status
    else:
        return 0 




def first_attempt_flow(collection, questions, answers, ai_client):

    if not st.session_state.get("waiver_status") == 1:
        st.error("You need to agree to the waiver to proceed.")
        return
    
    first_attempt_questions = {k: v for k, v in questions.items() if k not in ['6', '7', '8']}
    grouped_questions = group_question(first_attempt_questions)
    
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {q_id: "" for q_id in first_attempt_questions}
    if "feedbacks" not in st.session_state:
        st.session_state.feedbacks = {q_id: "" for q_id in first_attempt_questions}
    if "current_question_group" not in st.session_state:
        st.session_state.current_question_group = list(grouped_questions.keys())[0]
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    # Sidebar for question navigation
    with st.sidebar:
        st.title("Question Navigation")
        for group_id in grouped_questions:
            if st.button(f"Question {group_id}", key=f"nav_first_{group_id}"):
                st.session_state.current_question_group = group_id

    if not st.session_state.submitted:
        # Display current question group
        current_group = st.session_state.current_question_group
        st.markdown(f"<p class='big-font'>Question {current_group}</p>", unsafe_allow_html=True)
        
        with st.form(key=f"form_{current_group}"):
            for q_id, question in grouped_questions[current_group]:
                st.write(question)
                user_answer = st.text_area(
                    f"Your answer for {q_id}:",
                    value=st.session_state.user_answers[q_id],
                    key=f"answer_{q_id}",
                )
                if st.form_submit_button(f"Save Answer for {q_id}"):
                    st.session_state.user_answers[q_id] = user_answer
                    insert_student_answer(st.session_state.student_id, q_id, user_answer, attempt=1)
                    st.success("Your answered was saved!")
                    time.sleep(1)
                    st.rerun()
                   

        # Navigation buttons (outside the form)
        col1, col2 = st.columns(2)
        with col1:
            if list(grouped_questions.keys()).index(current_group) > 0:
                if st.button("Previous Question"):
                    current_index = list(grouped_questions.keys()).index(current_group)
                    if current_index > 0:
                        st.session_state.current_question_group = list(grouped_questions.keys())[current_index - 1]
                        st.rerun()
        with col2:
            if list(grouped_questions.keys()).index(current_group) < len(grouped_questions) - 1:
                if st.button("Next Question"):
                    current_index = list(grouped_questions.keys()).index(current_group)
                    if current_index < len(grouped_questions) - 1:
                        st.session_state.current_question_group = list(grouped_questions.keys())[current_index + 1]
                        st.rerun()

        # Submit all button
        if st.button("Submit Assessment"):
            st.session_state.submitted = True
            st.session_state.current_attempt = 2
            update_student_attempt(st.session_state.student_id, 2)
            st.success("All answers submitted. Generating AI feedback...")
            st.rerun()

    else:
        # Display all questions, answers, and generate feedback
        st.markdown("<h2 style='color: #215732;'>Submission Evaluation</h2>", unsafe_allow_html=True)

        for group_id, group_questions in grouped_questions.items():
            for q_id, question in group_questions:
                st.markdown(f"<p style='font-size: 20px; font-weight: bold; color: #00533E;'>Question {q_id}</p>", unsafe_allow_html=True)
                st.write(question)
                st.markdown("<p style='font-size: 18px; font-weight: bold; color: #00533E;'>Your Answer:</p>", unsafe_allow_html=True)
                st.write(st.session_state.user_answers[q_id])

                if st.session_state.user_answers[q_id].strip():
                    if not st.session_state.feedbacks[q_id]:
                        with st.spinner("Generating AI feedback..."):
                            relevant_content = get_relevant_content(
                                collection,
                                st.session_state.user_answers[q_id],
                                answers[q_id],
                                question,
                            )
                            feedback = get_feedback(
                                ai_client,
                                st.session_state.user_answers[q_id],
                                question,
                                relevant_content,
                                answers[q_id],
                            )
                            st.session_state.feedbacks[q_id] = feedback
                            insert_ai_feedback(st.session_state.student_id, feedback, q_id)

                    st.markdown("<p style='font-size: 18px; font-weight: bold; color: #00533E;'>AI Feedback:</p>", unsafe_allow_html=True)
                    st.write(st.session_state.feedbacks[q_id])
                else:
                    st.markdown("<p style='font-size: 18px; font-weight: bold; color: #00533E;'>AI Feedback:</p>", unsafe_allow_html=True)
                    st.write("No feedback generated for blank answer.")

                st.markdown("---")

        st.write("You have completed the first attempt. You can now close the window and return later for your second attempt, or start your second attempt now.")
        if st.button("Start Second Attempt"):
            for key in ["user_answers", "feedbacks", "current_question_group", "submitted"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
  
def second_attempt_flow(questions):
    # Include all questions for second attempt
    grouped_questions = group_question(questions)
    
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {q_id: "" for q_id in questions}
    if "current_question_group" not in st.session_state:
        st.session_state.current_question_group = list(grouped_questions.keys())[0]
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    st.write("This is your second assessment attempt, your submitted answers will be final.")

    # Sidebar for question navigation
    with st.sidebar:
        st.title("Question Navigation")
        for group_id_2 in grouped_questions:
            if st.button(f"Question {group_id_2}", key=f"nav_second_{group_id_2}"):
                st.session_state.current_question_group = group_id_2

    if not st.session_state.submitted:
        current_group = st.session_state.current_question_group
        st.markdown(f"<p class='big-font'>Question {current_group}</p>", unsafe_allow_html=True)
        
        with st.form(key=f"form_second_{current_group}"):
            for q_id, question in grouped_questions[current_group]:
                st.write(question)
                user_answer = st.text_area(
                    f"Your answer for {q_id}:",
                    value=st.session_state.user_answers[q_id],
                    key=f"second_attempt_{q_id}",
                )
                if st.form_submit_button(f"Save Answer for {q_id}"):
                    st.session_state.user_answers[q_id] = user_answer
                    insert_student_answer(st.session_state.student_id, q_id, user_answer, attempt=2)
                    st.success("Your answered was saved!")
                    time.sleep(1)
                    st.rerun()
                    

        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if list(grouped_questions.keys()).index(current_group) > 0:
                if st.button("Previous Question"):
                    current_index = list(grouped_questions.keys()).index(current_group)
                    if current_index > 0:
                        st.session_state.current_question_group = list(grouped_questions.keys())[current_index - 1]
                        st.rerun()
        with col2:
             if list(grouped_questions.keys()).index(current_group) < len(grouped_questions) - 1:
                 if st.button("Next Question"):
                    current_index = list(grouped_questions.keys()).index(current_group)
                    if current_index < len(grouped_questions) - 1:
                        st.session_state.current_question_group = list(grouped_questions.keys())[current_index + 1]
                        st.rerun()

        if st.button("Submit Assessment"):
            st.session_state.submitted = True
            st.session_state.current_attempt = 3
            update_student_attempt(st.session_state.student_id, 3)
            st.success("All answers for the second attempt have been submitted. You have completed the assessment.")
            st.rerun()
    else:
        st.write("You have completed both attempts of the assessment.")

def main(collection, questions_fp, ai_client):
    intro, questions, answers = initialize_resources(questions_fp)    

    # Brockport green color scheme
    st.markdown(
        """
    <style>
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
        color: #00533E;
    }
    .stButton>button {
        background-color: #00533E;
        color: white;
    }
    .stButton>button:hover {
        border-color: #00533E;
        color:#00533E;
        background-color: white; 
        transform: scale(1.05);
    }
    .stButton>button:active {
        background-color: #003D2A;
        color:#00533E;
        transform: scale(0.95); 
        transition: transform 0.1s; 
    }
    .stTextInput>div>div>input {
        border-color: #00533E;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Autism Spectrum Disorder (Part 1): An Overview for Educators")

    if "student_id" not in st.session_state:
        st.session_state.student_id = None
    if "current_attempt" not in st.session_state:
        st.session_state.current_attempt = None


    # Input for Banner ID
    if st.session_state.student_id is None:
        banner_id = st.text_input("Enter the last four digits of your Banner ID:")
        if st.button("Submit"):
            if banner_id and banner_id.isdigit() and len(banner_id) == 4:
                student_id, current_attempt, is_new_student = get_or_create_student(banner_id)
                st.session_state.student_id = student_id
                st.session_state.current_attempt = current_attempt
                if is_new_student:
                    st.success(f"New student record created. You are starting attempt 1.")
                    st.button("Start Test")
                    return
                else:
                    st.success(f"Returning student found. You are on attempt {current_attempt}.")
                    st.button("Start Test")
                    return
            else:   
                st.error("Please enter a valid 4-digit Banner ID.")
        return
    
    if st.session_state.current_attempt == 1:
        research_waiver(intro)  
        
    waiver_status = get_waiver_status()
    
    # Handle different attempts
    if st.session_state.current_attempt == 1 and waiver_status == 1:
        st.write("Current attempt: 1")
        st.markdown("<p class='instruction'>Be sure to save your answer before moving to the next question, or you will lose your progress. Answers will only be saved for this current active session, and they will only be submitted after you have clicked the 'Submit Assessment' button.</p>", unsafe_allow_html=True)
        first_attempt_flow(collection, questions, answers, ai_client)
    elif st.session_state.current_attempt == 2:
        if "submitted" in st.session_state and st.session_state.submitted:
            # If the first attempt was just submitted, show the feedback
            st.write("First attempt feedback:")
            first_attempt_flow(collection, questions, answers, ai_client)
        else:
            # Otherwise, start the second attempt
            st.write("Current attempt: 2")
            st.markdown("<p class='instruction'>Be sure to save your answer before moving to the next question, or you will lose your progress. Answers will only be saved for this current active session, and they will only be submitted after you have clicked the 'Submit Assessment' button.</p>", unsafe_allow_html=True)
            second_attempt_flow(questions)
    elif st.session_state.current_attempt == 3:
        st.write("You have completed both attempts of the assessment.")
        # Display a summary or final message here
        st.write("Thank you for completing the assessment. Your responses have been recorded.")