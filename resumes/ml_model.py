# resumes/ml_model.py
import os, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = os.path.dirname(__file__)

# Expand skill keywords to improve recall
SKILL_KEYWORDS = [
    'python','django','flask','rest api','rest','api','sql','mysql','postgres',
    'numpy','pandas','scikit-learn','sklearn','tensorflow','pytorch','machine learning','ml',
    'react','javascript','js','html','css','aws','azure','docker','kubernetes','git',
    'nlp','computer vision','deep learning','data analysis','excel','tableau','powerbi'
]

def normalize_text(txt):
    if not txt:
        return ''
    txt = txt.lower()
    # remove punctuation but keep plus and dots
    txt = re.sub(r'[^\w\s\+\.\-]', ' ', txt)
    # collapse whitespace
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

def score_resume_for_job(resume_text, job):
    """
    Compute a TF-IDF cosine-similarity score between job (title+description)
    and resume_text. Returns float 0..1.
    """
    job_text = normalize_text((job.title or '') + ' ' + (job.description or ''))
    resume_text = normalize_text(resume_text or '')
    if not job_text or not resume_text:
        return 0.0

    vec = TfidfVectorizer().fit([job_text, resume_text])
    mat = vec.transform([job_text, resume_text])
    # cosine_similarity returns 2x2 matrix; we want similarity between row0 and row1
    sim = cosine_similarity(mat[0], mat[1])[0, 0]
    # sim already between 0..1
    return float(sim)

def get_matched_skills(resume_text, job):
    """
    Return list of skills present both in job description and resume_text.
    Use normalized substring matching + check for multi-word tokens (e.g. 'rest api').
    """
    jd = normalize_text((job.title or '') + ' ' + (job.description or ''))
    rt = normalize_text(resume_text or '')

    jd_skills = []
    for kw in SKILL_KEYWORDS:
        nk = normalize_text(kw)
        # find whole-word or substring matches (covers multi-word like "rest api")
        if nk and nk in jd:
            jd_skills.append(nk)

    matched = []
    for skill in jd_skills:
        if skill in rt:
            matched.append(skill)
    # Deduplicate & sort
    seen = []
    for s in matched:
        if s not in seen:
            seen.append(s)
    return seen
