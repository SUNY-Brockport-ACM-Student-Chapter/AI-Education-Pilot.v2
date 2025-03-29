# Student Assessment Feedback System (Prototype for Brockport ACM Project)
<img width="1392" alt="Screenshot 2024-10-22 at 3 17 35 PM" src="https://github.com/user-attachments/assets/b9afa54f-78e0-4028-abb0-915074da6568">

## Description
This project is a Student Assessment Feedback System that uses AI to provide personalized feedback on student answers. It leverages OpenAI's GPT model and ChromaDB for efficient content storage and retrieval.

## Features
- Embeds and stores module content using ChromaDB
- Loads questions and answers from a JSON file
- Collects student answers through a Streamlit interface
- Generates AI-powered feedback based on student responses and relevant content

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/student-assessment-feedback-system.git
   cd student-assessment-feedback-system
   ```

2. Install the ODBC Driver: If you're on macOS, you need to install the ODBC driver to connect to Azure SQL Database. Run the following commands in your terminal:
   ```
   brew info unixodbc
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew update
   brew install msodbcsql18
   ```
3. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Set up your environment variables:
   Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   DB_USERNAME=your_db_usernmae
   DB_PASSWORD=your_db_password

   ```

## Usage

1. Prepare your module content:
   Place your PDF file in the appropriate directory and update the `module_content_fp` variable in the script.

2. Prepare your questions and answers:
   Create a JSON file with questions and answers, and update the `questions_fp` variable in the script.

3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

4. Open the provided URL in your web browser to access the Student Assessment Feedback System.

