from sqlalchemy import text, func

from database.models import (AIFeedback, Answer, Question, Session, Student,
                             StudentAnswer)


def insert_question(question_id, question):
    # Check if the question already exists
    session = Session()
    existing_question = (
        session.query(Question).filter_by(question_id=question_id).first()
    )
    if existing_question is None:
        new_question = Question(question_id=question_id, question=question)
        session.add(new_question)
        session.commit()
    else:
        print(f"Question with ID {question_id} already exists. Skipping insertion.")


def insert_answer(question_id, answer):
    session = Session()
    existing_answer = (
        session.query(Answer).filter_by(question_id=question_id, answer=answer).first()
    )
    if existing_answer is None:
        new_answer = Answer(question_id=question_id, answer=answer)
        session.add(new_answer)
        session.commit()
        print(f"Inserted answer: for question ID: {question_id}")
    else:
        print(
            f"Answer for question ID {question_id} already exists. Skipping insertion."
        )


def insert_student(banner_id):
    session = Session()
    new_student = Student(banner_id=banner_id)
    session.add(new_student)
    session.commit()
    student_id = new_student.id  # Get the generated student ID
    session.close()  # Close the session
    return student_id


def insert_student_answer(student_id, question_id, answer, attempt):
    session = Session()
    
    try:
        existing_student_answer = session.query(StudentAnswer).filter_by(question_id=question_id, student_id=student_id, attempt=attempt).first()
        if existing_student_answer:
            existing_student_answer.answer = answer
        else:
            new_student_answer = StudentAnswer(
                student_id=student_id, question_id=question_id, answer=answer, attempt=attempt
            )
            session.add(new_student_answer)
        session.commit()
    except Exception as e:
        print(f"Error inserting student answer: {e}")
    finally:
        session.close()

def get_student_answers(student_id):
    session = Session()
    answers = session.query(StudentAnswer).filter_by(student_id=student_id).all()
    session.close()
    return answers


def insert_ai_feedback(student_id, feedback, question_id):
    session = Session()
    try:
        new_feedback = AIFeedback(student_id=student_id, feedback=feedback, question_id=question_id)
        session.add(new_feedback)
        session.commit()
    except Exception as e:
        print(f"Error inserting AI feedback: {e}")
    finally:
        session.close()


def get_ai_feedback(student_id):
    session = Session()
    feedback = session.query(AIFeedback).filter_by(student_id=student_id).all()
    session.close()
    return feedback


def get_table_names():
    session = Session()
    # Use text() for the main query
    tables = session.execute(
        text(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';"
        )
    ).fetchall()

    table_columns = {}
    for table in tables:
        table_name = table[0]
        # Use text() for the column names query
        columns = session.execute(
            text(
                f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'"
            )
        ).fetchall()
        column_names = [column[0] for column in columns]
        table_columns[table_name] = column_names

    session.close()
    return table_columns

def get_current_attempt(student_id):
    session = Session()
    try:
        max_attempt = session.query(func.max(StudentAnswer.attempt)).filter(StudentAnswer.student_id == student_id).scalar()
        return max_attempt + 1 if max_attempt is not None else 1
    except Exception as e:
        print(f"Error getting current attempt: {e}")
        return 1
    finally:
        session.close()

def get_or_create_student(banner_id):
    session = Session()
    try:
        student = session.query(Student).filter_by(banner_id=banner_id).first()
        if student is None:
            new_student = Student(banner_id=banner_id, current_attempt=1)
            session.add(new_student)
            session.commit()
            return new_student.id, new_student.current_attempt, True
        return student.id, student.current_attempt, False
    finally:
        session.close()

def update_student_attempt(student_id, new_attempt):
    session = Session()
    try:
        student = session.query(Student).filter_by(id=student_id).first()
        if student:
            student.current_attempt = new_attempt
            session.commit()
    finally:
        session.close()

def enter_student_waiver(student_id, waiver_status):
    session = Session()
    try:
        student = session.query(Student).filter_by(id=student_id).first()
        if student:
            student.waiver_status = waiver_status
            session.commit()
    finally:
        session.close()

def retrieve_student_answers(student_id):
    session = Session()

    try:
        student = session.query(Student).filter_by(id=student_id).first()
        if student:
            results = (session.query(StudentAnswer.question_id, StudentAnswer.answer).filter_by(student_id=student_id).all())
            return {qid: text for qid, text in results}
    finally:
        session.close()

