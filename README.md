# AI Hiring Assistant

A full-stack web application designed to automate preliminary technical interviews. The system uses a generative AI backend to conduct conversational screening, evaluates candidate responses, and aggregates the data for recruiter analysis via a Power BI dashboard.

[Live Deployment](https://ai-hiring-assistant-l7l1.onrender.com/)

## System Architecture

The project is structured around a Python backend and a lightweight HTML/JS frontend, containerized for reliable deployment.

* **Backend:** FastAPI, Python 3.11
* **Database:** SQLite (managed via SQLAlchemy ORM)
* **AI Integration:** Google GenAI SDK (gemini-2.5-flash)
* **NLP / Processing:** TextBlob (for real-time sentiment analysis)
* **Frontend:** HTML, Vanilla JavaScript, CSS, Jinja2 Templates
* **Analytics:** Power BI 
* **Infrastructure:** Docker, deployed on Render

## Core Features

* **Stateful Interviews:** The system maintains session persistence. If a candidate reloads the page or loses connection, the interview resumes from the exact point of disruption.
* **Dynamic Technical Assessment:** The AI extracts the candidate's declared tech stack (e.g., Python, C++) and dynamically generates targeted follow-up questions.
* **Sentiment Tracking:** Candidate responses are parsed through TextBlob to evaluate tone and subjectivity, which is logged alongside their answers.
* **Analytics Integration:** Interview metadata (scores, sentiment, tech stacks) is stored in the database and formatted for ingestion into a custom Power BI dashboard for recruiter review.

## Local Development Setup

### Prerequisites
* Docker (recommended) or Python 3.11+
* A valid Google Gemini API Key

### 1. Clone the repository
```bash
git clone [https://github.com/ankushwadhwa05/Ai-Hiring-Assistant.git](https://github.com/ankushwadhwa05/Ai-Hiring-Assistant.git)
cd Ai-Hiring-Assistant
```

### 2. Environment Configuration
Create a `.env` file in the root directory. This file is ignored by version control.
```env
GEMINI_API_KEY="your_api_key_here"
```

### 3. Running the Application

**Option A: Using Docker (Recommended)**
This ensures the local environment perfectly mirrors production.
```bash
docker build -t ai-hiring-assistant .
docker run -p 8000:8000 --env-file .env ai-hiring-assistant
```

**Option B: Using Python Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The application will be accessible at `http://localhost:8000`.

## API Documentation
When running locally or in production, FastAPI automatically generates interactive API documentation. Navigate to `/docs` in your browser to view the endpoints and test the API directly via the Swagger UI.

## Deployment Notes
This application is configured for deployment on standard cloud platforms (e.g., Render, Railway) via the provided `Dockerfile`. Ensure that the `GEMINI_API_KEY` is added to the environment variables of your hosting provider. The application dynamically binds to the `$PORT` environment variable assigned by the host.
```

***

### How to use this:
1. Copy the text block above.
2. Open your `README.md` file and paste it in, replacing everything else.
3. Update the `[Live Deployment]` link at the top with your actual Render URL.
4. Run your standard `git add`, `commit`, and `push` to update the repository.
