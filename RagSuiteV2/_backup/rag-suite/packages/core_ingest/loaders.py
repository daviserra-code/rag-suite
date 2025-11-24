import io
from pypdf import PdfReader

def pdf_to_chunks(content: bytes, maxlen: int = 900):
    reader = PdfReader(io.BytesIO(content))
    chunks = []
    for pi, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text:
            continue
        text = " ".join(text.split())
        for i in range(0, len(text), maxlen):
            chunk = text[i:i+maxlen]
            chunks.append({"text": chunk, "page_from": pi, "page_to": pi})
    return chunks
