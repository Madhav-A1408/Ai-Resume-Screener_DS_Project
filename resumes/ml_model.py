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
    Hybrid scoring:
      60% — skill keyword match (how many job skills appear in resume)
      40% — TF-IDF cosine similarity (general content overlap)
    Returns float 0..1
    """
    # ── Part 1: Skill match score (60% weight) ────────────────────────────
    job_skills = [s.strip().lower() for s in (job.skills or '').split(',') if s.strip()]
    
    if job_skills:
        rt = normalize_text(resume_text or '')
        matched = sum(1 for skill in job_skills if normalize_text(skill) in rt)
        skill_score = matched / len(job_skills)   # 0..1
    else:
        skill_score = 0.0

    # ── Part 2: TF-IDF cosine similarity (40% weight) ────────────────────
    job_text = normalize_text((job.title or '') + ' ' + (job.description or ''))
    rt = normalize_text(resume_text or '')

    if job_text and rt:
        vec = TfidfVectorizer().fit([job_text, rt])
        mat = vec.transform([job_text, rt])
        tfidf_score = float(cosine_similarity(mat[0], mat[1])[0, 0])
    else:
        tfidf_score = 0.0

    # ── Weighted combination ──────────────────────────────────────────────
    final = (0.6 * skill_score) + (0.4 * tfidf_score)
    return final


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
