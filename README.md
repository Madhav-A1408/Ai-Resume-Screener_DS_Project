# AI Resume Screener – Job Portal

A Naukri-style job portal built with **Django**, with an **AI-powered resume screening system** that automatically scores each candidate's resume against the job description on a **0–100 scale**.

Built as the final project for the **Data Science and AI** course at Scope India (2025–2026).

---

## Features

### For Candidates
- Sign up, log in and manage a personal profile
- Browse job openings and view job details
- Upload a resume and apply for jobs
- Track the status of applications

### For Recruiters
- Separate recruiter login and dashboard
- Post and manage job openings
- View all applicants for each job with their **resume match score (0–100)**
- Shortlist or reject candidates based on the score and move selected ones to interviews

### For Admin
- User management dashboard to view and manage all candidate and recruiter accounts

### Account Security
- Password reset via email

---

## How the Resume Scoring Works

When a candidate applies, the system compares the uploaded resume with the job description:

1. **Text extraction** – the resume text is read from the uploaded file.
2. **TF-IDF similarity (60%)** – both texts are converted to TF-IDF vectors and compared using cosine similarity, which measures how closely the resume's overall content matches the job description.
3. **Skill keyword matching (40%)** – the job's required skills are checked against the resume to see how many are present.
4. **Final score** – the two parts are combined (60/40 weighting) into a single score from **0 to 100**.

Recruiters see this score next to each applicant, so the best-matching candidates stand out immediately.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, Django Templates |
| Database | SQLite |
| Resume Scoring | TF-IDF, Cosine Similarity, Skill Keyword Matching |

---

## Project Structure

```
├── resume_screen_project/   # Django project settings and URLs
├── templates/               # HTML templates
├── media/                   # Uploaded files (not committed)
├── resumes/                 # Uploaded resumes (not committed)
├── manage.py
└── requirements.txt
```

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Madhav-A1408/Ai-Resume-Screener_DS_Project.git
cd Ai-Resume-Screener_DS_Project
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the project root:
```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Set up the database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run the server
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000 in your browser.

---

## Author

**Madhav A**
[LinkedIn](https://www.linkedin.com/in/madhav-a-/)