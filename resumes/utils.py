import os
def extract_text_from_file(fpath):
    text = ''
    ext = os.path.splitext(fpath)[1].lower()
    try:
        if ext == '.pdf':
            from pdfminer.high_level import extract_text
            text = extract_text(fpath) or ''
        elif ext in ('.docx',):
            from docx import Document
            doc = Document(fpath)
            text = '\n'.join(p.text for p in doc.paragraphs)
        else:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
    except Exception:
        text = ''
    return text
